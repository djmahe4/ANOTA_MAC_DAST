"""
test_taint_syscall_integration.py

Verify that tainted objects reaching syscalls are detected by ANOTA_SYSCALL.
"""

import builtins
import os
import sys

def get_anota_taint():
    return builtins.ANOTA_TAINT

def test_tainted_path_open():
    print("=== test_tainted_path_open ===")
    taint = get_anota_taint()
    
    # Create a tainted path
    path = "/tmp/tainted_file.txt"
    taint(path)
    
    print(f"Opening tainted path: {path}")
    # This should trigger a violation in ANOTA_SYSCALL (logged to stderr)
    try:
        with open(path, "w") as f:
            f.write("test")
    except Exception as e:
        print(f"Caught exception (not expected to raise by default): {e}")
    
    print("Check stderr for 'tainted target object reached syscall' violation.")

if __name__ == "__main__":
    test_tainted_path_open()
