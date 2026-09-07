# Milestone 5 Verification — Real Recovery Evidence Integration

Date: 2026-09-07

## Authoritative starting point

```text
REPOSITORY = SportyRain/physical_ai_skill_intelligence
AUTHORITATIVE_BRANCH = main
AUTHORITATIVE_COMMIT_BEFORE_M5 = d15a77c85a405d8c36964bacf477f95f060e9a0f
AUTHORITATIVE_TREE_BEFORE_M5 = 1028195f0d1665d31f37a70591adb51064cc7a0f
```

The authoritative `main` branch was re-read before implementation. The existing Milestone 4 regression suite was re-run unchanged:

```text
PRE_M5_CURRENT_MAIN_REGRESSION = 30 passed
```

## Scope

Milestone 5 adds only read-only integration of real tracked failure/recovery evidence into the existing Milestone 4 recovery decision kernel:

```text
Tracked Provider Run Manifest
+
Tracked Raw Terminal Transcript
        |
        v
Deterministic Recovery Evidence Import
        |
        v
RecoveryExperienceRecord
        |
        v
EmpiricalRecoveryOutcomeEstimator
        |
        v
RecoveryDecisionEngine
```

No provider repository was modified. No new motion, controller, planner, LLM, RL, IL, VLA, ROS execution, provider adapter, or real UR3 execution was added or performed by this repository.

## Stable provider snapshot

```text
PROVIDER = SportyRain/ur3_visual_servoing
PROVIDER_MAIN_INSPECTION_COMMIT = fec0021d0d7b4ee076842923e7627f1e7486fa71
```

The existing provider `ready.py` retains the bounded exact stale ForceMode/Passthrough cleanup path and the high-level action identity `CLEAN_STALE_FORCE_PASSTHROUGH`. Milestone 5 reuses that existing provider semantic identity; it does not copy or execute its controller/runtime code.

## Imported real recovery evidence

Supported family in Milestone 5:

```text
CANONICAL_READY_STALE_FORCE_PASSTHROUGH_AUTO_CLEANUP
```

Primary tracked run manifest:

```text
evidence/runs/REAL_READY_STALE_CLEANUP_20260831_001.json
provider Git blob = b6455657ebb453bc2f5cf8b68e9c0068533c34bd
SHA256 = aeca04a9ccfd5362f5e5c23bd25fea66f6a83b89ab120e892eafeaa3c5c3f011
```

Required tracked raw transcript:

```text
evidence/logs/REAL_READY_STALE_CLEANUP_20260831_001_terminal_transcript.txt
provider Git blob = 0b5f60c4b5af5622da372618836c571badf6a86a
SHA256 = 835cc8fd475f0c38ba975d801499b469516503f322a495b63b9062099749ab2c
```

The fixture bytes in this repository have the same Git blob identities as the provider files above.

Records whose only raw evidence reference is an ephemeral `/tmp/...` path are not accepted by this Milestone 5 importer. The supported recovery family requires a tracked `evidence/logs/...` raw source.

## Raw semantics preserved

The raw transcript explicitly preserves the failure state:

```text
code = PA-READY-818
first_blocker = NONCANONICAL_CONTROLLER_ACTIVE
status = BUSY
ready = false
next_action = LEAVE_CONTROLLER_UNCHANGED
physical_action = NO
```

It also preserves the exact controller state before recovery:

```text
forward_position_controller = inactive
scaled_joint_trajectory_controller = inactive
passthrough_trajectory_controller = active
force_mode_controller = active
freedrive_mode_controller = inactive
```

The same transcript then contains exactly one `EXECUTE AUTO CLEANUP` section returning:

```text
code = PA-000
mode = EXECUTE
physical_action = YES
ready = true
EXEC_RC = 0
```

Post-recovery evidence preserves both stale controllers as inactive, `program_running=True`, and a final check-only `PA-000 / READY / FINAL_RC=0`.

The importer requires the manifest and raw transcript to agree on these states. Corrupt raw evidence, a manifest/raw mismatch, a path outside the supported evidence location, or a different unsupported recovery family is rejected.

## Normalized RecoveryExperienceRecord

Exactly one real recovery experience is emitted from the supported evidence pair:

```text
goal_predicate = CANONICAL_READY
failure_code = PA-READY-818
failure_attribution = NONCANONICAL_CONTROLLER_ACTIVE
recovery_action = CLEAN_STALE_FORCE_PASSTHROUGH
recovery_success = true
cost = 1.0
cost_semantics = OBSERVED_COST
cost_unit = RECOVERY_EXECUTION_COUNT
metrics.cost_semantics = RECOVERY_EXECUTION_COUNT (preserved legacy label)
```

The cost is an explicit deterministic count of the single `EXECUTE AUTO CLEANUP` block in the raw transcript, not a guessed duration or performance score.

The exact decision context is the five observed controller states at the failure boundary plus the recovery evidence family. No `UNKNOWN` value is treated as a wildcard.

The record preserves:

- experiment/trial identity
- source timestamp
- provider snapshot commit
- run-manifest path and SHA-256
- raw transcript path and SHA-256
- importer version
- before/after controller state evidence
- raw failure, execute, and final READY payloads

## Importer

```text
Ur3VisualServoingRecoveryEvidenceImporter.import_run_manifest(...)
RECOVERY_IMPORTER_VERSION = ur3_visual_servoing_recovery_evidence_v1 (historical M5)
M6_1_RECOVERY_IMPORTER_VERSION = ur3_visual_servoing_recovery_evidence_v2
```

The provider tree is accessed read-only. Derived normalized records remain reproducible from the tracked provider evidence snapshot.

## Real-evidence recovery decision integration

Offline candidates are existing provider high-level identities:

```text
LEAVE_CONTROLLER_UNCHANGED
CLEAN_STALE_FORCE_PASSTHROUGH
```

Without relevant recovery evidence:

```text
LEAVE_CONTROLLER_UNCHANGED:
  P(recovery_success) = 0.5
  evidence_count = 0

CLEAN_STALE_FORCE_PASSTHROUGH:
  P(recovery_success) = 0.5
  evidence_count = 0

selected = LEAVE_CONTROLLER_UNCHANGED
```

The declared order intentionally keeps the no-evidence tie on the fail-closed check-only action.

With the one imported real recovery experience:

```text
CLEAN_STALE_FORCE_PASSTHROUGH:
  P(recovery_success) = 2/3
  evidence_count = 1
  mean recovery execution count = 1.0

LEAVE_CONTROLLER_UNCHANGED:
  P(recovery_success) = 0.5
  evidence_count = 0

selected = CLEAN_STALE_FORCE_PASSTHROUGH
```

Therefore:

```text
REAL_RECOVERY_EVIDENCE_INFLUENCES_ESTIMATE = VERIFIED
REAL_RECOVERY_EVIDENCE_INFLUENCES_DECISION = VERIFIED
SELECTED_RECOVERY_CHANGED_IN_OFFLINE_REAL_EVIDENCE_BENCHMARK = YES
```

This does not establish that the decision is generally better. It is one exact real recovery experience for one exact failure/context and is not generalized to arbitrary controller combinations or other failure types.

## Tests added

`tests/test_real_recovery_evidence_import.py` verifies:

- exact real raw semantics and provenance are imported;
- the tracked manifest and transcript SHA-256 values are preserved;
- real recovery evidence reaches the M4 estimator/decision layer;
- the offline selected recovery changes only with applicable real evidence;
- different exact state context does not match;
- corrupt raw transcript is rejected;
- manifest/raw disagreement is rejected;
- untracked/ephemeral raw paths are rejected.

## Verification results

```text
PRE_M5_CURRENT_MAIN_REGRESSION = 30 passed
CURRENT_TOTAL_TESTS = 36 passed
PYTHON_COMPILE = PASS
```

## Claim boundary

```text
MILESTONE_5_REAL_RECOVERY_EVIDENCE_INTEGRATION = VERIFIED
REAL_RECOVERY_EVIDENCE_IMPORT = VERIFIED
REAL_RECOVERY_PROVENANCE_TRACEABILITY = VERIFIED
REAL_RECOVERY_EVIDENCE_INFLUENCES_ESTIMATE = VERIFIED
REAL_RECOVERY_EVIDENCE_INFLUENCES_DECISION = VERIFIED
OFFLINE_REAL_RECOVERY_EVIDENCE_REGRESSION = VERIFIED
SELECTED_RECOVERY_CHANGED_IN_OFFLINE_REAL_EVIDENCE_BENCHMARK = YES

REAL_RECOVERY_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
RECOVERY_DECISION_IS_BETTER = NOT_VERIFIED
GENERAL_RECOVERY_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
NOVEL_AI_ALGORITHM = NOT_VERIFIED
```

Milestone 5 does not reopen or upgrade any physical execution claim.


## M6.1 provenance and claim clarification

`artifact_snapshot_commit` is the provider evidence snapshot
`fec0021d0d7b4ee076842923e7627f1e7486fa71`; `experiment_runtime_commit` preserves
the manifest's `abbbf62489636641a9cada2d718af01304048cc5`. `source_commit` retains
the artifact snapshot value for compatibility. These are distinct claims;
SHA syntax validation does not prove experiment execution from a clean source tree.

```text
REAL_ROBOT_RUNTIME_RECOVERY_EVIDENCE = VERIFIED
REAL_PHYSICAL_TASK_RECOVERY_EVIDENCE = NOT_VERIFIED
```

The transcript verifies runtime stale-controller cleanup, with no trajectory or
force target command used to reproduce the stale pair. It does not demonstrate
recovery of a failed physical manipulation task. M6.1 checks resolved path
containment; the importer does not query Git to prove a file is tracked.
