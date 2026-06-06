#ifndef Py_BUILD_CORE
#  define Py_BUILD_CORE
#endif

#include "Python.h"
#include "anota_watch.h"
#include "pycore_pystate.h"   // _PyThreadState_GET()
#include "pycore_pyerrors.h"  // _PyErr_SetString
#include "pycore_hashtable.h"

/* Simple object access policy engine used by ANOTA_WATCH and ceval.c.
 *
 * Policy model:
 *   - Policies are stored in a C-level hash table.
 *   - Key: { void* obj, void* key } (Heap allocated)
 *       * key is NULL   -> policy for the whole object
 *       * key is not NULL -> policy for a specific attribute/element
 *   - Value: (uintptr_t) encoding:
 *         high byte: allow_mask (bits for R/W/X)
 *         low  byte: block_mask (bits for R/W/X)
 */

#define ANOTA_MODE_R 0x01
#define ANOTA_MODE_W 0x02
#define ANOTA_MODE_X 0x04

typedef struct {
    void *obj;
    void *key;
} WatchKey;

typedef struct {
    PyObject_HEAD
    _Py_hashtable_t *policies;
} AnotaWatchObject;

static PyTypeObject AnotaWatch_Type;
static PyObject *anota_singleton = NULL;

/* --- hashtable helpers ------------------------------------------------ */

static Py_uhash_t
watch_hash(const void *key)
{
    const WatchKey *wk = (const WatchKey *)key;
    return _Py_hashtable_hash_ptr(wk->obj) ^ _Py_hashtable_hash_ptr(wk->key);
}

static int
watch_compare(const void *key1, const void *key2)
{
    const WatchKey *wk1 = (const WatchKey *)key1;
    const WatchKey *wk2 = (const WatchKey *)key2;
    return wk1->obj == wk2->obj && wk1->key == wk2->key;
}

static void
watch_destroy_key(void *key)
{
    PyMem_RawFree(key);
}

/* --- internal helpers ------------------------------------------------- */

static inline AnotaWatchObject *
get_singleton_struct(void)
{
    return (AnotaWatchObject *)anota_singleton;
}

/* Update or create entry for (obj, key). */
static int
update_entry(AnotaWatchObject *aw,
             PyObject *obj, PyObject *key,
             unsigned char bits, int is_allow)
{
    WatchKey lookup_wk = { (void*)obj, (void*)(key ? key : NULL) };
    
    _Py_hashtable_entry_t *entry = _Py_hashtable_get_entry(aw->policies, &lookup_wk);
    
    unsigned char allow = 0;
    unsigned char block = 0;

    if (entry != NULL) {
        uintptr_t value = (uintptr_t)entry->value;
        allow = (unsigned char)((value >> 8) & 0xFFu);
        block = (unsigned char)(value & 0xFFu);
    }

    if (is_allow) {
        allow |= bits;
    }
    else {
        block |= bits;
    }

    uintptr_t new_value = ((uintptr_t)allow << 8) | (uintptr_t)block;
    
    if (entry != NULL) {
        entry->value = (void*)new_value;
    } else {
        WatchKey *new_wk = PyMem_RawMalloc(sizeof(WatchKey));
        if (new_wk == NULL) return -1;
        new_wk->obj = (void*)obj;
        new_wk->key = (void*)(key ? key : NULL);
        
        if (_Py_hashtable_set(aw->policies, new_wk, (void*)new_value) < 0) {
            PyMem_RawFree(new_wk);
            return -1;
        }
    }
    return 0;
}

/* Decide access for a single (obj, key) entry. */
static int
decide_for_entry(_Py_hashtable_t *policies,
                 PyObject *obj, PyObject *key,
                 unsigned char mode_bit)
{
    if (policies == NULL) return 0;
    
    WatchKey wk = { (void*)obj, (void*)(key ? key : NULL) };
    void *val_ptr = _Py_hashtable_get(policies, &wk);
    if (val_ptr == NULL) return 0;

    uintptr_t value = (uintptr_t)val_ptr;
    unsigned char allow = (unsigned char)((value >> 8) & 0xFFu);
    unsigned char block = (unsigned char)(value & 0xFFu);

    if (block & mode_bit) return -1;
    if (allow != 0 && !(allow & mode_bit)) return -1;
    if (allow & mode_bit) return 1;
    return 0;
}

/* Common implementation for all access checks. */
static int
_anota_check_access(PyThreadState *tstate,
                    PyObject *obj, PyObject *key,
                    unsigned char mode_bit,
                    const char *mode_str,
                    const char *kind_str)
{
    if (anota_singleton == NULL) return 0;
    AnotaWatchObject *aw = get_singleton_struct();
    if (aw->policies == NULL || _Py_hashtable_size(aw->policies) == 0) return 0;

    int r;
    if (key != NULL) {
        r = decide_for_entry(aw->policies, obj, key, mode_bit);
        if (r == -1) goto violation_member;
        if (r == 1) return 0;
    }

    r = decide_for_entry(aw->policies, obj, NULL, mode_bit);
    if (r == -1) goto violation_obj;
    return 0;

violation_member:
    PySys_FormatStderr("ANOTA_WATCH violation: blocked %s %s access on object %R with key %R\n",
                       kind_str, mode_str, obj, key);
    _PyErr_SetString(tstate, PyExc_RuntimeError, "ANOTA_WATCH policy violation");
    return -1;

violation_obj:
    PySys_FormatStderr("ANOTA_WATCH violation: blocked %s %s access on object %R\n",
                       kind_str, mode_str, obj);
    _PyErr_SetString(tstate, PyExc_RuntimeError, "ANOTA_WATCH policy violation");
    return -1;
}

/* --- Python-level methods --------------------------------------------- */

static int
parse_modes(PyObject *modes, unsigned char *out_bits)
{
    const char *s;
    Py_ssize_t len, i;
    unsigned char bits = 0;

    if (!PyUnicode_Check(modes)) {
        PyErr_SetString(PyExc_TypeError, "modes must be a string like 'R', 'RW', or 'RWX'");
        return -1;
    }
    s = PyUnicode_AsUTF8AndSize(modes, &len);
    if (s == NULL) return -1;

    for (i = 0; i < len; i++) {
        switch (s[i]) {
            case 'R': bits |= ANOTA_MODE_R; break;
            case 'W': bits |= ANOTA_MODE_W; break;
            case 'X': bits |= ANOTA_MODE_X; break;
            default:
                PyErr_Format(PyExc_ValueError, "unknown mode character %c", s[i]);
                return -1;
        }
    }
    if (bits == 0) {
        PyErr_SetString(PyExc_ValueError, "empty modes string");
        return -1;
    }
    *out_bits = bits;
    return 0;
}

static PyObject *
anota_allow(AnotaWatchObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"obj", "modes", "key", NULL};
    PyObject *obj, *modes, *key = NULL;
    unsigned char bits;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO|O:ALLOW", kwlist, &obj, &modes, &key))
        return NULL;

    if (parse_modes(modes, &bits) < 0) return NULL;
    if (update_entry(self, obj, key, bits, 1) < 0) return NULL;
    Py_RETURN_NONE;
}

static PyObject *
anota_block(AnotaWatchObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"obj", "modes", "key", NULL};
    PyObject *obj, *modes, *key = NULL;
    unsigned char bits;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO|O:BLOCK", kwlist, &obj, &modes, &key))
        return NULL;

    if (parse_modes(modes, &bits) < 0) return NULL;
    if (update_entry(self, obj, key, bits, 0) < 0) return NULL;
    Py_RETURN_NONE;
}

static PyObject *
anota_clear(AnotaWatchObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"obj", "key", NULL};
    PyObject *obj, *key = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|O:CLEAR", kwlist, &obj, &key))
        return NULL;

    WatchKey wk = { (void*)obj, (void*)(key ? key : NULL) };
    (void)_Py_hashtable_steal(self->policies, &wk);
    Py_RETURN_NONE;
}

static PyObject *
anota_clear_all(AnotaWatchObject *self, PyObject *Py_UNUSED(ignored))
{
    if (self->policies != NULL) {
        _Py_hashtable_clear(self->policies);
    }
    Py_RETURN_NONE;
}

static void
anota_dealloc(AnotaWatchObject *self)
{
    if (self->policies != NULL) {
        _Py_hashtable_destroy(self->policies);
    }
    Py_TYPE(self)->tp_free((PyObject *)self);
}

typedef struct {
    void *target_obj;
    _Py_hashtable_t *ht;
    WatchKey to_delete[64];
    Py_ssize_t count;
} DeallocContext;

static int
collect_obj_keys(_Py_hashtable_t *ht, const void *key, const void *value, void *user_data)
{
    DeallocContext *ctx = (DeallocContext *)user_data;
    const WatchKey *wk = (const WatchKey *)key;
    (void)value;

    if (wk->obj == ctx->target_obj || wk->key == ctx->target_obj) {
        if (ctx->count < 64) {
            ctx->to_delete[ctx->count++] = *wk;
        }
    }
    return 0;
}

static int in_dealloc_hook = 0;

void
_PyAnotaWatch_NotifyDealloc(PyObject *obj)
{
    if (in_dealloc_hook || anota_singleton == NULL) return;
    AnotaWatchObject *aw = get_singleton_struct();
    if (aw == NULL || aw->policies == NULL || _Py_hashtable_size(aw->policies) == 0) return;

    in_dealloc_hook = 1;
    PyObject *type, *value, *traceback;
    PyErr_Fetch(&type, &value, &traceback);

    DeallocContext ctx = { (void*)obj, aw->policies, {{0,0}}, 0 };
    (void)_Py_hashtable_foreach(aw->policies, collect_obj_keys, &ctx);

    for (Py_ssize_t i = 0; i < ctx.count; i++) {
        (void)_Py_hashtable_steal(aw->policies, &ctx.to_delete[i]);
    }

    PyErr_Restore(type, value, traceback);
    in_dealloc_hook = 0;
}

/* --- public entry points ---------------------------------------------- */

PyObject *
_PyAnotaWatch_GetSingleton(void)
{
    if (anota_singleton != NULL) {
        Py_INCREF(anota_singleton);
        return anota_singleton;
    }

    if (PyType_Ready(&AnotaWatch_Type) < 0) return NULL;

    AnotaWatchObject *self = PyObject_New(AnotaWatchObject, &AnotaWatch_Type);
    if (self == NULL) return NULL;

    self->policies = _Py_hashtable_new_full(
        watch_hash, watch_compare,
        watch_destroy_key, NULL, NULL);

    if (self->policies == NULL) {
        PyObject_Del(self);
        return NULL;
    }

    anota_singleton = (PyObject *)self;
    Py_INCREF(anota_singleton);
    return anota_singleton;
}

/* check functions called from ceval.c */

int _PyAnota_CheckReadObject(PyThreadState *tstate, PyObject *obj) {
    return _anota_check_access(tstate, obj, NULL, ANOTA_MODE_R, "R", "object");
}
int _PyAnota_CheckWriteObject(PyThreadState *tstate, PyObject *obj) {
    return _anota_check_access(tstate, obj, NULL, ANOTA_MODE_W, "W", "object");
}
int _PyAnota_CheckExecObject(PyThreadState *tstate, PyObject *obj) {
    return _anota_check_access(tstate, obj, NULL, ANOTA_MODE_X, "X", "object");
}
int _PyAnota_CheckReadMember(PyThreadState *tstate, PyObject *container, PyObject *key) {
    return _anota_check_access(tstate, container, key, ANOTA_MODE_R, "R", "member");
}
int _PyAnota_CheckWriteMember(PyThreadState *tstate, PyObject *container, PyObject *key) {
    return _anota_check_access(tstate, container, key, ANOTA_MODE_W, "W", "member");
}

static PyMethodDef anota_methods[] = {
    {"ALLOW", (PyCFunction)anota_allow, METH_VARARGS | METH_KEYWORDS, NULL},
    {"BLOCK", (PyCFunction)anota_block, METH_VARARGS | METH_KEYWORDS, NULL},
    {"CLEAR", (PyCFunction)anota_clear, METH_VARARGS | METH_KEYWORDS, NULL},
    {"CLEAR_ALL", (PyCFunction)anota_clear_all, METH_NOARGS, NULL},
    {NULL, NULL}
};

static PyTypeObject AnotaWatch_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "ANOTA_WATCH",
    sizeof(AnotaWatchObject),
    0,
    (destructor)anota_dealloc,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    PyObject_GenericGetAttr,
    0, 0, Py_TPFLAGS_DEFAULT,
    0, 0, 0, 0, 0, 0, 0,
    anota_methods,
};
