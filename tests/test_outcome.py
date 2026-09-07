from physical_ai_skill_intelligence import ExperienceRecord, ExperienceStore
from physical_ai_skill_intelligence import EmpiricalOutcomeEstimator

def test_empirical_estimate_uses_only_exact_context():
    ctx = {"visibility": "GOOD"}
    store = ExperienceStore([
        ExperienceRecord("AT", ctx, "a", True, cost=2),
        ExperienceRecord("AT", ctx, "a", False, cost=4),
        ExperienceRecord("AT", {"visibility": "BAD"}, "a", True, cost=1),
    ])
    est = EmpiricalOutcomeEstimator(store).estimate(
        goal_predicate="AT",
        state_context=ctx,
        skill_name="a",
    )
    assert est.evidence_count == 2
    assert est.success_probability == 0.5
    assert est.mean_cost == 3.0
