"""A simple store to pass "global-like" objects between modules.
Simply provides put and fetch methods to insert/retrieve an object.

The store is used to pass objects between modules, instead of function arguments.
Each module has to import this object_store and fetch/put the objects it needs.

This helps for loose coupling and testability of the modules.

"""

STORE = {}


def fetch(key: str):
    """Get an object for a given key, or None."""
    return STORE.get(key)


def put(key: str, value):
    """Put an object into the store, at the given key."""
    STORE[key] = value
