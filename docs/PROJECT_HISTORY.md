# Project History

This is an **append-oriented chronological decision history**.
[VERIFICATION_REPORT.txt](../VERIFICATION_REPORT.txt) remains the authoritative
current claim ledger. History provides rationale/context and cannot override
verification. Historical entries are not rewritten except for explicit factual
correction with evidence; later decisions are appended and may supersede earlier
states without erasing them.

Read [PROJECT_START_HERE.md](../PROJECT_START_HERE.md) and
[VERIFICATION_STATUS.md](VERIFICATION_STATUS.md) before continuing project work.
Backfill was prepared from committed repository reports and Git history at
`f9c111e84c83eeea3352767a958688c29d6eb58e`, through the M7.1 closure. Dates below
use repository commit dates in Asia/Seoul (UTC+09:00), not the older experiment
dates embedded in imported evidence. Test counts are historical recorded results,
not fresh reruns. NEXT describes the subsequent gate supported by the reports and
commit sequence; it is not execution authorization or a claim of completion.

The older M6.1 and M7.1 detailed reports retain pending-review wording, and
`TEST_RESULTS.txt` retains the M7.1 pending-review snapshot. Later finalization
commits and the current claim ledger establish closure. Those historical files
are preserved, not silently rewritten by this backfill. The M8 source/ledger
discrepancy is recorded after the M7.1 entry; no M8 verification is inferred.

## 2026-09-07 — Clean-room baseline

DATE = 2026-09-07

MILESTONE / DECISION = Clean-room v0.1.0 decision kernel

COMMIT = `419678519079c550514d5641cbf1ed343063090b`

STATUS = CLEAN_ROOM_BUILD and SOFTWARE_CORE VERIFIED within software scope

WHAT_CHANGED = Established the clean-room Goal, WorldState, skill contract,
experience, provenance, outcome estimation, and deterministic decision core.

WHY = Select among existing physical skills using goal/state/experience while
keeping robot-specific control in existing providers. Earlier temporary code,
normalized data, and verification claims were excluded as evidence.

EVIDENCE = [M1–M3 scope and baseline](MILESTONE_1_3_VERIFICATION.md), the baseline
commit tree, and [claim ledger](../VERIFICATION_REPORT.txt). Recorded clean
baseline: 12 tests passed.

REVIEW_DECISION = Clean-room software scope is verified by the repository reports;
no independent baseline reviewer identity is recorded there.

UNRESOLVED = Real provider execution, real robot execution, performance improvement,
self-learning, and novel algorithm claims were not established.

NEXT = Semantically explicit multi-experience representation and tracked evidence
import, followed by experience-conditioned decision evaluation.

## 2026-09-07 — M1: Multi-experience semantics

DATE = 2026-09-07

MILESTONE / DECISION = M1 semantically clean multi-experience representation

COMMIT = `768be0f0cceb6fcd1a72f38bc1370968183c654a`; joint verification report
`c73812af2f0d251d74c0902f9c8671edd8686121`

STATUS = VERIFIED; M1 is CLOSED in the current ledger/status

WHAT_CHANGED = Preserved experience/experiment/trial/attempt identities, exact
decision context, before/after state, planned/accepted/executed actions, distinct
task/action outcomes, failure/recovery fields, and raw-source provenance.
Duplicate identities are idempotent; conflicting duplicate records are rejected.

WHY = Reuse experience without inventing missing identity, collapsing different
outcome meanings, or allowing unknown context to match arbitrary situations.

EVIDENCE = [M1 representation and regression checks](MILESTONE_1_3_VERIFICATION.md)
and the implementation commit. M1–M3 together recorded 22 tests passed.

REVIEW_DECISION = Representation and offline regression VERIFIED in the report;
`UNKNOWN` remains literal data, never a wildcard.

UNRESOLVED = Missing object/target/scene identities and absent physical fields
remain UNKNOWN / NOT_VERIFIED / UNRESOLVED or source null, as recorded.

NEXT = Import supported tracked UR3 Push and Pick / Place evidence.

## 2026-09-07 — M2: Tracked real evidence import

DATE = 2026-09-07

MILESTONE / DECISION = M2 real evidence import with explicit provenance

COMMIT = `bee7f25ec63a08381d2aa8e8c02262bf1d3cbf7b`; importer identity/provenance
correction `c5f91ba016836312808bcded8f443ebeb1cbc9ca`; joint report
`c73812af2f0d251d74c0902f9c8671edd8686121`

STATUS = VERIFIED for the supported tracked evidence families; M2 CLOSED

WHAT_CHANGED = Imported two Push trial experiences and one Pick / Place manifest
experience with source paths, record identities, snapshot provenance, and hashes.
The provider inspection commit was `b91d3be5a7643f6e91023da8c9d7f339811c7b14`.

WHY = Ground the decision kernel in preserved real evidence while retaining its
exact semantics. Push task success is an explicit error-versus-tolerance
derivation; Pick / Place task_success=True and action_success=False coexist.

EVIDENCE = [M2 sources, SHA256 values, and normalized outcomes](MILESTONE_1_3_VERIFICATION.md)
and committed fixtures under `tests/fixtures/ur3_visual_servoing/evidence/`.

REVIEW_DECISION = Raw import and provenance traceability VERIFIED; historical
provider evidence does not establish execution by this repository.

UNRESOLVED = Push applicability context contains `goal_displacement_y_m=0.02`
while the tested relative goal is 0.015 m. Both are preserved without semantic
reconciliation. Unknown identities cannot be generalized to known identities.

NEXT = Compare candidate estimates and decisions with and without exact-context
real experience.

## 2026-09-07 — M3: Experience-conditioned decision

DATE = 2026-09-07

MILESTONE / DECISION = M3 deterministic experience-conditioned decision benchmark

COMMIT = `9311b78b8c2132a74612ba534bdc5d694aa2f1b2`; verification
`c73812af2f0d251d74c0902f9c8671edd8686121`; repository publication records
`866c70f0db4fc49359a16e90e7eb6cadda18642a` and
`5a06b2958516a5744fe15c0194c794862f713835`

STATUS = VERIFIED as deterministic software evaluation; M3 CLOSED

WHAT_CHANGED = Used an explicit Beta(1,1) prior and separate success probability,
mean attempt cost, uncertainty, evidence count, and provenance. The benchmark
ranks lexicographically by success, cost, uncertainty, then stable candidate order.

WHY = Make experience influence estimates and decisions transparently without
claiming a scientifically justified combined utility or strategy superiority.

EVIDENCE = [M3 benchmark and publication record](MILESTONE_1_3_VERIFICATION.md).
Both candidates move from prior probability 0.5 to 2/3 with one relevant trial
each; observed costs are 2 versus 3 attempts. M1–M3 total: 22 passed, compile PASS.

REVIEW_DECISION = EXPERIENCE_CONDITIONED_DECISION VERIFIED;
SELECTED_STRATEGY_CHANGED_IN_REAL_EVIDENCE_BENCHMARK = NO. The selected strategy
remains nominal_baseline. GitHub repository establishment was recorded VERIFIED.

UNRESOLVED = One trial per candidate does not establish DECISION_IS_BETTER,
repeatable improvement, self-learning, or a novel AI algorithm.

NEXT = Failure-aware recovery decision after the normal selection gate.

## 2026-09-07 — M4: Failure-aware recovery decision

DATE = 2026-09-07

MILESTONE / DECISION = M4 software recovery decision kernel

COMMIT = `d15a77c85a405d8c36964bacf477f95f060e9a0f`

STATUS = VERIFIED within offline recovery decision scope; M4 CLOSED

WHAT_CHANGED = Added failure state, recovery specifications/experience, empirical
recovery estimates, and deterministic ranking. Matching requires exact goal,
state context, failure code, attribution, and recovery action; preconditions fail
closed. Recovery success remains distinct from task/action success.

WHY = Select among declared existing recovery actions after an observed failure
without generating low-level robot commands or inventing provider capabilities.

EVIDENCE = [M4 verification](MILESTONE_4_VERIFICATION.md),
`tests/test_recovery_decision.py` at the commit. Baseline 22 passed; total 30
passed; compile PASS.

REVIEW_DECISION = Recovery model, exact matching, estimation, ranking, and offline
regression VERIFIED. Fixture action names are not proof of physical capability.

UNRESOLVED = Real recovery evidence import was NOT_VERIFIED at this gate; recovery
provider execution, decision superiority, and real robot execution remained
NOT_VERIFIED.

NEXT = Integrate tracked real failure/recovery evidence into the existing kernel.

## 2026-09-07 — M5: Real recovery evidence integration

DATE = 2026-09-07

MILESTONE / DECISION = M5 exact stale-controller runtime recovery evidence

COMMIT = `a7c773c02c8c4abb3ef60f2da1551913d5d45617`

STATUS = VERIFIED for preserved real runtime recovery evidence and offline import;
M5 CLOSED

WHAT_CHANGED = Imported one manifest/transcript pair for
`CANONICAL_READY_STALE_FORCE_PASSTHROUGH_AUTO_CLEANUP` from provider snapshot
`fec0021d0d7b4ee076842923e7627f1e7486fa71`. Exact PA-READY-818 /
NONCANONICAL_CONTROLLER_ACTIVE evidence connects to the existing
CLEAN_STALE_FORCE_PASSTHROUGH identity without executing provider code.

WHY = Let real recovery evidence influence the existing estimator and decision
while rejecting unsupported evidence families and manifest/raw disagreement.

EVIDENCE = [M5 verification, manifest/transcript hashes, and benchmark](MILESTONE_5_VERIFICATION.md);
tracked `REAL_READY_STALE_CLEANUP_20260831_001` fixture pair. One cleanup block
supports an observed recovery execution count of 1, not a measured duration.
Baseline 30 passed; total 36 passed; compile PASS.

REVIEW_DECISION = The offline selected recovery changes from
LEAVE_CONTROLLER_UNCHANGED to CLEAN_STALE_FORCE_PASSTHROUGH with exact applicable
evidence. This establishes evidence influence, not general recovery superiority.

UNRESOLVED = The evidence is runtime stale-controller cleanup, not physical task
recovery. Real recovery adapter/execution and improved recovery performance
remain NOT_VERIFIED. M6.1 later clarified snapshot/runtime commit and cost fields.

NEXT = Compose existing normal and recovery decisions in a bounded offline loop.

## 2026-09-07 — M6: Bounded decision/recovery evaluation harness

DATE = 2026-09-07

MILESTONE / DECISION = M6 bounded decision → failure → recovery → re-evaluation

COMMIT = `6b9127e54a86cbb041fd2a456f349128865efec4`

STATUS = VERIFIED within OFFLINE_REFERENCE_EVALUATION_HARNESS scope; M6 CLOSED

WHAT_CHANGED = Composed existing DecisionEngine and RecoveryDecisionEngine in
BoundedDecisionRecoveryExecutor with explicit step/recovery/recurrence/cost
budgets, traces, state observations, original-goal re-evaluation, and terminal abort.

WHY = Evaluate bounded decision/recovery transitions without replacing the
existing kernels with a generic production orchestrator. Action or recovery
success must not be treated as original goal success.

EVIDENCE = [M6 verification and M6.1 clarifications](MILESTONE_6_VERIFICATION.md).
Baseline 36 passed; total 45 passed; compile PASS. The fixture's
`goal:CANONICAL_READY=True` is explicitly synthetic, separate from M5 raw evidence.

REVIEW_DECISION = Offline transitions, original-goal checks, deterministic bounds,
and aborts VERIFIED. Preserve the DO_NOT_REIMPLEMENT boundary: this is an offline
evaluation harness, not a new generic production orchestration/retry framework.

UNRESOLVED = Step bounds cover synchronous calls that return; costs are checked
after returned observations. Wall-clock bounds, timeout/cancel, general failure
cycle prevention, real execution, and physical autonomy are not established.
Nested immutability and same-failure history required the subsequent M6.1 fixes.

NEXT = Integrity hardening of the existing core and correction of claim scope.

## 2026-09-07 — M6.1: Integrity hardening and authoritative correction

DATE = 2026-09-07

MILESTONE / DECISION = M6.1 fail-closed decision-core integrity hardening

COMMIT = source `838a37084fe7f662894f8dc637bbc22ed0db612d`; top-level result
correction `1ac3ff7d79bb89ce90e8b966cde9b3847d4aa097`; authoritative-main
finalization `e43889173e00a5c73cf1b31d729609d6eb9ede18`

STATUS = MILESTONE_6_1_INTEGRITY_HARDENING VERIFIED; CLOSED in the current ledger

WHAT_CHANGED = Hardened recursive JSON-like snapshots, empty skill capability,
goal identity, finite numeric checks, contradictory observation rejection,
executor exception normalization, artifact/runtime commit separation, raw path
containment, cost semantics, and same-failure history while the goal stays false.

WHY = Correct defects in existing contracts rather than add a new framework.
Frozen dataclasses alone did not protect nested data; action success did not
justify clearing failure history; configured limits were not observed costs.

EVIDENCE = [M6.1 defects, adversarial tests, and limits](MILESTONE_6_1_VERIFICATION.md),
[M5 provenance correction](MILESTONE_5_VERIFICATION.md), and the finalization
commits. Recorded regression: 45 → 195 passed, compile PASS.

REVIEW_DECISION = Current ledger records M6_1_SOURCE_REVIEW = CODE_PASS with
USER_SUPPLIED_REVIEWER_AUDIT, top-level verification correction COMPLETE, and
M6.1 CLOSED in BASE_STATUS. The detailed report's earlier pending-review wording
is historical, not the current closure decision.

UNRESOLVED = REAL_ROBOT_RUNTIME_RECOVERY_EVIDENCE is VERIFIED only for preserved
M5 cleanup; REAL_PHYSICAL_TASK_RECOVERY_EVIDENCE is NOT_VERIFIED. SHA syntax is
not runtime attestation. General failure-cycle prevention, hanging callback
bounds, physical cost, timeout/cancel, and robot execution are not established.

NEXT = Reuse an existing skill provider through a thin software-only adapter.

## 2026-09-07 — M7: Thin existing-provider software integration

DATE = 2026-09-07

MILESTONE / DECISION = M7 software provider adapter and reviewed main finalization

COMMIT = approved source `5d7581275c7af6ee9f9c0773bf04ea5e290083f2`;
documentation finalization `c1a38f80bf7db6baf4bd595b716e7cc973044688`

STATUS = M7_REVIEW PASS; M7_STATUS CLOSED; M7_FINALIZED_ON_MAIN

WHAT_CHANGED = RelationalPlaceTargetProvider implements the existing SkillProvider
contract with one capability mapping, COMPUTE_ON_TOP_OF_PLACE_TARGET, to the
existing provider's compute_on_top_of_place_target. Immutable results preserve
provenance; input/result/failure normalization fails closed.

WHY = Reuse the existing geometry provider without duplicating placement logic,
adding a provider registry, or developing a generic production orchestrator.

EVIDENCE = [M7 verification](MILESTONE_7_VERIFICATION.md),
[test records](../TEST_RESULTS.txt), and pinned
`SportyRain/ur3_visual_servoing@dd12a75bbe55df65ce8112fe4fd6fdf2c903eb9f`.
The report records source SHA256
`1c3c147b3e32e51326437339ab458dfaf2476719493b83db0b2d3ac5953af328`.
Integration exports and checks committed provider source, not working-tree imports.
Recorded results: 366 passed with external integration; 11 passed separately;
355 passed / 11 skipped by default; compile PASS.

REVIEW_DECISION = USER_SUPPLIED_REVIEWER_PASS_AND_MERGE_APPROVAL closed only the
software integration scope. DO_NOT_REIMPLEMENT_VIOLATIONS = NONE. Provider
software success != physical task success: the observation bridge leaves
state_updates empty and original goal satisfaction false in the one-step fixture.

UNRESOLVED = Runtime provider source attestation was NOT_VERIFIED at M7 and became
the M7.1 gate. Real-provider retryability/cost, timeout/cancel/wall-clock bounds,
real UR3 adapter/execution, decision superiority, and learning remain separate
unverified claims. Skipped external tests do not verify integration.

NEXT = Runtime source attestation and explicit provider failure/cost/runtime
semantics, preserving the thin boundary and offline harness.

## 2026-09-07 — M7.1: Runtime contract readiness and closure

DATE = 2026-09-07

MILESTONE / DECISION = M7.1 runtime source attestation and failure/cost contract

COMMIT = reviewed source `1a200c7df53d2d24c18eeb787a5336c80cec9c52`;
pending-review evidence report `efc99f8452db785b085a243cb8de256a22d1a35f`;
authoritative closure `466f9196c168d5db8f3da1718ff1b337a5a58dae`

STATUS = M7_1_REVIEW PASS; M7_1_STATUS CLOSED; M7_1_FINALIZED_ON_MAIN

WHAT_CHANGED = Checked loaded provider Python identity/source/definitions against
caller-pinned committed source before capability calls. Added declared retryable /
terminal / unknown failure semantics, observed/configured-limit/unknown cost
semantics, and declarative runtime contracts. Unknown failure stops the existing
offline harness without inferred recovery; unknown cost is not an observed zero.

WHY = Separate source identity and declared contracts from unsupported physical
execution, retry, cost, timeout, and cancellation guarantees before runtime work.

EVIDENCE = [M7.1 implementation and rerun report](MILESTONE_7_1_VERIFICATION.md),
`tests/test_runtime_provider_contract.py`, [current ledger](../VERIFICATION_REPORT.txt),
and `git show 466f9196c168d5db8f3da1718ff1b337a5a58dae`.
Recorded results: 400 passed with external integration; separate external suite
11 passed; default 389 passed / 11 skipped; compile PASS. Provider runtime source
audit at `892f0df027fc719fe9fe49dcc9032ddc97b66c9a` was read-only, not execution.

REVIEW_DECISION = INDEPENDENT_REVIEWER_AUDIT PASS finalized M7.1 on main. The
closure commit supersedes the pending-review status retained in TEST_RESULTS and
the detailed milestone report; it changes only the authoritative ledger/status.
Attestation is VERIFIED for CALLER_PINNED_GIT_PYTHON_SOURCE_ONLY. Failure/cost
semantics contracts are VERIFIED; runtime contract declarations enforce no timer.

UNRESOLVED = APPROVED_PROVIDER_VERSION_POLICY, THIRD_PARTY_DEPENDENCY_ATTESTATION,
NATIVE_LIBRARY_ATTESTATION, CONCURRENT_RUNTIME_MUTATION_GUARD,
REAL_PROVIDER_FAILURE_RETRYABILITY, REAL_PROVIDER_COST, WALL_CLOCK_BOUND,
PROVIDER_TIMEOUT, PROVIDER_CANCEL, REAL_UR3_PROVIDER_ADAPTER, and
REAL_ROBOT_EXECUTION remain NOT_VERIFIED in the ledger. Decision superiority,
repeatable improvement, self-learning, and novel algorithms are not established.

NEXT = Controlled real runtime validation (M8), subject to the unresolved physical
gate: operation-scoped timeout evidence, cancellation acknowledgement and completed
stop, and end-to-end monotonic bounds including observation/cleanup. Declaration,
wait timeout, cancel request, or thread join alone is insufficient. This history
does not authorize or perform that gate.

## 2026-09-08 — Source ahead of the last closed verification gate

DATE = 2026-09-08

MILESTONE / DECISION = M8 source publication observed; verification not closed

COMMIT = adapter `b3c61ad6a8da3d048a01fc5fe25b343c7a90d9a3`; tests
`5494f6cd065bf337840f09b161d2dfd19ac45a4c`; published-command requirement
`c1fd07c59a5d6983cd7262cb4a74e08c84436c6d`; merge
`f9c111e84c83eeea3352767a958688c29d6eb58e`

STATUS = Source merged; M8 verification closure not recorded in the claim ledger

WHAT_CHANGED = Git history records PR #1 adding the source-attested real UR3
free-space adapter and contract tests, including a published-command requirement.

WHY = Preserve the actual main source context without confusing source publication
with verified physical execution or overriding M7.1 closure.

EVIDENCE = `git log` and the four commits above; merged paths
`src/physical_ai_skill_intelligence/adapters/real_ur3_free_space.py` and
`tests/test_real_ur3_free_space_adapter.py`. The ledger/status still contain the
M7.1-finalization statement `M8_STARTED = NO`; they were not updated by this merge.

REVIEW_DECISION = No final M8 reviewer verification decision is established by
these repository records. A merge or contract test result is not physical evidence.

UNRESOLVED = Source and the last finalized status differ on M8 work having started.
This is an explicit unresolved discrepancy, not a new verification claim.
Existing NOT_VERIFIED physical/runtime claims remain unchanged.

NEXT = Resolve the M8 controlled real runtime validation/reviewer gate with actual
evidence in its own scope. This documentation task stops after workflow publication.

## 2026-09-08 — Repository-owned GitHub-first continuity

DATE = 2026-09-08

MILESTONE / DECISION = Shared repository entry point and evidence-based history

COMMIT = The commit introducing this entry, titled
`docs: establish GitHub-first project workflow`; resolve with
`git log --diff-filter=A --format='%H %s' -- docs/PROJECT_HISTORY.md`.
Inspected base: `f9c111e84c83eeea3352767a958688c29d6eb58e`.

STATUS = Documentation workflow established; existing verification claims unchanged

WHAT_CHANGED = Added root Start Here and agent workflow documents, a short README
discovery pointer, and a status-to-history link, plus this M1–M7.1 decision backfill.

WHY = Give Reviewer, Execution, Research, and Codex/agent sessions the same latest
main context without relying on external Knowledge or restarting prior reasoning.
Unavailable live access is handled through exact user commands and returned
evidence, without premature VERIFIED claims.

EVIDENCE = [Start Here](../PROJECT_START_HERE.md), [agent rules](../AGENTS.md),
[README](../README.md), and this commit's diff. Required `python3 -m pytest -q`
and `python3 -m compileall -q src tests` exited 0. The default run skipped 11
optional external-provider cases; it is not a new external integration or
physical runtime verification. Links, history fields, and preservation of the
ledger, existing status body, source, and tests were checked.

REVIEW_DECISION = Documentation consistency checked against committed evidence;
no new milestone closure or independent M8 reviewer decision is asserted.

UNRESOLVED = External GPTs must actually read the repository entry point; a
repository file cannot prove that every external session follows it. The M8
source/ledger discrepancy and physical/runtime NOT_VERIFIED items remain open.

NEXT = Use this entry workflow for subsequent authorized work; retain M8 as a
separate controlled runtime validation/reviewer gate.

## 2026-09-08 — M8 first real-runtime failure root cause and READY gate correction

DATE = 2026-09-08

MILESTONE / DECISION = M8 controlled real-runtime validation remains ACTIVE; first
physical trial did not verify +Z success, and readiness was hardened fail-closed
before any retry.

WHAT_CHANGED = The first controlled real-UR3 M8 call reached the existing provider
and entered the FPC motion lifecycle, but the requested +Z 5 mm outcome was not
achieved. Follow-up read-only diagnostics isolated the failure boundary. Direct
RTDE output reported `runtime_state=PAUSED(4)` and `speed_scaling=0.0` in 5/5
samples while safety remained NORMAL and robot mode RUNNING. The previous canonical
`ur3-ready` nevertheless returned `PA-000 / READY`. Provider PR #217 added fresh
effective-speed-scaling observation and blocks unknown/non-finite scaling as
`PA-READY-823` and zero/non-positive scaling as `PA-READY-824`. The exact merged
provider was rebuilt into the canonical install and the installed source SHA
matched the merged source.

WHY = M8 requires a fail-closed pre-motion machine gate. External-Control liveness,
robot RUNNING, safety NORMAL, fresh TCP, and inactive motion controllers were
insufficient to establish that the UR hardware was actually in an execution-capable
runtime state. Allowing `PA-000` while effective scaling was zero would permit
another physical call that cannot execute.

EVIDENCE =
- Physical AI adapter merge: `f9c111e84c83eeea3352767a958688c29d6eb58e`
- Provider bounded +5 mm action merge: `8733c1f0a1172200d5a0b42a3fea4cd76bc4bcc2`
- Provider READY fix PR #217 / merged main: `c0f10051a0ea1881df2ccf90d12c7ddb7f74f16a`
- Trial: `M8_REAL_Z5MM_20260908_003646`
- Trial log SHA256: `e36b8bf321c5ca8ec2eca0da9eeecb52a43dbbd8fbc4eab5d41ccddfcc492347`
- RTDE root-cause evidence SHA256: `c623261d7f35f5cb35be2a5da12ef8b9412ca049cebd08acbafdd624385982a1`
- READY software + live CHECK_ONLY A/B SHA256: `155ac2c5b6d95fd18f3e5af9d5f35d48d1a9d6e67a1cfa4bd87abd5baa4dd789`
- Provider READY commit/push evidence SHA256: `532b02be25baa086a766b47aba8d13741ce85107edfaf9c036ef3e395607873a`
- Canonical rebuild/fail-closed evidence SHA256: `4f8cc22f9f7ac785e0a2c1a3ba3d96102913b4e7aa2ea0d8fbfb88d9c344b0d9`
- Focused provider READY regression: `56 passed`
- Canonical old/new A/B: old `PA-000 / READY`, effective scaling `0.0`; new
  `PA-READY-824 / MOTION_SCALING_ZERO / BLOCKED`
- Physical action during diagnostic/fix validation: NO

REVIEW_DECISION =
`M8_TRIAL001_ROOT_CAUSE = VERIFIED`.
`READY_FALSE_POSITIVE = VERIFIED`.
`READY_SPEED_SCALING_FIX_SOFTWARE = VERIFIED`.
`READY_SPEED_SCALING_FIX_REAL_CHECK_ONLY = VERIFIED`.
`CANONICAL_READY_SPEED_SCALING_FIX = VERIFIED`.

These decisions are limited to the failure diagnosis and readiness boundary. They
do not establish successful real skill execution.

UNRESOLVED =
`REAL_UR3_+Z_5MM_SUCCESS = NOT_VERIFIED`.
`REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED`.
`REAL_ROBOT_EXECUTION = NOT_VERIFIED`.
`PROVIDER_TIMEOUT = NOT_VERIFIED`.
`PROVIDER_CANCEL = NOT_VERIFIED`.
`PHYSICAL_STOP_AFTER_CANCEL = NOT_VERIFIED`.
`WALL_CLOCK_BOUND = NOT_VERIFIED`.
`BOUNDED_REAL_RUNTIME_TERMINATION = NOT_VERIFIED`.
The trial's structured provider JSON was lost because evidence serialization failed
after the provider call returned, so timeout is not promoted from inference.

NEXT = Keep the second real motion blocked. With all motion controllers inactive,
restore the verified headless External-Control runtime using the existing
`resend_robot_program` service, then prove with read-only evidence that RTDE
`runtime_state=PLAYING`, effective speed scaling is positive, and canonical
`ur3-ready=PA-000`. Only after that machine gate and renewed physical safety
confirmation may a second +Z 5 mm trial be considered.

## 2026-09-08 — M8 headless runtime recovery gate closed

DATE = 2026-09-08

MILESTONE / DECISION = M8 headless runtime recovery boundary VERIFIED and CLOSED;
M8 remains ACTIVE and advances to the pre-Trial002 software evidence gate.

WHAT_CHANGED = No new recovery logic was introduced. With all canonical motion
controllers inactive, the existing headless
`/io_and_status_controller/resend_robot_program` service was called exactly once
and returned success. Read-only RTDE verification then produced 5/5 consecutive
samples with `runtime_state=PLAYING(2)`, raw `speed_scaling=1.0`,
`target_speed_fraction=0.02`, combined scaling `0.02`, robot mode RUNNING and
safety NORMAL. Canonical `ur3-ready --json` returned `PA-000 / READY`, and all
motion controllers remained inactive. No Servo target, FPC activation, or +Z
motion was issued during this gate.

WHY = Trial001 had already established the PAUSED/zero-scaling failure mechanism,
and the READY false-positive had already been fixed. The only remaining runtime
boundary was to prove that the existing headless runtime could be restored to an
execution-capable state without reopening or reimplementing recovery logic.

EVIDENCE =
- Recovery log:
  `/home/rosystem/ur_projects/physical_ai_evidence/M8_REAL_UR3_20260908/M8_HEADLESS_RUNTIME_RECOVERY_20260908_020652.log`
- Recovery log SHA256:
  `d5349ea88c197536ece90d1084805580f8dad40206ab27c7cb017b3947f62ed1`
- `RESEND_RC=0`
- RTDE 5/5: `runtime_state=2 (PLAYING)`, `speed_scaling=1.0`,
  `target_speed_fraction=0.02`, combined `0.02`, `robot_mode=7`, `safety_mode=1`
- `RTDE_RUNTIME_GATE=PASS`
- `POST_READY_CODE=PA-000`, `POST_READY_RC=0`
- `POST_MOTION_CONTROLLER_GATE=PASS`
- `HEADLESS_RUNTIME_RECOVERY_GATE=PASS`
- Physical motion command during this gate: NO

REVIEW_DECISION =
`HEADLESS_RUNTIME_RECOVERY = VERIFIED`.
`HEADLESS_RUNTIME_RECOVERY_STATUS = CLOSED`.
`CANONICAL_READY_AFTER_RUNTIME_RECOVERY = VERIFIED`.
The earlier `RESTORE_HEADLESS_RUNTIME_PLAYING_AND_POSITIVE_SPEED_SCALING` boundary
is closed and must not be repeated absent contradictory new evidence.

UNRESOLVED =
`STRUCTURED_EVIDENCE_SERIALIZER = NOT_VERIFIED`.
`REAL_UR3_+Z_5MM_SUCCESS = NOT_VERIFIED`.
`REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED`.
`REAL_ROBOT_EXECUTION = NOT_VERIFIED`.
`PROVIDER_TIMEOUT = NOT_VERIFIED`.
`PROVIDER_CANCEL = NOT_VERIFIED`.
`PHYSICAL_STOP_AFTER_CANCEL = NOT_VERIFIED`.
`WALL_CLOCK_BOUND = NOT_VERIFIED`.
`BOUNDED_REAL_RUNTIME_TERMINATION = NOT_VERIFIED`.
M8 as a whole remains ACTIVE and is not closed.

NEXT = `M8_PRE_TRIAL002_SOFTWARE_EVIDENCE_GATE`: verify a JSON-safe structured
evidence serializer software-only so Trial002 cannot lose the provider result as
Trial001 did. Only after that software gate and the separate Trial002 pre-motion
gates may one controlled +Z 5 mm physical trial be considered.

## 2026-09-08 — M8 structured evidence serializer gate closed

DATE = 2026-09-08

MILESTONE / DECISION = M8 pre-Trial002 structured evidence serializer boundary
VERIFIED and CLOSED; M8 remains ACTIVE and advances to the Trial002 pre-motion
gate.

WHAT_CHANGED = Physical AI PR #4 added a narrow JSON-safe evidence serializer for
immutable ProviderResult records. The helper traverses dataclass fields and
mapping/list/tuple/scalar values without `dataclasses.asdict()` deepcopy, preserving
immutable runtime objects while producing plain JSON data. No robot control,
adapter behavior, recovery logic, ROS behavior, or physical action was changed.

WHY = Trial001 returned from the provider but lost its structured result because
the wrapper called `dataclasses.asdict()` on a ProviderResult containing immutable
`mappingproxy` mappings, causing `TypeError: cannot pickle 'mappingproxy' object`.
Trial002 must not repeat a physical experiment while its structured evidence can
still be lost after the provider returns.

EVIDENCE =
- Serializer test head: `01e4d77fd095a9de11c2641a98e79b6556fcea33`
- PR #4 merged main: `2e542100987ab7772f6e36c136aa99243ae5f7fa`
- Software evidence log:
  `/home/rosystem/ur_projects/physical_ai_evidence/M8_REAL_UR3_20260908/M8_STRUCTURED_EVIDENCE_SERIALIZER_20260908_022328.log`
- Evidence SHA256:
  `4d888440df99920025f09ef3e38fbffef4def8053d83844150ccbf3412e753cc`
- Exact source head gate: PASS
- Diff check: PASS; exactly serializer source + serializer tests
- Compile: PASS
- Focused serializer + M8 adapter regression: 10 passed
- Trial001 old failure reproduction: `TypeError: cannot pickle 'mappingproxy' object`
- Old failure reproduction: PASS
- New JSON serialization: PASS
- Direct serialization RC: 0
- Default regression RC: 0
- Physical action: NO; ROS action: NO; robot motion command: NO

REVIEW_DECISION =
`STRUCTURED_EVIDENCE_SERIALIZER = VERIFIED`.
`STRUCTURED_EVIDENCE_SERIALIZER_STATUS = CLOSED`.
This closes the serializer implementation/serialization boundary only. It does not
prove that an eventual Trial002 execution wrapper is wired to call the helper.

UNRESOLVED =
`TRIAL002_EVIDENCE_PATH_WIRING = NOT_VERIFIED`.
`REAL_UR3_+Z_5MM_SUCCESS = NOT_VERIFIED`.
`REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED`.
`REAL_ROBOT_EXECUTION = NOT_VERIFIED`.
`PROVIDER_TIMEOUT = NOT_VERIFIED`.
`PROVIDER_CANCEL = NOT_VERIFIED`.
`PHYSICAL_STOP_AFTER_CANCEL = NOT_VERIFIED`.
`WALL_CLOCK_BOUND = NOT_VERIFIED`.
`BOUNDED_REAL_RUNTIME_TERMINATION = NOT_VERIFIED`.
M8 as a whole remains ACTIVE and is not closed.

NEXT = `TRIAL002_PRE_MOTION_MACHINE_SOURCE_AND_EVIDENCE_PATH_GATE`: pin exact
Physical AI/provider source identity, prove the Trial002 structured result path
uses the verified JSON-safe serializer, and perform a fresh CHECK_ONLY machine
readiness observation immediately before any motion authorization. This is not a
reopening of the already CLOSED headless runtime recovery gate. A second +Z 5 mm
physical action remains blocked until those gates and renewed physical safety
confirmation pass.

## 2026-09-08 — M8 Trial002 evidence path wiring gate closed

DATE = 2026-09-08

MILESTONE / DECISION = Trial002 structured evidence-path wiring and complete
provider-source provenance boundary VERIFIED and CLOSED; M8 remains ACTIVE.

WHAT_CHANGED = Physical AI PR #6 added one narrow repository-owned Trial002 runner
that calls the existing +5 mm adapter exactly once, defaults to
`execute_real=False`, refuses to overwrite an existing evidence path, records the
caller-pinned Physical AI/provider identities, serializes the immutable
`ProviderResult` through the already VERIFIED `to_jsonable()` helper, and writes
JSON atomically. The first real-provider dry run failed closed with
`RUNTIME_PROVIDER_IDENTITY_UNVERIFIED` because runner provenance contained only the
main action file and omitted provider-owned Python modules loaded by the import
path. No physical action occurred. The runner was corrected to require exactly the
loaded related source set: `ur3_visual_servoing/__init__.py`, `se3.py`,
`runtime/__init__.py`, and `robot_camera_collect.py`, in addition to
`real_free_space_translation.py`.

WHY = A verified serializer helper alone did not prove that Trial002 would invoke
it, and caller-pinned source attestation must cover the complete loaded provider
source set rather than only the entry-point file. Repeating a physical trial before
closing both boundaries could either lose evidence or execute against incompletely
attested source.

EVIDENCE =
- PR #6 tested head: `6c773c8b8bffff5a4210a3e84a5a4b02113ace4b`
- PR #6 merged main: `3319720f709facbd9fcb7b7090087ae464b40c2e`
- Provider main pinned for R2: `ce04cce26e486e5bd3c2dd77f85b91b4bf8d17f5`
- Dry run #1 log SHA256:
  `9d6d662b6ca910deccb2aeb008836c59ccdd356e80f47185a1af7178b3a00b36`
- Dry run #1 JSON SHA256:
  `0acd4502046e171069f4302d1f45ddd071a9e4c37f404d759c781839f316d06b`
- Dry run #1 failure: `RUNTIME_PROVIDER_IDENTITY_UNVERIFIED`; exception type
  `ValueError`; runtime identity remained `NOT_VERIFIED`; physical action NO.
- Dry run #1 root cause: incomplete related-source provenance.
- R2 gate log SHA256:
  `16646666e079dfee34e463c33fd5a5e01f38d0be9459d7579900620bfdc4a8d5`
- R2 structured JSON SHA256:
  `b9fd7825352314fae46536b3c8c71658e593fa4e7e2660ef8169de06f21a00fd`
- Exact provider disk/Git SHA match for five loaded files: PASS.
- Compile: PASS; focused runner/serializer/adapter tests: PASS; default regression:
  PASS.
- `RUNTIME_PROVIDER_IDENTITY_STATUS=VERIFIED`.
- `PROVIDER_RESULT_PRESENT=YES`.
- `FAILURE_CODE=BLOCKED_EXECUTION_REQUIRED`.
- `COMMAND_PUBLISHED=False`, `PROVIDER_COMPLETED=True`, `TIMED_OUT=False`.
- `TRIAL002_COMPLETE_SOURCE_ATTESTATION=PASS`.
- `TRIAL002_EVIDENCE_PATH_DRYRUN=PASS`.
- `STRUCTURED_JSON_WRITTEN=YES`.
- Physical action NO; ROS runtime mutation NO; Servo target NO; FPC activation NO.

REVIEW_DECISION =
`M8_TRIAL002_EVIDENCE_PATH_DRYRUN1_ROOT_CAUSE = VERIFIED`.
`M8_TRIAL002_COMPLETE_PROVIDER_SOURCE_IDENTITY = VERIFIED`.
`M8_TRIAL002_RUNTIME_PROVIDER_IDENTITY = VERIFIED`.
`TRIAL002_EVIDENCE_PATH_WIRING = VERIFIED`.
`TRIAL002_EVIDENCE_PATH_WIRING_STATUS = CLOSED`.
The failed first dry run remains preserved evidence and is not erased by R2.

UNRESOLVED =
`REAL_UR3_+Z_5MM_SUCCESS = NOT_VERIFIED`.
`REAL_UR3_PROVIDER_ADAPTER = NOT_VERIFIED`.
`REAL_ROBOT_EXECUTION = NOT_VERIFIED`.
`PROVIDER_TIMEOUT = NOT_VERIFIED`.
`PROVIDER_CANCEL = NOT_VERIFIED`.
`PHYSICAL_STOP_AFTER_CANCEL = NOT_VERIFIED`.
`WALL_CLOCK_BOUND = NOT_VERIFIED`.
`BOUNDED_REAL_RUNTIME_TERMINATION = NOT_VERIFIED`.
M8 as a whole remains ACTIVE and is not closed.

NEXT = `TRIAL002_PRE_MOTION_FRESH_MACHINE_AND_SOURCE_GATE`: immediately before any
physical authorization, pin the merged Physical AI source and current approved
provider source, perform a fresh canonical CHECK_ONLY machine readiness observation,
and confirm that the source identity still matches the already-verified Trial002
runner contract. Do not reopen or re-run the CLOSED runtime recovery, serializer,
or evidence-path capability absent contradictory evidence. A single +Z 5 mm
physical Trial002 remains blocked until this fresh gate and renewed physical safety
confirmation pass.
