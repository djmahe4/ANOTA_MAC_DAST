"""
test_taint_address_reuse.py

Reproduce address reuse bug in ANOTA_TAINT.
"""

import builtins
import gc
import sys

def get_anota_taint():
    return builtins.ANOTA_TAINT

def is_tainted(obj):
    # Register a sink to check
    get_anota_taint()("dummy", Sink=[print])
    try:
        # Use print as sink
        print(obj)
        return False
    except RuntimeError:
        return True

def log(msg):
    sys.stderr.write(str(msg) + "\n")

def test_address_reuse():
    log("=== test_address_reuse ===")
    taint = get_anota_taint()
    builtins.ANOTA_TAINT_CLEAR()
    
    # 1. Create a string and taint it.
    s1 = "very-specific-secret-string-12345"
    taint(s1)
    addr1 = id(s1)
    log(f"Created s1 at {addr1}, tainted: {is_tainted(s1)}")
    
    # 2. Delete s1 and force GC.
    del s1
    gc.collect()
    log("Deleted s1")
    
    # 3. Try to get a new string at the same address.
    found_reuse = False
    for i in range(10000):
        # We need something that's likely to reuse the exact same memory block
        s2 = f"other-string-{i:05d}"
        if id(s2) == addr1:
            found_reuse = True
            log(f"SUCCESS: Found address reuse at {addr1} after {i} attempts")
            
            # 4. Check if s2 is incorrectly tainted.
            if is_tainted(s2):
                log("s2 is TAINTED (BUG: Address reuse not handled!)")
                raise AssertionError("BUG: New object at old address inherited the taint")
            else:
                log("s2 is clean (Correct behavior)")
            break
            
    if not found_reuse:
        log("Could not reproduce address reuse in 10000 attempts.")

if __name__ == "__main__":
    test_address_reuse()
