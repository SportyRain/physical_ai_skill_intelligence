"""Resolve evidence paths inside the declared, trusted provider snapshot root."""
from pathlib import Path


def contained_path(root: Path, path: Path, error_type: type[ValueError]) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise error_type("evidence path escapes provider root")
    return resolved


def validate_raw_paths(root: Path, references, error_type: type[ValueError]) -> None:
    if not isinstance(references, list):
        raise error_type("raw_evidence must be a list")
    for reference in references:
        if not isinstance(reference, str) or not reference:
            raise error_type("raw_evidence path must be a nonempty string")
        contained_path(root, root / reference, error_type)
