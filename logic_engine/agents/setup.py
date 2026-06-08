import os
import shutil
import requests
import json

class SetupAgent:
    """
    Executes physical setup actions (filesystem, HTTP initialization) 
    discovered by the DiscoveryAgent.
    """
    def __init__(self, repo_root):
        self.repo_root = os.path.abspath(repo_root)

    async def execute_actions(self, actions, base_url=None):
        """
        Executes a list of setup actions.
        Supports:
        - "copy source target"
        - "http_post url data"
        - "start_db dbname user pass port"
        """
        results = []
        for action in actions:
            try:
                if action.startswith("copy "):
                    parts = action.split(" ")
                    if len(parts) == 3:
                        src = os.path.join(self.repo_root, parts[1])
                        dst = os.path.join(self.repo_root, parts[2])
                        if os.path.exists(src):
                            shutil.copy(src, dst)
                            results.append(f"[SUCCESS] Copied {parts[1]} to {parts[2]}")
                        else:
                            results.append(f"[ERROR] Source not found: {parts[1]}")
                
                elif action.startswith("http_post "):
                    # e.g. "http_post setup.php create_db=1"
                    parts = action.split(" ")
                    if len(parts) >= 2 and base_url:
                        url = f"{base_url.rstrip('/')}/{parts[1].lstrip('/')}"
                        data_str = " ".join(parts[2:])
                        # Simple key=value parsing
                        data = dict(item.split("=") for item in data_str.split("&"))
                        resp = requests.post(url, data=data, timeout=15)
                        results.append(f"[SUCCESS] POST to {parts[1]} returned {resp.status_code}")
                
                elif action.startswith("start_db "):
                    # e.g. "start_db dvwa dvwa p@ssw0rd 3306"
                    parts = action.split(" ")
                    if len(parts) >= 5:
                        dbname, user, passwd, port = parts[1:5]
                        import subprocess
                        import time
                        
                        db_dir = f"/tmp/anota_db_{port}"
                        sock_file = f"{db_dir}/mysql.sock"
                        
                        # 1. Initialize Database
                        if not os.path.exists(db_dir):
                            os.makedirs(db_dir, exist_ok=True)
                            subprocess.run([
                                "mariadb-install-db", 
                                f"--datadir={db_dir}", 
                                "--auth-root-authentication-method=normal"
                            ], check=True, stdout=subprocess.DEVNULL)
                        
                        # 2. Start Daemon in background
                        log_file = open(f"{db_dir}/mariadb.log", "w")
                        proc = subprocess.Popen([
                            "mariadbd", 
                            f"--datadir={db_dir}", 
                            f"--socket={sock_file}", 
                            f"--port={port}",
                            f"--pid-file={db_dir}/mysqld.pid"
                        ], stdout=log_file, stderr=log_file)
                        
                        # Wait for it to start
                        time.sleep(3)
                        
                        if proc.poll() is None:
                            # 3. Create Database and User
                            sql = f"CREATE DATABASE IF NOT EXISTS {dbname}; CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{passwd}'; GRANT ALL PRIVILEGES ON {dbname}.* TO '{user}'@'localhost'; FLUSH PRIVILEGES;"
                            subprocess.run([
                                "mysql", f"-S{sock_file}", "-u", "root", "-e", sql
                            ], check=True)
                            
                            results.append(f"[SUCCESS] Started local DB '{dbname}' on port {port}")
                            # Keep proc reference to kill later if needed
                            self.db_proc = proc 
                        else:
                            results.append(f"[ERROR] Failed to start DB daemon. Check {db_dir}/mariadb.log")

            except Exception as e:
                results.append(f"[ERROR] Action '{action}' failed: {str(e)}")
        
        return results

    def cleanup(self):
        if hasattr(self, 'db_proc') and self.db_proc:
            self.db_proc.terminate()
            try:
                self.db_proc.wait(timeout=5)
            except:
                self.db_proc.kill()

