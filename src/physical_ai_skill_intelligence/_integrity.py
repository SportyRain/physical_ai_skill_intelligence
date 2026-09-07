"""Small boundaries for the existing JSON-like records; no runtime machinery."""
from collections.abc import Mapping
from math import isfinite
from types import MappingProxyType


def snapshot(value):
    """Copy JSON-like containers into recursively read-only mappings/tuples."""
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("snapshot mapping keys must be strings")
        return MappingProxyType({key: snapshot(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(snapshot(item) for item in value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ValueError("snapshot values must be JSON-like")


def identity_key(value):
    if isinstance(value, Mapping):
        return ("object", tuple((key, identity_key(item)) for key, item in sorted(value.items())))
    if isinstance(value, tuple):
        return ("array", tuple(identity_key(item) for item in value))
    return (type(value).__name__, value)


def snapshot_mapping(value):
    if not isinstance(value, Mapping):
        raise ValueError("snapshot field must be a mapping")
    return snapshot(value)


def finite_number(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        valid = isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (value <= 0 if positive else value < 0):
        bound = "> 0" if positive else ">= 0"
        raise ValueError(f"{name} must be finite and {bound}")
