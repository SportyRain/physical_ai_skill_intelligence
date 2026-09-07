from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from physical_ai_skill_intelligence import (
    EmpiricalOutcomeEstimator, ExperienceStore, Provenance,
    Ur3VisualServoingRecoveryEvidenceImporter,
)
from physical_ai_skill_intelligence.importers import Ur3VisualServoingEvidenceImporter

ROOT = Path(__file__).parent / "fixtures" / "ur3_visual_servoing"
FAMILIES = [
    ("REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING_20260906_001", Ur3VisualServoingEvidenceImporter),
    ("REAL_UR3_PICK_PLACE_20260905_001", Ur3VisualServoingEvidenceImporter),
    ("REAL_READY_STALE_CLEANUP_20260831_001", Ur3VisualServoingRecoveryEvidenceImporter),
]
SNAPSHOT = "b91d3be5a7643f6e91023da8c9d7f339811c7b14"
RECOVERY_SNAPSHOT = "fec0021d0d7b4ee076842923e7627f1e7486fa71"


def fixture(tmp_path, family):
    name, importer_type = family
    root = tmp_path / "provider"
    shutil.copytree(ROOT, root)
    path = root / "evidence" / "runs" / f"{name}.json"
    payload = json.loads(path.read_text())
    commit = RECOVERY_SNAPSHOT if importer_type is Ur3VisualServoingRecoveryEvidenceImporter else SNAPSHOT
    return root, path, payload, importer_type(provider_commit=commit)


@pytest.mark.parametrize("family", FAMILIES)
def test_artifact_and_runtime_commits_preserved_with_original_hashes(tmp_path, family):
    root, path, payload, importer = fixture(tmp_path, family)
    raw = path.read_bytes()
    records = importer.import_run_manifest(path, provider_root=root)
    for record in records:
        provenance = record.provenance
        assert provenance.artifact_snapshot_commit == importer.provider_commit
        assert provenance.source_commit == importer.provider_commit
        assert provenance.experiment_runtime_commit == payload["commit"]
        assert provenance.artifact_snapshot_commit != provenance.experiment_runtime_commit
        assert provenance.raw_sha256 == hashlib.sha256(raw).hexdigest()
        for source in provenance.related_sources:
            assert source.raw_sha256 == hashlib.sha256((root / source.source_path).read_bytes()).hexdigest()
        provenance.validate()


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("raw_commit", [None, "abc123", "UNKNOWN", "NOT_VERIFIED"])
def test_missing_or_abbreviated_runtime_commit_not_invented(tmp_path, family, raw_commit):
    root, path, payload, importer = fixture(tmp_path, family)
    payload["commit"] = raw_commit
    path.write_text(json.dumps(payload))
    for record in importer.import_run_manifest(path, provider_root=root):
        assert record.provenance.experiment_runtime_commit == (
            "NOT_VERIFIED" if raw_commit == "NOT_VERIFIED" else "UNKNOWN")
        metadata = record.metrics if family[1] is Ur3VisualServoingRecoveryEvidenceImporter else record.scene_context
        key = "manifest_commit" if family[1] is Ur3VisualServoingRecoveryEvidenceImporter else "source_record_commit"
        assert metadata[key] == raw_commit


@pytest.mark.parametrize("field", ["artifact_snapshot_commit", "experiment_runtime_commit"])
@pytest.mark.parametrize("value", ["main", "abc123", "g" * 40, "a" * 41, "a" * 39])
def test_invalid_authoritative_commit_rejected(field, value):
    kwargs = dict(source_repository="repo", source_commit="a" * 40, source_path="path",
                  source_record_id="id", raw_sha256="b" * 64, schema_version="v1")
    kwargs[field] = value
    with pytest.raises(ValueError, match="full 40-character"):
        Provenance(**kwargs)


@pytest.mark.parametrize("family", FAMILIES)
def test_importer_requires_full_snapshot_and_rejects_invalid_runtime_sha(tmp_path, family):
    with pytest.raises(ValueError, match="full 40-character"):
        family[1](provider_commit="main")
    root, path, payload, importer = fixture(tmp_path, family)
    payload["commit"] = "g" * 40
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="full 40-character"):
        importer.import_run_manifest(path, provider_root=root)


def test_legacy_provenance_preserves_abbreviation_without_promoting_it():
    provenance = Provenance("repo", "abc123", "path", "id", "a" * 64, "v1")
    provenance.validate()
    assert provenance.source_commit == "abc123"
    assert provenance.artifact_snapshot_commit == "UNKNOWN"
    assert provenance.experiment_runtime_commit == "UNKNOWN"
    with pytest.raises(ValueError, match="must match"):
        replace(provenance, artifact_snapshot_commit="b" * 40)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("escape", ["../outside.json", "absolute", "nested_traversal", "symlink"])
def test_all_importers_reject_raw_evidence_escape(tmp_path, family, escape):
    root, path, payload, importer = fixture(tmp_path, family)
    outside = tmp_path / "outside.json"
    outside.write_text('{"outside": true}')
    if escape == "absolute":
        reference = str(outside)
    elif escape == "nested_traversal":
        reference = "evidence/logs/../../../outside.json"
    elif escape == "symlink":
        link = root / "evidence/logs/escape_experience_readback.json"
        link.symlink_to(outside)
        reference = link.relative_to(root).as_posix()
    else:
        reference = escape
    # Also reject unused links (Pick/Place currently reads only its manifest).
    payload["raw_evidence"] = [reference]
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="escapes provider root|tracked evidence/logs path"):
        importer.import_run_manifest(path, provider_root=root)


@pytest.mark.parametrize("family", FAMILIES)
def test_valid_nested_evidence_paths_are_accepted(tmp_path, family):
    root, path, payload, importer = fixture(tmp_path, family)
    nested = root / "evidence/logs/nested"
    nested.mkdir()
    refs = []
    for reference in payload["raw_evidence"]:
        source = root / reference
        if not source.exists():
            # The Push excerpt is a preserved reference, not an imported fixture.
            refs.append(reference)
            continue
        dest = nested / source.name
        shutil.copyfile(source, dest)
        refs.append(dest.relative_to(root).as_posix())
    if not refs:  # Pick/Place's references are contained, but are not consumed.
        (nested / "reference.json").write_text("{}")
        refs = ["evidence/logs/nested/reference.json"]
    payload["raw_evidence"] = refs
    path.write_text(json.dumps(payload))
    assert importer.import_run_manifest(path, provider_root=root)


@pytest.mark.parametrize("family", FAMILIES)
def test_manifest_itself_cannot_escape_declared_provider_root(tmp_path, family):
    root, path, payload, importer = fixture(tmp_path, family)
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="escapes provider root"):
        importer.import_run_manifest(outside, provider_root=root)
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes provider root"):
        importer.import_run_manifest(path, provider_root=root)


def test_pick_configuration_limit_is_preserved_but_never_observed_cost(tmp_path):
    root, path, payload, importer = fixture(tmp_path, FAMILIES[1])
    (record,) = importer.import_run_manifest(path, provider_root=root)
    assert record.cost == payload["metrics"]["max_pick_attempts"]
    assert record.cost_semantics == "CONFIGURED_LIMIT"
    assert record.metrics["cost_semantics"] == "MAX_PICK_ATTEMPTS"
    estimate = EmpiricalOutcomeEstimator(ExperienceStore([record])).estimate(
        goal_predicate=record.goal_predicate, state_context=record.state_context, skill_name=record.skill_name)
    assert estimate.evidence_count == 1
    assert estimate.cost_evidence_count == 0
    assert estimate.mean_cost == 0
    assert estimate.cost_unit == "UNKNOWN"
    del payload["metrics"]["max_pick_attempts"]
    path.write_text(json.dumps(payload))
    (unknown,) = importer.import_run_manifest(path, provider_root=root)
    assert unknown.cost_semantics == "UNKNOWN"


@pytest.mark.parametrize("metric", ["goal_tolerance_m", "trial1_final_goal_error_m", "trial1_first_action_m"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_push_outcome_metrics_cannot_verify_success(tmp_path, metric, value):
    root, path, payload, importer = fixture(tmp_path, FAMILIES[0])
    payload["metrics"][metric] = value
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="invalid Push"):
        importer.import_run_manifest(path, provider_root=root)
