# Milestone 7 — software provider adapter verification

```text
AUTHORITATIVE_BRANCH = main
M7_REVIEW = PASS
M7_STATUS = CLOSED
STATUS = M7_FINALIZED_ON_MAIN
```

The canonical current claim ledger is [VERIFICATION_REPORT.txt](../VERIFICATION_REPORT.txt).
[Test results](../TEST_RESULTS.txt) distinguish the full external-source run from
an ordinary run where external tests are skipped. M1–M6 and M6.1 are closed at
base `e43889173e00a5c73cf1b31d729609d6eb9ede18`, per this task's authority.
Reviewer PASS and merge approval were supplied for
`5d7581275c7af6ee9f9c0773bf04ea5e290083f2`. The clean `main` branch and live
`origin/main` were both at the M7 base before the fast-forward; remote-main versus
approved-branch divergence was 0 / 1. The approved commit was fast-forward merged
and pushed to `main`. Finalization modifies documentation only.

Post-merge validation: `python3 -m pytest -q` passed (355 tests, with 11 optional
external tests skipped); the full run with `M7_PROVIDER_REPOSITORY` passed all
366 tests, and the separate pinned-source integration passed 11 tests.
`python3 -m compileall -q src tests` exited 0. Source and tests remain identical
to the approved commit. See the canonical test results for exact commands.

## Authoritative source and scope

Implementation uses the current working tree, current Git history, this task's
instructions, and directly read committed provider source. No previous temporary
implementation was restored or used as an implementation basis.

Provider status was checked before inspection and again after integration:

```text
PROVIDER_REPOSITORY = SportyRain/ur3_visual_servoing
PROVIDER_COMMIT = dd12a75bbe55df65ce8112fe4fd6fdf2c903eb9f
PROVIDER_WORKTREE_STATUS = CLEAN_AT_PRECHECK_AND_POSTCHECK
PROVIDER_MODULE = ur3_visual_servoing.task.relational_pick_place
PROVIDER_CALLABLE = compute_on_top_of_place_target
PROVIDER_SOURCE_SHA256 = 1c3c147b3e32e51326437339ab458dfaf2476719493b83db0b2d3ac5953af328
```

Both `task/push.py` (including `plan_push` and `evaluate_outcome`) and
`task/relational_pick_place.py` were read at that exact commit. The latter's
module contract explicitly describes pure software logic without camera
observation, UR3 commands, or Pick/Place motion ownership. Only its target
computation capability was integrated. `evaluate_on_top_of`, revalidation,
Push planning, and provider recovery are not called by the adapter.

`vision/scene_objects.py`, package initializers, and import dependencies were
inspected. Ordinary provider imports also load existing software definitions
through the provider's vision package initializer; no camera capture, controller,
simulation, or motion callable is invoked. NumPy and SciPy are optional provider
import dependencies, not core dependencies. No initializer was bypassed or
replaced with a fake module in the real integration tests.

The integration fixture obtains source bytes with read-only `git ls-tree` and
`git show` at the pinned SHA. It writes read-only source files to a temporary
snapshot and imports the actual package from that snapshot. Every imported
provider source file is checked for snapshot containment and matching SHA256
against its committed bytes. No provider working-tree source is imported, no
provider source is vendored, and no provider repository file or Git state is
modified. An independently prepared snapshot was also used during inspection.

## Minimal boundary

`RelationalPlaceTargetProvider` implements the existing
`SkillProvider.execute(skill_name, goal, state)` signature. There is no new
request bus, manager, registry, or execution framework. The sole exact mapping is:

```text
COMPUTE_ON_TOP_OF_PLACE_TARGET
-> ur3_visual_servoing.task.relational_pick_place.compute_on_top_of_place_target
```

The original goal must be an unparameterized `ON_TOP_OF` with explicit, distinct
subject and reference identities. `UNKNOWN` and unsupported skills never match.
Geometry is immutable adapter configuration, separate from original goal identity.
It requires all six existing `OnTopOfGeometry` fields:

- `tabletop_z_m`
- `picked_object_height_m`
- `destination_object_height_m`
- `destination_support_radius_m`
- `support_margin_m`
- `z_tolerance_m`

The destination is selected by exact `state.facts["objects"][goal.reference]`.
That record requires exactly `label`, `confidence`, `bbox_xyxy`, and `base_xyz_m`.
These are explicit caller inputs; the bbox is passed to the existing `SceneObject`
contract, never used to infer physical dimensions. Unrelated world facts and
other object records remain untouched. There is no world-state inference.

Missing, UNKNOWN, nonnumeric, boolean numeric, NaN/Inf, malformed vectors,
unsupported fields, invalid goal identities, and out-of-range confidence fail
closed. Existing provider constructors own positive geometry, margin/radius,
and bbox bounds validation. Invalid construction stops before the target callable.
Invalid configuration container types or malformed provenance are rejected when
constructing the adapter; request and provider errors return structured results
from `execute`. No hardware values or geometry defaults are guessed.

The callable owns all placement geometry. The adapter preserves its target
identity, source coordinates, and computed coordinates, rejecting malformed,
nonfinite, or identity/source-inconsistent results. Even finite input overflow
is tested. It neither recomputes nor independently certifies the provider's
placement algorithm.

## Result, provenance, and goal semantics

The only shared contract extension is optional `ProviderResult.provenance`, using
the existing immutable M6.1 `Provenance` / `SourceArtifact` types and validation.
The adapter requires the exact repository, module source path, callable identity,
and a full artifact snapshot SHA. The integration fixture supplies the source
SHA256 plus hashes for imported related source files. The caller declares
provenance in production; full SHA syntax alone is not Git attestation. Actual
source matching is verified by the committed-source integration fixture.
`experiment_runtime_commit` remains `NOT_VERIFIED`: no physical experiment occurs.

`action_success=True` means target computation returned a valid result.
`observations` hold the unchanged provider target and capability identity.
`failure_code` is absent on success. `metrics={}` on success means no metrics were
reported; failure metrics are unspecified (`None`). Neither is a physical cost
measurement. Nested result data is copied to immutable mappings and tuples.

Failure codes are `UNSUPPORTED_CAPABILITY`, `INVALID_PROVIDER_INPUT`,
`PROVIDER_UNAVAILABLE`, `PROVIDER_CALL_FAILED`, and `INVALID_PROVIDER_RESULT`.
Import/call exceptions are normalized with exception type at the provider boundary.
Provider constructor rejection uses `INVALID_PROVIDER_INPUT`; callable rejection
uses `PROVIDER_CALL_FAILED`. Exceptions do not escape into decision evaluation.

`software_result_to_observation` retains observations, metrics, and provenance in
`ExecutionObservation.details`, with **empty state_updates**. It never promotes
provider observations into physical facts, even if they contain goal-like keys.
Failures are terminal and nonretryable in this software bridge. Cost is the
existing zero accumulator placeholder with `execution_cost=NOT_VERIFIED` and
unknown semantics/unit. Metrics are never silently treated as observed cost.

The real integration goes through the existing `DecisionEngine` and
`BoundedDecisionRecoveryExecutor`. The one-step fixture selects the mapped skill,
receives a successful computed target, keeps the original WorldState unchanged,
and ends with `MAX_TOTAL_STEPS_EXCEEDED`, with goal satisfaction false. This is
the intended software compatibility result, not a physical task failure or
physical success claim. The existing harness remains OFFLINE / REFERENCE
EVALUATION HARNESS. No recovery provider is called.

## Reproduction and evidence

Observed environment: Python 3.12.3, pytest 7.4.4, NumPy 1.26.4, SciPy 1.11.4.
No package installation was needed. Core imports do not load the provider.
From the repository root, using a clone containing the recorded commit:

```bash
# Full M1–M7 regression, including actual committed external source.
M7_PROVIDER_REPOSITORY=../ur3_visual_servoing python3 -m pytest -o addopts='' -q
# 366 passed

python3 -m compileall -q src tests
# exit 0

# Explicit external integration and printed source provenance.
M7_PROVIDER_REPOSITORY=../ur3_visual_servoing python3 -m pytest -o addopts='' -q -s tests/test_external_provider_integration.py
# 11 passed

# Optional provider absent from the test configuration.
python3 -m pytest -o addopts='' -q
# 355 passed, 11 skipped; skipped external tests do not establish integration.
```

The sibling path appears only in test execution instructions, never production
source. The fixture uses the recorded commit even if the sibling worktree later
becomes dirty or moves. A configured clone missing that commit fails the test;
it is not silently skipped. Test numeric values are synthetic software inputs,
not measured object geometry or hardware calibration.

Pre-M7 baseline was 195 passed. All existing tests are preserved. Added tests
cover explicit mapping, non-call on unsupported skills/invalid parameters,
optional dependency failure, actual source calls, result/failure normalization,
immutable configuration/results, source provenance, no goal completion confusion,
bounded harness success/failure compatibility, forbidden core imports, lazy
loading, and no production local paths. Fault-injection unit tests use explicit
fakes; the separate real integration imports and calls committed provider source.

## DO_NOT_REIMPLEMENT review and limits

Direct source/diff review found no robot motion code, push planning duplication,
relational placement duplication, generic retry loop, generic recovery engine,
ROS wrapper framework, provider registry framework, or task orchestration
framework. Geometry computation remains one external callable invocation.
`decision.py`, `goal.py`, `state.py`, `bounded_loop.py`, `_integrity.py`, `cost.py`,
and original goal evaluation are unchanged. Core modules import no provider,
ROS, controller, or message packages.

M7 verifies a thin software provider boundary and normalized software output.
Real UR3 skill execution, UR3 provider execution adapter, recovery provider
adapter, robot execution, timeouts, cancellation, and wall-clock bounds remain
NOT_VERIFIED. Decision/recovery superiority, repeatable improvement, self-learning,
and novel AI algorithms remain NOT_VERIFIED. No ROS launch/action/service,
controller switch, MoveIt/Servo/trajectory execution, camera hardware access,
M7.1 or M8 work is performed. Main publication is limited to the approved
fast-forward and documentation finalization.

The review closes only the M7 software integration scope. These boundaries are
unchanged and explicitly retained in the canonical ledger:

```text
RUNTIME_PROVIDER_SOURCE_ATTESTATION = NOT_VERIFIED
REAL_PROVIDER_FAILURE_RETRYABILITY = NOT_VERIFIED
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
