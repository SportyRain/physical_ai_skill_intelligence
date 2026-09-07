# Physical AI Skill Intelligence

Clean-room software core for **Physical Decision Intelligence**.

This project does not implement robot motion, visual servoing, planning, IK/FK, trajectory execution, camera drivers, or robot-specific manipulation. Existing robot repositories remain stable skill/evidence providers.

## Core question

> Given a Goal, Current World State, Candidate Physical Skills / Strategies, and Past Physical Experience, which candidate should be selected next, and why?

```text
Goal
+
Current World State
+
Candidate Skills / Strategies
+
Past Physical Experience
        |
        v
Outcome Estimation
        |
        v
Decision / Ranking
        |
        v
Existing Skill Provider
```

Milestone 4 adds a separate recovery decision path after an observed failure:

```text
Goal + Current World State + Failure + Candidate Recoveries + Past Recovery Experience
-> Recovery Outcome Estimation
-> Recovery Ranking / Selection
```

Milestone 5 connects tracked real failure/recovery evidence to that recovery
decision path without executing the provider or the robot.

Milestone 6 composes the existing normal and recovery decisions into a bounded
offline decision -> failure -> recovery -> state re-evaluation loop.

## Authoritative repository

```text
SportyRain/physical_ai_skill_intelligence
branch: main
status: VERIFIED
```

## Implemented software boundary

- semantically explicit multi-experience representation
- exact-context matching with fail-closed `UNKNOWN` behavior
- source provenance and SHA-256 traceability
- deterministic read-only import of tracked UR3 evidence
- real Push and Pick / Place evidence families
- inspectable empirical outcome baseline
- deterministic experience-conditioned candidate evaluation
- evidence IDs and provenance trace in decision output
- failure-aware recovery experience representation
- exact failure-code / attribution / context matching
- deterministic recovery outcome estimation and ranking
- read-only import of tracked real robot runtime recovery evidence
- runtime recovery provenance trace through outcome estimate and recovery decision
- bounded normal-decision -> failure -> recovery -> original-goal re-evaluation loop
- explicit step/recovery/same-failure/cost budgets with structured aborts
- immutable offline decision/execution trace with observable WorldState transitions
- offline negative and regression tests

## Stable provider investigated

```text
SportyRain/ur3_visual_servoing
Milestone 1-3 inspection commit: b91d3be5a7643f6e91023da8c9d7f339811c7b14
Milestone 5 recovery-evidence snapshot: fec0021d0d7b4ee076842923e7627f1e7486fa71
```

The repository does not copy its controller, perception, ROS, MoveIt, or robot execution implementation. Milestone 4 also does not execute or modify provider-side recovery behavior.

## DO_NOT_REIMPLEMENT

- Universal Robots ROS 2 Driver
- ros2_control
- MoveIt 2 / MoveIt Servo
- IK / FK / Jacobian
- trajectory generation / execution
- collision checking
- camera drivers
- robot-specific visual servoing
- robot-specific pick/place implementation
- robot-specific peg-in-hole controllers
- generic ROS orchestration frameworks

## Current real-evidence benchmark

Candidates:

```text
goal_directed_continuous_push/nominal_baseline
goal_directed_continuous_push/experience_adapted
```

Without relevant experience, both use the explicit Beta(1,1) prior (`P(success)=0.5`).

With the imported real Push evidence:

```text
nominal_baseline:     P(success)=2/3, evidence=1, mean attempts=2
experience_adapted:  P(success)=2/3, evidence=1, mean attempts=3
```

The selected strategy remains `nominal_baseline`. Experience changes the estimates and decision evidence, but this dataset does **not** verify that the decision is better or that the adapted strategy improves performance.

## Failure-aware recovery decision

Milestone 4 introduces a software-only recovery kernel using:

```text
FailureState
RecoverySpec
RecoveryExperienceRecord
EmpiricalRecoveryOutcomeEstimator
RecoveryDecisionEngine
```

Recovery evidence matches exact goal predicate, state context, failure code, failure attribution, and recovery action. `UNKNOWN` is never a wildcard. Recovery candidates must explicitly support the observed failure and satisfy state preconditions.

The recovery estimator is an inspectable Beta-prior baseline, not a learned controller or novel AI algorithm. It selects only a high-level recovery identity; it does not generate motion.

## Real robot runtime recovery evidence integration

Milestone 5 imports the tracked provider pair:

```text
evidence/runs/REAL_READY_STALE_CLEANUP_20260831_001.json
evidence/logs/REAL_READY_STALE_CLEANUP_20260831_001_terminal_transcript.txt
```

The raw transcript explicitly records `PA-READY-818 / NONCANONICAL_CONTROLLER_ACTIVE`, the exact stale ForceMode/Passthrough controller pair, one execute cleanup, canonical inactive controller states afterward, and final `PA-000 / READY`.

The normalized record uses the existing provider high-level action identity `CLEAN_STALE_FORCE_PASSTHROUGH`. In the offline benchmark the no-evidence tie selects `LEAVE_CONTROLLER_UNCHANGED`; with the one applicable real recovery record, `CLEAN_STALE_FORCE_PASSTHROUGH` is selected with `P(recovery_success)=2/3` and evidence count 1. This verifies evidence influence, not general decision superiority.

## Bounded decision / recovery loop

Milestone 6 adds only a software-level executor that composes the existing
`DecisionEngine` and `RecoveryDecisionEngine`:

```text
Goal -> Normal Decision -> Offline Execution
  success -> explicit WorldState update -> Goal Verification
  failure -> Recovery Decision -> Offline Recovery Execution
             -> explicit WorldState update -> original Goal Verification
```

`ExecutionBudget` bounds total synchronous execution calls and recovery attempts,
counts same-key failure recurrences across action successes, and checks reported
cost after each returned observation. Terminal failures and exhausted budgets return
structured `ABORT` results. A successful skill or recovery never implies goal
success; `COMPLETE` is produced only after the updated `WorldState` passes the
goal evaluator.

## M6.1 integrity boundaries

M6.1 hardens the existing offline/reference evaluation harness. Nested JSON-like
record data is copied into read-only mappings and tuples, including state,
experience, goals, observations, and the state snapshots retained in traces.
An empty skill capability list is unsupported. The built-in goal evaluators
support unparameterized `ON_TOP_OF`, `AT`, and `INSERTED` relations with explicit
subject/reference identities, and the global `Goal("CANONICAL_READY")` without
subject/reference/parameters. Other evaluator shapes return false.

Provenance separates `artifact_snapshot_commit` from `experiment_runtime_commit`;
`source_commit` remains the legacy artifact reference. Importers require a full
snapshot SHA, preserve the manifest runtime SHA separately, and never expand
historical abbreviated SHAs by guessing. All manifest and raw evidence paths
must resolve within the declared provider root.

Cost records declare `OBSERVED_COST`, `CONFIGURED_LIMIT`, or `UNKNOWN`, plus a
unit. Only observed costs with a declared compatible unit contribute to the
mean. Pick/Place's `max_pick_attempts` remains a configured limit. Estimates and
candidate details expose `cost_evidence_count` and `cost_unit`; `mean_cost=0`
with zero cost samples is a compatibility placeholder, not a zero-cost observation.
Nominal costs remain caller-declared ranking penalties in the chosen cost unit.

Normal/recovery executor exceptions and malformed returned observations produce
a terminal `ABORT` with exception details in the trace. State remains the last
known snapshot; cost of the failed call is `NOT_VERIFIED`, with zero added to the
reported-cost accumulator. These are synchronous boundaries without timeout or
cancellation. A callback that does not return is not bounded in wall-clock time.

Action success does not reset the same-failure history while the goal remains
false. The key is `(failure code, attribution)`; a different failure key starts
a new recurrence count. No partial-progress detector or general failure-cycle
prevention is claimed. The total-step bound remains authoritative for returned
calls, including alternating failures and successful actions without goal completion.

```text
REAL_ROBOT_RUNTIME_RECOVERY_EVIDENCE = VERIFIED
REAL_PHYSICAL_TASK_RECOVERY_EVIDENCE = NOT_VERIFIED
WALL_CLOCK_BOUND = NOT_VERIFIED
PROVIDER_TIMEOUT = NOT_VERIFIED
PROVIDER_CANCEL = NOT_VERIFIED
```

These evidence statuses describe the preserved M5 stale-controller cleanup
transcript. M6.1 performs no robot execution. See
[the M6.1 verification report](docs/MILESTONE_6_1_VERIFICATION.md).

## Verification status

```text
CLEAN_BASELINE = 12 passed
PRE_M4_CURRENT_MAIN = 22 passed
PRE_M5_CURRENT_MAIN = 30 passed
PRE_M6_CURRENT_MAIN = 36 passed
PRE_M6_1_CURRENT_BRANCH = 45 passed
CURRENT_TOTAL = 195 passed
PYTHON_COMPILE = PASS

MULTI_EXPERIENCE_MODEL = VERIFIED
RAW_EVIDENCE_IMPORT = VERIFIED
PROVENANCE_TRACEABILITY = VERIFIED
EXPERIENCE_CONDITIONED_OUTCOME_ESTIMATION = VERIFIED
EXPERIENCE_CONDITIONED_DECISION = VERIFIED
OFFLINE_REGRESSION = VERIFIED

MILESTONE_4_FAILURE_AWARE_RECOVERY_DECISION = VERIFIED
RECOVERY_EXPERIENCE_MODEL = VERIFIED
EXACT_FAILURE_CONTEXT_MATCHING = VERIFIED
RECOVERY_OUTCOME_ESTIMATION_BASELINE = VERIFIED
DETERMINISTIC_RECOVERY_RANKING = VERIFIED
OFFLINE_RECOVERY_REGRESSION = VERIFIED

MILESTONE_5_REAL_RECOVERY_EVIDENCE_INTEGRATION = VERIFIED
REAL_RECOVERY_EVIDENCE_IMPORT = VERIFIED
REAL_RECOVERY_PROVENANCE_TRACEABILITY = VERIFIED
REAL_RECOVERY_EVIDENCE_INFLUENCES_ESTIMATE = VERIFIED
REAL_RECOVERY_EVIDENCE_INFLUENCES_DECISION = VERIFIED
OFFLINE_REAL_RECOVERY_EVIDENCE_REGRESSION = VERIFIED
SELECTED_RECOVERY_CHANGED_IN_OFFLINE_REAL_EVIDENCE_BENCHMARK = YES

MILESTONE_6_BOUNDED_DECISION_RECOVERY_LOOP = VERIFIED
BOUNDED_DECISION_RECOVERY_LOOP = VERIFIED
NORMAL_DECISION_TO_FAILURE_TRANSITION = VERIFIED
FAILURE_TO_RECOVERY_DECISION = VERIFIED
RECOVERY_TO_STATE_REEVALUATION = VERIFIED
GOAL_REEVALUATION_AFTER_RECOVERY = VERIFIED
MAX_STEP_BOUND = VERIFIED
RECOVERY_ATTEMPT_BOUND = VERIFIED
SAME_FAILURE_NON_PROGRESS_REGRESSION = VERIFIED
GENERAL_FAILURE_CYCLE_PREVENTION = NOT_VERIFIED
TOTAL_COST_BOUND = VERIFIED
TERMINAL_ABORT = VERIFIED
DETERMINISTIC_BOUNDED_LOOP = VERIFIED
OFFLINE_DECISION_RECOVERY_REGRESSION = VERIFIED

REAL_RECOVERY_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
RECOVERY_DECISION_IS_BETTER = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
NOVEL_AI_ALGORITHM = NOT_VERIFIED
```

See `docs/MILESTONE_1_3_VERIFICATION.md`, `docs/MILESTONE_4_VERIFICATION.md`, `docs/MILESTONE_5_VERIFICATION.md`, and `docs/MILESTONE_6_VERIFICATION.md` for verification boundaries.

## Run

```bash
python -m pytest
python -m compileall -q src tests
```
