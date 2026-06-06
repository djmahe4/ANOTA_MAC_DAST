"""
test_watch_address_reuse.py

Prove the address reuse bug in ANOTA_WATCH.
If an object is watched, then deleted, and a new object is created at the same address,
the new object should NOT be watched by the old policy.
"""

import builtins
import os
import sys
import gc

def get_anota_watch():
    if not hasattr(builtins, "ANOTA_WATCH"):
        raise RuntimeError("ANOTA_WATCH builtin is not available")
    return builtins.ANOTA_WATCH

def test_address_reuse():
    print("=== test_address_reuse ===")
    watch = get_anota_watch()
    
    # 1. Create an object and watch it.
    obj1 = [1, 2, 3]
    addr1 = id(obj1)
    print(f"Created obj1 at {addr1}")
    
    # Block reading obj1
    watch.BLOCK(obj1, "R")
    
    # Verify it's blocked
    try:
        x = obj1[0]
        raise AssertionError("obj1 read should be blocked")
    except RuntimeError:
        print("obj1 read successfully blocked")
    
    # 2. Delete obj1 and force collection.
    del obj1
    gc.collect()
    print("Deleted obj1")
    
    # 3. Try to create a new object at the same address.
    # We might need to try a few times or use a specific type.
    found_reuse = False
    for i in range(1000):
        obj2 = [4, 5, 6]
        if id(obj2) == addr1:
            found_reuse = True
            print(f"SUCCESS: Found address reuse at {addr1} after {i} attempts")
            
            # 4. Check if obj2 is incorrectly blocked.
            print("Checking if obj2 is blocked (it SHOULD NOT be)...")
            try:
                x = obj2[0]
                print("obj2 read is allowed (Correct behavior - address reuse handled or not occurred)")
            except RuntimeError:
                print("obj2 read is BLOCKED (BUG: Address reuse not handled!)")
                raise AssertionError("BUG: New object at old address inherited the policy")
            break
            
    if not found_reuse:
        print("Could not reproduce address reuse in 1000 attempts.")

if __name__ == "__main__":
    try:
        test_address_reuse()
        print("test_address_reuse: OK")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
