import pytest
from physical_ai_skill_intelligence import Provenance

def test_valid_provenance():
    p = Provenance(
        source_repository="SportyRain/ur3_visual_servoing",
        source_commit="abc123",
        source_path="evidence/run.json",
        source_record_id="run-1",
        raw_sha256="a" * 64,
        schema_version="v1",
    )
    p.validate()

def test_invalid_sha_rejected():
    p = Provenance("repo", "commit", "path", "id", "bad", "v1")
    with pytest.raises(ValueError):
        p.validate()

def test_invalid_related_source_sha_rejected():
    from physical_ai_skill_intelligence import SourceArtifact
    p = Provenance(
        "repo", "commit", "path", "id", "a" * 64, "v1", "importer-v1",
        (SourceArtifact("raw.txt", "bad"),),
    )
    with pytest.raises(ValueError):
        p.validate()
