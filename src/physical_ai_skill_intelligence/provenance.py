from __future__ import annotations
from dataclasses import dataclass
import re


def validate_commit(value: str, name: str, *, allow_unknown: bool = True) -> None:
    if allow_unknown and value in ("UNKNOWN", "NOT_VERIFIED"):
        return
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{40}", value) is None:
        raise ValueError(f"{name} must be a full 40-character commit SHA")


def runtime_commit(raw) -> str:
    """Do not invent a full SHA from historical missing/abbreviated evidence.

    Importers retain the original manifest value in the legacy raw metadata.
    """
    if raw is None or raw in ("", "UNKNOWN", "NOT_VERIFIED"):
        return "NOT_VERIFIED" if raw == "NOT_VERIFIED" else "UNKNOWN"
    if isinstance(raw, str) and re.fullmatch(r"[0-9a-fA-F]{4,39}", raw):
        return "UNKNOWN"
    validate_commit(raw, "experiment_runtime_commit")
    return raw


@dataclass(frozen=True)
class SourceArtifact:
    source_path: str
    raw_sha256: str

    def validate(self) -> None:
        if not self.source_path.strip():
            raise ValueError("source_path is required")
        if len(self.raw_sha256) != 64:
            raise ValueError("raw_sha256 must be a 64-character SHA-256 hex digest")
        int(self.raw_sha256, 16)


@dataclass(frozen=True)
class Provenance:
    """Artifact location and experiment source are distinct provenance claims.

    source_commit is retained as the legacy artifact snapshot reference. An
    abbreviated legacy reference is not promoted to an authoritative full SHA.
    Full SHA syntax does not itself verify Git object existence or execution.
    """
    source_repository: str
    source_commit: str
    source_path: str
    source_record_id: str
    raw_sha256: str
    schema_version: str
    importer_version: str = "UNKNOWN"
    related_sources: tuple[SourceArtifact, ...] = ()
    artifact_snapshot_commit: str = "UNKNOWN"
    experiment_runtime_commit: str = "UNKNOWN"

    def __post_init__(self) -> None:
        object.__setattr__(self, "related_sources", tuple(self.related_sources))
        if self.artifact_snapshot_commit == "UNKNOWN" and re.fullmatch(
            r"[0-9a-fA-F]{40}", self.source_commit
        ):
            object.__setattr__(self, "artifact_snapshot_commit", self.source_commit)
        validate_commit(self.artifact_snapshot_commit, "artifact_snapshot_commit")
        validate_commit(self.experiment_runtime_commit, "experiment_runtime_commit")
        if self.artifact_snapshot_commit not in ("UNKNOWN", "NOT_VERIFIED"):
            if self.source_commit != self.artifact_snapshot_commit:
                raise ValueError("source_commit must match artifact_snapshot_commit")

    def validate(self) -> None:
        validate_commit(self.artifact_snapshot_commit, "artifact_snapshot_commit")
        validate_commit(self.experiment_runtime_commit, "experiment_runtime_commit")
        required = {
            "source_repository": self.source_repository,
            "source_commit": self.source_commit,
            "source_path": self.source_path,
            "source_record_id": self.source_record_id,
            "raw_sha256": self.raw_sha256,
            "schema_version": self.schema_version,
            "importer_version": self.importer_version,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"missing provenance fields: {', '.join(missing)}")
        if len(self.raw_sha256) != 64:
            raise ValueError("raw_sha256 must be a 64-character SHA-256 hex digest")
        int(self.raw_sha256, 16)
        for source in self.related_sources:
            source.validate()
