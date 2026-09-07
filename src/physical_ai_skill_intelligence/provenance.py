from __future__ import annotations
from dataclasses import dataclass


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
    source_repository: str
    source_commit: str
    source_path: str
    source_record_id: str
    raw_sha256: str
    schema_version: str
    importer_version: str = "UNKNOWN"
    related_sources: tuple[SourceArtifact, ...] = ()

    def validate(self) -> None:
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
