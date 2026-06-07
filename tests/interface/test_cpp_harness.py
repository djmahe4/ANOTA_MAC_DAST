import unittest
import os
import subprocess
import time
import socket
from interface.cpp_ebpf.harness import CPPHarness

class TestCPPHarness(unittest.TestCase):
    def test_uprobe_tracing(self):
        """
        Test that CPPHarness can attach a uprobe to a C++ binary and detect execution.
        """
        # Skip if monitor is not running or no permissions
        harness = CPPHarness()
        if not os.path.exists(harness.socket_path):
            self.skipTest(f"Syscall monitor socket {harness.socket_path} not found")
        
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(harness.socket_path)
        except PermissionError:
            self.skipTest("No permission to connect to syscall monitor socket")
        except Exception as e:
            self.skipTest(f"Syscall monitor unavailable: {e}")

        # 1. Ensure target is built
        target_path = os.path.abspath("tests/fixtures/simple_target")
        if not os.path.exists(target_path):
            subprocess.run(["g++", "-g", "tests/fixtures/simple_target.cpp", "-o", target_path], check=True)
            
        # 2. Run target with uprobe on 'target_function'
        res = subprocess.run(["nm", target_path], capture_output=True, text=True)
        symbol = None
        for line in res.stdout.splitlines():
            if "target_function" in line and " T " in line:
                symbol = line.split()[-1]
                break
        
        self.assertIsNotNone(symbol, "Could not find target_function symbol")
        
        print(f"Tracing symbol: {symbol}")
        
        events = harness.trace(target_path, symbols=[symbol], args=["test_message"])
        
        # 3. Verify event was captured
        self.assertTrue(any(e['symbol'] == symbol for e in events))

if __name__ == "__main__":
    unittest.main()
