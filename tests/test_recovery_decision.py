import pytest

from physical_ai_skill_intelligence import (
    EmpiricalRecoveryOutcomeEstimator,
    FailureState,
    Goal,
    RecoveryDecisionEngine,
    RecoveryExperienceRecord,
    RecoveryExperienceStore,
    RecoverySpec,
    WorldState,
)


CONTEXT_KEYS = ("vision_quality", "object_visible")
STATE = WorldState({"vision_quality": "GOOD", "object_visible": True})
GOAL = Goal("ON_TOP_OF", "red", "blue")
FAILURE = FailureState("GRASP_FAILED", "ATTACHMENT_NOT_VERIFIED")


def engine(records=()):
    return RecoveryDecisionEngine(
        EmpiricalRecoveryOutcomeEstimator(RecoveryExperienceStore(records)),
        context_keys=CONTEXT_KEYS,
    )


def recoveries():
    return [
        RecoverySpec(
            "retry_same",
            ("GRASP_FAILED",),
            provider="ur3_visual_servoing",
        ),
        RecoverySpec(
            "visual_realign",
            ("GRASP_FAILED",),
            {"object_visible": True},
            provider="ur3_visual_servoing",
        ),
        RecoverySpec(
            "abort",
            ("GRASP_FAILED",),
            provider="ur3_visual_servoing",
            nominal_cost=10.0,
        ),
    ]


def record(action, success, *, cost=1.0, failure=FAILURE, context=None):
    return RecoveryExperienceRecord(
        goal_predicate="ON_TOP_OF",
        state_context=context or STATE.context(CONTEXT_KEYS),
        failure_code=failure.code,
        failure_attribution=failure.attribution,
        recovery_action=action,
        recovery_success=success,
        cost=cost,
    )


def test_no_recovery_evidence_uses_explicit_prior_and_is_deterministic():
    first = engine().rank(goal=GOAL, state=STATE, failure=FAILURE, recoveries=recoveries())
    second = engine().rank(goal=GOAL, state=STATE, failure=FAILURE, recoveries=recoveries())
    assert first == second
    assert first.selected_recovery == "retry_same"
    assert all(candidate.expected_success == 0.5 for candidate in first.candidates)
    assert all(candidate.evidence_count == 0 for candidate in first.candidates)
    assert first.candidates[0].estimator_method == "explicit_beta_prior_no_recovery_evidence"


def test_recovery_experience_can_change_recovery_selection():
    records = [
        record("retry_same", False),
        record("retry_same", False),
        record("visual_realign", True),
        record("visual_realign", True),
        record("visual_realign", True),
    ]
    decision = engine(records).rank(
        goal=GOAL, state=STATE, failure=FAILURE, recoveries=recoveries()
    )
    assert decision.selected_recovery == "visual_realign"
    selected = decision.candidates[0]
    assert selected.evidence_count == 3
    assert selected.expected_success == 0.8
    assert "failure=GRASP_FAILED" in decision.reason


def test_different_failure_code_does_not_match_recovery_experience():
    records = [record("retry_same", True)]
    different = FailureState("PLACE_FAILED", "TARGET_NOT_VISIBLE")
    estimate = EmpiricalRecoveryOutcomeEstimator(RecoveryExperienceStore(records)).estimate(
        goal_predicate="ON_TOP_OF",
        state_context=STATE.context(CONTEXT_KEYS),
        failure=different,
        recovery_action="retry_same",
    )
    assert estimate.evidence_count == 0
    assert estimate.success_probability == 0.5


def test_different_failure_attribution_does_not_silently_match():
    records = [record("retry_same", True)]
    different = FailureState("GRASP_FAILED", "VACUUM_IO")
    estimate = EmpiricalRecoveryOutcomeEstimator(RecoveryExperienceStore(records)).estimate(
        goal_predicate="ON_TOP_OF",
        state_context=STATE.context(CONTEXT_KEYS),
        failure=different,
        recovery_action="retry_same",
    )
    assert estimate.evidence_count == 0


def test_unknown_failure_is_not_wildcard():
    with pytest.raises(RuntimeError, match="NO_APPLICABLE_RECOVERY"):
        engine().rank(
            goal=GOAL,
            state=STATE,
            failure=FailureState("UNKNOWN", "UNKNOWN"),
            recoveries=recoveries(),
        )


def test_failure_code_filters_recovery_candidates():
    decision = engine().rank(
        goal=GOAL,
        state=STATE,
        failure=FAILURE,
        recoveries=[
            RecoverySpec("reobserve", ("PERCEPTION_FAILED",)),
            RecoverySpec("retry_same", ("GRASP_FAILED",)),
        ],
    )
    assert decision.selected_recovery == "retry_same"
    assert tuple(c.recovery_action for c in decision.candidates) == ("retry_same",)


def test_recovery_precondition_filters_candidate_fail_closed():
    decision = engine().rank(
        goal=GOAL,
        state=WorldState({"vision_quality": "GOOD", "object_visible": False}),
        failure=FAILURE,
        recoveries=[
            RecoverySpec("visual_realign", ("GRASP_FAILED",), {"object_visible": True}),
            RecoverySpec("retry_same", ("GRASP_FAILED",)),
        ],
    )
    assert decision.selected_recovery == "retry_same"


def test_duplicate_recovery_experience_is_idempotent_and_conflict_rejected():
    base = RecoveryExperienceRecord(
        goal_predicate="ON_TOP_OF",
        state_context=STATE.context(CONTEXT_KEYS),
        failure_code=FAILURE.code,
        failure_attribution=FAILURE.attribution,
        recovery_action="retry_same",
        recovery_success=True,
        experience_id="recovery-1",
    )
    store = RecoveryExperienceStore([base])
    assert store.add(base) is False
    assert len(store.exact_context(
        goal_predicate="ON_TOP_OF",
        state_context=STATE.context(CONTEXT_KEYS),
        failure=FAILURE,
        recovery_action="retry_same",
    )) == 1
    with pytest.raises(ValueError, match="conflicting duplicate recovery experience_id"):
        store.add(RecoveryExperienceRecord(
            goal_predicate="ON_TOP_OF",
            state_context=STATE.context(CONTEXT_KEYS),
            failure_code=FAILURE.code,
            failure_attribution=FAILURE.attribution,
            recovery_action="retry_same",
            recovery_success=False,
            experience_id="recovery-1",
        ))
