from physical_ai_skill_intelligence import ExperienceRecord, ExperienceStore
from physical_ai_skill_intelligence import EmpiricalOutcomeEstimator

def test_empirical_estimate_uses_only_exact_context():
    ctx = {"visibility": "GOOD"}
    store = ExperienceStore([
        ExperienceRecord("AT", ctx, "a", True, cost=2, cost_semantics="OBSERVED_COST", cost_unit="ATTEMPT_COUNT"),
        ExperienceRecord("AT", ctx, "a", False, cost=4, cost_semantics="OBSERVED_COST", cost_unit="ATTEMPT_COUNT"),
        ExperienceRecord("AT", {"visibility": "BAD"}, "a", True, cost=1, cost_semantics="OBSERVED_COST", cost_unit="ATTEMPT_COUNT"),
    ])
    est = EmpiricalOutcomeEstimator(store).estimate(
        goal_predicate="AT",
        state_context=ctx,
        skill_name="a",
    )
    assert est.evidence_count == 2
    assert est.success_probability == 0.5
    assert est.mean_cost == 3.0

def test_no_evidence_is_explicit_prior_baseline():
    est = EmpiricalOutcomeEstimator(ExperienceStore()).estimate(
        goal_predicate="AT",
        state_context={"visibility": "GOOD"},
        skill_name="a",
    )
    assert est.evidence_count == 0
    assert est.method == "explicit_beta_prior_no_evidence"
    assert est.success_probability == 0.5
