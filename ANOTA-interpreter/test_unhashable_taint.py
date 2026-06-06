"""
test_unhashable_taint.py

Reproduction test case for tainting unhashable objects.
Currently, ANOTA_TAINT only supports hashable objects because it uses a dict internally.
"""

import builtins
import traceback

def get_anota_taint():
    if not hasattr(builtins, "ANOTA_TAINT"):
        raise RuntimeError("ANOTA_TAINT builtin is not available")
    return builtins.ANOTA_TAINT

def expect_runtime_error(callable_obj, *args, **kwargs):
    try:
        callable_obj(*args, **kwargs)
    except RuntimeError:
        return
    except Exception as exc:
        raise AssertionError(
            f"Expected RuntimeError, got {type(exc).__name__}: {exc!r}"
        ) from exc
    else:
        raise AssertionError("Expected RuntimeError, but call succeeded")

def test_taint_list():
    """Taint a list (unhashable) and verify it works (currently fails with TypeError)."""
    print("=== test_taint_list ===")
    taint = get_anota_taint()
    
    my_list = [1, 2, 3]
    try:
        taint(my_list, Sink=[print])
    except TypeError as e:
        print(f"Caught expected TypeError (reproduced!): {e}")
        raise e
    except Exception as e:
        print(f"Caught unexpected exception: {type(e).__name__}: {e}")
        raise e

    print("Checking if taint is enforced on the list...")
    expect_runtime_error(print, my_list)
    print("test_taint_list: OK")

def test_taint_dict():
    """Taint a dict (unhashable) and verify it works."""
    print("=== test_taint_dict ===")
    taint = get_anota_taint()
    
    my_dict = {"key": "value"}
    try:
        taint(my_dict, Sink=[print])
    except TypeError as e:
        print(f"Caught expected TypeError (reproduced!): {e}")
        raise e
    
    print("Checking if taint is enforced on the dict...")
    expect_runtime_error(print, my_dict)
    print("test_taint_dict: OK")

if __name__ == "__main__":
    try:
        test_taint_list()
    except Exception:
        traceback.print_exc()
    
    try:
        test_taint_dict()
    except Exception:
        traceback.print_exc()
