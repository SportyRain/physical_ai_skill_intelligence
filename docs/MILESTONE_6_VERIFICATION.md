# Milestone 6 Verification — Bounded Decision → Failure → Recovery → Re-evaluation Loop

Date: 2026-09-07

## Authoritative starting point

```text
REPOSITORY = SportyRain/physical_ai_skill_intelligence
AUTHORITATIVE_BRANCH = main
AUTHORITATIVE_COMMIT_BEFORE_M6 = a7c773c02c8c4abb3ef60f2da1551913d5d45617
AUTHORITATIVE_TREE_BEFORE_M6 = a2ecc2d5259868c42f09174a3feb1e32b5d085e8
PRE_M6_CURRENT_MAIN_REGRESSION = 36 passed
```

The authoritative `main` branch was re-read before implementation. The M1-M5 source/test blobs used for development match the authoritative M5 tree. The existing 36-test suite was re-run before M6 and passed unchanged.

## Scope

Milestone 6 connects the already-existing normal decision and recovery decision paths into one bounded software-only loop:

```text
Goal
-> Current World State
-> Normal Skill Decision
-> Offline / Mock Execution
-> Observed Outcome
   -> success: explicit state update -> goal verification -> complete or normal re-evaluation
   -> failure: FailureState -> Recovery Decision -> offline recovery execution
      -> explicit state update -> original goal verification -> complete or normal re-evaluation
```

The original `Goal` object is preserved through the complete trace. No new goal is substituted after failure or recovery.

This milestone does not add or execute real UR3 motion, ROS motion, controllers, MoveIt wrappers, visual servoing, LLMs, RL, VLA, online learning, or self-learning. Existing UR3 repositories remain stable skill/evidence providers and were not modified.

## Implemented component

New module:

```text
src/physical_ai_skill_intelligence/bounded_loop.py
```

Minimal types:

- `ExecutionBudget`
- `ExecutionObservation`
- `BudgetRemaining`
- `ExecutionTraceStep`
- `TerminalResult`
- `BoundedDecisionRecoveryExecutor`

The executor composes the existing `DecisionEngine` and `RecoveryDecisionEngine`; it does not replace them with a new manager/orchestration framework.

## Bounded autonomy contract

`ExecutionBudget` requires explicit bounds for:

```text
max_total_steps
max_recovery_attempts
max_same_failure_repeats
max_total_cost
```

Clean terminal abort reasons include:

```text
MAX_TOTAL_STEPS_EXCEEDED
MAX_RECOVERY_ATTEMPTS_EXCEEDED
MAX_SAME_FAILURE_REPEATS_EXCEEDED
MAX_TOTAL_COST_EXCEEDED
TERMINAL_FAILURE:<failure-code>
NO_APPLICABLE_SKILL
NO_APPLICABLE_RECOVERY
```

`max_same_failure_repeats` counts consecutive recurrences after the first occurrence. A successful recovery does not erase the prior failure recurrence history before the original goal has made progress; therefore a repeated failure -> recovery -> same failure cycle cannot continue indefinitely. Any loop is also independently bounded by `max_total_steps`.

## Action success remains separate from goal success

`ExecutionObservation.action_success` represents only the selected skill/recovery execution outcome.

After every observation:

1. `state_updates` are applied to a new observable `WorldState`;
2. the same original `Goal` is evaluated against that updated state;
3. only the goal evaluator may produce `COMPLETE`.

Therefore:

```text
recovery action success != original goal success
skill action success != original goal success
```

A successful recovery with a still-false goal returns to the normal decision phase.

## State update contract

Offline/mock executors return explicit `state_updates`. The bounded loop applies those updates to `WorldState`; no hidden success mutation exists inside the decision layer.

The M6 success fixture uses the real M5 recovery family for decision evidence:

```text
failure = PA-READY-818
failure attribution = NONCANONICAL_CONTROLLER_ACTIVE
selected recovery = CLEAN_STALE_FORCE_PASSTHROUGH
```

The M5 raw evidence supports the stale ForceMode/Passthrough controller pair becoming inactive and final READY. M6 additionally uses an explicitly labelled synthetic evaluator fact (`goal:CANONICAL_READY=True`) in the offline fixture to express the post-transition goal check. That synthetic fact is test-fixture state, not a new raw-evidence claim.

## Execution trace

Every executed normal skill or recovery produces one immutable `ExecutionTraceStep` containing:

```text
step_index
phase
goal
state_before
decision
selected_skill / selected_recovery
observed_result
failure
state_after
goal_satisfied_after
budget_remaining
terminal_status
abort_reason
```

The trace is decision/execution evidence only; no raw sensor logging framework was added.

## Required scenarios verified

### 1. Recovery success -> goal complete

```text
normal decision
-> PA-READY-818 failure
-> recovery decision selects CLEAN_STALE_FORCE_PASSTHROUGH using M5 real recovery evidence
-> offline recovery succeeds
-> explicit controller-state update + synthetic goal evaluator fact
-> original CANONICAL_READY goal verified
-> COMPLETE
```

### 2. Recovery success but goal remains false

```text
normal failure
-> recovery success
-> state updated
-> goal remains false
-> normal decision runs again
-> later explicit state update satisfies goal
-> COMPLETE
```

This verifies that recovery success is not treated as task/goal success.

### 3. Recovery failure

A failed recovery remains in recovery handling only while the recovery-attempt budget permits. With one allowed recovery attempt, the next attempted recovery is prevented and returns `MAX_RECOVERY_ATTEMPTS_EXCEEDED`.

### 4. Same failure loop prevention

A repeated identical `(failure code, attribution)` after a successful recovery increments the recurrence count. When the configured recurrence bound is reached, execution ends with `MAX_SAME_FAILURE_REPEATS_EXCEEDED` before another unbounded recovery cycle can start.

### 5. Total step budget

Repeated action-success-but-goal-false execution ends with `MAX_TOTAL_STEPS_EXCEEDED` at the configured step bound.

### 6. Recovery budget

A configuration with zero permitted recovery attempts allows the normal failure observation but prevents recovery execution and returns `MAX_RECOVERY_ATTEMPTS_EXCEEDED`.

### 7. Terminal failure

A non-retryable/terminal normal failure returns `TERMINAL_FAILURE:<code>` immediately. Recovery execution is not entered.

### 8. Determinism

Two separately constructed loops with identical Goal, initial WorldState, stores, mock transitions, and budgets produce equal `TerminalResult` objects and equal execution traces.

### Additional total-cost bound

A mock observation that consumes more than `max_total_cost` returns structured `MAX_TOTAL_COST_EXCEEDED`. This is independent of the hard total-step bound.

## Verification results

```text
PRE_M6_CURRENT_MAIN_REGRESSION = 36 passed
MILESTONE_6_TOTAL_TESTS = 45 passed
PYTHON_COMPILE = PASS
```

## Claim boundary

```text
BOUNDED_DECISION_RECOVERY_LOOP = VERIFIED
NORMAL_DECISION_TO_FAILURE_TRANSITION = VERIFIED
FAILURE_TO_RECOVERY_DECISION = VERIFIED
RECOVERY_TO_STATE_REEVALUATION = VERIFIED
GOAL_REEVALUATION_AFTER_RECOVERY = VERIFIED

MAX_STEP_BOUND = VERIFIED
RECOVERY_ATTEMPT_BOUND = VERIFIED
SAME_FAILURE_LOOP_PREVENTION = VERIFIED
TOTAL_COST_BOUND = VERIFIED
TERMINAL_ABORT = VERIFIED
DETERMINISTIC_BOUNDED_LOOP = VERIFIED

OFFLINE_DECISION_RECOVERY_REGRESSION = VERIFIED

REAL_RECOVERY_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
RECOVERY_DECISION_IS_BETTER = NOT_VERIFIED
GENERAL_RECOVERY_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
NOVEL_AI_ALGORITHM = NOT_VERIFIED
```

Offline completion does not establish real-robot autonomy or real-world performance improvement.
