"""Read-only source attestation for the existing Python provider boundary.

The caller configures a Git repository; Provenance pins its commit and blobs.
Loaded Python package sources must match that committed snapshot, including
related_sources. Source-defined function bytecode is checked against those bytes
to reject stale imports. No provider code is evaluated by this helper.

This is a pre-call source identity check in a trusted, stable Python process,
not a sandbox against concurrent monkeypatching or a third-party dependency /
native-library attestation. Import side effects and physical execution are not
verified. Missing files, Git identity, or source metadata fail closed.
"""
from hashlib import sha256
import ast
from pathlib import Path, PurePosixPath
import subprocess
import sys
from types import CodeType, FunctionType, ModuleType

from ..provenance import Provenance, SourceArtifact, validate_commit


def _repository_identity(url: str) -> str:
    for prefix in ("https://github.com/", "ssh://git@github.com/", "git@github.com:"):
        if url.startswith(prefix):
            return url[len(prefix):].removesuffix(".git").rstrip("/")
    raise ValueError("unsupported provider repository origin")


def _codes(code):
    yield code
    for item in code.co_consts:
        if isinstance(item, CodeType):
            yield from _codes(item)


def _check_definitions(nodes, namespace, codes, module_name):
    # Walk source declarations rather than trusting runtime __module__ labels;
    # replacing a helper/constructor with a foreign callable must also fail.
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            value = namespace.get(node.name)
            if isinstance(value, (staticmethod, classmethod)):
                value = value.__func__
            if isinstance(value, property):
                functions = (value.fget, value.fset, value.fdel)
            else:
                functions = (value,)
            if not any(isinstance(function, FunctionType)
                       and function.__module__ == module_name
                       and function.__code__ in codes
                       and function.__code__.co_name == node.name
                       for function in functions):
                raise ValueError(f"loaded provider definition mismatch: {node.name}")
        elif isinstance(node, ast.ClassDef):
            value = namespace.get(node.name)
            if not isinstance(value, type) or value.__module__ != module_name:
                raise ValueError(f"loaded provider class mismatch: {node.name}")
            _check_definitions(node.body, vars(value), codes, module_name)


def attest_provider_source(provider, provenance: Provenance, repository,
                           module_name: str, callable_name: str) -> dict:
    if repository is None:
        raise ValueError("runtime provider repository is required")
    provenance.validate()
    commit = provenance.artifact_snapshot_commit
    validate_commit(commit, "provider commit", allow_unknown=False)

    def git(*args):
        return subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(repository), *args],
            stderr=subprocess.PIPE,
        )

    if _repository_identity(git("remote", "get-url", "origin").decode().strip()) != provenance.source_repository:
        raise ValueError("runtime provider repository mismatch")
    if git("rev-parse", f"{commit}^{{commit}}").decode().strip() != commit:
        raise ValueError("runtime provider commit mismatch")
    if (not isinstance(provider, ModuleType) or provider.__name__ != module_name
            or sys.modules.get(module_name) is not provider):
        raise ValueError("runtime provider module mismatch")
    entry = getattr(provider, callable_name, None)
    if not isinstance(entry, FunctionType) or entry.__module__ != module_name:
        raise ValueError("runtime provider callable identity missing or mismatched")

    source = PurePosixPath(provenance.source_path)
    if source.is_absolute() or ".." in source.parts:
        raise ValueError("provider source must be repository-relative")
    main_path = Path(provider.__file__).resolve(strict=True)
    root = main_path.parents[len(source.parts) - 1]
    if root.joinpath(*source.parts).resolve() != main_path:
        raise ValueError("runtime provider source path mismatch")
    artifacts = (SourceArtifact(provenance.source_path, provenance.raw_sha256),
                 *provenance.related_sources)
    expected = {item.source_path: item.raw_sha256 for item in artifacts}
    if len(expected) != len(artifacts):
        raise ValueError("duplicate provider source identity")
    package = module_name.split(".")[0]
    loaded = {}
    for name, module in tuple(sys.modules.items()):
        if name != package and not name.startswith(package + "."):
            continue
        if not isinstance(module, ModuleType) or module.__spec__ is None:
            raise ValueError("missing loaded provider metadata")
        path = Path(module.__file__).resolve(strict=True)
        relative = path.relative_to(root).as_posix()
        if (module.__name__ != name or module.__spec__.name != name
                or module.__spec__.origin is None
                or Path(module.__spec__.origin).resolve() != path
                or path.suffix != ".py"):
            raise ValueError("loaded provider module origin mismatch")
        # Module name must agree with its source path, not just a matching hash.
        suffix = name.replace(".", "/") + ("/__init__.py" if hasattr(module, "__path__") else ".py")
        if not relative.endswith("/" + suffix):
            raise ValueError("loaded provider module path mismatch")
        raw = git("show", f"{commit}:{relative}")
        digest = sha256(raw).hexdigest()
        if expected.get(relative) != digest or path.read_bytes() != raw:
            raise ValueError("runtime provider source identity mismatch")
        codes = tuple(_codes(compile(raw, str(path), "exec", dont_inherit=True)))
        _check_definitions(ast.parse(raw).body, vars(module), codes, name)
        loaded[relative] = digest
    if loaded != expected:
        raise ValueError("missing or unexpected loaded provider sources")
    return {"source_repository": provenance.source_repository,
            "source_commit": commit, "module": module_name,
            "callable": callable_name, "sources": loaded,
            "status": "VERIFIED"}
