import unittest
import os
import subprocess
import time
from interface.cpp_ebpf.harness import CPPHarness

class TestCPPHarness(unittest.TestCase):
    def test_uprobe_tracing(self):
        """
        Test that CPPHarness can attach a uprobe to a C++ binary and detect execution.
        """
        # 1. Ensure target is built
        target_path = os.path.abspath("tests/fixtures/simple_target")
        if not os.path.exists(target_path):
            subprocess.run(["g++", "-g", "tests/fixtures/simple_target.cpp", "-o", target_path], check=True)
            
        harness = CPPHarness()
        
        # 2. Run target with uprobe on 'target_function'
        # We need the symbol name. For C++ it might be mangled, but here it's extern "C" or we use the mangled name.
        # Actually in my simple_target.cpp it's just void target_function(const char*).
        # Let's check the symbol name.
        res = subprocess.run(["nm", target_path], capture_output=True, text=True)
        symbol = None
        for line in res.stdout.splitlines():
            if "target_function" in line and " T " in line:
                symbol = line.split()[-1]
                break
        
        self.assertIsNotNone(symbol, "Could not find target_function symbol")
        
        print(f"Tracing symbol: {symbol}")
        
        # This will start the Rust monitor in the background (with SKIP_EBPF if needed for CI, but here we want real tests)
        # For the test, we'll assume the monitor is already running or we start a mock.
        # Actually, let's use a mock for the monitor in this test to verify the harness logic.
        
        events = harness.trace(target_path, symbols=[symbol], args=["test_message"])
        
        # 3. Verify event was captured
        # In a real environment, we'd check eBPF logs. 
        # For TDD, we'll implement the harness to return a list of hit symbols.
        self.assertTrue(any(e['symbol'] == symbol for e in events))

if __name__ == "__main__":
    unittest.main()
