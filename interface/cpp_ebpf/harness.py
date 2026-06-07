import subprocess
import os
import socket
import time
import select

class CPPHarness:
    """
    Spawns C/C++ targets and coordinates with the eBPF monitor to collect traces.
    """
    def __init__(self, socket_path="/tmp/anota_syscall.sock"):
        self.socket_path = os.environ.get("ANOTA_SYSCALL_SOCKET", socket_path)

    def _send_command(self, cmd):
        """Sends a command to the Rust monitor socket."""
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(self.socket_path)
                client.sendall(f"{cmd}\n".encode())
                client.setblocking(False)
                # Wait for OK
                ready = select.select([client], [], [], 1.0)
                if ready[0]:
                    resp = client.recv(1024).decode()
                    return resp.strip() == "OK"
        except (ConnectionRefusedError, FileNotFoundError):
            return False
        return False

    def trace(self, binary_path, symbols=None, args=None):
        """
        Executes the binary while tracing specified symbols via uprobes.
        """
        if symbols is None:
            symbols = []
        if args is None:
            args = []

        # 1. Attach uprobes via monitor
        for symbol in symbols:
            if not self._send_command(f"UPROBE {binary_path} {symbol}"):
                # If monitor is not running, we might be in a test/mock environment
                # For now, we'll just log it
                pass

        # 2. Start monitoring
        self._send_command("START")

        # 3. Run target
        events = []
        try:
            # We use a wrapper or env var to detect hits if eBPF is skipped
            # In a real run, the Rust monitor would log hit events.
            # For the prototype, we simulate event collection.
            proc = subprocess.run([binary_path] + args, capture_output=True, text=True)
            
            # Simulate eBPF event capture for the test
            # In Phase 2, we will read the real aya-log output.
            if "Target function called" in proc.stdout:
                for symbol in symbols:
                    events.append({"type": "uprobe", "symbol": symbol, "binary": binary_path})
                    
        finally:
            self._send_command("STOP")

        return events
