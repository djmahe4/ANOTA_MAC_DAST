import subprocess
import os
import json
import re
import tempfile
import time
import requests
from .coverage_parser import PHPXdebugParser

class PHPRunner:
    """
    Executes PHP scripts with Xdebug instrumentation and extracts telemetry data.
    Supports both CLI and HTTP execution modes.
    """
    def __init__(self, php_bin="php", host="127.0.0.1", port=8001):
        self.php_bin = php_bin
        self.parser = PHPXdebugParser()
        self.instrument_script = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "instrument.php"
        ))
        self.host = host
        self.port = port
        self.server_proc = None
        self.session = requests.Session()

    def start_server(self, repo_root, env=None):
        if self.server_proc:
            self.stop_server()
        repo_root = os.path.abspath(repo_root)
        
        # 1. Create a custom router to force logic overrides without file edits
        router_content = f"""<?php
require_once '{self.instrument_script}';

// Resolve the actual script
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
error_log("[ROUTER DEBUG] REQUEST_URI: " . $_SERVER['REQUEST_URI']);
error_log("[ROUTER DEBUG] URI: " . $uri);
error_log("[ROUTER DEBUG] SCRIPT_FILENAME: " . (isset($_SERVER['SCRIPT_FILENAME']) ? $_SERVER['SCRIPT_FILENAME'] : 'NOT SET'));
error_log("[ROUTER DEBUG] PHP_SELF: " . (isset($_SERVER['PHP_SELF']) ? $_SERVER['PHP_SELF'] : 'NOT SET'));

$file = '{repo_root}' . $uri;

error_log("[ROUTER DEBUG] Constructed file path: " . $file);

if (is_file($file) && strpos($file, '.php') !== false) {{
    chdir(dirname($file)); // Fix relative path resolution
    require $file;
}} else {{
    return false; // Let built-in server handle static files
}}
?>
"""
        self.router_file = f"/tmp/anota_router_{int(time.time())}.php"
        with open(self.router_file, "w") as f:
            f.write(router_content)

        # 2. Start server using the router
        cmd = [
            self.php_bin, 
            "-d", "xdebug.mode=coverage",
            "-d", "display_errors=0",
            "-d", "log_errors=1",
            "-d", "error_log=/home/kali/.gemini/tmp/mac-blm-dast/anota_php_error.log",
            "-S", f"{self.host}:{self.port}",
            self.router_file
        ]
        
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
            
        log_path = "/tmp/anota_php_server.log"
        with open(log_path, "w") as f:
            self.server_proc = subprocess.Popen(cmd, stdout=f, stderr=f, cwd=repo_root, env=run_env)
        print(f" [*] Started PHP Web Server on http://{self.host}:{self.port} with env: {env}")
        time.sleep(2)

    def stop_server(self):
        if self.server_proc:
            self.server_proc.terminate()
            self.server_proc.wait()
            self.server_proc = None
            print(" [*] Stopped PHP Web Server.")

    def run(self, script_path, args=None, env=None, params=None, repo_root=None, use_http=False, session=None):
        if use_http:
            # If server env changed, restart it
            if not self.server_proc or (env and env != getattr(self, '_last_env', None)):
                self.start_server(repo_root, env=env)
                self._last_env = env
            return self.run_http(script_path, params, repo_root, session_cookies=session, env=env)
        return self.run_cli(script_path, args, env, params, repo_root)

    def run_http(self, script_path, params=None, repo_root=None, session_cookies=None, env=None):
        if not self.server_proc:
            self.start_server(repo_root)
        rel_path = os.path.relpath(script_path, repo_root)
        url = f"http://{self.host}:{self.port}/{rel_path}"
        temp_telemetry = f"/tmp/anota_http_{int(time.time()*1000)}.json"
        
        method = "POST" if params and "POST" in params else "GET"
        data = params.get("POST") if params else None
        query = params.get("GET") if params else {}
        
        if session_cookies:
            self.session.cookies.update(session_cookies)
            
        try:
            headers = {
                "X-ANOTA-TELEMETRY-TARGET": temp_telemetry
            }
            
            # Use params directly as the payload, falling back to legacy env if needed
            request_payload = params or {}
            if env and "ENV" not in request_payload:
                request_payload["ENV"] = env

            headers["X-ANOTA-REQUEST-PARAMS"] = json.dumps(request_payload)

            cookies = params.get("COOKIE", {}) if params else {}
            
            response = self.session.request(
                method, url, 
                params=query, 
                data=data, 
                cookies=cookies, 
                headers=headers, 
                timeout=10
            )
            print(f" [PHP RUNNER] HTTP {method} {url} -> Status {response.status_code}")
            
            # Wait for telemetry file (Robust read)
            raw = None
            for _ in range(30):
                if os.path.exists(temp_telemetry) and os.path.getsize(temp_telemetry) > 0:
                    try:
                        with open(temp_telemetry, "r") as f:
                            raw = json.load(f)
                        break
                    except json.JSONDecodeError:
                        pass # Wait and retry
                time.sleep(0.1)
                
            if raw:
                os.unlink(temp_telemetry)
                return self._process_raw_telemetry(raw), self.session.cookies.get_dict()
            return {"error": "HTTP execution succeeded but no valid telemetry generated."}, self.session.cookies.get_dict()
        except Exception as e:
            return {"error": str(e)}, self.session.cookies.get_dict()

    def _get_include_path(self, script_path, repo_root):
        script_dir = os.path.dirname(script_path)
        paths = ["."]
        if script_dir: paths.append(script_dir)
        if repo_root:
            abs_root = os.path.abspath(repo_root)
            if abs_root not in paths:
                paths.append(abs_root)
        return ":".join(paths)

    def run_cli(self, script_path, args=None, env=None, params=None, repo_root=None):
        script_path = os.path.abspath(script_path)
        if not os.path.exists(script_path): return {"error": f"Not found: {script_path}"}, {}
        
        temp_path = f"/tmp/anota_cli_{int(time.time()*1000)}.json"
        run_env = os.environ.copy()
        if env: run_env.update(env)
        run_env.update({"ANOTA_TELEMETRY_TARGET": temp_path})
        if params: run_env["ANOTA_REQUEST_PARAMS"] = json.dumps(params)
        
        inc = self._get_include_path(script_path, repo_root)
        cmd = [
            self.php_bin, 
            "-d", f"auto_prepend_file={self.instrument_script}", 
            "-d", f"include_path={inc}", 
            "-d", "xdebug.mode=coverage", 
            script_path
        ] + (args or [])
        
        try:
            print(f" [PHP RUNNER] Executing CLI: {' '.join(cmd)}")
            subprocess.run(cmd, capture_output=True, text=True, env=run_env, cwd=os.path.dirname(script_path), timeout=15)
            
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                with open(temp_path, "r") as f:
                    raw = json.load(f)
                os.unlink(temp_path)
                return self._process_raw_telemetry(raw), {}
            return {"error": "No telemetry generated (CLI)"}, {}
        except Exception as e:
            return {"error": str(e)}, {}

    def _process_raw_telemetry(self, raw_telemetry):
        coverage_data = self.parser.parse_raw_data(raw_telemetry.get("coverage", {}))
        coverage_data["state"] = raw_telemetry.get("state", {})
        return coverage_data
