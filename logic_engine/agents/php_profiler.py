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
        root_dir = os.path.abspath(root_dir)
        entry_points = set()
        
        # 1. Search for Composer Autoloader
        try:
            result = subprocess.run(
                ["rg", "-l", "vendor/autoload.php", root_dir],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                entry_points.update([os.path.abspath(p) for p in result.stdout.splitlines()])
        except Exception:
            pass 
            
        # 2. Search for Framework Kernels
        try:
            result = subprocess.run(
                ["rg", "-l", r"Illuminate\\Http\\Kernel|AppKernel", root_dir],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                entry_points.update([os.path.abspath(p) for p in result.stdout.splitlines()])
        except Exception:
            pass

        # 3. Search for Global Security Constants (define)
        try:
            result = subprocess.run(
                ["rg", "-l", r"define\(", "--max-depth", "2", root_dir],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                entry_points.update([os.path.abspath(p) for p in result.stdout.splitlines()])
        except Exception:
            pass
            
        # Security: Jail check - ensure all entries are within root_dir
        safe_entries = [p for p in entry_points if p.startswith(root_dir)]
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
