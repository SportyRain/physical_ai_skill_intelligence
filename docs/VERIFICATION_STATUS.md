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

## M8 controlled real runtime validation — VERIFIED / CLOSED / 2026-09-09

This section supersedes the earlier `M8_STATUS = ACTIVE` and five physical
termination `NOT_VERIFIED` values above. Historical statements are preserved to
show the sequence of evidence rather than rewritten.

The exact existing M8 provider was exercised in real UR3 timeout and cancellation
termination paths after fresh source/machine/safety gates. No new robot framework,
manager, controller, planner, or recovery framework was introduced. The timeout
path returned `TIMEOUT / MOTION_SETTLE_TIMEOUT` after a published command and
completed cleanup. The cancellation path was triggered only after an independent
TCP observer measured at least 0.5 mm of real +Z motion; the provider returned
`CANCELLED / CANCEL_REQUESTED`, acknowledged cancellation, completed cleanup, left
FPC inactive and Servo paused, and an independent continuous TCP trace established
a stable post-return physical stop.

```text
M8_STATUS = CLOSED
M8_GATE = CLOSED
M8_CLOSURE_DATE = 2026-09-09

M8_CLOSURE_PHYSICAL_AI_SOURCE = 74c7c9ec483d8d852052b850516fa89f08d7b897
M8_TIMEOUT_PROVIDER_SOURCE = 8d711a3d5ce874b7bf09555f2952252d8ddeed13
M8_CANCEL_PROVIDER_SOURCE = 89a2eda0dcce1fc5e492cd2f64dec5faca68c788
M8_PROVIDER_RUNTIME_BLOB = 8612a25b172618b00bf5176e1dc9b5546a7b21ee
M8_PROVIDER_RUNTIME_SHA256 = 329f700dd25a25584f9e460caa364b5de58849138596b3907abf6435ba92181c
M8_CANCEL_PROVIDER_EXECUTION_SOURCE_UNCHANGED = VERIFIED

M8_TRIAL_PRE_MOTION_ISOLATION_GATE = VERIFIED
M8_TERMINATION_SOURCE_ATTESTED_DRYRUN = VERIFIED

PROVIDER_TIMEOUT = VERIFIED
PROVIDER_CANCEL = VERIFIED
PHYSICAL_STOP_AFTER_CANCEL = VERIFIED
WALL_CLOCK_BOUND = VERIFIED
BOUNDED_REAL_RUNTIME_TERMINATION = VERIFIED

TIMEOUT_TRIAL_ID = M8_TERMINATION_TIMEOUT_R2_20260909_001056
TIMEOUT_MOTION_TIMEOUT_S = 0.05
TIMEOUT_MOTION_ELAPSED_S = 0.05008394699689234
TIMEOUT_PROVIDER_WALL_CLOCK_ELAPSED_S = 3.298580510003376
TIMEOUT_WRAPPER_ELAPSED_S = 3.3476631119992817
TIMEOUT_CONFIGURED_WALL_CLOCK_LIMIT_S = 20.0
TIMEOUT_JSON_SHA256 = 7f29aaad4974fbdc3fa786991b827f96e36bf0efe397c1874af7bf600a0b29b1
TIMEOUT_LOG_SHA256 = e6dd69255479b3e9789911aa614b42b361c5f973f8172d32d30c580cae52200c

CANCEL_TRIAL_ID = M8_TERMINATION_CANCEL_20260909_001826
CANCEL_MOTION_TRIGGER_Z_M = 0.000558267621881936
CANCEL_SAMPLE_Z_M = 0.0012466677137311089
CANCEL_MAX_ADDITIONAL_DISPLACEMENT_FROM_CANCEL_SAMPLE_M = 0.0018598379582002113
CANCEL_TO_PROVIDER_RETURN_S = 0.3867265429944382
CANCEL_POST_RETURN_TAIL_MAX_DISPLACEMENT_M = 0.000058838893773006324
CANCEL_PROVIDER_WALL_CLOCK_ELAPSED_S = 4.575946910998027
CANCEL_WRAPPER_ELAPSED_S = 4.621870205999585
CANCEL_CONFIGURED_WALL_CLOCK_LIMIT_S = 20.0
CANCEL_JSON_SHA256 = 4f3682d4c621546ad27a25f7a59c503a3ab314277a55ade847eea74171d0c69f
CANCEL_TCP_TRACE_SHA256 = 058fb7b97c43a672b39b333b0d23139c5222d9608de48785b04302962c9a0c30
CANCEL_LOG_SHA256 = 5dc93f7950952bb0de21d652691535bb20adc99e7b9251283ac84986829c8c97

PHYSICAL_STOP_AFTER_CANCEL_SCOPE = COMPLETED STOP AFTER CANCEL AND CLEANUP; NOT IMMEDIATE STOP. CANCEL WAS FOLLOWED BY UP TO 1.859838 MM ADDITIONAL OBSERVED DISPLACEMENT BEFORE THE POST-RETURN STABLE TAIL.
WALL_CLOCK_BOUND_SCOPE = EXACT M8 PROVIDER OPERATION+SAFETY-CLEANUP CONTRACT. BOTH REAL TIMEOUT AND CANCEL PATHS RETURNED WITHIN THE CONFIGURED 20 S LIMIT. THIS DOES NOT CLAIM A GENERAL OS HARD-KILL OR UNBOUNDED EXTERNAL SERIALIZATION GUARANTEE.
BOUNDED_REAL_RUNTIME_TERMINATION_SCOPE = EXACT M8 TIMEOUT AND CANCEL PATHS; PROVIDER RETURN + COMPLETED SAFE CLEANUP + FINAL FPC INACTIVE + SERVO PAUSED.

CONCURRENT_RUNTIME_MUTATION_GUARD = NOT_VERIFIED
CONCURRENT_RUNTIME_MUTATION_GUARD_SCOPE = TRIAL-SPECIFIC PRE-MOTION ISOLATION VERIFIED ONLY; NO GLOBAL CONTINUOUS GUARD CLAIM
M8_TRIAL002_COMMAND_ACCEPTANCE = NOT_VERIFIED

NEXT_GATE = NONE_M8_CLOSED
STATUS = M8_CLOSED_CONTROLLED_REAL_RUNTIME_VALIDATION
```

The first timeout attempt used `motion_timeout_s=0.25` but the robot settled in
`0.19381318900559563` s, so it was preserved as an unexpected normal PASS rather
than mislabeled as timeout evidence. The retry at `0.05` s exercised the actual
real timeout path. At the provider timeout snapshot little TCP translation had yet
been observed, while the later post-return observation showed that physical motion
continued during termination/cleanup before becoming stable. Therefore timeout or
cancel acknowledgement is not interpreted as an instantaneous physical stop.

For cancellation, the external TCP observer triggered at +Z
`0.000558267621881936` m. The nearest cancel sample was already +Z
`0.0012466677137311089` m, and up to `0.0018598379582002113` m additional physical
displacement from that cancel sample was observed before completion. The provider
returned 0.3867265429944382 s after the cancel request; the post-return tail had
220 samples with maximum displacement `0.000058838893773006324` m. This supports
completed physical stop after cancellation and cleanup, but explicitly does not
support an immediate-stop claim.

M8 is CLOSED within this controlled provider/runtime scope. Remaining separate
NOT_VERIFIED claims, including the global concurrent-runtime-mutation guard,
command acceptance, approved provider version policy, third-party/native-library
attestation, physical cost, retryability, decision superiority, performance
improvement, self-learning, and novel algorithm claims are not promoted by this
closure.
