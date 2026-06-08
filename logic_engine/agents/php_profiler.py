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
        # Exclude library and internal directories from the search (Recursive)
        exclude_dirs = ["vendor", "includes", "source", "logic", "tests", "DBMS", "database", "DBMS", "help"]
        rg_excludes = []
        for d in exclude_dirs:
            rg_excludes.extend(["--glob", f"!**/{d}/*"])

        for pattern in ["vendor/autoload.php", r"Illuminate\\Http\\Kernel|AppKernel", r"define\("]:
            try:
                cmd = ["rg", "-l"] + rg_excludes + [pattern, root_dir]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.stdout:
                    candidates.update([os.path.abspath(p) for p in result.stdout.splitlines()])
            except Exception:
                pass 
            
        # 2. Deep Walk: Identify standalone PHP files, respecting recursive exclusions
        for root, dirs, files in os.walk(root_dir):
            # Prune directories: if any part of the path is in exclude_dirs
            path_parts = root.split(os.sep)
            if any(d in path_parts for d in exclude_dirs):
                continue
            if "/." in root: continue
            
            for file in files:
                if file.endswith(".php"):
                    full_path = os.path.abspath(os.path.join(root, file))
                    
                    # Target-agnostic heuristics for entry points:
                    # 1. Common entry point filenames
                    common_entry_names = ["index.php", "api.php", "main.php", "login.php", "setup.php"]
                    
                    # 2. Files that handle global request data (High signal)
                    # We check the first 500 chars for $_GET, $_POST, etc.
                    handles_request = False
                    try:
                        with open(full_path, "r") as f:
                            head = f.read(1000)
                            if any(x in head for x in ["$_GET", "$_POST", "$_REQUEST", "$_COOKIE"]):
                                handles_request = True
                    except Exception:
                        pass
                        
                    if file in common_entry_names or handles_request:
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

    def get_logic_source_files(self, entry_point_path):
        """
        Heuristic: Find files in 'source/' or 'includes/' subdirectories 
        that likely contain the core business logic for this entry point.
        """
        entry_dir = os.path.dirname(entry_point_path)
        logic_files = []
        for sub in ["source", "includes", "logic"]:
            sub_dir = os.path.join(entry_dir, sub)
            if os.path.exists(sub_dir) and os.path.isdir(sub_dir):
                for f in os.listdir(sub_dir):
                    if f.endswith(".php"):
                        logic_files.append(os.path.abspath(os.path.join(sub_dir, f)))
        return logic_files

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
