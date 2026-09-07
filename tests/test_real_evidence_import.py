from pathlib import Path
import json
import pytest

from physical_ai_skill_intelligence import ExperienceStore, UNKNOWN
from physical_ai_skill_intelligence.importers import (
    EvidenceImportError,
    Ur3VisualServoingEvidenceImporter,
)

PROVIDER_COMMIT = "b91d3be5a7643f6e91023da8c9d7f339811c7b14"
ROOT = Path(__file__).parent / "fixtures" / "ur3_visual_servoing"
PUSH_RUN = ROOT / "evidence/runs/REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING_20260906_001.json"
PICK_RUN = ROOT / "evidence/runs/REAL_UR3_PICK_PLACE_20260905_001.json"


def importer():
    return Ur3VisualServoingEvidenceImporter(provider_commit=PROVIDER_COMMIT)


def test_import_real_push_family_preserves_multi_experience_semantics():
    rows = importer().import_run_manifest(PUSH_RUN, provider_root=ROOT)
    assert len(rows) == 2
    assert rows[0].trial_id.endswith("TRIAL_1")
    assert rows[1].trial_id.endswith("TRIAL_2")
    assert rows[0].state_context == rows[1].state_context
    assert rows[0].state_context["relative_goal_displacement_m"] == 0.015
    # Preserve provider applicability context separately; do not reconcile it silently.
    assert rows[0].state_context["provider_experience_context"]["goal_displacement_y_m"] == 0.02
    assert rows[0].object_identity == UNKNOWN
    assert rows[0].target_identity == UNKNOWN
    assert rows[0].task_success is True
    assert rows[1].task_success is True
    assert rows[0].cost == 2.0
    assert rows[1].cost == 3.0
    assert rows[0].provenance.source_commit == PROVIDER_COMMIT
    assert len(rows[0].provenance.related_sources) == 1


def test_import_real_pick_place_preserves_task_vs_action_success_distinction():
    (row,) = importer().import_run_manifest(PICK_RUN, provider_root=ROOT)
    assert row.task_success is True
    assert row.success is True
    assert row.action_success is False
    assert row.failure_code == "PLACE_RESULT_UNKNOWN_TARGET_NOT_VISIBLE"
    assert row.timestamp is None  # source explicitly preserved null rather than guessing
    assert row.object_identity == UNKNOWN


def test_idempotent_import_does_not_duplicate_experience():
    rows = importer().import_run_manifest(PUSH_RUN, provider_root=ROOT)
    store = ExperienceStore()
    assert store.add_many(rows) == 2
    assert store.add_many(rows) == 0
    assert len(store.all()) == 2


def test_conflicting_duplicate_identity_is_rejected():
    rows = importer().import_run_manifest(PUSH_RUN, provider_root=ROOT)
    store = ExperienceStore(rows)
    bad = rows[0].__class__(**{**rows[0].__dict__, "cost": 99.0})
    with pytest.raises(ValueError, match="conflicting duplicate"):
        store.add(bad)


def test_corrupt_raw_evidence_rejected(tmp_path):
    root = tmp_path / "provider"
    path = root / "evidence/runs/bad.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(EvidenceImportError, match="corrupt JSON"):
        importer().import_run_manifest(path, provider_root=root)


def test_missing_required_identity_rejected(tmp_path):
    root = tmp_path / "provider"
    path = root / "evidence/runs/missing.json"
    path.parent.mkdir(parents=True)
    payload = json.loads(PICK_RUN.read_text(encoding="utf-8"))
    payload.pop("experiment_id")
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(EvidenceImportError, match="missing required identity"):
        importer().import_run_manifest(path, provider_root=root)
