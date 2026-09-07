# M6.1 — Decision Core Integrity Hardening

Repository: `SportyRain/physical_ai_skill_intelligence`
Working branch: `m6.1-integrity-hardening`
Base: `6b9127e54a86cbb041fd2a456f349128865efec4` (M6)
Status: `M6.1_HARDENING_COMPLETE_PENDING_REVIEW`

## Authority and scope

Implementation was derived from the prepared current tree, its base Git history,
and the existing tracked evidence fixtures. No discarded temporary implementation
or remembered UR3 decision was used as implementation authority. No external UR3
repository was modified. No M7, ROS integration, provider adapter, real robot
execution, manager, controller, or learning algorithm was added.

The existing bounded loop remains an offline/reference evaluation harness.
Independent reviewer PASS is pending; the results below are local software checks.

## Defects and regression evidence

| Item | Minimal boundary and verification |
| --- | --- |
| Immutable snapshots | JSON-like mappings become copied read-only mappings, sequences become tuples. Original nested dictionary mutations cannot change WorldState, Goal, ExperienceRecord (including scene_context), RecoveryExperienceRecord, FailureState, observation or prior trace snapshots. Tests also reject direct nested writes and preserve exact-context matching and duplicate identity behavior. No separate MultiExperienceRecord class exists in the base tree. |
| Skill capability | Empty goal_predicates supports no goal; ranking returns NO_APPLICABLE_SKILL. |
| Goal identity | Explicit unparameterized relation evaluators preserve subject/reference. Parameterized and unknown evaluators return false. Colon-containing relation identities are rejected to avoid delimiter aliasing. CANONICAL_READY is supported only as a global goal without subject/reference/parameters; the one scoped global fixture was corrected to that explicit shape. |
| Numeric validation | Costs, nominal costs, normal ranking weights and cost budget require finite nonnegative numbers. Alpha/beta require finite positive numbers; step budgets require integers with their existing bounds. NaN and both infinities are rejected. RecoveryDecisionEngine has no weight parameters: it retains lexicographic ranking. Push metrics used to infer success/action bounds reject nonfinite values. |
| Contradictory observations | Success with a failure or terminal_failure is rejected, as are missing failure on failed observations and nonboolean result flags. ProviderResult also rejects contradictory action/failure combinations. The real Pick/Place task-success versus runtime-action-failure distinction is preserved. |
| Executor exceptions | Synchronous normal/recovery callback exceptions and invalid results become terminal observations, producing ABORT, explicit phase-specific abort_reason and exception type/message in the trace. The attempted call consumes one step (and one recovery attempt when applicable). |
| Commit provenance | artifact_snapshot_commit is separate from experiment_runtime_commit. source_commit retains the legacy artifact reference. Authoritative fields require full 40-hex SHAs or explicit UNKNOWN/NOT_VERIFIED; importer snapshot SHAs must be full. Historical missing/abbreviated runtime SHAs are not expanded; original values remain in raw metadata. Fixture artifact hashes, record identities and both differing full commits are preserved. |
| Path containment | Manifest paths and every raw reference resolve inside the declared provider root; consumed files are checked before reads. Push, Pick/Place and Recovery tests reject parent traversal, outside absolute paths and symlink escape, and accept valid nested paths. Pick/Place references are checked even though its importer consumes only the manifest. |
| Cost semantics | OBSERVED_COST, CONFIGURED_LIMIT and UNKNOWN plus cost_unit are formal record fields. Only observed samples with a known common unit enter mean_cost. Different observed units are rejected both within an estimate and across ranked candidates. Pick/Place retains max_pick_attempts as a configured limit; no observed attempts are invented. |
| Same failure without progress | failure → recovery success → normal success with false goal → same failure aborts at the configured recurrence bound. Normal success no longer resets history. Irrelevant state updates do not establish goal progress. |

Adversarial tests are in `tests/test_integrity_hardening.py`,
`tests/test_evidence_integrity.py`, and additions to
`tests/test_bounded_decision_recovery_loop.py`. Existing outcome fixtures now
explicitly declare observed attempt costs. Existing raw fixture bytes are unchanged.
Both importer version labels advance
to `evidence_v2` to identify the changed normalized provenance/cost contract;
source schema versions and legacy raw metadata remain preserved.

## Validation

Executed before edits on the base commit:

```text
python3 -m pytest
45 passed
```

Executed after hardening:

```text
python3 -m pytest
195 passed
python3 -m compileall -q src tests
PASS
git diff --check
git diff --cached --check
PASS
```

The initial `python` command was unavailable; validation used the installed
`python3`. Test counts reflect collected regression/adversarial cases, including
parameterized invalid values, fields and evidence families.

## Contract limits

Read-only mapping/tuple snapshots cover the supported JSON-like data model and
normal caller mutations, not deliberate Python object-internal tampering. They
are not a serialization framework; callers must explicitly convert containers
when using serializers that require mutable dictionaries/lists.

Cost estimates expose cost_evidence_count and cost_unit in estimator and candidate
outputs. With no observed cost samples, mean_cost=0 is only the compatibility
placeholder. Unknown/configured costs still contribute their verified outcome
labels to outcome probability, but not to observed cost. Nominal costs remain
caller-declared penalties in the chosen ranking unit.

Exception normalization retains the last known state. The failed call's actual
cost/state are NOT_VERIFIED; zero additional reported cost is recorded, rather
than inventing consumption. The cost budget checks returned reported costs and
may be exceeded by one observation; it is not a predictive physical safety cap.

The same-failure key is (code, attribution). Different failure keys restart the
recurrence count. There is no general progress detector: binary goal completion
ends the loop, and action success alone does not prove progress. The total-step
bound remains authoritative for synchronous calls that return. A hanging callback
is not bounded in wall-clock time. Custom goal evaluator exceptions are outside
the executor/provider exception boundary.

Path containment assumes a stable provider snapshot during read-only import;
concurrent adversarial filesystem replacement is not handled. Containment does
not assert that every referenced file is Git-tracked or read. The Push excerpt
reference is preserved but not consumed; the readback and manifest are consumed.
Full SHA validation establishes syntax and preserves declared provenance, not
Git object existence, clean runtime source, or an independent physical replay.

## Evidence and claims

```text
REAL_ROBOT_RUNTIME_RECOVERY_EVIDENCE = VERIFIED
REAL_PHYSICAL_TASK_RECOVERY_EVIDENCE = NOT_VERIFIED
WALL_CLOCK_BOUND = NOT_VERIFIED
PROVIDER_TIMEOUT = NOT_VERIFIED
PROVIDER_CANCEL = NOT_VERIFIED
REAL_PROVIDER_ADAPTER = NOT_VERIFIED
REAL_ROBOT_EXECUTION = NOT_VERIFIED
RECOVERY_DECISION_IS_BETTER = NOT_VERIFIED
GENERAL_RECOVERY_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
REPEATABLE_PERFORMANCE_IMPROVEMENT = NOT_VERIFIED
SELF_LEARNING = NOT_VERIFIED
NOVEL_AI_ALGORITHM = NOT_VERIFIED
REAL_ROBOT_AUTONOMY = NOT_VERIFIED
```

The verified runtime recovery evidence is the already tracked M5 exact stale
ForceMode/Passthrough cleanup transcript. M6.1 imported and checked those bytes;
it did not execute recovery or establish physical task recovery performance.


## Modified files

```text
README.md
docs/MILESTONE_5_VERIFICATION.md
docs/MILESTONE_6_VERIFICATION.md
docs/MILESTONE_6_1_VERIFICATION.md
docs/VERIFICATION_STATUS.md
src/physical_ai_skill_intelligence/_evidence_paths.py
src/physical_ai_skill_intelligence/_integrity.py
src/physical_ai_skill_intelligence/bounded_loop.py
src/physical_ai_skill_intelligence/cost.py
src/physical_ai_skill_intelligence/decision.py
src/physical_ai_skill_intelligence/experience.py
src/physical_ai_skill_intelligence/goal.py
src/physical_ai_skill_intelligence/goal_verification.py
src/physical_ai_skill_intelligence/importers.py
src/physical_ai_skill_intelligence/outcome.py
src/physical_ai_skill_intelligence/provenance.py
src/physical_ai_skill_intelligence/provider_contract.py
src/physical_ai_skill_intelligence/recovery.py
src/physical_ai_skill_intelligence/recovery_importers.py
src/physical_ai_skill_intelligence/skill.py
src/physical_ai_skill_intelligence/state.py
tests/test_bounded_decision_recovery_loop.py
tests/test_evidence_integrity.py
tests/test_integrity_hardening.py
tests/test_outcome.py
```
