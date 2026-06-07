import subprocess
import os
import re

class PHPProfiler:
    """
    Tactical playbook for identifying PHP entry points and profiling architecture.
    """
    def find_entry_points(self, root_dir):
        """
        Uses ripgrep to find signature footprints of PHP entry points AND performs a deep walk
        of all functional scripts in the repository.
        """
        root_dir = os.path.abspath(root_dir)
        candidates = set()
        
        # 1. Search for Signature Footprints (Fast Track)
        for pattern in ["vendor/autoload.php", r"Illuminate\\Http\\Kernel|AppKernel", r"define\("]:
            try:
                result = subprocess.run(
                    ["rg", "-l", pattern, root_dir],
                    capture_output=True, text=True, timeout=10
                )
                if result.stdout:
                    candidates.update([os.path.abspath(p) for p in result.stdout.splitlines()])
            except Exception:
                pass 
            
        # 2. Deep Walk: Identify all standalone PHP files that aren't purely configuration
        # This fixes the issue of missing sub-files like source/low.php
        for root, _, files in os.walk(root_dir):
            if "/." in root or "vendor" in root: continue
            for file in files:
                if file.endswith(".php"):
                    full_path = os.path.abspath(os.path.join(root, file))
                    # Skip common pure-config names or noise
                    if any(x in file.lower() for x in ["config", "version", "setup", "install"]):
                        continue
                    candidates.add(full_path)
            
        # Security: Jail check
        safe_entries = [p for p in candidates if p.startswith(root_dir)]
        return safe_entries

    def profile_architecture(self, file_path):
        """
        Uses head to fingerprint the PHP application architecture.
        """
        file_path = os.path.abspath(file_path)
        try:
            with open(file_path, "r") as f:
                head = "".join([f.readline() for _ in range(20)])
                
            if "autoload.php" in head:
                return "MVC"
            if "session_start()" in head and "<html>" in head.lower():
                return "Legacy Procedural"
            if "WP_USE_THEMES" in head:
                return "WordPress"
                
            return "Unknown"
        except Exception:
            return "Error"

    def get_dependencies(self, script_path):
        """
        Uses a PHP one-liner to list all included/required files in a script.
        """
        script_path = os.path.abspath(script_path)
        script_dir = os.path.dirname(script_path)
        try:
            # Change directory to script dir to resolve relative paths
            cmd = [
                "php", "-r", 
                f"chdir('{script_dir}'); include '{script_path}'; print_r(get_included_files());"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            # Basic parsing of print_r output
            files = re.findall(r'\[\d+\] => (.*)', result.stdout)
            
            # Fallback: Static analysis if PHP fails or returns empty
            if not files:
                with open(script_path, "r") as f:
                    content = f.read()
                # Find common patterns like require_once('../path')
                static_matches = re.findall(r"(?:include|require)(?:_once)?\s*\(['\"](.*?)['\"]\)", content)
                for sm in static_matches:
                    dep_path = os.path.abspath(os.path.join(script_dir, sm))
                    if os.path.exists(dep_path):
                        files.append(dep_path)

            return [os.path.abspath(f.strip()) for f in files]
        except Exception:
            return []

    def strip_noise(self, file_path):
        """
        Uses php -w to strip comments and whitespaces.
        """
        file_path = os.path.abspath(file_path)
        try:
            # Note: subprocess.run with a list is safe from shell injection
            result = subprocess.run(
                ["php", "-w", file_path],
                capture_output=True, text=True, check=True, timeout=5
            )
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback: simple regex based stripping if php is not available
            with open(file_path, "r") as f:
                content = f.read()
            return re.sub(r'//.*|/\*.*?\*/', '', content, flags=re.DOTALL)
