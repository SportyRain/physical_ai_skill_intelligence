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
- offline negative and regression tests

## Stable provider investigated

```text
SportyRain/ur3_visual_servoing
inspection commit: b91d3be5a7643f6e91023da8c9d7f339811c7b14
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

Recovery evidence matches exact goal, state context, failure code, failure attribution, and recovery action. `UNKNOWN` is never a wildcard. Recovery candidates must explicitly support the observed failure and satisfy state preconditions.

The recovery estimator is an inspectable Beta-prior baseline, not a learned controller or novel AI algorithm. It selects only a high-level recovery identity; it does not generate motion.

## Verification status

```text
CLEAN_BASELINE = 12 passed
PRE_M4_CURRENT_MAIN = 22 passed
CURRENT_TOTAL = 30 passed
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

REAL_RECOVERY_EVIDENCE_IMPORT = NOT_VERIFIED
REAL_RECOVERY_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
RECOVERY_DECISION_IS_BETTER = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
NOVEL_AI_ALGORITHM = NOT_VERIFIED
```

See `docs/MILESTONE_1_3_VERIFICATION.md` and `docs/MILESTONE_4_VERIFICATION.md` for verification boundaries.

## Run

```bash
python -m pytest
python -m compileall -q src tests
```
