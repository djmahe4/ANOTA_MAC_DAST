#ifndef Py_BUILD_CORE
#  define Py_BUILD_CORE
#endif

#include "Python.h"
#include "anota_taint.h"
#include "pycore_pystate.h"  /* PyThreadState */
#include "pycore_hashtable.h"

/* Very simple taint-tracking engine.
 *
 * Model:
 *   - A C-level hash table of tainted object addresses:
 *         taint_objects: { void* address -> 1 }
 *   - A global mapping of sanitizer functions:
 *         sanitizers: { func -> True }
 *   - A global mapping of sink functions:
 *         sinks: { func -> True }
 */

static _Py_hashtable_t *taint_objects = NULL;
static PyObject *taint_sanitizers = NULL; /* { func -> True } */
static PyObject *taint_sinks = NULL;      /* { func -> True } */

/* --- internal helpers -------------------------------------------------- */

static int
ensure_state(void)
{
    if (taint_objects == NULL) {
        taint_objects = _Py_hashtable_new(_Py_hashtable_hash_ptr,
                                          _Py_hashtable_compare_direct);
        if (taint_objects == NULL) {
            return -1;
        }
    }
    if (taint_sanitizers == NULL) {
        taint_sanitizers = PyDict_New();
        if (taint_sanitizers == NULL) {
            return -1;
        }
    }
    if (taint_sinks == NULL) {
        taint_sinks = PyDict_New();
        if (taint_sinks == NULL) {
            return -1;
        }
    }
    return 0;
}

/* Return 1 if obj is tainted, 0 if not, -1 on error. */
static int
is_tainted(PyObject *obj)
{
    if (taint_objects == NULL || obj == NULL) {
        return 0;
    }
    if (_Py_hashtable_get(taint_objects, obj) != NULL) {
        return 1;
    }
    return 0;
}

/* Mark obj as tainted. Returns 0 on success, -1 on error. */
static int
mark_tainted(PyObject *obj)
{
    if (ensure_state() < 0) {
        return -1;
    }
    if (obj == NULL) return 0;
    
    if (is_tainted(obj)) return 0;
    
    if (_Py_hashtable_set(taint_objects, obj, (void*)1) < 0) {
        return -1;
    }
    return 0;
}

/* Unmark obj as tainted. Returns 0 on success, -1 on error. */
static int
unmark_tainted(PyObject *obj)
{
    if (taint_objects == NULL || obj == NULL) {
        return 0;
    }
    (void)_Py_hashtable_steal(taint_objects, obj);
    return 0;
}

/* Register all callable items in 'seq' into the given dict. */
static int
register_funcs_from_seq(PyObject *seq, PyObject *target_dict,
                        const char *role)
{
    if (seq == NULL || Py_IsNone(seq)) {
        return 0;
    }

    PyObject *fast = PySequence_Fast(seq,
        role && *role ? "ANOTA_TAINT: expected a sequence for argument" : "ANOTA_TAINT: bad sequence");
    if (fast == NULL) {
        return -1;
    }

    Py_ssize_t n = PySequence_Fast_GET_SIZE(fast);
    PyObject **items = PySequence_Fast_ITEMS(fast);
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *f = items[i];
        if (!PyCallable_Check(f)) {
            Py_DECREF(fast);
            PyErr_Format(PyExc_TypeError,
                         "ANOTA_TAINT: %s entry at index %zd is not callable",
                         role ? role : "list", i);
            return -1;
        }
        if (PyDict_SetItem(target_dict, f, Py_True) < 0) {
            Py_DECREF(fast);
            return -1;
        }
    }

    Py_DECREF(fast);
    return 0;
}

/* --- public registration helpers -------------------------------------- */

void
_PyAnotaTaint_Clear(void)
{
    if (taint_objects != NULL) {
        _Py_hashtable_clear(taint_objects);
    }
    if (taint_sanitizers != NULL) {
        PyDict_Clear(taint_sanitizers);
    }
    if (taint_sinks != NULL) {
        PyDict_Clear(taint_sinks);
    }
}

void
_PyAnotaTaint_NotifyDealloc(PyObject *obj)
{
    if (taint_objects != NULL) {
        (void)unmark_tainted(obj);
    }
}

int
_PyAnotaTaint_Register(PyObject *obj, PyObject *sanitizers, PyObject *sinks)
{
    if (ensure_state() < 0) {
        return -1;
    }

    if (mark_tainted(obj) < 0) {
        return -1;
    }

    if (sanitizers && !Py_IsNone(sanitizers)) {
        if (register_funcs_from_seq(sanitizers, taint_sanitizers,
                                    "sanitization") < 0) {
            return -1;
        }
    }

    if (sinks && !Py_IsNone(sinks)) {
        if (register_funcs_from_seq(sinks, taint_sinks,
                                    "Sink") < 0) {
            return -1;
        }
    }

    return 0;
}

/* --- Python-level ANOTA_TAINT builtin --------------------------------- */

PyObject *
_PyAnota_Taint(PyObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"obj", "sanitization", "Sink", NULL};
    PyObject *obj;
    PyObject *sanitization = Py_None;
    PyObject *sink = Py_None;

    if (!PyArg_ParseTupleAndKeywords(
            args, kwds, "O|OO:ANOTA_TAINT", kwlist,
            &obj, &sanitization, &sink)) {
        return NULL;
    }

    if (_PyAnotaTaint_Register(obj, sanitization, sink) < 0) {
        return NULL;
    }

    Py_RETURN_NONE;
}

PyObject *
_PyAnota_Taint_Clear(PyObject *self, PyObject *args)
{
    (void)self;
    (void)args;
    _PyAnotaTaint_Clear();
    Py_RETURN_NONE;
}

/* --- sink checks for various call paths ------------------------------- */

static int
is_sink(PyObject *func)
{
    if (taint_sinks == NULL) {
        return 0;
    }
    int contains = PyDict_Contains(taint_sinks, func);
    if (contains < 0) {
        return -1;
    }
    return contains;
}

static int
deep_is_tainted_recursive(PyObject *obj, int depth)
{
    if (obj == NULL) return 0;
    if (depth > 20) return 0;

    int ta = is_tainted(obj);
    if (ta != 0) return ta;

    if (PyList_Check(obj)) {
        Py_ssize_t size = PyList_GET_SIZE(obj);
        for (Py_ssize_t i = 0; i < size; i++) {
            if (deep_is_tainted_recursive(PyList_GET_ITEM(obj, i), depth + 1)) 
                return 1;
        }
    }
    else if (PyTuple_Check(obj)) {
        Py_ssize_t size = PyTuple_GET_SIZE(obj);
        for (Py_ssize_t i = 0; i < size; i++) {
            if (deep_is_tainted_recursive(PyTuple_GET_ITEM(obj, i), depth + 1)) 
                return 1;
        }
    }
    else if (PyDict_Check(obj)) {
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(obj, &pos, &key, &value)) {
            if (deep_is_tainted_recursive(key, depth + 1)) return 1;
            if (deep_is_tainted_recursive(value, depth + 1)) return 1;
        }
    }
    return 0;
}

static int
deep_is_tainted(PyObject *obj)
{
    return deep_is_tainted_recursive(obj, 0);
}

static int
check_args_for_taint(PyObject *func, PyObject *const *stack,
                     Py_ssize_t total_args, int is_sink_func)
{
    if (taint_objects == NULL) {
        return 0;
    }

    int found_taint = 0;
    for (Py_ssize_t i = 0; i < total_args; i++) {
        PyObject *arg = stack[i];
        int ta = deep_is_tainted(arg);
        if (ta < 0) {
            return -1;
        }
        if (ta) {
            if (is_sink_func) {
                PySys_FormatStderr(
                    "ANOTA_TAINT violation: tainted object %R passed to sink %R\n",
                    arg, func);
                PyErr_SetString(PyExc_RuntimeError,
                                "ANOTA_TAINT sink violation");
                return -1;
            }
            found_taint = 1;
        }
    }
    return found_taint;
}

static int
check_tuple_for_taint(PyObject *func, PyObject *tuple, int is_sink_func)
{
    if (taint_objects == NULL || tuple == NULL) {
        return 0;
    }

    int found_taint = 0;
    Py_ssize_t n = PyTuple_GET_SIZE(tuple);
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *arg = PyTuple_GET_ITEM(tuple, i);
        int ta = deep_is_tainted(arg);
        if (ta < 0) {
            return -1;
        }
        if (ta) {
            if (is_sink_func) {
                PySys_FormatStderr(
                    "ANOTA_TAINT violation: tainted object %R passed to sink %R\n",
                    arg, func);
                PyErr_SetString(PyExc_RuntimeError,
                                "ANOTA_TAINT sink violation");
                return -1;
            }
            found_taint = 1;
        }
    }
    return found_taint;
}

static int
check_dict_values_for_taint(PyObject *func, PyObject *dict, int is_sink_func)
{
    if (taint_objects == NULL || dict == NULL) {
        return 0;
    }

    PyObject *key, *value;
    Py_ssize_t pos = 0;
    int found_taint = 0;

    while (PyDict_Next(dict, &pos, &key, &value)) {
        int ta = deep_is_tainted(value);
        if (ta < 0) {
            return -1;
        }
        if (ta) {
            if (is_sink_func) {
                PySys_FormatStderr(
                    "ANOTA_TAINT violation: tainted object %R passed to sink %R "
                    "via keyword argument %R\n",
                    value, func, key);
                PyErr_SetString(PyExc_RuntimeError,
                                "ANOTA_TAINT sink violation");
                return -1;
            }
            found_taint = 1;
        }
    }
    return found_taint;
}

int
_PyAnotaTaint_CheckVectorcall(PyThreadState *tstate,
                              PyObject *func,
                              PyObject *const *stack,
                              Py_ssize_t nargs,
                              Py_ssize_t nkwargs,
                              PyObject *kwnames)
{
    (void)tstate;

    if (taint_objects == NULL) {
        return 0;
    }

    int sink = is_sink(func);
    if (sink < 0) {
        return -1;
    }

    Py_ssize_t total = nargs + nkwargs;
    return check_args_for_taint(func, stack, total, sink);
}

int
_PyAnotaTaint_CheckTupleDictCall(PyThreadState *tstate,
                                 PyObject *func,
                                 PyObject *args_tuple,
                                 PyObject *kwargs_dict)
{
    (void)tstate;

    if (taint_objects == NULL) {
        return 0;
    }

    int sink = is_sink(func);
    if (sink < 0) {
        return -1;
    }

    int t1 = check_tuple_for_taint(func, args_tuple, sink);
    if (t1 < 0) return -1;

    int t2 = check_dict_values_for_taint(func, kwargs_dict, sink);
    if (t2 < 0) return -1;

    return (t1 || t2);
}

static int
is_sanitizer(PyObject *func)
{
    if (taint_sanitizers == NULL) {
        return 0;
    }
    int contains = PyDict_Contains(taint_sanitizers, func);
    if (contains < 0) {
        return -1;
    }
    return contains;
}

int
_PyAnotaTaint_IsTainted(PyObject *obj)
{
    return is_tainted(obj);
}

void
_PyAnotaTaint_PostCall(PyObject *func, PyObject *result, int taint_source_found)
{
    if (result == NULL || taint_objects == NULL) {
        return;
    }

    int sani = is_sanitizer(func);
    if (sani < 0) {
        PyErr_Clear();
        return;
    }

    if (sani) {
        if (unmark_tainted(result) < 0) {
            PyErr_Clear();
        }
    }
    else if (taint_source_found) {
        if (mark_tainted(result) == 0) {
             PySys_FormatStderr("ANOTA_TAINT propagation: call to %R returned %R (tainted)\n", func, result);
        }
    }
}

void
_PyAnotaTaint_Propagate(PyObject *source, PyObject *target)
{
    if (taint_objects == NULL || source == NULL || target == NULL) {
        return;
    }
    int ta = is_tainted(source);
    if (ta > 0) {
        if (mark_tainted(target) == 0) {
            PySys_FormatStderr("ANOTA_TAINT propagation: %R -> %R\n", source, target);
        }
    }
}

void
_PyAnotaTaint_PropagateBinary(PyObject *left, PyObject *right, PyObject *result)
{
    if (taint_objects == NULL || result == NULL) {
        return;
    }
    int t1 = (left != NULL) ? is_tainted(left) : 0;
    int t2 = (right != NULL) ? is_tainted(right) : 0;

    if (t1 > 0 || t2 > 0) {
        if (mark_tainted(result) == 0) {
            PySys_FormatStderr("ANOTA_TAINT propagation: %R, %R -> %R\n",
                               left ? left : Py_None,
                               right ? right : Py_None,
                               result);
        }
    }
}
