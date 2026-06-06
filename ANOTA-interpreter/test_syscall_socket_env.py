"""
test_syscall_socket_env.py

Test that ANOTA_SYSCALL signal helpers respect the ANOTA_SYSCALL_SOCKET
environment variable.
"""

import builtins
import os
import socket
import threading
import time
import sys

CUSTOM_SOCKET_PATH = "/tmp/custom_anota_syscall.sock"

class DummyMonitorServer:
    def __init__(self, path):
        self.path = path
        if os.path.exists(self.path):
            os.unlink(self.path)
        self._stop = threading.Event()
        self._commands = []
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(self.path)
        self._sock.listen(1)
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def start(self):
        self._thread.start()

    def close(self):
        self._stop.set()
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._sock.close()
        if os.path.exists(self.path):
            os.unlink(self.path)
        self._thread.join(timeout=1)

    def _serve(self):
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        self._commands.append(data.decode())
                    conn.sendall(b"OK\n")
            except OSError:
                break

def test_custom_socket_path():
    print(f"=== test_custom_socket_path (Target: {CUSTOM_SOCKET_PATH}) ===")
    os.environ["ANOTA_SYSCALL_SOCKET"] = CUSTOM_SOCKET_PATH
    
    server = DummyMonitorServer(CUSTOM_SOCKET_PATH)
    server.start()
    
    try:
        print("Calling ANOTA_SYSCALL_SIGNAL_START()...")
        builtins.ANOTA_SYSCALL_SIGNAL_START()
        time.sleep(0.1)
        
        if "START\n" in server._commands:
            print("Successfully connected to custom socket path!")
        else:
            print(f"FAILED: Commands received at {CUSTOM_SOCKET_PATH}: {server._commands}")
            raise AssertionError("Custom socket path not used")
            
    except OSError as e:
        print(f"Caught expected failure (if not implemented): {e}")
        raise e
    finally:
        server.close()
        if "ANOTA_SYSCALL_SOCKET" in os.environ:
            del os.environ["ANOTA_SYSCALL_SOCKET"]

if __name__ == "__main__":
    if os.name != "posix":
        print("Skip on non-posix")
        sys.exit(0)
        
    try:
        test_custom_socket_path()
        print("test_custom_socket_path: OK")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
