from dataclasses import replace
import math

import pytest

from physical_ai_skill_intelligence import (
    DecisionEngine, EmpiricalOutcomeEstimator, EmpiricalRecoveryOutcomeEstimator,
    ExecutionBudget, ExecutionObservation, ExperienceRecord, ExperienceStore,
    FailureState, Goal, RecoveryExperienceRecord, RecoveryExperienceStore,
    RecoverySpec, SkillSpec, WorldState,
)
from physical_ai_skill_intelligence.goal_verification import goal_satisfied
from physical_ai_skill_intelligence.provider_contract import ProviderResult


def recovery_record(**kwargs):
    return RecoveryExperienceRecord("AT", {}, "FAILED", "UNKNOWN", "recover", True, **kwargs)


def test_world_goal_and_spec_nested_inputs_are_immutable_snapshots():
    original = {"nested": [{"value": 1}]}
    state = WorldState(original)
    goal = Goal("AT", "a", "b", original)
    spec = SkillSpec("skill", ["AT"], original)
    recovery = RecoverySpec("recover", ["FAILED"], original)
    original["nested"][0]["value"] = 9
    original["extra"] = True
    for stored in (state.facts, goal.parameters, spec.preconditions, recovery.preconditions):
        assert stored["nested"][0]["value"] == 1
        assert "extra" not in stored
        with pytest.raises(TypeError):
            stored["nested"][0]["value"] = 2
    assert hash(goal.key())
    assert goal.key() != Goal("AT", "a", "b", {"nested": [{"value": 2}]}).key()
    assert state.satisfies({"nested": [{"value": 1}]})


def test_experience_store_preserves_all_nested_record_snapshots_and_identity():
    original = {"nested": [{"value": 1}]}
    record = ExperienceRecord(
        "AT", original, "skill", True, metrics=original, scene_context=original,
        state_before=original, state_after=original, goal_semantics=original,
        planned_action=original, accepted_action=original, executed_action=original,
        physical_outcome=original, object_identity=original, target_identity=original,
        failure_attribution=original, recovery_action=original, experience_id="one",
    )
    store = ExperienceStore([record])
    original["nested"][0]["value"] = 99
    for name in ("state_context", "metrics", "scene_context", "state_before", "state_after",
                 "goal_semantics", "planned_action", "accepted_action", "executed_action",
                 "physical_outcome", "object_identity", "target_identity",
                 "failure_attribution", "recovery_action"):
        stored = getattr(store.all()[0], name)
        assert stored["nested"][0]["value"] == 1
        with pytest.raises(TypeError):
            stored["nested"][0]["value"] = 2
    assert store.add(replace(record)) is False
    assert store.exact_context(goal_predicate="AT", state_context={"nested": [{"value": 1}]}) == (record,)


def test_recovery_failure_and_observation_snapshots():
    original = {"nested": [{"value": 1}]}
    record = replace(recovery_record(), state_context=original, metrics=original)
    store = RecoveryExperienceStore([record])
    failure = FailureState("FAILED", details=original)
    observation = ExecutionObservation(False, original, failure=failure, details=original)
    provider = ProviderResult(True, original, metrics={"cost": 1})
    original["nested"][0]["value"] = 9
    for stored in (record.state_context, record.metrics, failure.details,
                   observation.state_updates, observation.details, provider.observations):
        assert stored["nested"][0]["value"] == 1
        with pytest.raises(TypeError):
            stored["nested"][0]["value"] = 2
    assert store.exact_context(goal_predicate="AT", state_context={"nested": [{"value": 1}]},
                               failure=FailureState("FAILED")) == (record,)


def test_empty_skill_capability_is_not_a_wildcard():
    skill = SkillSpec("undeclared")
    assert not skill.supports_goal("ARBITRARY")
    with pytest.raises(RuntimeError, match="NO_APPLICABLE_SKILL"):
        DecisionEngine(EmpiricalOutcomeEstimator(ExperienceStore()), context_keys=()).rank(
            goal=Goal("AT", "a", "b"), state=WorldState(), skills=[skill])


@pytest.mark.parametrize("predicate", ["ON_TOP_OF", "AT", "INSERTED"])
def test_relation_goal_identity_never_aliases(predicate):
    state = WorldState({f"{predicate.lower()}:a:b": True, f"goal:{predicate}": True})
    assert goal_satisfied(Goal(predicate, "a", "b"), state)
    assert not goal_satisfied(Goal(predicate, "c", "b"), state)
    assert not goal_satisfied(Goal(predicate, "a", "c"), state)
    assert not goal_satisfied(Goal(predicate, "a", "b", {"tolerance": 1}), state)
    assert not goal_satisfied(Goal(predicate), state)
    assert not goal_satisfied(Goal(predicate, "a:b", "c"), WorldState({f"{predicate.lower()}:a:b:c": True}))


def test_unsupported_and_global_goal_identity_fail_closed():
    state = WorldState({"goal:CUSTOM": True, "goal:CANONICAL_READY": True})
    for goal in (Goal("CUSTOM"), Goal("CUSTOM", "a"), Goal("CUSTOM", "b"),
                 Goal("CUSTOM", "a", "b"), Goal("CUSTOM", "a", "c"),
                 Goal("CANONICAL_READY", "ur3_runtime"), Goal("CANONICAL_READY", reference="other"),
                 Goal("CANONICAL_READY", parameters={"mode": "other"})):
        assert not goal_satisfied(goal, state)
    assert goal_satisfied(Goal("CANONICAL_READY"), state)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -1.0])
@pytest.mark.parametrize("factory", [
    lambda v: ExperienceRecord("AT", {}, "skill", True, cost=v),
    lambda v: recovery_record(cost=v),
    lambda v: SkillSpec("skill", ("AT",), nominal_cost=v),
    lambda v: RecoverySpec("recover", ("FAILED",), nominal_cost=v),
    lambda v: ExecutionObservation(True, cost=v),
    lambda v: ExecutionBudget(1, 1, 1, v),
    lambda v: DecisionEngine(EmpiricalOutcomeEstimator(ExperienceStore()), context_keys=(), cost_weight=v),
    lambda v: DecisionEngine(EmpiricalOutcomeEstimator(ExperienceStore()), context_keys=(), uncertainty_weight=v),
])
def test_nonfinite_or_negative_decision_numbers_are_rejected(factory, value):
    with pytest.raises(ValueError):
        factory(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -1.0, 0.0])
@pytest.mark.parametrize("field", ["alpha", "beta"])
@pytest.mark.parametrize("estimator,store", [
    (EmpiricalOutcomeEstimator, ExperienceStore),
    (EmpiricalRecoveryOutcomeEstimator, RecoveryExperienceStore),
])
def test_invalid_beta_prior_rejected(estimator, store, field, value):
    with pytest.raises(ValueError):
        estimator(store(), **{field: value})


@pytest.mark.parametrize("field", ["max_total_steps", "max_recovery_attempts", "max_same_failure_repeats"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 1.5, True])
def test_step_budgets_require_finite_integers(field, value):
    kwargs = dict(max_total_steps=1, max_recovery_attempts=1, max_same_failure_repeats=1, max_total_cost=0)
    kwargs[field] = value
    with pytest.raises(ValueError):
        ExecutionBudget(**kwargs)


@pytest.mark.parametrize("kwargs", [
    {"action_success": True, "failure": FailureState("FAILED")},
    {"action_success": True, "terminal_failure": True},
    {"action_success": False},
    {"action_success": True, "retryable": "false"},
    {"action_success": True, "terminal_failure": "false"},
    {"action_success": False, "failure": FailureState("FAILED"), "terminal_failure": True, "retryable": True},
])
def test_contradictory_or_ambiguous_observation_rejected(kwargs):
    with pytest.raises(ValueError):
        ExecutionObservation(**kwargs)


@pytest.mark.parametrize("success,code", [(True, "FAILED"), (False, None)])
def test_contradictory_provider_result_rejected(success, code):
    with pytest.raises(ValueError):
        ProviderResult(success, {}, failure_code=code)


def estimate(records, recovery=False):
    if recovery:
        return EmpiricalRecoveryOutcomeEstimator(RecoveryExperienceStore(records)).estimate(
            goal_predicate="AT", state_context={}, failure=FailureState("FAILED"), recovery_action="recover")
    return EmpiricalOutcomeEstimator(ExperienceStore(records)).estimate(
        goal_predicate="AT", state_context={}, skill_name="skill")


@pytest.mark.parametrize("recovery", [False, True])
def test_nonobserved_costs_excluded_with_explicit_sample_count(recovery):
    make = recovery_record if recovery else lambda **kw: ExperienceRecord("AT", {}, "skill", True, **kw)
    observed = make(cost=2, cost_semantics="OBSERVED_COST", cost_unit="ATTEMPT_COUNT")
    configured = make(cost=100, cost_semantics="CONFIGURED_LIMIT", cost_unit="ATTEMPT_COUNT")
    unknown = make(cost=200)
    unknown_unit = make(cost=300, cost_semantics="OBSERVED_COST")
    result = estimate([observed, configured, unknown, unknown_unit], recovery)
    assert result.evidence_count == 4
    assert result.mean_cost == 2
    assert result.cost_evidence_count == 1
    assert result.cost_unit == "ATTEMPT_COUNT"
    empty_cost = estimate([configured, unknown, unknown_unit], recovery)
    assert empty_cost.cost_evidence_count == 0
    assert empty_cost.cost_unit == "UNKNOWN"
    assert empty_cost.mean_cost == 0  # compatibility placeholder, no observed samples
    with pytest.raises(ValueError, match="INCOMPATIBLE_COST_UNITS"):
        estimate([observed, replace(observed, cost_unit="RECOVERY_EXECUTION_COUNT")], recovery)


def test_extreme_finite_priors_keep_probability_finite():
    result = EmpiricalOutcomeEstimator(ExperienceStore(), alpha=1e308, beta=1e308).estimate(
        goal_predicate="AT", state_context={}, skill_name="skill")
    assert math.isfinite(result.success_probability)
    assert result.success_probability == 0.5


@pytest.mark.parametrize("recovery", [False, True])
def test_decision_rejects_incompatible_cost_units_across_candidates(recovery):
    from physical_ai_skill_intelligence import RecoveryDecisionEngine
    if recovery:
        records = [recovery_record(cost=1, cost_semantics="OBSERVED_COST", cost_unit="ATTEMPT_COUNT"),
                   replace(recovery_record(cost=1, cost_semantics="OBSERVED_COST", cost_unit="RECOVERY_EXECUTION_COUNT"),
                           recovery_action="other")]
        engine = RecoveryDecisionEngine(EmpiricalRecoveryOutcomeEstimator(RecoveryExperienceStore(records)), context_keys=())
        args = dict(failure=FailureState("FAILED"), recoveries=[RecoverySpec("recover", ("FAILED",)), RecoverySpec("other", ("FAILED",))])
    else:
        records = [ExperienceRecord("AT", {}, "skill", True, cost=1, cost_semantics="OBSERVED_COST", cost_unit="ATTEMPT_COUNT"),
                   ExperienceRecord("AT", {}, "other", True, cost=1, cost_semantics="OBSERVED_COST", cost_unit="RECOVERY_EXECUTION_COUNT")]
        engine = DecisionEngine(EmpiricalOutcomeEstimator(ExperienceStore(records)), context_keys=())
        args = dict(skills=[SkillSpec("skill", ("AT",)), SkillSpec("other", ("AT",))])
    with pytest.raises(ValueError, match="INCOMPATIBLE_COST_UNITS"):
        engine.rank(goal=Goal("AT", "a", "b"), state=WorldState(), **args)


def test_malformed_state_updates_are_rejected_at_observation_boundary():
    with pytest.raises(ValueError, match="must be a mapping"):
        ExecutionObservation(True, state_updates=[{"goal:CANONICAL_READY": True}])
