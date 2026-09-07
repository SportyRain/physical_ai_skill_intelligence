"""M7.1 software contracts; all synthetic execution below is nonphysical.

Read-only provider source audit (dirty/untracked worktree excluded):
SportyRain/ur3_visual_servoing@dd12a75bbe55df65ce8112fe4fd6fdf2c903eb9f
  src/ur3_visual_servoing/task/relational_pick_place.py:
  compute_on_top_of_place_target returns geometry only; ValueError/RuntimeError
  carry no retryability or cost, and the synchronous API has no timeout/cancel.

Additional committed runtime audit @892f0df027fc719fe9fe49dcc9032ddc97b66c9a:
  src/ur3_visual_servoing/task/push.py:NextDecision/decide_next (lines 31, 507+)
  distinguishes RETRY/REPLAN/STOP_FAILURE in its own bounded task context, not
  generic exception-code policy. No mapping is transplanted to this callable.
  runtime/push_runtime.py:AttemptRecord/PushRuntimeResult (lines 55-79) retain
  attempts/displacement separately from configuration limits; no generic cost.
  runtime/push_runtime.py:MoveGroupPushMotion.move_to (lines 326-342) waits 10/120s,
  requests cancel_goal_async and waits 2s, without validating stop completion.
  runtime/real_push_runtime.py:RealServoFpcPushMotion._wait_until/_call/_move_tcp
  (lines 553-679) uses per-phase monotonic deadlines and raises RuntimeError;
  _call does not cancel a timed-out future. cleanup (lines 856-920) can perform
  further retracts and controller operations; it is not an immediate cancel API.
  No above runtime code was imported/executed. No end-to-end bound, completed
  cancellation, real-provider retryability, or physical cost was verified.

M8 must supply explicit operation-scoped semantics/evidence and completed-stop
observation before physical execution readiness can be claimed. M8 not started.
The unchanged BoundedDecisionRecoveryExecutor remains an offline harness.
"""
from dataclasses import replace
import hashlib
import importlib
from pathlib import Path
import subprocess
import sys

import pytest

from physical_ai_skill_intelligence import Goal, WorldState, ExperienceStore
from physical_ai_skill_intelligence.experience import ExperienceRecord
from physical_ai_skill_intelligence.cost import OBSERVED_COST, CONFIGURED_LIMIT, observed_cost
from physical_ai_skill_intelligence.provenance import Provenance, SourceArtifact
from physical_ai_skill_intelligence.provider_contract import (
    ProviderCost, ProviderResult, ProviderRuntimeContract,
)
from physical_ai_skill_intelligence.provider_observation import software_result_to_observation
from physical_ai_skill_intelligence.adapters import relational_place as adapter
from test_relational_place_provider import geometry, facts, make_loop


@pytest.fixture
def source_provider(tmp_path, monkeypatch):
    """Small synthetic Git repository; no external provider or hardware imports."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), *args], stderr=subprocess.PIPE)
    files = {
        'src/ur3_visual_servoing/__init__.py': '',
        'src/ur3_visual_servoing/task/__init__.py': '',
        'src/ur3_visual_servoing/vision/__init__.py': '',
        'src/ur3_visual_servoing/vision/scene_objects.py': '''
class SceneObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
class BBox2D:
    def __init__(self, *args):
        pass
''',
        adapter.SOURCE_PATH: '''
from dataclasses import dataclass
CALLED = 0
class OnTopOfGeometry:
    def __init__(self, **kwargs):
        pass
@dataclass
class ObjectRelativePlaceTarget:
    destination_object_id: str
    source_destination_xyz_m: tuple
    picked_object_center_xyz_m: tuple
def compute_on_top_of_place_target(observed, geometry):
    global CALLED
    CALLED += 1
    return ObjectRelativePlaceTarget(observed.object_id, observed.base_xyz_m, (0.3, -0.2, 0.1))
''',
    }
    for name, contents in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    git('init', '-q')
    git('remote', 'add', 'origin', 'https://github.com/' + adapter.PROVIDER_REPOSITORY + '.git')
    git('add', '--', 'src')
    git('-c', 'user.name=M7.1 test', '-c', 'user.email=test@example.invalid',
        '-c', 'commit.gpgsign=false', 'commit', '-qm', 'synthetic provider source')
    commit = git('rev-parse', 'HEAD').decode().strip()
    digests = {name: hashlib.sha256(contents.encode()).hexdigest() for name, contents in files.items()}
    provenance = Provenance(
        adapter.PROVIDER_REPOSITORY, commit, adapter.SOURCE_PATH, adapter.PROVIDER_CALLABLE,
        digests[adapter.SOURCE_PATH], 'm7.1-synthetic-test',
        related_sources=tuple(SourceArtifact(name, digest) for name, digest in digests.items()
                              if name != adapter.SOURCE_PATH),
        experiment_runtime_commit='NOT_VERIFIED')
    monkeypatch.setattr(sys, 'dont_write_bytecode', True)
    monkeypatch.syspath_prepend(str(tmp_path / 'src'))
    for name in tuple(sys.modules):
        if name == 'ur3_visual_servoing' or name.startswith('ur3_visual_servoing.'):
            monkeypatch.delitem(sys.modules, name)
    importlib.invalidate_caches()
    module = importlib.import_module(adapter.PROVIDER_MODULE)
    importlib.import_module('ur3_visual_servoing.vision.scene_objects')
    yield module, provenance, tmp_path, git
    for name in tuple(sys.modules):
        if name == 'ur3_visual_servoing' or name.startswith('ur3_visual_servoing.'):
            del sys.modules[name]


def run(source_provider, geometry, facts, **changes):
    _, provenance, repository, _ = source_provider
    return adapter.RelationalPlaceTargetProvider(
        geometry, changes.get('provenance', provenance),
        changes.get('provider_repository', str(repository))).execute(
        adapter.SKILL_NAME, Goal('ON_TOP_OF', 'picked', 'support'), WorldState(facts))


def test_runtime_attestation_passes_with_committed_sources(source_provider, geometry, facts):
    result = run(source_provider, geometry, facts)
    assert result.action_success
    identity = result.observations['runtime_provider_identity']
    assert identity['status'] == 'VERIFIED'
    assert identity['source_commit'] == source_provider[1].source_commit
    assert identity['module'] == adapter.PROVIDER_MODULE
    assert result.cost.value is None and result.cost.semantics == 'UNKNOWN'
    assert result.provenance.experiment_runtime_commit == 'NOT_VERIFIED'


@pytest.mark.parametrize('fault', [
    'missing_repository', 'wrong_repository', 'missing_commit', 'wrong_hash',
    'missing_file', 'missing_spec', 'wrong_module', 'dirty_source',
    'missing_related_source', 'dirty_dependency', 'unexpected_module',
    'stale_loaded_code', 'replaced_constructor', 'replaced_callable',
])
def test_runtime_identity_failure_never_calls_provider(fault, source_provider, geometry, facts, monkeypatch):
    module, provenance, repository, git = source_provider
    changes = {}
    if fault == 'missing_repository':
        changes['provider_repository'] = None
    elif fault == 'wrong_repository':
        git('remote', 'set-url', 'origin', 'https://github.com/example/other.git')
    elif fault == 'missing_commit':
        changes['provenance'] = replace(provenance, source_commit='f' * 40, artifact_snapshot_commit='f' * 40)
    elif fault == 'wrong_hash':
        changes['provenance'] = replace(provenance, raw_sha256='f' * 64)
    elif fault == 'missing_file':
        monkeypatch.delattr(module, '__file__')
    elif fault == 'missing_spec':
        monkeypatch.setattr(module, '__spec__', None)
    elif fault == 'wrong_module':
        monkeypatch.setattr(module, '__name__', 'other.module')
    elif fault == 'dirty_source':
        Path(module.__file__).write_text('# uncommitted source replacement\n')
    elif fault == 'missing_related_source':
        changes['provenance'] = replace(provenance, related_sources=())
    elif fault == 'dirty_dependency':
        path = repository / 'src/ur3_visual_servoing/vision/scene_objects.py'
        path.write_text(path.read_text() + '\n# uncommitted change\n')
    elif fault == 'unexpected_module':
        monkeypatch.setitem(sys.modules, 'ur3_visual_servoing.unidentified', None)
    elif fault == 'stale_loaded_code':
        # Runtime function from different bytes with the SAME filename/module;
        # the committed disk source remains unchanged.
        exec(compile('def compute_on_top_of_place_target(*args):\n    return None\n',
                     module.__file__, 'exec'), module.__dict__)
    elif fault == 'replaced_constructor':
        monkeypatch.setattr(module, 'OnTopOfGeometry', lambda **kwargs: None)
    elif fault == 'replaced_callable':
        monkeypatch.setattr(module, adapter.PROVIDER_CALLABLE, lambda *args: None)
    result = run(source_provider, geometry, facts, **changes)
    assert not result.action_success
    assert result.failure_code == 'RUNTIME_PROVIDER_IDENTITY_UNVERIFIED'
    assert result.observations['runtime_provider_identity']['status'] == 'NOT_VERIFIED'
    assert module.CALLED == 0


@pytest.mark.parametrize('meaning,retryable,terminal', [
    ('retryable', True, False), ('terminal', False, True), ('unknown', False, False),
])
def test_failure_semantics_are_preserved_without_failure_code_policy(meaning, retryable, terminal):
    result = ProviderResult(False, {}, 'SAME_CODE', failure_retryability=meaning,
                            failure_semantics_reference='synthetic provider declaration')
    observation = software_result_to_observation(result)
    assert observation.retryable is retryable
    assert observation.terminal_failure is terminal
    assert observation.details['failure_retryability'] == meaning


@pytest.mark.parametrize('meaning', ['retryable', 'terminal'])
def test_known_failure_semantics_require_evidence(meaning):
    with pytest.raises(ValueError, match='evidence'):
        ProviderResult(False, {}, 'FAILURE', failure_retryability=meaning)


def test_unknown_failure_aborts_offline_harness_without_recovery():
    class UnknownProvider:
        def execute(self, *args):
            return ProviderResult(False, {}, 'UNMAPPED_FAILURE')
    result = make_loop(UnknownProvider()).run(goal=Goal('ON_TOP_OF', 'picked', 'support'),
                                            initial_state=WorldState({}))
    assert result.status == 'ABORT' and result.recovery_attempts == 0
    assert not result.trace[0].observed_result.terminal_failure
    assert not result.trace[0].observed_result.retryable


@pytest.mark.parametrize('cost', [ProviderCost(), ProviderCost(5, CONFIGURED_LIMIT, 'ATTEMPT_COUNT')])
def test_unobserved_cost_cannot_be_persisted_as_observed_or_train_zero(cost):
    result = ProviderResult(True, {}, metrics={'cost': 0.0, 'elapsed_seconds': 0.0}, cost=cost)
    with pytest.raises(ValueError, match='not observed'):
        cost.observed_experience_fields()
    observation = software_result_to_observation(result)
    assert observation.details['provider_cost']['value'] == cost.value
    assert observation.details['execution_cost'] == 'NOT_VERIFIED'
    # Compatibility trace serialization preserves semantics. Its placeholder
    # never contributes an observed sample to the existing experience estimator.
    record = ExperienceRecord('ON_TOP_OF', {}, 'SYNTHETIC', False,
                              cost=observation.cost,
                              cost_semantics=observation.details['cost_semantics'],
                              cost_unit=observation.details['cost_unit'])
    store = ExperienceStore([record])
    assert observed_cost(store.all()) == (0.0, 0, 'UNKNOWN')


@pytest.mark.parametrize('value', [0.0, 2.0])
def test_explicit_observed_cost_including_zero_is_a_sample(value):
    cost = ProviderCost(value, OBSERVED_COST, 'ATTEMPT_COUNT', 'synthetic observed attempt log')
    record = ExperienceRecord('ON_TOP_OF', {}, 'SYNTHETIC', False,
                              **cost.observed_experience_fields())
    assert observed_cost(ExperienceStore([record]).all()) == (value, 1, 'ATTEMPT_COUNT')


@pytest.mark.parametrize('kwargs', [
    {'value': 0}, {'value': 5, 'semantics': 'UNKNOWN'},
    {'value': None, 'semantics': OBSERVED_COST, 'unit': 'SECONDS'},
    {'value': 0, 'semantics': OBSERVED_COST, 'unit': 'SECONDS'},
    {'value': 0, 'semantics': OBSERVED_COST, 'evidence_reference': 'synthetic'},
    {'value': True, 'semantics': CONFIGURED_LIMIT, 'unit': 'SECONDS'},
    {'value': float('nan'), 'semantics': CONFIGURED_LIMIT, 'unit': 'SECONDS'},
    {'value': -1, 'semantics': CONFIGURED_LIMIT, 'unit': 'SECONDS'},
])
def test_invalid_or_ambiguous_cost_fails_closed(kwargs):
    with pytest.raises(ValueError):
        ProviderCost(**kwargs)


def test_declared_timeout_and_cancel_do_not_verify_runtime_guarantees():
    contract = ProviderRuntimeContract(configured_wall_clock_limit_s=30,
        configured_timeout_s=10, timeout_api='synthetic.wait', timeout_scope='one wait',
        cancel_api='synthetic.request_cancel', cancel_completion_semantics='UNKNOWN')
    result = ProviderResult(True, {}, runtime_contract=contract)
    declared = software_result_to_observation(result).details['runtime_contract']
    assert declared['wall_clock_bound'] == 'NOT_VERIFIED'
    assert declared['provider_timeout'] == 'NOT_VERIFIED'
    assert declared['provider_cancel'] == 'NOT_VERIFIED'
    assert declared['cancel_completion_semantics'] == 'UNKNOWN'
