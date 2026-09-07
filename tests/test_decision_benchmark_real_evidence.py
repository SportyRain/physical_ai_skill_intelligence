from pathlib import Path

from physical_ai_skill_intelligence import run_push_decision_benchmark
from physical_ai_skill_intelligence.importers import Ur3VisualServoingEvidenceImporter

PROVIDER_COMMIT = "b91d3be5a7643f6e91023da8c9d7f339811c7b14"
ROOT = Path(__file__).parent / "fixtures" / "ur3_visual_servoing"
PUSH_RUN = ROOT / "evidence/runs/REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING_20260906_001.json"


def test_real_experience_conditioned_outcome_and_decision_are_deterministic():
    importer = Ur3VisualServoingEvidenceImporter(provider_commit=PROVIDER_COMMIT)
    records = importer.import_run_manifest(PUSH_RUN, provider_root=ROOT)
    a = run_push_decision_benchmark(records)
    b = run_push_decision_benchmark(records)
    assert a == b

    before = a.without_relevant_experience
    after = a.with_relevant_real_experience
    assert all(c.evidence_count == 0 for c in before.candidates)
    assert all(c.estimator_method == "explicit_beta_prior_no_evidence" for c in before.candidates)
    assert [c.evidence_count for c in after.candidates] == [1, 1]
    assert all(c.estimator_method == "empirical_beta_baseline" for c in after.candidates)
    assert a.estimate_changed is True
    assert a.evidence_count == 2
    assert after.selected_skill == "goal_directed_continuous_push/nominal_baseline"
    nominal, adapted = after.candidates
    assert nominal.expected_success == adapted.expected_success == 2 / 3
    assert nominal.mean_cost == 2.0
    assert adapted.mean_cost == 3.0
    assert nominal.evidence_ids and adapted.evidence_ids
    assert nominal.provenance_trace and adapted.provenance_trace
    assert a.selection_changed is False
