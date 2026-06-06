"""
test_taint_propagation_comprehensive.py

Identify all common Python operations that should propagate taint but currently don't.
"""

import builtins
import os
import sys

def get_anota_taint():
    if not hasattr(builtins, "ANOTA_TAINT"):
        raise RuntimeError("ANOTA_TAINT builtin is not available")
    return builtins.ANOTA_TAINT

def is_tainted(obj):
    # We can use a sink to check if something is tainted.
    # If calling print(obj) raises RuntimeError, it's tainted.
    # Note: we must register print as a sink for EACH object we check,
    # because ANOTA_TAINT registers sinks PER OBJECT.
    # Wait, that's not right. ANOTA_TAINT(obj, Sink=[print]) registers 'print'
    # as a sink for 'obj'.
    # So we can't easily check if an arbitrary object is tainted without
    # registering a sink for it.
    
    # Actually, we can just try to register a sink and see if it's already tainted?
    # No, that doesn't work.
    
    # Let's use the fact that propagation happens by calling _PyAnotaTaint_Propagate.
    # If we want to check if 'res' is tainted after 'res = tainted + untainted',
    # we can try to use 'res' in a known sink.
    
    # BUT, we need to register the sink for 'res' BEFORE the operation?
    # No, the sink is registered for the SOURCE.
    # Wait, let's re-read anota_taint.c.
    
    # _PyAnotaTaint_CheckVectorcall checks if 'func' is a sink.
    # If it is, it checks if any ARGS are tainted.
    # A function is a sink if it's in 'taint_sinks' dict.
    # Taint sinks is a global mapping: { func -> True }.
    # SO, once a function is registered as a sink (for ANY object), 
    # it will ALWAYS check for taint in its arguments.
    
    # Let's verify this assumption.
    return None

def check_taint(obj):
    try:
        print(obj)
        return False
    except RuntimeError:
        return True

def report(msg):
    # Use sys.stderr to avoid print() sink during reporting
    sys.stderr.write(str(msg) + "\n")

def test_propagation():
    taint = get_anota_taint()
    
    # 0. Register print as a sink globally (by tainting a dummy object)
    dummy = "dummy"
    taint(dummy, Sink=[print])
    
    source = "tainted"
    taint(source) # Mark as tainted
    
    report(f"Source tainted: {check_taint(source)}")
    
    # 1. Binary Addition
    res_add = source + " suffix"
    report(f"Addition propagated: {check_taint(res_add)}")
    
    # 2. String formatting (modulo)
    res_mod = "prefix %s" % source
    report(f"Modulo propagated: {check_taint(res_mod)}")
    
    # 3. f-strings
    res_f = f"prefix {source}"
    report(f"f-string propagated: {check_taint(res_f)}")
    
    # 4. str.join
    res_join = "".join([source, " other"])
    report(f"join propagated: {check_taint(res_join)}")
    
    # 5. str.replace
    res_replace = source.replace("tainted", "clean")
    report(f"replace propagated: {check_taint(res_replace)}")

if __name__ == "__main__":
    test_propagation()
