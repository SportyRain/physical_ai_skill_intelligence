from __future__ import annotations

from dataclasses import dataclass

from .goal import Goal
from .recovery import (
    EmpiricalRecoveryOutcomeEstimator,
    FailureState,
    RecoveryDecision,
    RecoveryDecisionEngine,
    RecoveryExperienceRecord,
    RecoveryExperienceStore,
    RecoverySpec,
)
from .state import WorldState


@dataclass(frozen=True)
class RecoveryEvidenceBenchmarkResult:
    without_relevant_experience: RecoveryDecision
    with_relevant_real_experience: RecoveryDecision
    selection_changed: bool
    estimate_changed: bool
    evidence_count: int


def run_ready_recovery_decision_benchmark(
    records: tuple[RecoveryExperienceRecord, ...],
) -> RecoveryEvidenceBenchmarkResult:
    """Connect imported real READY recovery evidence to the M4 decision kernel."""

    if not records:
        raise ValueError("recovery benchmark requires real recovery evidence")
    context = records[0].state_context
    if any(record.state_context != context for record in records):
        raise ValueError("recovery benchmark records must have exactly identical context")
    if any(record.goal_predicate != "CANONICAL_READY" for record in records):
        raise ValueError("recovery benchmark requires CANONICAL_READY evidence")
    if any(record.failure_code != records[0].failure_code for record in records):
        raise ValueError("recovery benchmark records must share one exact failure code")
    if any(record.failure_attribution != records[0].failure_attribution for record in records):
        raise ValueError("recovery benchmark records must share one exact failure attribution")

    goal = Goal("CANONICAL_READY", subject="ur3_runtime")
    state = WorldState(dict(context))
    failure = FailureState(records[0].failure_code, records[0].failure_attribution)
    # Both identities come from the existing provider READY contract. Declared
    # order intentionally makes the no-evidence baseline choose the fail-closed
    # CHECK_ONLY action. Real evidence must earn any change away from that tie.
    recoveries = [
        RecoverySpec(
            "LEAVE_CONTROLLER_UNCHANGED",
            (records[0].failure_code,),
            provider="ur3_visual_servoing",
        ),
        RecoverySpec(
            "CLEAN_STALE_FORCE_PASSTHROUGH",
            (records[0].failure_code,),
            provider="ur3_visual_servoing",
        ),
    ]
    context_keys = tuple(context.keys())

    def decide(store: RecoveryExperienceStore) -> RecoveryDecision:
        return RecoveryDecisionEngine(
            EmpiricalRecoveryOutcomeEstimator(store),
            context_keys=context_keys,
        ).rank(goal=goal, state=state, failure=failure, recoveries=recoveries)

    without = decide(RecoveryExperienceStore())
    with_real = decide(RecoveryExperienceStore(records))
    before_by_action = {row.recovery_action: row for row in without.candidates}
    after_by_action = {row.recovery_action: row for row in with_real.candidates}
    estimate_changed = any(
        before_by_action[action].expected_success != after_by_action[action].expected_success
        or before_by_action[action].evidence_count != after_by_action[action].evidence_count
        or before_by_action[action].mean_cost != after_by_action[action].mean_cost
        for action in before_by_action
    )
    return RecoveryEvidenceBenchmarkResult(
        without_relevant_experience=without,
        with_relevant_real_experience=with_real,
        selection_changed=without.selected_recovery != with_real.selected_recovery,
        estimate_changed=estimate_changed,
        evidence_count=sum(row.evidence_count for row in with_real.candidates),
    )
