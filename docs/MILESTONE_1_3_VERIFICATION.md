# Milestone 1-3 Verification

Date: 2026-09-07

## Scope

This repository was established from the supplied clean-room `physical_ai_skill_intelligence_clean_v0.1.0` package. The earlier temporary project, earlier importer/normalized data, and earlier verification claims were not reused as verification evidence.

The development scope is software-only Physical Decision Intelligence:

```text
Goal + Current World State + Candidate Physical Skills + Past Physical Experience
-> Outcome Estimation
-> Skill / Strategy Evaluation
-> Decision
```

No real UR3 action was executed by this repository during these milestones.

## Provider source investigated

Primary stable provider:

```text
SportyRain/ur3_visual_servoing
canonical inspection commit = b91d3be5a7643f6e91023da8c9d7f339811c7b14
```

Source-level files inspected included:

- `src/ur3_visual_servoing/runtime/push_trial_adaptation.py`
- `src/ur3_visual_servoing/runtime/pick_place_trial_experience.py`
- `evidence/runs/REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING_20260906_001.json`
- `evidence/logs/REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING_20260906_001_trial1_experience_readback.txt`
- `evidence/runs/REAL_UR3_PICK_PLACE_20260905_001.json`

The Push provider's explicit applicability context and the actual task goal are preserved separately. The evidence records an actual relative +Y 15 mm task while the persisted provider context contains `goal_displacement_y_m=0.02`. This mismatch is preserved rather than silently reconciled.

## Milestone 1 - Semantically clean multi-experience representation

Status: `VERIFIED`

`ExperienceRecord` now preserves, where available:

- `experience_id`
- `experiment_id`
- `trial_id`
- `attempt_id`
- goal semantics
- exact decision context
- `state_before` / `state_after`
- object / target / scene identity
- skill / strategy identity
- planned / accepted / executed action
- physical outcome
- task success
- action success
- failure code / attribution
- recovery action
- metrics
- timestamp
- source repository / commit / path / record ID
- raw SHA-256
- source schema version
- importer version
- related raw source hashes

Missing values remain `UNKNOWN`, `NOT_VERIFIED`, `UNRESOLVED`, or source `null`; they are not filled by guessing.

Identity-bearing imported records are deduplicated by `experience_id`. Re-importing the same record is idempotent; a conflicting record with the same identity is rejected.

Exact-context behavior remains fail-closed. `UNKNOWN` is literal data and is never a wildcard.

## Milestone 2 - Real evidence import

Status: `VERIFIED` for the supported tracked evidence families below.

Importer:

```text
physical_ai_skill_intelligence.importers.Ur3VisualServoingEvidenceImporter
IMPORTER_VERSION = ur3_visual_servoing_evidence_v1
```

Supported families in this milestone:

1. Goal-directed continuous Push inter-trial evidence
2. Real Pick / Place run-manifest evidence

Tracked provider snapshots used by tests:

```text
tests/fixtures/ur3_visual_servoing/evidence/runs/REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING_20260906_001.json
SHA256 = 62eeecaaa4c976218c987c75bebce7fc816100f0583bf6bfdfea216d33ed2774

tests/fixtures/ur3_visual_servoing/evidence/logs/REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING_20260906_001_trial1_experience_readback.txt
SHA256 = 85186fffe201eb014c5cbe0e8d0e5b4ac38551b5045e8bf537a5cba2063e5e5d

tests/fixtures/ur3_visual_servoing/evidence/runs/REAL_UR3_PICK_PLACE_20260905_001.json
SHA256 = 4860ea3e53bd03904869570319f150b8f84f72f7733aa3db2051175d45054bd7
```

Imported normalized experience count from these fixtures:

```text
Push Trial 1 = 1
Push Trial 2 = 1
Pick / Place = 1
TOTAL = 3
```

Push trial task success is not silently guessed. It is an explicit deterministic derivation recorded in the normalized outcome:

```text
FINAL_GOAL_ERROR_LE_GOAL_TOLERANCE
```

The raw manifest provides both values. Per-trial fields absent from the manifest, such as actual TCP first-action displacement, remain `UNKNOWN`.

The Pick / Place source explicitly records physical Place success while the runtime final status is `FAILURE` with `PLACE_RESULT_UNKNOWN_TARGET_NOT_VISIBLE`; the normalized representation therefore preserves `task_success=True` and `action_success=False` as distinct fields rather than collapsing them.

## Milestone 3 - Experience-conditioned decision benchmark

Status: `VERIFIED` as a deterministic software benchmark.

Candidates:

```text
goal_directed_continuous_push/nominal_baseline
goal_directed_continuous_push/experience_adapted
```

Estimator:

```text
EmpiricalOutcomeEstimator
Beta(1,1) prior
success probability and mean attempt-count cost remain separate outputs
```

Ranking policy used by the benchmark:

```text
lexicographic_success_then_cost
1. higher estimated task-success probability
2. lower mean attempt-count cost
3. lower uncertainty
4. stable declared candidate order as final tie-break
```

This avoids claiming that unrelated metrics were merged into a scientifically meaningful scalar utility.

### WITHOUT RELEVANT EXPERIENCE

```text
nominal_baseline:
  P(success) = 0.5
  evidence_count = 0
  mean_attempt_cost = 0.0
  estimator = explicit_beta_prior_no_evidence

experience_adapted:
  P(success) = 0.5
  evidence_count = 0
  mean_attempt_cost = 0.0
  estimator = explicit_beta_prior_no_evidence

selected = nominal_baseline
```

### WITH RELEVANT REAL EXPERIENCE

```text
nominal_baseline:
  P(success) = 2/3
  evidence_count = 1
  mean_attempt_cost = 2.0

experience_adapted:
  P(success) = 2/3
  evidence_count = 1
  mean_attempt_cost = 3.0

selected = nominal_baseline
```

Observed benchmark conclusions:

```text
EXPERIENCE_INFLUENCES_ESTIMATE = VERIFIED
EXPERIENCE_CONDITIONED_DECISION = VERIFIED
SELECTED_STRATEGY_CHANGED = NO
DECISION_IS_BETTER = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
```

The evidence changes candidate estimates, evidence counts, costs, uncertainty, evidence IDs, and provenance traces. It does not justify claiming that the adapted strategy is better, and it does not change the selected strategy in this dataset.

## Required negative / regression checks

Verified by tests:

- `UNKNOWN is not wildcard`
- different context does not silently match
- invalid provenance rejected
- duplicate import does not duplicate evidence
- conflicting duplicate identity rejected
- corrupt raw JSON rejected
- missing required identity rejected
- same input produces same decision
- inapplicable skill filtered
- no evidence uses explicit prior baseline
- action success is represented separately from task success
- provider robot-control code is not copied into the intelligence core

## Test and compile status

```text
CLEAN_BASELINE = 12 passed
CURRENT_TOTAL = 22 passed
PYTHON_COMPILE = PASS
```

## Claim boundary

```text
SOFTWARE_CORE = VERIFIED
MULTI_EXPERIENCE_MODEL = VERIFIED
RAW_EVIDENCE_IMPORT = VERIFIED
PROVENANCE_TRACEABILITY = VERIFIED
OFFLINE_MULTI_EXPERIENCE_TESTS = VERIFIED
EXPERIENCE_CONDITIONED_OUTCOME_ESTIMATION = VERIFIED
EXPERIENCE_CONDITIONED_DECISION = VERIFIED
OFFLINE_REGRESSION = VERIFIED

REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
NOVEL_AI_ALGORITHM = NOT_VERIFIED
```

## Unresolved / intentionally deferred

- GitHub repository creation is not exposed by the currently available GitHub connector, so the local `main` repository cannot yet be pushed to `SportyRain/physical_ai_skill_intelligence` from this session.
- Only one real Push trial exists per benchmark candidate strategy in the current exact comparable context. This is enough to validate the software path but not enough to establish strategy superiority.
- The Push provider applicability context includes `goal_displacement_y_m=0.02` while the actual tested relative goal is 0.015 m. Both are preserved; semantic reconciliation is deferred.
- Object, target, and scene identities are unavailable in the imported Push/Pick run manifests and therefore remain `UNKNOWN`. Because exact matching is fail-closed, these records must not be generalized to known different identities.
- Recovery decision is intentionally deferred until the normal skill-selection gate is stable.
- Real provider adapter and real robot execution remain separate future gates.
