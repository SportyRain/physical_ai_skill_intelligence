# Verification Status

Chronological project decisions and rationale are recorded in [PROJECT_HISTORY.md](PROJECT_HISTORY.md).

The canonical current claim ledger is [VERIFICATION_REPORT.txt](../VERIFICATION_REPORT.txt).
Current test counts and commands are in [TEST_RESULTS.txt](../TEST_RESULTS.txt).
The M7.1 claim scope below mirrors that ledger.

M1–M6 and M6.1 remain closed. M7 software provider integration is CLOSED on
`main`; its historical verification is in [M7 verification](MILESTONE_7_VERIFICATION.md).
The authoritative M7.1 base is `c1a38f80bf7db6baf4bd595b716e7cc973044688` on `main`.
M7.1 is CLOSED on authoritative `main`.

Independent reviewer audit passed M7.1, including source commit
`1a200c7df53d2d24c18eeb787a5336c80cec9c52`. This documentation-only follow-up
finalized M7.1 after independent reviewer approval. M8 remains ACTIVE. Trial001 did
not establish physical +Z success, but its failure/recovery boundary, structured
evidence serializer boundary, Trial002 evidence-path wiring boundary, and fresh
pre-motion machine/source boundary are CLOSED. Trial002 subsequently established
the real Physical AI adapter/provider/UR3 execution path and a settled +Z result
within the configured 1 mm tolerance. M8 now advances to the remaining controlled
runtime boundary: timeout, cancellation/completed stop, and end-to-end wall-clock
bounding.

```text
AUTHORITATIVE_BRANCH = main
M7_1_BASE_COMMIT = c1a38f80bf7db6baf4bd595b716e7cc973044688
M7_1_REVIEWED_SOURCE_COMMIT = 1a200c7df53d2d24c18eeb787a5336c80cec9c52
M7_1_REVIEW = PASS
M7_1_CODE_REVIEW = PASS
M7_1_CODE_REVIEW_AUTHORITY = INDEPENDENT_REVIEWER_AUDIT
M7_1_STATUS = CLOSED
M7_1_FOLLOW_UP_SCOPE = DOCUMENTATION_ONLY; SOURCE_AND_TESTS_UNCHANGED_FROM_REVIEWED_COMMIT
M8_STARTED = YES
M7_1_RUNTIME_CONTRACT_READINESS = VERIFIED
RUNTIME_PROVIDER_SOURCE_ATTESTATION = VERIFIED
RUNTIME_PROVIDER_SOURCE_ATTESTATION_SCOPE = CALLER_PINNED_GIT_PYTHON_SOURCE_ONLY
APPROVED_PROVIDER_VERSION_POLICY = NOT_VERIFIED
THIRD_PARTY_DEPENDENCY_ATTESTATION = NOT_VERIFIED
NATIVE_LIBRARY_ATTESTATION = NOT_VERIFIED
CONCURRENT_RUNTIME_MUTATION_GUARD = NOT_VERIFIED
PROVIDER_FAILURE_SEMANTICS_CONTRACT = VERIFIED
REAL_PROVIDER_FAILURE_RETRYABILITY = NOT_VERIFIED
PROVIDER_COST_SEMANTICS_CONTRACT = VERIFIED
REAL_PROVIDER_COST = NOT_VERIFIED
WALL_CLOCK_BOUND = NOT_VERIFIED
PROVIDER_TIMEOUT = NOT_VERIFIED
PROVIDER_CANCEL = NOT_VERIFIED
REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
M7_1_FINALIZATION_STATUS = M7_1_FINALIZED_ON_MAIN
```

## M8 current controlled-runtime gate

```text
M8_STARTED = YES
M8_STATUS = ACTIVE
M8_GATE = TIMEOUT_CANCEL_WALL_CLOCK_VALIDATION_GATE

PHYSICAL_AI_ADAPTER_MERGE = f9c111e84c83eeea3352767a958688c29d6eb58e
PROVIDER_ACTION_MERGE = 8733c1f0a1172200d5a0b42a3fea4cd76bc4bcc2
PROVIDER_READY_FIX_MERGE = c0f10051a0ea1881df2ccf90d12c7ddb7f74f16a

M8_TRIAL001_ROOT_CAUSE = VERIFIED
M8_TRIAL001_ROOT_CAUSE_DETAIL = ROBOT_RUNTIME_PAUSED
READY_FALSE_POSITIVE = VERIFIED
READY_SPEED_SCALING_FIX_SOFTWARE = VERIFIED
READY_SPEED_SCALING_FIX_REAL_CHECK_ONLY = VERIFIED
CANONICAL_READY_SPEED_SCALING_FIX = VERIFIED

HEADLESS_RUNTIME_RECOVERY = VERIFIED
HEADLESS_RUNTIME_RECOVERY_STATUS = CLOSED
POST_RECOVERY_RTDE_RUNTIME_STATE = PLAYING(2), 5/5
POST_RECOVERY_RTDE_SPEED_SCALING = 1.0, 5/5
POST_RECOVERY_TARGET_SPEED_FRACTION = 0.02, 5/5
POST_RECOVERY_COMBINED_SPEED_SCALING = 0.02, 5/5
POST_RECOVERY_CANONICAL_READY = PA-000 / READY
POST_RECOVERY_MOTION_CONTROLLER_GATE = PASS
POST_RECOVERY_EVIDENCE_SHA256 = d5349ea88c197536ece90d1084805580f8dad40206ab27c7cb017b3947f62ed1

STRUCTURED_EVIDENCE_SERIALIZER = VERIFIED
STRUCTURED_EVIDENCE_SERIALIZER_STATUS = CLOSED
STRUCTURED_EVIDENCE_SERIALIZER_PR = 4
STRUCTURED_EVIDENCE_SERIALIZER_MERGE = 2e542100987ab7772f6e36c136aa99243ae5f7fa
STRUCTURED_EVIDENCE_SERIALIZER_TEST_HEAD = 01e4d77fd095a9de11c2641a98e79b6556fcea33
STRUCTURED_EVIDENCE_SERIALIZER_EVIDENCE_SHA256 = 4d888440df99920025f09ef3e38fbffef4def8053d83844150ccbf3412e753cc
STRUCTURED_EVIDENCE_SERIALIZER_FOCUSED_TEST = 10 passed
STRUCTURED_EVIDENCE_SERIALIZER_DIRECT_REPRODUCTION = PASS
STRUCTURED_EVIDENCE_SERIALIZER_DEFAULT_REGRESSION = PASS

TRIAL002_RUNNER_PR = 6
TRIAL002_RUNNER_TEST_HEAD = 6c773c8b8bffff5a4210a3e84a5a4b02113ace4b
TRIAL002_RUNNER_MERGE = 3319720f709facbd9fcb7b7090087ae464b40c2e
TRIAL002_PROVIDER_COMMIT = ce04cce26e486e5bd3c2dd77f85b91b4bf8d17f5
TRIAL002_EVIDENCE_PATH_DRYRUN1_FAILURE = RUNTIME_PROVIDER_IDENTITY_UNVERIFIED
TRIAL002_EVIDENCE_PATH_DRYRUN1_ROOT_CAUSE = INCOMPLETE_PROVIDER_RELATED_SOURCE_PROVENANCE
TRIAL002_EVIDENCE_PATH_DRYRUN1_LOG_SHA256 = 9d6d662b6ca910deccb2aeb008836c59ccdd356e80f47185a1af7178b3a00b36
TRIAL002_EVIDENCE_PATH_R2_LOG_SHA256 = 16646666e079dfee34e463c33fd5a5e01f38d0be9459d7579900620bfdc4a8d5
TRIAL002_EVIDENCE_PATH_R2_JSON_SHA256 = b9fd7825352314fae46536b3c8c71658e593fa4e7e2660ef8169de06f21a00fd
TRIAL002_COMPLETE_PROVIDER_SOURCE_IDENTITY = VERIFIED
TRIAL002_RUNTIME_PROVIDER_IDENTITY = VERIFIED
TRIAL002_EVIDENCE_PATH_WIRING = VERIFIED
TRIAL002_EVIDENCE_PATH_WIRING_STATUS = CLOSED

TRIAL002_PRE_MOTION_FRESH_MACHINE_AND_SOURCE_GATE = VERIFIED
TRIAL002_PRE_MOTION_FRESH_MACHINE_AND_SOURCE_GATE_STATUS = CLOSED
TRIAL002_PRE_MOTION_EVIDENCE_SHA256 = 2953509c56913a07a045d05cb1ff315d79054da4d36483668f6cc91a3f6a2336
TRIAL002_PRE_MOTION_PAI_MAIN = 28b6e3da0a66c88ca385aa1ab3a725aa28205de3
TRIAL002_PRE_MOTION_PROVIDER_MAIN = ce04cce26e486e5bd3c2dd77f85b91b4bf8d17f5
TRIAL002_PRE_MOTION_PAI_SOURCE_UNCHANGED = VERIFIED
TRIAL002_PRE_MOTION_PROVIDER_SOURCE_UNCHANGED = VERIFIED
TRIAL002_PRE_MOTION_CANONICAL_INSTALL_SOURCE_MATCH = VERIFIED
TRIAL002_PRE_MOTION_CANONICAL_READY = PA-000 / READY
TRIAL002_PRE_MOTION_MOTION_CONTROLLER_GATE = PASS
TRIAL002_PRE_MOTION_RTDE_RUNTIME_STATE = PLAYING(2), 5/5
TRIAL002_PRE_MOTION_RTDE_SPEED_SCALING = 1.0, 5/5
TRIAL002_PRE_MOTION_TARGET_SPEED_FRACTION = 0.02, 5/5
TRIAL002_PRE_MOTION_COMBINED_SPEED_SCALING = 0.02, 5/5
TRIAL002_PHYSICAL_SAFETY_CONFIRMATION = VERIFIED

TRIAL002_PRECALL_BLOCKED_ID = M8_REAL_Z5MM_TRIAL002_20260908_032603
TRIAL002_PRECALL_BLOCKED_FAILURE = RUNTIME_PROVIDER_IDENTITY_UNVERIFIED
TRIAL002_PRECALL_BLOCKED_ROOT_CAUSE = PROVIDER_IMPORTED_FROM_CANONICAL_INSTALL_OUTSIDE_SOURCE_ATTESTATION_PATH_CONTRACT
TRIAL002_PRECALL_BLOCKED_JSON_SHA256 = b6721febb0d00bced7056b69c2ed34a34fc099295f82079d8f04750687a3751c

TRIAL002_ID = M8_REAL_Z5MM_TRIAL002_20260908_032842
TRIAL002_RESULT = PASS
TRIAL002_RUNTIME_PROVIDER_IDENTITY = VERIFIED
TRIAL002_PROVIDER_CALL = VERIFIED
TRIAL002_COMMAND_PUBLISHED = VERIFIED
TRIAL002_COMMAND_ACCEPTANCE = NOT_VERIFIED
TRIAL002_PROVIDER_COMPLETED = VERIFIED
TRIAL002_SETTLED = VERIFIED
TRIAL002_TIMED_OUT = FALSE_VERIFIED
TRIAL002_INITIAL_TCP_BASE_M = [0.22595878378145123, -0.08115447707721629, 0.1453542557242874]
TRIAL002_FINAL_TCP_BASE_M = [0.2259875848028193, -0.08115966526156596, 0.14941279618600023]
TRIAL002_OBSERVED_Z_TRANSLATION_M = 0.004058540461712834
TRIAL002_OBSERVED_TRANSLATION_NORM_M = 0.004058645968232375
TRIAL002_FINAL_ERROR_MM = 0.9419142627227715
TRIAL002_MOTION_ELAPSED_S = 4.559423718004837
TRIAL002_WRAPPER_ELAPSED_S = 8.301585738998256
TRIAL002_FINAL_FPC_INACTIVE = VERIFIED
TRIAL002_SERVO_PAUSED = VERIFIED
TRIAL002_STRUCTURED_JSON = VERIFIED
TRIAL002_JSON_SHA256 = 53f447e0c2d91409532a17e2dbb4c89fc9a6677cdfb445f942f5135cb1e28500
TRIAL002_OBSERVED_RUN_RETURNED = VERIFIED

REAL_UR3_+Z_5MM_SUCCESS = VERIFIED
REAL_UR3_+Z_5MM_SUCCESS_SCOPE = REQUESTED 5 mm; settled within 1 mm tolerance; observed +Z 4.058540 mm; final error 0.941914 mm
REAL_UR3_PROVIDER_ADAPTER = VERIFIED
REAL_ROBOT_EXECUTION = VERIFIED
PROVIDER_TIMEOUT = NOT_VERIFIED
PROVIDER_CANCEL = NOT_VERIFIED
PHYSICAL_STOP_AFTER_CANCEL = NOT_VERIFIED
WALL_CLOCK_BOUND = NOT_VERIFIED
BOUNDED_REAL_RUNTIME_TERMINATION = NOT_VERIFIED

SECOND_REAL_MOTION = COMPLETED
NEXT_GATE = M8_TIMEOUT_CANCEL_WALL_CLOCK_VALIDATION
STATUS = M8_ACTIVE_TIMEOUT_CANCEL_WALL_CLOCK_VALIDATION_GATE
```

The first physical call reached the provider and activated
`forward_position_controller`, but the requested +Z 5 mm outcome was not
established. Direct read-only RTDE samples then showed the robot runtime in
`PAUSED(4)` with effective speed scaling `0.0`. The old canonical READY check
incorrectly returned `PA-000`; provider PR #217 added a fresh effective
speed-scaling gate and the rebuilt canonical install correctly blocked that state.

That runtime boundary is closed by later evidence. A single existing headless
`resend_robot_program` recovery returned success, followed by 5/5 RTDE samples at
`runtime_state=PLAYING(2)`, raw speed scaling `1.0`, target speed fraction `0.02`,
combined scaling `0.02`, robot mode RUNNING and safety NORMAL. Canonical
`ur3-ready` then returned `PA-000 / READY`, and all motion controllers remained
inactive. No Servo target, FPC activation, or second +Z motion occurred during
that recovery gate.

The Trial001 result-loss boundary is also closed at the serializer level. PR #4
added a JSON-safe conversion path that does not use `dataclasses.asdict()` across
immutable `mappingproxy` snapshots. Exact-head Ubuntu verification reproduced the
old `TypeError: cannot pickle 'mappingproxy' object`, then serialized the same
ProviderResult shape successfully, passed 10 focused serializer/adapter tests,
compile, and the default regression suite. No ROS or physical action occurred.

The Trial002 evidence path is also verified. The first dry run failed closed
before physical action with `RUNTIME_PROVIDER_IDENTITY_UNVERIFIED` because the
runner provenance omitted provider-owned Python modules that were loaded as
related sources. The runner was corrected to require the exact loaded source set:
`real_free_space_translation.py`, package `__init__.py`, `se3.py`,
`runtime/__init__.py`, and `robot_camera_collect.py`. The second dry run pinned
provider main `ce04cce26e486e5bd3c2dd77f85b91b4bf8d17f5`, matched disk bytes to
committed bytes for all five files, obtained runtime provider identity VERIFIED,
returned `BLOCKED_EXECUTION_REQUIRED` with no command publication, and atomically
wrote the structured JSON through `to_jsonable()`. No ROS mutation or physical
motion occurred.

The fresh Trial002 pre-motion source/machine gate is closed. Physical AI main
`28b6e3da0a66c88ca385aa1ab3a725aa28205de3` and provider main
`ce04cce26e486e5bd3c2dd77f85b91b4bf8d17f5` matched the expected heads at that
gate. Later synchronization advanced Physical AI to `c28bc3e5b9d832c46718cf70cc5aa3ffa2057dd6`;
the intervening Physical AI changes were record-only and did not change execution
source. A fresh recheck at the synchronized heads reconfirmed clean execution
source, matching installed provider bytes, canonical `PA-000 / READY`, positive ROS
effective scaling, and inactive motion controllers. The attempted direct RTDE
recheck was incomplete only because the then-selected Python environment lacked
`rtde_receive`; no contradictory robot-state evidence was observed.

Two pre-call execution attempts were blocked before robot motion by shell/runtime
identity setup mistakes. One stopped while sourcing ROS setup under shell
`nounset`; the later structured blocked attempt
`M8_REAL_Z5MM_TRIAL002_20260908_032603` failed closed with
`RUNTIME_PROVIDER_IDENTITY_UNVERIFIED` because the provider was imported from the
canonical install path while the attestation contract requires the Git source-tree
path. Its JSON was preserved with SHA256
`b6721febb0d00bced7056b69c2ed34a34fc099295f82079d8f04750687a3751c`;
FPC remained inactive and no provider action or physical motion occurred.

The successful Trial002 was `M8_REAL_Z5MM_TRIAL002_20260908_032842`. Runtime
provider identity was VERIFIED against
`SportyRain/ur3_visual_servoing@ce04cce26e486e5bd3c2dd77f85b91b4bf8d17f5`.
The provider published the +Z command, completed, settled without timeout, and
returned PASS. Initial TCP was
`[0.22595878378145123, -0.08115447707721629, 0.1453542557242874]` m; final TCP was
`[0.2259875848028193, -0.08115966526156596, 0.14941279618600023]` m. Observed +Z
translation was `0.004058540461712834` m, with final target error
`0.9419142627227715` mm, satisfying the configured 1 mm settle tolerance. Motion
elapsed time was `4.559423718004837` s and wrapper elapsed time was
`8.301585738998256` s. Final FPC state was inactive, Servo was paused, and the
structured JSON was saved with SHA256
`53f447e0c2d91409532a17e2dbb4c89fc9a6677cdfb445f942f5135cb1e28500`.

This establishes `REAL_UR3_+Z_5MM_SUCCESS`, `REAL_UR3_PROVIDER_ADAPTER`, and
`REAL_ROBOT_EXECUTION` within this narrow Trial002 scope. `command_acceptance`
remains `NOT_VERIFIED`; command publication and observed physical motion do not
invent a separate acknowledgement claim.

M8 is not closed by this successful normal run. The runtime contract reports a
12 s timeout only for the motion settle loop, while startup and cleanup are
excluded and the configured wall-clock limit is null. This run did not exercise
the timeout path or any cancellation API. Therefore `PROVIDER_TIMEOUT`,
`PROVIDER_CANCEL`, `PHYSICAL_STOP_AFTER_CANCEL`, `WALL_CLOCK_BOUND`, and
`BOUNDED_REAL_RUNTIME_TERMINATION` remain `NOT_VERIFIED`.

See [M7.1 verification](MILESTONE_7_1_VERIFICATION.md) for the implementation
boundary, committed provider audit, adversarial coverage, and fresh rerun results:
400 passed with external integration enabled; 11 passed in the separate external
suite; 389 passed and 11 skipped with the external setting unset; compile PASS.
Skipped external tests do not verify integration.

Attestation establishes matching Python provider source against a caller-selected
Git pin. It does not establish an approved provider version policy, third-party or
native-library identity, or protection from concurrent runtime mutation. Failure
and cost contracts preserve declared semantics; real-provider retryability and
physical cost remain unverified. The existing `BoundedDecisionRecoveryExecutor`
remains an offline evaluation harness.

The existing M5 runtime recovery evidence remains historical preserved evidence.
Real recovery adapter/execution, decision superiority, repeatable performance
improvement, self-learning, and novel algorithm claims remain NOT_VERIFIED.
M8 remains ACTIVE only for the controlled timeout/cancel/wall-clock boundary; no
additional normal-motion proof is required.

Historical milestone reports describe their own source snapshots, test counts,
and review states; they do not override this current ledger/status.

## M8 timeout/cancel/wall-clock software integration — VERIFIED / CLOSED

The reviewed software contract is now on both authoritative `main` branches. The
provider implementation was merged by `ur3_visual_servoing` PR #219 at
`f3f692b70c7194e6f6007d3539cd5ad340515492`; Physical AI consumer propagation was
merged by PR #9 at `3a9dbeceb4c077157f265edb01d3e40b0006e43c`.

Post-merge workflow run `34177727857` checked those exact merged main heads. Python
compile passed; provider focused/adversarial coverage passed `28` tests; Physical
AI focused/adversarial tests passed; the actual provider-to-consumer software
contract passed for `PASS`, `TIMEOUT`, and `CANCELLED`; and the full Physical AI
software regression passed. No physical action occurred in this validation.

The provider repository subsequently advanced to
`4e1351467536cd1bc323851e345c370088265d22` while closing its separate
`REAL_MULTI_EXPERIENCE_DECISION_VALIDATION` physical milestone. The M8
`real_free_space_translation.py` blob remains unchanged from PR #219 at
`8612a25b172618b00bf5176e1dc9b5546a7b21ee`. That separate Continuous Push /
multi-experience physical evidence is not evidence for the M8 termination claims.

Therefore the software integration sub-boundary is VERIFIED and CLOSED, while
`PROVIDER_TIMEOUT`, `PROVIDER_CANCEL`, `PHYSICAL_STOP_AFTER_CANCEL`,
`WALL_CLOCK_BOUND`, and `BOUNDED_REAL_RUNTIME_TERMINATION` remain `NOT_VERIFIED`.
M8 remains ACTIVE at the same timeout/cancel/wall-clock validation Gate. Any real
UR3 termination validation requires a separate fresh machine/source gate and
explicit physical approval.
