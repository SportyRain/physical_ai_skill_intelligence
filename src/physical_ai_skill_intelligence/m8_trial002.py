"""Narrow repository-owned Trial002 execution and evidence path.

This module does not add retry, recovery, orchestration, motion planning, or robot
control. It invokes the existing M8 +5 mm adapter exactly once and persists its
immutable ProviderResult through the verified JSON-safe evidence serializer.
Physical execution remains fail-closed unless ``execute_real=True`` is supplied
explicitly by the caller after the separate pre-motion gates.
"""
from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import time
from typing import Any

from .adapters.real_ur3_free_space import (
    GOAL_PREDICATE,
    GOAL_SUBJECT,
    PROVIDER_CALLABLE,
    PROVIDER_REPOSITORY,
    SKILL_NAME,
    SOURCE_PATH,
    VALID_AXES,
    RealUr3PositiveAxis5mmProvider,
)
from .evidence_serialization import to_jsonable
from .goal import Goal
from .provenance import Provenance, SourceArtifact, validate_commit
from .state import WorldState


TRIAL_SCHEMA_VERSION = "M8_REAL_UR3_TRIAL_V1"
RUNNER_VERSION = "M8_TRIAL002_RUNNER_V1"
REQUESTED_TRANSLATION_M = 0.005
REQUIRED_RELATED_SOURCE_PATHS = (
    "src/ur3_visual_servoing/__init__.py",
    "src/ur3_visual_servoing/se3.py",
    "src/ur3_visual_servoing/runtime/__init__.py",
    "src/ur3_visual_servoing/robot_camera_collect.py",
)


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a 64-character SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a 64-character SHA-256 hex digest") from exc
    return value.lower()


def _related_source_hashes(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("provider_related_sources_sha256 must be a mapping")
    if set(value) != set(REQUIRED_RELATED_SOURCE_PATHS):
        raise ValueError(
            "provider_related_sources_sha256 must identify exactly the required "
            "loaded provider sources"
        )
    return {
        path: _sha256(value[path], f"provider related source {path}")
        for path in REQUIRED_RELATED_SOURCE_PATHS
    }


def build_m8_provider_provenance(
    *,
    provider_commit: str,
    provider_raw_sha256: str,
    provider_related_sources_sha256: Mapping[str, str],
) -> Provenance:
    """Build complete provenance for the exact loaded M8 provider source set."""

    validate_commit(provider_commit, "provider_commit", allow_unknown=False)
    raw_sha256 = _sha256(provider_raw_sha256, "provider_raw_sha256")
    related = _related_source_hashes(provider_related_sources_sha256)
    return Provenance(
        source_repository=PROVIDER_REPOSITORY,
        source_commit=provider_commit,
        source_path=SOURCE_PATH,
        source_record_id=PROVIDER_CALLABLE,
        raw_sha256=raw_sha256,
        schema_version=TRIAL_SCHEMA_VERSION,
        importer_version=RUNNER_VERSION,
        related_sources=tuple(
            SourceArtifact(path, related[path])
            for path in REQUIRED_RELATED_SOURCE_PATHS
        ),
        artifact_snapshot_commit=provider_commit,
        experiment_runtime_commit=provider_commit,
    )


def run_trial002_positive_axis_5mm(
    *,
    trial_id: str,
    axis: str,
    physical_ai_commit: str,
    provider_commit: str,
    provider_raw_sha256: str,
    provider_related_sources_sha256: Mapping[str, str],
    provider_repository: str,
    output_path: str | Path,
    execute_real: bool = False,
    motion_timeout_s: float = 12.0,
    settle_error_mm: float = 1.0,
) -> dict[str, Any]:
    """Invoke the existing adapter once and atomically persist structured evidence.

    The output path must not already exist. This check happens before constructing
    or invoking the provider so an existing immutable evidence record cannot cause
    an accidental repeat execution.
    """

    trial_id = _nonempty(trial_id, "trial_id")
    if not isinstance(axis, str) or axis not in VALID_AXES:
        raise ValueError("axis must be exactly X, Y, or Z")
    if type(execute_real) is not bool:
        raise ValueError("execute_real must be boolean")
    validate_commit(physical_ai_commit, "physical_ai_commit", allow_unknown=False)
    validate_commit(provider_commit, "provider_commit", allow_unknown=False)
    provider_repository = _nonempty(provider_repository, "provider_repository")
    provider_raw_sha256 = _sha256(provider_raw_sha256, "provider_raw_sha256")
    related_sources = _related_source_hashes(provider_related_sources_sha256)

    path = Path(output_path)
    if path.exists():
        raise FileExistsError(f"evidence output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary evidence output already exists: {temporary}")

    provenance = build_m8_provider_provenance(
        provider_commit=provider_commit,
        provider_raw_sha256=provider_raw_sha256,
        provider_related_sources_sha256=related_sources,
    )
    provider = RealUr3PositiveAxis5mmProvider(
        provenance,
        provider_repository=provider_repository,
        execute_real=execute_real,
        motion_timeout_s=motion_timeout_s,
        settle_error_mm=settle_error_mm,
    )
    goal = Goal(
        predicate=GOAL_PREDICATE,
        subject=GOAL_SUBJECT,
        reference=None,
        parameters={"axis": axis},
    )

    started = time.monotonic()
    result = provider.execute(SKILL_NAME, goal, WorldState())
    wrapper_elapsed_s = time.monotonic() - started

    record = {
        "schema_version": TRIAL_SCHEMA_VERSION,
        "runner_version": RUNNER_VERSION,
        "trial_id": trial_id,
        "physical_ai_commit": physical_ai_commit,
        "provider_commit": provider_commit,
        "provider_raw_sha256": provider_raw_sha256,
        "provider_related_sources_sha256": related_sources,
        "provider_repository": provider_repository,
        "axis": axis,
        "requested_translation_m": REQUESTED_TRANSLATION_M,
        "execute_real": execute_real,
        "wrapper_elapsed_s": wrapper_elapsed_s,
        "serialization": "to_jsonable",
        "result": to_jsonable(result),
    }
    encoded = json.dumps(
        record,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"

    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        finally:
            raise

    return record
