import subprocess
import os
import json
import re
import tempfile
import shlex
from .coverage_parser import PHPXdebugParser

class PHPRunner:
    """
    Executes PHP scripts with Xdebug instrumentation and extracts telemetry data.
    """
    def __init__(self, php_bin="php"):
        self.php_bin = php_bin
        self.parser = PHPXdebugParser()
        self.instrument_script = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "instrument.php"
        ))

    def run(self, script_path, args=None, env=None, params=None):
        """
        Runs a PHP script and returns the parsed telemetry.
        Supports passing parameters via env vars that instrument.php can pick up.
        """
        script_path = os.path.abspath(script_path)
        if not os.path.exists(script_path):
            return {"error": f"Script not found: {script_path}"}

        if args is None:
            args = []
        
        # Use a temporary file for telemetry to avoid stdout pollution
        fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="anota_telemetry_")
        os.close(fd)

        # Merge custom env if provided
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        
        run_env["ANOTA_TELEMETRY_TARGET"] = temp_path
        
        # If params provided, pass them via JSON env var
        if params:
            run_env["ANOTA_REQUEST_PARAMS"] = json.dumps(params)

        # Command to run PHP with auto-prepend and explicit include_path
        script_dir = os.path.dirname(script_path)
        cmd = [
            self.php_bin,
            "-d", f"auto_prepend_file={self.instrument_script}",
            "-d", f"include_path=.:{script_dir}",
            "-d", "xdebug.mode=coverage",
            script_path
        ] + args
        
        # Ensure authentication is disabled and use SQLite for mobility
        run_env["DISABLE_AUTHENTICATION"] = "1"
        run_env["SQLI_DB"] = "sqlite"
        run_env["DBMS"] = "sqlite" # Try to bypass the MySQL block

        try:
            # Security: subprocess.run with list is safe
            # We change CWD to the script's directory so relative includes work!
            script_dir = os.path.dirname(script_path)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=run_env,
                cwd=script_dir,
                timeout=10 # Reduced timeout for faster iteration
            )
            
            if result.stderr:
                print(f" [PHP DEBUG] Stderr: {result.stderr}")
            
            # Try reading from file first
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                with open(temp_path, "r") as f:
                    try:
                        raw_telemetry = json.load(f)
                        return self._process_raw_telemetry(raw_telemetry)
                    except json.JSONDecodeError:
                        pass # Fallback to stdout parsing
            
            # Fallback to stdout parsing
            return self._extract_telemetry_from_stdout(result.stdout)
            
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out after 300s"}
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _process_raw_telemetry(self, raw_telemetry):
        """
        Processes the raw dictionary from PHP into the final telemetry format.
        """
        coverage_data = self.parser.parse_raw_data(raw_telemetry.get("coverage", {}))
        coverage_data["state"] = raw_telemetry.get("state", {})
        return coverage_data

    def _extract_telemetry_from_stdout(self, output):
        """
        Extracts the JSON telemetry block from the raw PHP output (fallback).
        """
        pattern = r"---ANOTA_TELEMETRY_START---\n(.*?)\n---ANOTA_TELEMETRY_END---"
        match = re.search(pattern, output, re.DOTALL)
        
        if not match:
            return {"type": "telemetry", "files": {}, "state": {}, "error": "No telemetry found"}

        try:
            raw_telemetry = json.loads(match.group(1))
            return self._process_raw_telemetry(raw_telemetry)
        except json.JSONDecodeError:
            return {"type": "telemetry", "error": "Failed to decode telemetry JSON"}
