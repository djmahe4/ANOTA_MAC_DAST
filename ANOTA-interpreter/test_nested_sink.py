"""
test_nested_sink.py

Test that taint propagates through nested containers.
Currently, deep_is_tainted only checks one level deep.
"""

import builtins
import sys

def get_anota_taint():
    return builtins.ANOTA_TAINT

def test_nested_list():
    print("=== test_nested_list ===")
    taint = get_anota_taint()
    builtins.ANOTA_TAINT_CLEAR()
    
    # Register print as a sink
    taint("dummy", Sink=[print])
    
    source = "secret"
    taint(source)
    
    nested = [[source]]
    print(f"Checking if nested list is blocked: {nested}")
    
    try:
        print(nested)
        raise AssertionError("Nested tainted list should have been blocked!")
    except RuntimeError:
        print("Nested list successfully blocked (Correct behavior)")

def test_nested_dict():
    print("=== test_nested_dict ===")
    taint = get_anota_taint()
    builtins.ANOTA_TAINT_CLEAR()
    
    taint("dummy", Sink=[print])
    
    source = "secret"
    taint(source)
    
    nested = {"a": {"b": source}}
    print(f"Checking if nested dict is blocked: {nested}")
    
    try:
        print(nested)
        raise AssertionError("Nested tainted dict should have been blocked!")
    except RuntimeError:
        print("Nested dict successfully blocked (Correct behavior)")

if __name__ == "__main__":
    try:
        test_nested_list()
    except Exception as e:
        print(f"test_nested_list FAILED: {e}")
        
    try:
        test_nested_dict()
    except Exception as e:
        print(f"test_nested_dict FAILED: {e}")
