import subprocess
import os
import re

class PHPProfiler:
    """
    Tactical playbook for identifying PHP entry points and profiling architecture.
    """
    def find_entry_points(self, root_dir):
        """
        Uses ripgrep to find signature footprints of PHP entry points.
        """
        entry_points = set()
        
        # 1. Search for Composer Autoloader
        try:
            result = subprocess.run(
                ["rg", "-l", "vendor/autoload.php", root_dir],
                capture_output=True, text=True
            )
            if result.stdout:
                entry_points.update([os.path.abspath(p) for p in result.stdout.splitlines()])
        except FileNotFoundError:
            pass # rg not installed
            
        # 2. Search for Framework Kernels
        try:
            result = subprocess.run(
                ["rg", "-l", r"Illuminate\\Http\\Kernel|AppKernel", root_dir],
                capture_output=True, text=True
            )
            if result.stdout:
                entry_points.update([os.path.abspath(p) for p in result.stdout.splitlines()])
        except FileNotFoundError:
            pass

        # 3. Search for Global Security Constants (define)
        try:
            result = subprocess.run(
                ["rg", "-l", r"define\(", "--max-depth", "2", root_dir],
                capture_output=True, text=True
            )
            if result.stdout:
                # Basic heuristic: if it defines something, it's likely an entry point
                entry_points.update([os.path.abspath(p) for p in result.stdout.splitlines()])
        except FileNotFoundError:
            pass
            
        return list(entry_points)

    def profile_architecture(self, file_path):
        """
        Uses head to fingerprint the PHP application architecture.
        """
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

    def strip_noise(self, file_path):
        """
        Uses php -w to strip comments and whitespaces.
        """
        try:
            result = subprocess.run(
                ["php", "-w", file_path],
                capture_output=True, text=True, check=True
            )
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: simple regex based stripping if php is not available
            with open(file_path, "r") as f:
                content = f.read()
            # This is a very basic fallback
            return re.sub(r'//.*|/\*.*?\*/', '', content, flags=re.DOTALL)
