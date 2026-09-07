# Milestone 7.1 — Real Provider Runtime Contract Readiness

The user supplied CODE PASS for `1a200c7df53d2d24c18eeb787a5336c80cec9c52`. This documentation-only follow-up
records fresh software verification without changing source or tests. M7.1 is
pending reviewer approval; it is not CLOSED, merged to main, or an M8 start.

```text
REPOSITORY = SportyRain/physical_ai_skill_intelligence
AUTHORITATIVE_BASE_BRANCH = main
WORKING_BRANCH = m7.1-runtime-contract-readiness
M7_1_BASE_COMMIT = c1a38f80bf7db6baf4bd595b716e7cc973044688
M7_1_REVIEWED_SOURCE_COMMIT = 1a200c7df53d2d24c18eeb787a5336c80cec9c52
M7_1_CODE_REVIEW = PASS
M7_1_CODE_REVIEW_AUTHORITY = USER_SUPPLIED_REVIEWER_RESULT
M7_1_STATUS = PENDING_REVIEWER_APPROVAL
M7_1_FOLLOW_UP_SCOPE = DOCUMENTATION_ONLY; SOURCE_AND_TESTS_UNCHANGED_FROM_REVIEWED_COMMIT
M8_STARTED = NO
STATUS = M7_1_RUNTIME_CONTRACT_COMPLETE_PENDING_REVIEW
```

The current claim ledger is [VERIFICATION_REPORT.txt](../VERIFICATION_REPORT.txt);
commands and test results are in [TEST_RESULTS.txt](../TEST_RESULTS.txt).
M7 remains CLOSED. The project purpose remains:

```text
Physical State + Goal + Experience
→ Outcome Estimate
→ Skill / Recovery Decision
→ Existing Robot Capability
→ Observed Physical Outcome
```

## Verified boundary and exclusions

```text
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
DECISION_IS_BETTER = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
NOVEL_AI_ALGORITHM = NOT_VERIFIED
```

`RelationalPlaceTargetProvider` reuses `Provenance`, `SourceArtifact`, and provider
metadata. Its configurable Git repository path is checked against the expected
repository identity and caller-pinned commit. Before provider constructors and
the target callable, the helper checks loaded module identity/origin, package
source bytes and related-source hashes against committed Git blobs, and checks
source-declared Python definitions against compiled committed code. Missing or
mismatched identity returns `RUNTIME_PROVIDER_IDENTITY_UNVERIFIED` and prevents
the capability call. Production source contains no local repository path.

This proves caller-pinned Git Python source consistency in a trusted, stable
process. The caller chooses the expected commit: the adapter does not implement
an approved-version allowlist or authenticate an approved deployment. Import
side effects, generated methods, third-party dependencies, native libraries, and
concurrent runtime mutations are outside the verified boundary. Attestation does
not establish physical execution or an experiment runtime commit.

`ProviderResult` distinguishes `retryable`, `terminal`, and `unknown`. Known
semantics require an explicit provider evidence reference, whose acceptance does
not independently verify that evidence. No failure-code retry policy is inferred.
The software geometry provider leaves retryability unknown. The bridge preserves
this meaning with both retryable and terminal flags false, stopping the existing
offline harness without invoking recovery. Its legacy abort reason may still
say `TERMINAL_FAILURE`; the preserved provider semantic remains unknown.

`ProviderCost` distinguishes `OBSERVED_COST`, `CONFIGURED_LIMIT`, and `UNKNOWN`.
Unknown cost has no numeric value. Observed cost requires an explicit value,
metric unit, and evidence reference. `observed_experience_fields()` rejects
unknown costs and limits; actual observed zero remains distinct. The bridge keeps
the existing offline numeric accumulator placeholder for unobserved cost while
preserving its semantics and original provider cost in details. It stores no
physical experience, and metrics are not automatically converted into cost.
Real physical cost is not verified by the software result or this contract.

`ProviderRuntimeContract` records configured durations and timeout/cancel API,
scope, and completion descriptions. It implements no timer, cancel action, or
wall-clock enforcement. Before any later physical milestone, evidence must cover
the operation-scoped timeout, cancellation acknowledgement and completed stop,
and an end-to-end monotonic bound including observation and cleanup. Declaring
a limit, timing out a wait, requesting cancel, or joining a thread is insufficient.

## Committed provider evidence

The M7 software integration remains pinned to
`SportyRain/ur3_visual_servoing@dd12a75bbe55df65ce8112fe4fd6fdf2c903eb9f`,
module `ur3_visual_servoing.task.relational_pick_place`, callable
`compute_on_top_of_place_target`. Its source SHA256 is
`1c3c147b3e32e51326437339ab458dfaf2476719493b83db0b2d3ac5953af328`.
The integration fixture exports committed blobs into a temporary source snapshot;
it does not import the provider's working-tree files. Success means computed
geometry, with no physical WorldState update.

The source audit recorded with the reviewed implementation also read commit
`892f0df027fc719fe9fe49dcc9032ddc97b66c9a`, excluding dirty/untracked evidence:

- `src/ur3_visual_servoing/task/push.py:NextDecision/decide_next` has contextual
  RETRY/REPLAN/STOP_FAILURE semantics, not generic exception retryability.
- `runtime/push_runtime.py:AttemptRecord/PushRuntimeResult` separates attempts and
  displacement from configured limits. `MoveGroupPushMotion.move_to` waits for
  acceptance/result and requests cancellation on expiry without validating a
  completed physical stop.
- `runtime/real_push_runtime.py:RealServoFpcPushMotion` uses per-phase monotonic
  deadlines; `_call` does not cancel a timed-out future. Cleanup can include
  further retract/controller operations, so it is not an immediate cancel API.

The latter two paths are under `src/ur3_visual_servoing/`. These runtime sources
were read, not executed. The audit is retained in
[the reviewed contract tests](../tests/test_runtime_provider_contract.py).
No provider repository was modified by the M7.1 implementation or this follow-up.

## Rerun evidence

All follow-up commands ran with source/tests at `1a200c7df53d2d24c18eeb787a5336c80cec9c52`.
The pre-implementation 366-pass result was actually recorded at the M7.1 base
before implementation; it is preserved as baseline evidence, not presented as
a new run of old code during this documentation-only follow-up.

```text
PRE_M7_1_TESTS = 366 passed (external enabled)
PRE_M7_1_TESTS_SCOPE = RECORDED_PRE_IMPLEMENTATION_RUN_AT_M7_1_BASE; NOT_RERUN_DURING_DOCUMENTATION_FOLLOW_UP
POST_M7_1_TESTS = 400 passed (external enabled)
EXTERNAL_PROVIDER_TESTS = 11 passed
DEFAULT_NO_EXTERNAL_TESTS = 389 passed, 11 skipped
PYTHON_COMPILE = PASS
```

```bash
# Fresh default/no-external run: 389 passed, 11 skipped in 1.35s.
env -u M7_PROVIDER_REPOSITORY python3 -m pytest -o addopts='' -q

# Fresh full regression: 400 passed in 4.48s.
M7_PROVIDER_REPOSITORY=../ur3_visual_servoing python3 -m pytest -o addopts='' -q

# Fresh separate external suite: 11 passed in 3.19s.
M7_PROVIDER_REPOSITORY=../ur3_visual_servoing python3 -m pytest -o addopts='' -q -s tests/test_external_provider_integration.py

# Fresh compile validation: exit 0.
python3 -m compileall -q src tests
```

The existing M7 regression remains included. The 34 additional contract cases
cover missing/mismatched identities, changed source/dependencies, stale code,
replaced definitions, separated failure semantics, unknown/limit cost rejection,
explicit observed zero, and declarations that remain NOT_VERIFIED. No synthetic
timeout/cancel execution test is used to claim a physical guarantee.

`BoundedDecisionRecoveryExecutor` remains unchanged as an offline evaluation
harness. No new controller, motion, retry/recovery engine, orchestrator, or robot
framework was added. This follow-up modifies only this report, `TEST_RESULTS.txt`,
`VERIFICATION_REPORT.txt`, and `docs/VERIFICATION_STATUS.md`. Source and tests are
unchanged from the reviewed commit. No main merge, hardware action, or M8 work
is part of this follow-up.
