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
finalized M7.1 after independent reviewer approval. M8 is now ACTIVE. The first
controlled real-UR3 trial was performed, but physical execution success was not
established. Its runtime failure boundary has since been recovered and closed;
the current M8 boundary is the pre-Trial002 software evidence serializer gate.

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
M8_GATE = PRE_TRIAL002_SOFTWARE_EVIDENCE_GATE

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

STRUCTURED_EVIDENCE_SERIALIZER = NOT_VERIFIED
REAL_UR3_+Z_5MM_SUCCESS = NOT_VERIFIED
REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
PROVIDER_TIMEOUT = NOT_VERIFIED
PROVIDER_CANCEL = NOT_VERIFIED
PHYSICAL_STOP_AFTER_CANCEL = NOT_VERIFIED
WALL_CLOCK_BOUND = NOT_VERIFIED
BOUNDED_REAL_RUNTIME_TERMINATION = NOT_VERIFIED

SECOND_REAL_MOTION = BLOCKED
NEXT_GATE = M8_PRE_TRIAL002_SOFTWARE_EVIDENCE_GATE
STATUS = M8_ACTIVE_PRE_TRIAL002_SOFTWARE_EVIDENCE_GATE
```

The first physical call reached the provider and activated
`forward_position_controller`, but the requested +Z 5 mm outcome was not
established. Direct read-only RTDE samples then showed the robot runtime in
`PAUSED(4)` with effective speed scaling `0.0`. The old canonical READY check
incorrectly returned `PA-000`; provider PR #217 added a fresh effective
speed-scaling gate and the rebuilt canonical install correctly blocked that state.

That runtime boundary is now closed by later evidence. A single existing headless
`resend_robot_program` recovery returned success, followed by 5/5 RTDE samples at
`runtime_state=PLAYING(2)`, raw speed scaling `1.0`, target speed fraction `0.02`,
combined scaling `0.02`, robot mode RUNNING and safety NORMAL. Canonical
`ur3-ready` then returned `PA-000 / READY`, and all motion controllers remained
inactive. No Servo target, FPC activation, or second +Z motion occurred during
that recovery gate.

The next boundary is software-only evidence serialization. The Trial001 structured
result was lost after the provider returned because the wrapper attempted a
`dataclasses.asdict()` deepcopy across immutable `mappingproxy` fields. M8 must
verify a JSON-safe serialization path before Trial002 so that another physical
trial cannot lose its structured result.

This status does not promote real provider-adapter success, real robot execution,
provider timeout/cancel, completed physical stop, or wall-clock bounds. Those
claims remain NOT_VERIFIED until their own evidence gates are satisfied.

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
improvement, self-learning, and novel AI algorithm claims remain NOT_VERIFIED.
The M7.1 documentation follow-up itself performed no robot execution. Subsequent
M8 work is tracked separately above; M8 as a whole remains ACTIVE and not closed.

Historical milestone reports describe their own source snapshots, test counts,
and review states; they do not override this current ledger/status.
