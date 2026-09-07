from __future__ import annotations

from pathlib import Path

from physical_ai_skill_intelligence import (
    BoundedDecisionRecoveryExecutor,
    DecisionEngine,
    EmpiricalOutcomeEstimator,
    EmpiricalRecoveryOutcomeEstimator,
    ExecutionBudget,
    ExecutionObservation,
    ExperienceStore,
    FailureState,
    Goal,
    RecoveryDecisionEngine,
    RecoveryExperienceStore,
    RecoverySpec,
    SkillSpec,
    Ur3VisualServoingRecoveryEvidenceImporter,
    WorldState,
)

PROVIDER_COMMIT = "fec0021d0d7b4ee076842923e7627f1e7486fa71"
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "ur3_visual_servoing"
RUN_PATH = FIXTURE_ROOT / "evidence/runs/REAL_READY_STALE_CLEANUP_20260831_001.json"


def _real_recovery_record():
    return Ur3VisualServoingRecoveryEvidenceImporter(
        provider_commit=PROVIDER_COMMIT
    ).import_run_manifest(RUN_PATH, provider_root=FIXTURE_ROOT)[0]


def _engines(*, recovery_records=(), recovery_context_keys=()):
    normal = DecisionEngine(
        EmpiricalOutcomeEstimator(ExperienceStore()),
        context_keys=("goal:CANONICAL_READY",),
        ranking_mode="lexicographic_success_then_cost",
    )
    recovery = RecoveryDecisionEngine(
        EmpiricalRecoveryOutcomeEstimator(RecoveryExperienceStore(recovery_records)),
        context_keys=tuple(recovery_context_keys),
    )
    return normal, recovery


def _executor(
    *,
    normal_executor,
    recovery_executor,
    budget=None,
    recovery_records=(),
    recovery_context_keys=(),
    recoveries=None,
):
    normal, recovery = _engines(
        recovery_records=recovery_records,
        recovery_context_keys=recovery_context_keys,
    )
    return BoundedDecisionRecoveryExecutor(
        normal_decision_engine=normal,
        recovery_decision_engine=recovery,
        skills=[SkillSpec("CHECK_CANONICAL_READY", ("CANONICAL_READY",), provider="mock")],
        recoveries=recoveries
        or [RecoverySpec("RECOVER", ("PA-READY-818",), provider="mock")],
        normal_executor=normal_executor,
        recovery_executor=recovery_executor,
        budget=budget
        or ExecutionBudget(
            max_total_steps=8,
            max_recovery_attempts=3,
            max_same_failure_repeats=2,
            max_total_cost=20.0,
        ),
    )


def test_real_recovery_success_updates_state_then_goal_complete():
    record = _real_recovery_record()
    initial_facts = dict(record.state_context)
    initial_facts["goal:CANONICAL_READY"] = False
    initial = WorldState(initial_facts)
    failure = FailureState(record.failure_code, record.failure_attribution)

    def normal_execute(_skill, _goal, _state):
        return ExecutionObservation(action_success=False, failure=failure, cost=1.0)

    def recovery_execute(action, _goal, _state, _failure):
        assert action == "CLEAN_STALE_FORCE_PASSTHROUGH"
        return ExecutionObservation(
            action_success=True,
            state_updates={
                "passthrough_trajectory_controller": "inactive",
                "force_mode_controller": "inactive",
                # Synthetic evaluator fact for the offline fixture; the M5 raw
                # evidence itself remains preserved separately in its fixture.
                "goal:CANONICAL_READY": True,
            },
            cost=1.0,
        )

    loop = _executor(
        normal_executor=normal_execute,
        recovery_executor=recovery_execute,
        recovery_records=(record,),
        recovery_context_keys=tuple(record.state_context.keys()),
        recoveries=[
            RecoverySpec("LEAVE_CONTROLLER_UNCHANGED", (record.failure_code,), provider="ur3_visual_servoing"),
            RecoverySpec("CLEAN_STALE_FORCE_PASSTHROUGH", (record.failure_code,), provider="ur3_visual_servoing"),
        ],
    )
    result = loop.run(goal=Goal("CANONICAL_READY", subject="ur3_runtime"), initial_state=initial)

    assert result.status == "COMPLETE"
    assert result.goal_satisfied is True
    assert [step.phase for step in result.trace] == ["NORMAL_EXECUTION", "RECOVERY_EXECUTION"]
    assert result.trace[1].selected_recovery == "CLEAN_STALE_FORCE_PASSTHROUGH"
    assert result.trace[1].observed_result.action_success is True
    assert result.trace[1].goal_satisfied_after is True
    assert result.final_state.get("force_mode_controller") == "inactive"


def test_recovery_success_does_not_imply_goal_success_and_normal_re_evaluates():
    calls = {"normal": 0}
    failure = FailureState("PA-READY-818", "NONCANONICAL_CONTROLLER_ACTIVE")

    def normal_execute(_skill, _goal, _state):
        calls["normal"] += 1
        if calls["normal"] == 1:
            return ExecutionObservation(action_success=False, failure=failure)
        return ExecutionObservation(
            action_success=True,
            state_updates={"goal:CANONICAL_READY": True},
        )

    def recovery_execute(_action, _goal, _state, _failure):
        return ExecutionObservation(
            action_success=True,
            state_updates={"noncanonical_controller_active": False},
        )

    loop = _executor(normal_executor=normal_execute, recovery_executor=recovery_execute)
    result = loop.run(
        goal=Goal("CANONICAL_READY"),
        initial_state=WorldState({"goal:CANONICAL_READY": False, "noncanonical_controller_active": True}),
    )

    assert result.status == "COMPLETE"
    assert [step.phase for step in result.trace] == [
        "NORMAL_EXECUTION",
        "RECOVERY_EXECUTION",
        "NORMAL_EXECUTION",
    ]
    assert result.trace[1].observed_result.action_success is True
    assert result.trace[1].goal_satisfied_after is False
    assert result.trace[1].terminal_status == "CONTINUE"


def test_recovery_failure_is_stopped_by_recovery_attempt_budget():
    failure = FailureState("PA-READY-818", "NONCANONICAL_CONTROLLER_ACTIVE")
    recovery_calls = {"count": 0}

    def normal_execute(_skill, _goal, _state):
        return ExecutionObservation(action_success=False, failure=failure)

    def recovery_execute(_action, _goal, _state, _failure):
        recovery_calls["count"] += 1
        return ExecutionObservation(action_success=False, failure=failure)

    loop = _executor(
        normal_executor=normal_execute,
        recovery_executor=recovery_execute,
        budget=ExecutionBudget(8, 1, 5, 20.0),
    )
    result = loop.run(goal=Goal("CANONICAL_READY"), initial_state=WorldState({"goal:CANONICAL_READY": False}))

    assert result.status == "ABORT"
    assert result.abort_reason == "MAX_RECOVERY_ATTEMPTS_EXCEEDED"
    assert recovery_calls["count"] == 1
    assert result.recovery_attempts == 1


def test_same_failure_repeat_budget_prevents_infinite_recovery_loop():
    failure = FailureState("PA-READY-818", "NONCANONICAL_CONTROLLER_ACTIVE")
    recovery_calls = {"count": 0}

    def normal_execute(_skill, _goal, _state):
        return ExecutionObservation(action_success=False, failure=failure)

    def recovery_execute(_action, _goal, _state, _failure):
        recovery_calls["count"] += 1
        return ExecutionObservation(action_success=True, state_updates={"progress_marker": recovery_calls["count"]})

    loop = _executor(
        normal_executor=normal_execute,
        recovery_executor=recovery_execute,
        budget=ExecutionBudget(10, 5, 1, 20.0),
    )
    result = loop.run(goal=Goal("CANONICAL_READY"), initial_state=WorldState({"goal:CANONICAL_READY": False}))

    assert result.status == "ABORT"
    assert result.abort_reason == "MAX_SAME_FAILURE_REPEATS_EXCEEDED"
    assert recovery_calls["count"] == 1
    assert result.total_steps == 3


def test_total_step_budget_aborts_before_unbounded_re_evaluation():
    def normal_execute(_skill, _goal, _state):
        return ExecutionObservation(action_success=True, state_updates={"counter": 1})

    def recovery_execute(*_args):
        raise AssertionError("recovery must not run")

    loop = _executor(
        normal_executor=normal_execute,
        recovery_executor=recovery_execute,
        budget=ExecutionBudget(2, 2, 2, 20.0),
    )
    result = loop.run(goal=Goal("CANONICAL_READY"), initial_state=WorldState({"goal:CANONICAL_READY": False}))

    assert result.status == "ABORT"
    assert result.abort_reason == "MAX_TOTAL_STEPS_EXCEEDED"
    assert result.total_steps == 2
    assert len(result.trace) == 2


def test_recovery_budget_zero_blocks_recovery_execution():
    failure = FailureState("PA-READY-818", "NONCANONICAL_CONTROLLER_ACTIVE")

    def normal_execute(_skill, _goal, _state):
        return ExecutionObservation(action_success=False, failure=failure)

    def recovery_execute(*_args):
        raise AssertionError("recovery must not run")

    loop = _executor(
        normal_executor=normal_execute,
        recovery_executor=recovery_execute,
        budget=ExecutionBudget(5, 0, 2, 20.0),
    )
    result = loop.run(goal=Goal("CANONICAL_READY"), initial_state=WorldState({"goal:CANONICAL_READY": False}))

    assert result.status == "ABORT"
    assert result.abort_reason == "MAX_RECOVERY_ATTEMPTS_EXCEEDED"
    assert result.recovery_attempts == 0


def test_terminal_failure_aborts_without_entering_recovery():
    failure = FailureState("PA-FATAL-001", "TERMINAL_FIXTURE_FAILURE")

    def normal_execute(_skill, _goal, _state):
        return ExecutionObservation(
            action_success=False,
            failure=failure,
            retryable=False,
            terminal_failure=True,
        )

    def recovery_execute(*_args):
        raise AssertionError("terminal failure must not enter recovery")

    loop = _executor(normal_executor=normal_execute, recovery_executor=recovery_execute)
    result = loop.run(goal=Goal("CANONICAL_READY"), initial_state=WorldState({"goal:CANONICAL_READY": False}))

    assert result.status == "ABORT"
    assert result.abort_reason == "TERMINAL_FAILURE:PA-FATAL-001"
    assert result.recovery_attempts == 0
    assert len(result.trace) == 1


def test_total_cost_budget_aborts_with_structured_terminal_result():
    def normal_execute(_skill, _goal, _state):
        return ExecutionObservation(action_success=True, cost=2.5)

    def recovery_execute(*_args):
        raise AssertionError("recovery must not run")

    loop = _executor(
        normal_executor=normal_execute,
        recovery_executor=recovery_execute,
        budget=ExecutionBudget(5, 2, 2, 2.0),
    )
    result = loop.run(goal=Goal("CANONICAL_READY"), initial_state=WorldState({"goal:CANONICAL_READY": False}))

    assert result.status == "ABORT"
    assert result.abort_reason == "MAX_TOTAL_COST_EXCEEDED"
    assert result.total_cost == 2.5
    assert result.trace[-1].terminal_status == "ABORT"


def test_determinism_same_inputs_produce_identical_trace_and_terminal_result():
    failure = FailureState("PA-READY-818", "NONCANONICAL_CONTROLLER_ACTIVE")

    def build_loop():
        calls = {"normal": 0}

        def normal_execute(_skill, _goal, _state):
            calls["normal"] += 1
            if calls["normal"] == 1:
                return ExecutionObservation(action_success=False, failure=failure, cost=1.0)
            return ExecutionObservation(action_success=True, state_updates={"goal:CANONICAL_READY": True}, cost=1.0)

        def recovery_execute(_action, _goal, _state, _failure):
            return ExecutionObservation(action_success=True, state_updates={"recovered": True}, cost=1.0)

        return _executor(normal_executor=normal_execute, recovery_executor=recovery_execute)

    goal = Goal("CANONICAL_READY")
    initial = WorldState({"goal:CANONICAL_READY": False})
    first = build_loop().run(goal=goal, initial_state=initial)
    second = build_loop().run(goal=goal, initial_state=initial)

    assert first == second
    assert first.trace == second.trace
    assert first.status == "COMPLETE"
