"""JSON-safe serialization for preserved Physical AI evidence.

This helper intentionally avoids ``dataclasses.asdict`` because core immutable
records may contain ``MappingProxyType`` snapshots. ``asdict`` deep-copies values
and fails on those read-only mappings. Evidence serialization must preserve the
record content without mutating or weakening the immutable runtime objects.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from math import isfinite
from typing import Any


def to_jsonable(value: Any) -> Any:
    """Convert supported immutable evidence values into JSON-safe plain data.

    Supported values are dataclass instances, string-key mappings, list/tuple
    containers, and JSON scalar values. Non-finite floats and unsupported object
    types fail closed instead of being stringified or silently dropped.
    """

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("evidence mapping keys must be strings")
        return {key: to_jsonable(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]

    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("evidence floats must be finite")
        return value

    raise TypeError(f"unsupported evidence value type: {type(value).__name__}")
