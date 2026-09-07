from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable

from ._integrity import snapshot_mapping, finite_number
from .decision import Decision, DecisionEngine
from .goal import Goal
from .goal_verification import goal_satisfied
from .recovery import FailureState, RecoveryDecision, RecoveryDecisionEngine, RecoverySpec
from .skill import SkillSpec
from .state import WorldState


@dataclass(frozen=True)
class ExecutionBudget:
    max_total_steps: int
    max_recovery_attempts: int
    max_same_failure_repeats: int
    max_total_cost: float

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        for name in ("max_total_steps", "max_recovery_attempts", "max_same_failure_repeats"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer")
        if self.max_total_steps <= 0:
            raise ValueError("max_total_steps must be > 0")
        if self.max_recovery_attempts < 0:
            raise ValueError("max_recovery_attempts must be >= 0")
        if self.max_same_failure_repeats < 0:
            raise ValueError("max_same_failure_repeats must be >= 0")
        finite_number(self.max_total_cost, "max_total_cost")


@dataclass(frozen=True)
class ExecutionObservation:
    """Observable result returned by an offline/mock execution fixture.

    ``action_success`` is only execution success. Goal completion is evaluated
    separately after applying ``state_updates`` to the explicit WorldState.
    """

    action_success: bool
    state_updates: Mapping[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    failure: FailureState | None = None
    retryable: bool = True
    terminal_failure: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "state_updates", snapshot_mapping(self.state_updates))
        object.__setattr__(self, "details", snapshot_mapping(self.details))
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.action_success, bool):
            raise ValueError("action_success must be bool")
        finite_number(self.cost, "cost")
        if type(self.retryable) is not bool or type(self.terminal_failure) is not bool:
            raise ValueError("retryable and terminal_failure must be bool")
        if self.action_success and (self.failure is not None or self.terminal_failure):
            raise ValueError("successful execution cannot carry a failure")
        if self.terminal_failure and self.retryable:
            raise ValueError("terminal failure cannot be retryable")
        if not self.action_success and self.failure is None:
            raise ValueError("failed execution requires explicit failure")
        if self.failure is not None:
            self.failure.validate()


@dataclass(frozen=True)
class BudgetRemaining:
    total_steps: int
    recovery_attempts: int
    same_failure_repeats: int
    total_cost: float


@dataclass(frozen=True)
class ExecutionTraceStep:
    step_index: int
    phase: str
    goal: Goal
    state_before: WorldState
    decision: Decision | RecoveryDecision
    selected_skill: str | None
    selected_recovery: str | None
    observed_result: ExecutionObservation
    failure: FailureState | None
    state_after: WorldState
    goal_satisfied_after: bool
    budget_remaining: BudgetRemaining
    terminal_status: str
    abort_reason: str | None = None


@dataclass(frozen=True)
class TerminalResult:
    status: str
    goal: Goal
    final_state: WorldState
    goal_satisfied: bool
    total_steps: int
    recovery_attempts: int
    total_cost: float
    abort_reason: str | None
    trace: tuple[ExecutionTraceStep, ...]


NormalExecutor = Callable[[str, Goal, WorldState], ExecutionObservation]
RecoveryExecutor = Callable[[str, Goal, WorldState, FailureState], ExecutionObservation]
GoalEvaluator = Callable[[Goal, WorldState], bool]


class BoundedDecisionRecoveryExecutor:
    """Minimal software-only decision -> failure -> recovery -> re-evaluation loop."""

    def __init__(
        self,
        *,
        normal_decision_engine: DecisionEngine,
        recovery_decision_engine: RecoveryDecisionEngine,
        skills: list[SkillSpec],
        recoveries: list[RecoverySpec],
        normal_executor: NormalExecutor,
        recovery_executor: RecoveryExecutor,
        budget: ExecutionBudget,
        goal_evaluator: GoalEvaluator = goal_satisfied,
    ):
        budget.validate()
        self.normal_decision_engine = normal_decision_engine
        self.recovery_decision_engine = recovery_decision_engine
        self.skills = list(skills)
        self.recoveries = list(recoveries)
        self.normal_executor = normal_executor
        self.recovery_executor = recovery_executor
        self.budget = budget
        self.goal_evaluator = goal_evaluator

    @staticmethod
    def _execute(executor, *args, phase: str) -> ExecutionObservation:
        # Only the synchronous call/result boundary is normalized. No timeout or cancel.
        try:
            observation = executor(*args)
            if not isinstance(observation, ExecutionObservation):
                raise ValueError("executor must return ExecutionObservation")
            observation.validate()
            return observation
        except Exception as exc:
            return ExecutionObservation(
                action_success=False,
                failure=FailureState(f"{phase}_EXECUTOR_EXCEPTION"),
                retryable=False,
                terminal_failure=True,
                details={"exception_type": type(exc).__name__, "exception_message": str(exc),
                         "execution_cost": "NOT_VERIFIED", "state_updates": "NOT_VERIFIED"},
            )

    @staticmethod
    def _apply_updates(state: WorldState, updates: dict[str, Any]) -> WorldState:
        facts = dict(state.facts)
        facts.update(updates)
        return WorldState(facts)

    def _remaining(
        self,
        *,
        total_steps: int,
        recovery_attempts: int,
        same_failure_repeats: int,
        total_cost: float,
    ) -> BudgetRemaining:
        return BudgetRemaining(
            total_steps=max(0, self.budget.max_total_steps - total_steps),
            recovery_attempts=max(0, self.budget.max_recovery_attempts - recovery_attempts),
            same_failure_repeats=max(
                0, self.budget.max_same_failure_repeats - same_failure_repeats
            ),
            total_cost=max(0.0, self.budget.max_total_cost - total_cost),
        )

    @staticmethod
    def _failure_key(failure: FailureState) -> tuple[str, Any]:
        return failure.code, failure.attribution

    @staticmethod
    def _abort(
        *,
        reason: str,
        goal: Goal,
        state: WorldState,
        total_steps: int,
        recovery_attempts: int,
        total_cost: float,
        trace: list[ExecutionTraceStep],
        goal_evaluator: GoalEvaluator,
    ) -> TerminalResult:
        return TerminalResult(
            status="ABORT",
            goal=goal,
            final_state=state,
            goal_satisfied=goal_evaluator(goal, state),
            total_steps=total_steps,
            recovery_attempts=recovery_attempts,
            total_cost=total_cost,
            abort_reason=reason,
            trace=tuple(trace),
        )

    def run(self, *, goal: Goal, initial_state: WorldState) -> TerminalResult:
        state = initial_state
        trace: list[ExecutionTraceStep] = []
        total_steps = 0
        recovery_attempts = 0
        total_cost = 0.0
        phase = "NORMAL"
        current_failure: FailureState | None = None
        last_failure_key: tuple[str, Any] | None = None
        same_failure_repeats = 0

        if self.goal_evaluator(goal, state):
            return TerminalResult(
                status="COMPLETE",
                goal=goal,
                final_state=state,
                goal_satisfied=True,
                total_steps=0,
                recovery_attempts=0,
                total_cost=0.0,
                abort_reason=None,
                trace=(),
            )

        while True:
            if total_steps >= self.budget.max_total_steps:
                return self._abort(
                    reason="MAX_TOTAL_STEPS_EXCEEDED",
                    goal=goal,
                    state=state,
                    total_steps=total_steps,
                    recovery_attempts=recovery_attempts,
                    total_cost=total_cost,
                    trace=trace,
                    goal_evaluator=self.goal_evaluator,
                )

            if phase == "NORMAL":
                try:
                    decision = self.normal_decision_engine.rank(
                        goal=goal,
                        state=state,
                        skills=self.skills,
                    )
                except RuntimeError as exc:
                    return self._abort(
                        reason=str(exc),
                        goal=goal,
                        state=state,
                        total_steps=total_steps,
                        recovery_attempts=recovery_attempts,
                        total_cost=total_cost,
                        trace=trace,
                        goal_evaluator=self.goal_evaluator,
                    )

                before = state
                observation = self._execute(
                    self.normal_executor, decision.selected_skill, goal, before, phase="NORMAL"
                )
                state = self._apply_updates(before, observation.state_updates)
                total_steps += 1
                total_cost += observation.cost
                goal_ok = self.goal_evaluator(goal, state)
                abort_reason: str | None = None

                if total_cost > self.budget.max_total_cost:
                    abort_reason = "MAX_TOTAL_COST_EXCEEDED"
                elif observation.action_success:
                    # A successful skill execution is not automatically goal success.
                    current_failure = None
                    # Goal false provides no verified progress boundary. Retain history.
                else:
                    assert observation.failure is not None
                    current_failure = observation.failure
                    key = self._failure_key(current_failure)
                    if key == last_failure_key:
                        same_failure_repeats += 1
                        if same_failure_repeats >= self.budget.max_same_failure_repeats:
                            abort_reason = "MAX_SAME_FAILURE_REPEATS_EXCEEDED"
                    else:
                        last_failure_key = key
                        same_failure_repeats = 0

                    if observation.terminal_failure or not observation.retryable:
                        abort_reason = f"TERMINAL_FAILURE:{current_failure.code}"

                terminal_status = (
                    "ABORT" if abort_reason else "COMPLETE" if goal_ok else "CONTINUE"
                )
                trace.append(
                    ExecutionTraceStep(
                        step_index=total_steps,
                        phase="NORMAL_EXECUTION",
                        goal=goal,
                        state_before=before,
                        decision=decision,
                        selected_skill=decision.selected_skill,
                        selected_recovery=None,
                        observed_result=observation,
                        failure=observation.failure,
                        state_after=state,
                        goal_satisfied_after=goal_ok,
                        budget_remaining=self._remaining(
                            total_steps=total_steps,
                            recovery_attempts=recovery_attempts,
                            same_failure_repeats=same_failure_repeats,
                            total_cost=total_cost,
                        ),
                        terminal_status=terminal_status,
                        abort_reason=abort_reason,
                    )
                )

                if abort_reason:
                    return self._abort(
                        reason=abort_reason,
                        goal=goal,
                        state=state,
                        total_steps=total_steps,
                        recovery_attempts=recovery_attempts,
                        total_cost=total_cost,
                        trace=trace,
                        goal_evaluator=self.goal_evaluator,
                    )
                if goal_ok:
                    return TerminalResult(
                        status="COMPLETE",
                        goal=goal,
                        final_state=state,
                        goal_satisfied=True,
                        total_steps=total_steps,
                        recovery_attempts=recovery_attempts,
                        total_cost=total_cost,
                        abort_reason=None,
                        trace=tuple(trace),
                    )
                phase = "NORMAL" if observation.action_success else "RECOVERY"
                continue

            assert current_failure is not None
            if recovery_attempts >= self.budget.max_recovery_attempts:
                return self._abort(
                    reason="MAX_RECOVERY_ATTEMPTS_EXCEEDED",
                    goal=goal,
                    state=state,
                    total_steps=total_steps,
                    recovery_attempts=recovery_attempts,
                    total_cost=total_cost,
                    trace=trace,
                    goal_evaluator=self.goal_evaluator,
                )

            try:
                recovery_decision = self.recovery_decision_engine.rank(
                    goal=goal,
                    state=state,
                    failure=current_failure,
                    recoveries=self.recoveries,
                )
            except RuntimeError as exc:
                return self._abort(
                    reason=str(exc),
                    goal=goal,
                    state=state,
                    total_steps=total_steps,
                    recovery_attempts=recovery_attempts,
                    total_cost=total_cost,
                    trace=trace,
                    goal_evaluator=self.goal_evaluator,
                )

            before = state
            observed_failure = current_failure
            observation = self._execute(
                self.recovery_executor,
                recovery_decision.selected_recovery,
                goal,
                before,
                observed_failure,
                phase="RECOVERY",
            )
            state = self._apply_updates(before, observation.state_updates)
            recovery_attempts += 1
            total_steps += 1
            total_cost += observation.cost
            goal_ok = self.goal_evaluator(goal, state)
            abort_reason = None

            if total_cost > self.budget.max_total_cost:
                abort_reason = "MAX_TOTAL_COST_EXCEEDED"
            elif observation.action_success:
                # Recovery success is independent from the original goal result.
                current_failure = None
            else:
                next_failure = observation.failure or observed_failure
                current_failure = next_failure
                key = self._failure_key(next_failure)
                if key == last_failure_key:
                    same_failure_repeats += 1
                    if same_failure_repeats >= self.budget.max_same_failure_repeats:
                        abort_reason = "MAX_SAME_FAILURE_REPEATS_EXCEEDED"
                else:
                    last_failure_key = key
                    same_failure_repeats = 0
                if observation.terminal_failure or not observation.retryable:
                    abort_reason = f"TERMINAL_FAILURE:{next_failure.code}"

            terminal_status = (
                "ABORT" if abort_reason else "COMPLETE" if goal_ok else "CONTINUE"
            )
            trace.append(
                ExecutionTraceStep(
                    step_index=total_steps,
                    phase="RECOVERY_EXECUTION",
                    goal=goal,
                    state_before=before,
                    decision=recovery_decision,
                    selected_skill=None,
                    selected_recovery=recovery_decision.selected_recovery,
                    observed_result=observation,
                    failure=observation.failure or observed_failure,
                    state_after=state,
                    goal_satisfied_after=goal_ok,
                    budget_remaining=self._remaining(
                        total_steps=total_steps,
                        recovery_attempts=recovery_attempts,
                        same_failure_repeats=same_failure_repeats,
                        total_cost=total_cost,
                    ),
                    terminal_status=terminal_status,
                    abort_reason=abort_reason,
                )
            )

            if abort_reason:
                return self._abort(
                    reason=abort_reason,
                    goal=goal,
                    state=state,
                    total_steps=total_steps,
                    recovery_attempts=recovery_attempts,
                    total_cost=total_cost,
                    trace=trace,
                    goal_evaluator=self.goal_evaluator,
                )
            if goal_ok:
                return TerminalResult(
                    status="COMPLETE",
                    goal=goal,
                    final_state=state,
                    goal_satisfied=True,
                    total_steps=total_steps,
                    recovery_attempts=recovery_attempts,
                    total_cost=total_cost,
                    abort_reason=None,
                    trace=tuple(trace),
                )
            phase = "NORMAL" if observation.action_success else "RECOVERY"
