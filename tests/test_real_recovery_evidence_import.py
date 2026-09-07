from pathlib import Path
import json
import shutil

import pytest

from physical_ai_skill_intelligence import (
    EmpiricalRecoveryOutcomeEstimator,
    FailureState,
    RecoveryExperienceStore,
    run_ready_recovery_decision_benchmark,
)
from physical_ai_skill_intelligence.recovery_importers import (
    RecoveryEvidenceImportError,
    READY_RECOVERY_GOAL,
    READY_STALE_FAILURE_ATTRIBUTION,
    READY_STALE_FAILURE_CODE,
    READY_STALE_RECOVERY_ACTION,
    RECOVERY_IMPORTER_VERSION,
    Ur3VisualServoingRecoveryEvidenceImporter,
)


PROVIDER_COMMIT = "fec0021d0d7b4ee076842923e7627f1e7486fa71"
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "ur3_visual_servoing"
MANIFEST_REL = Path("evidence/runs/REAL_READY_STALE_CLEANUP_20260831_001.json")
TRANSCRIPT_REL = Path(
    "evidence/logs/REAL_READY_STALE_CLEANUP_20260831_001_terminal_transcript.txt"
)
MANIFEST_SHA256 = "aeca04a9ccfd5362f5e5c23bd25fea66f6a83b89ab120e892eafeaa3c5c3f011"
TRANSCRIPT_SHA256 = "835cc8fd475f0c38ba975d801499b469516503f322a495b63b9062099749ab2c"


def importer():
    return Ur3VisualServoingRecoveryEvidenceImporter(provider_commit=PROVIDER_COMMIT)


def import_record(root=FIXTURE_ROOT):
    records = importer().import_run_manifest(
        root / MANIFEST_REL,
        provider_root=root,
    )
    assert len(records) == 1
    return records[0]


def copied_fixture(tmp_path):
    root = tmp_path / "ur3_visual_servoing"
    shutil.copytree(FIXTURE_ROOT, root)
    return root


def test_real_stale_controller_recovery_import_preserves_raw_semantics_and_provenance():
    record = import_record()
    assert record.goal_predicate == READY_RECOVERY_GOAL
    assert record.failure_code == READY_STALE_FAILURE_CODE
    assert record.failure_attribution == READY_STALE_FAILURE_ATTRIBUTION
    assert record.recovery_action == READY_STALE_RECOVERY_ACTION
    assert record.recovery_success is True
    assert record.cost == 1.0
    assert record.metrics["cost_semantics"] == "RECOVERY_EXECUTION_COUNT"
    assert record.metrics["controller_state_before_recovery"]["force_mode_controller"] == "active"
    assert record.metrics["controller_state_before_recovery"]["passthrough_trajectory_controller"] == "active"
    assert record.metrics["controller_state_after_recovery"]["force_mode_controller"] == "inactive"
    assert record.metrics["controller_state_after_recovery"]["passthrough_trajectory_controller"] == "inactive"
    assert record.metrics["experiment_id"] == "REAL_READY_STALE_CLEANUP_20260831_001"
    assert record.metrics["timestamp"] == "2026-08-31T19:49:02.095+09:00"
    assert record.provenance is not None
    assert record.provenance.source_repository == "SportyRain/ur3_visual_servoing"
    assert record.provenance.source_commit == PROVIDER_COMMIT
    assert record.provenance.source_path == MANIFEST_REL.as_posix()
    assert record.provenance.raw_sha256 == MANIFEST_SHA256
    assert record.provenance.importer_version == RECOVERY_IMPORTER_VERSION
    assert len(record.provenance.related_sources) == 1
    assert record.provenance.related_sources[0].source_path == TRANSCRIPT_REL.as_posix()
    assert record.provenance.related_sources[0].raw_sha256 == TRANSCRIPT_SHA256


def test_real_recovery_evidence_changes_offline_recovery_decision_with_trace():
    record = import_record()
    result = run_ready_recovery_decision_benchmark((record,))
    assert result.without_relevant_experience.selected_recovery == "LEAVE_CONTROLLER_UNCHANGED"
    assert result.with_relevant_real_experience.selected_recovery == READY_STALE_RECOVERY_ACTION
    assert result.selection_changed is True
    assert result.estimate_changed is True
    assert result.evidence_count == 1
    selected = result.with_relevant_real_experience.candidates[0]
    assert selected.recovery_action == READY_STALE_RECOVERY_ACTION
    assert selected.expected_success == pytest.approx(2.0 / 3.0)
    assert selected.evidence_count == 1
    assert selected.estimator_method == "empirical_recovery_beta_baseline"
    assert selected.provenance_trace == (record.provenance,)


def test_real_recovery_evidence_does_not_match_different_exact_state_context():
    record = import_record()
    changed_context = dict(record.state_context)
    changed_context["force_mode_controller"] = "inactive"
    estimate = EmpiricalRecoveryOutcomeEstimator(
        RecoveryExperienceStore((record,))
    ).estimate(
        goal_predicate=record.goal_predicate,
        state_context=changed_context,
        failure=FailureState(record.failure_code, record.failure_attribution),
        recovery_action=record.recovery_action,
    )
    assert estimate.evidence_count == 0
    assert estimate.success_probability == 0.5


def test_corrupt_real_recovery_transcript_is_rejected(tmp_path):
    root = copied_fixture(tmp_path)
    transcript = root / TRANSCRIPT_REL
    transcript.write_text(
        transcript.read_text(encoding="utf-8").replace(
            '"code": "PA-READY-818"',
            '"code": "PA-READY-999"',
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(RecoveryEvidenceImportError):
        importer().import_run_manifest(root / MANIFEST_REL, provider_root=root)


def test_manifest_raw_recovery_mismatch_is_rejected(tmp_path):
    root = copied_fixture(tmp_path)
    manifest_path = root / MANIFEST_REL
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["metrics"]["execute_code"] = "PA-READY-999"
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RecoveryEvidenceImportError, match="manifest/raw recovery mismatch"):
        importer().import_run_manifest(manifest_path, provider_root=root)


def test_untracked_or_missing_recovery_raw_path_is_rejected(tmp_path):
    root = copied_fixture(tmp_path)
    manifest_path = root / MANIFEST_REL
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["raw_evidence"] = ["/tmp/not_durable/full.log"]
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RecoveryEvidenceImportError, match="tracked evidence/logs path"):
        importer().import_run_manifest(manifest_path, provider_root=root)
