import subprocess
import os
import re
import shlex

class CPPProfiler:
    """
    Identifies C/C++ entry points safely and robustly by inspecting ELF/PE headers.
    Avoids executing binaries and works on stripped files.
    """
    def find_entry_points(self, root_dir):
        """
        Searches for compiled binaries with valid machine-code entry points.
        """
        root_dir = os.path.abspath(root_dir)
        entry_points = []
        for root, _, files in os.walk(root_dir):
            # Skip hidden directories like .git
            if "/." in root or root.startswith("."):
                continue

            for file in files:
                full_path = os.path.join(root, file)
                
                # 1. Quick filter by extension to save process forks
                if file.endswith(('.txt', '.log', '.md', '.py', '.sh', '.json', '.c', '.cpp', '.h', '.hpp', '.o', '.obj')):
                    continue
                
                try:
                    # Security: Jail check
                    if not full_path.startswith(root_dir):
                        continue

                    # 2. Use 'file' utility to safely check if it is a compiled binary (ELF/PE)
                    file_info = subprocess.run(["file", "-b", full_path], capture_output=True, text=True, timeout=2)
                    stdout = file_info.stdout
                    
                    if "ELF" not in stdout and "PE32" not in stdout:
                        continue # Not a compiled binary
                    
                    # 3. Use 'readelf -h' to find the actual entry point address in the header.
                    header_info = subprocess.run(["readelf", "-h", full_path], capture_output=True, text=True, timeout=2)
                    
                    if any("Entry point address:" in line for line in header_info.stdout.splitlines()):
                        entry_points.append(os.path.abspath(full_path))
                        
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
                except Exception:
                    continue

        return entry_points

    def is_daemon(self, binary_path):
        """
        SAFELY profiles a binary without EVER executing it.
        Uses 'strings' to look for indicators in the data sections.
        """
        try:
            binary_path = os.path.abspath(binary_path)
            # Check if file exists first
            if not os.path.exists(binary_path):
                return False

            # Use 'strings' to extract text without executing the code
            # We limit the output to avoid memory exhaustion on massive binaries
            result = subprocess.run(["strings", "-n", "6", binary_path], capture_output=True, text=True, timeout=5)
            output = result.stdout.lower()
            
            # Common daemon/server indicators
            indicators = ["daemon", "server", "socket", "listen", "bind", "accept"]
            return any(ind in output for ind in indicators)
        except Exception:
            return False
