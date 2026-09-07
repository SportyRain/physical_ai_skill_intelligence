from dataclasses import dataclass, replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from physical_ai_skill_intelligence import (
    BoundedDecisionRecoveryExecutor, DecisionEngine, EmpiricalOutcomeEstimator,
    EmpiricalRecoveryOutcomeEstimator, ExecutionBudget, ExperienceStore, Goal,
    RecoveryDecisionEngine, RecoveryExperienceStore, SkillSpec, WorldState,
)
from physical_ai_skill_intelligence.adapters import relational_place as adapter
from physical_ai_skill_intelligence.provenance import Provenance
from physical_ai_skill_intelligence.provider_contract import ProviderResult
from physical_ai_skill_intelligence.provider_observation import software_result_to_observation


@pytest.fixture
def geometry():
    return dict(tabletop_z_m=0.0, picked_object_height_m=0.04,
                destination_object_height_m=0.08, destination_support_radius_m=0.05,
                support_margin_m=0.005, z_tolerance_m=0.002)


@pytest.fixture
def facts():
    # Synthetic explicit observations; no camera or physical measurement claim.
    return {"objects": {"support": {"label": "support", "confidence": 0.9,
            "bbox_xyxy": [10., 20., 30., 40.], "base_xyz_m": [0.3, -0.2, 0.04]}}}


@pytest.fixture
def provenance():
    # Deliberately synthetic provenance for fault-injection unit tests only.
    return Provenance(adapter.PROVIDER_REPOSITORY, "a" * 40, adapter.SOURCE_PATH,
                      adapter.PROVIDER_CALLABLE, "b" * 64, "m7-software-call-v1",
                      importer_version="m7-adapter-v1", experiment_runtime_commit="NOT_VERIFIED")


@dataclass(frozen=True)
class FakeTarget:
    destination_object_id: str
    source_destination_xyz_m: tuple
    picked_object_center_xyz_m: tuple


@pytest.fixture
def fake_provider(monkeypatch):
    call = Mock(return_value=FakeTarget("support", (0.3, -0.2, 0.04), (0.3, -0.2, 0.1)))
    module = SimpleNamespace(OnTopOfGeometry=Mock(side_effect=lambda **kw: kw),
                             ObjectRelativePlaceTarget=FakeTarget,
                             compute_on_top_of_place_target=call)
    scene = SimpleNamespace(SceneObject=Mock(side_effect=lambda **kw: kw),
                            BBox2D=Mock(side_effect=lambda *args: args))
    loader = Mock(side_effect=lambda name: module if name == adapter.PROVIDER_MODULE else scene)
    monkeypatch.setattr(adapter, "import_module", loader)
    return module, scene, loader


def execute(geometry, provenance, facts, skill=adapter.SKILL_NAME, goal=None):
    return adapter.RelationalPlaceTargetProvider(geometry, provenance).execute(
        skill, goal or Goal("ON_TOP_OF", "picked", "support"), WorldState(facts))


def make_loop(provider):
    def forbidden_recovery(*args):
        pytest.fail("no recovery provider may run")
    return BoundedDecisionRecoveryExecutor(
        normal_decision_engine=DecisionEngine(
            EmpiricalOutcomeEstimator(ExperienceStore()), context_keys=()),
        recovery_decision_engine=RecoveryDecisionEngine(
            EmpiricalRecoveryOutcomeEstimator(RecoveryExperienceStore()), context_keys=()),
        skills=[SkillSpec(adapter.SKILL_NAME, ("ON_TOP_OF",), provider=adapter.PROVIDER_REPOSITORY)],
        recoveries=[],
        normal_executor=lambda skill, goal, state: software_result_to_observation(
            provider.execute(skill, goal, state)),
        recovery_executor=forbidden_recovery,
        budget=ExecutionBudget(1, 0, 0, 0),
    )


def test_exact_mapping_and_result_normalization(geometry, provenance, facts, fake_provider):
    result = execute(geometry, provenance, facts)
    module, scene, loader = fake_provider
    assert result.action_success and result.failure_code is None
    assert result.observations["capability_id"] == f"{adapter.PROVIDER_MODULE}.{adapter.PROVIDER_CALLABLE}"
    assert result.observations["target"]["picked_object_center_xyz_m"] == (0.3, -0.2, 0.1)
    assert result.metrics == {} and result.provenance == provenance
    assert module.compute_on_top_of_place_target.call_count == 1
    observed, dimensions = module.compute_on_top_of_place_target.call_args.args
    assert observed["object_id"] == "support"
    assert observed["base_xyz_m"] == (0.3, -0.2, 0.04)
    assert dimensions == geometry
    assert loader.call_args_list[0].args == (adapter.PROVIDER_MODULE,)


@pytest.mark.parametrize("skill", ["UNKNOWN", "NOT_VERIFIED", "PICK_PLACE", "", None, 7])
def test_unsupported_never_imports_or_calls(skill, geometry, provenance, facts, fake_provider):
    result = execute(geometry, provenance, facts, skill=skill)
    assert result.failure_code == "UNSUPPORTED_CAPABILITY"
    fake_provider[2].assert_not_called()
    fake_provider[0].compute_on_top_of_place_target.assert_not_called()


@pytest.mark.parametrize("field", sorted(adapter.GEOMETRY_FIELDS))
@pytest.mark.parametrize("bad", ["MISSING", "UNKNOWN", "NOT_VERIFIED", None, True, "0.1", [], {},
                                  float("nan"), float("inf"), float("-inf"), 10**400])
def test_all_geometry_fields_fail_closed(field, bad, geometry, provenance, facts, fake_provider):
    if bad == "MISSING":
        del geometry[field]
    else:
        geometry[field] = bad
    result = execute(geometry, provenance, facts)
    assert not result.action_success and result.failure_code == "INVALID_PROVIDER_INPUT"
    fake_provider[2].assert_not_called()


@pytest.mark.parametrize("field", ["label", "confidence", "bbox_xyxy", "base_xyz_m"])
@pytest.mark.parametrize("bad", ["MISSING", "UNKNOWN", None, True, float("nan"), float("inf"), {}])
def test_required_observation_fields(field, bad, geometry, provenance, facts, fake_provider):
    if bad == "MISSING":
        del facts["objects"]["support"][field]
    else:
        facts["objects"]["support"][field] = bad
    assert execute(geometry, provenance, facts).failure_code == "INVALID_PROVIDER_INPUT"
    fake_provider[2].assert_not_called()


@pytest.mark.parametrize("field,length", [("base_xyz_m", 3), ("bbox_xyxy", 4)])
@pytest.mark.parametrize("bad", ["UNKNOWN", True, None, "1.2", float("nan"), float("inf")])
def test_vector_elements(field, length, bad, geometry, provenance, facts, fake_provider):
    for index in range(length):
        facts["objects"]["support"][field] = [0.0] * length
        facts["objects"]["support"][field][index] = bad
        assert execute(geometry, provenance, facts).failure_code == "INVALID_PROVIDER_INPUT"
    fake_provider[2].assert_not_called()


@pytest.mark.parametrize("goal", [Goal("UNKNOWN", "picked", "support"),
    Goal("ON_TOP_OF", "UNKNOWN", "support"), Goal("ON_TOP_OF", "picked", "UNKNOWN"),
    Goal("ON_TOP_OF", "support", "support"), Goal("ON_TOP_OF", None, "support"),
    Goal("ON_TOP_OF", "a:b", "support"), Goal("ON_TOP_OF", "picked", "support", {"extra": 1})])
def test_goal_identity_and_parameters(goal, geometry, provenance, facts, fake_provider):
    assert execute(geometry, provenance, facts, goal=goal).failure_code == "INVALID_PROVIDER_INPUT"
    fake_provider[2].assert_not_called()


@pytest.mark.parametrize("change", ["geometry_extra", "observation_extra", "objects_missing",
                                     "destination_missing", "confidence_low", "confidence_high",
                                     "short_xyz", "long_bbox"])
def test_unsupported_and_invalid_values(change, geometry, provenance, facts, fake_provider):
    if change == "geometry_extra": geometry["unexpected"] = 1
    if change == "observation_extra": facts["objects"]["support"]["unexpected"] = 1
    if change == "objects_missing": facts.clear()
    if change == "destination_missing": facts["objects"].clear()
    if change == "confidence_low": facts["objects"]["support"]["confidence"] = -0.1
    if change == "confidence_high": facts["objects"]["support"]["confidence"] = 1.1
    if change == "short_xyz": facts["objects"]["support"]["base_xyz_m"] = [0, 0]
    if change == "long_bbox": facts["objects"]["support"]["bbox_xyxy"] = [0] * 5
    assert execute(geometry, provenance, facts).failure_code == "INVALID_PROVIDER_INPUT"
    fake_provider[2].assert_not_called()


@pytest.mark.parametrize("error,code", [(ModuleNotFoundError, "PROVIDER_UNAVAILABLE"),
    (ImportError, "PROVIDER_UNAVAILABLE"), (RuntimeError, "PROVIDER_CALL_FAILED")])
def test_import_failure(error, code, geometry, provenance, facts, fake_provider):
    fake_provider[2].side_effect = error("injected import failure")
    assert execute(geometry, provenance, facts).failure_code == code
    fake_provider[0].compute_on_top_of_place_target.assert_not_called()


@pytest.mark.parametrize("phase,error,code", [
    ("OnTopOfGeometry", ValueError, "INVALID_PROVIDER_INPUT"),
    ("OnTopOfGeometry", RuntimeError, "PROVIDER_CALL_FAILED"),
    ("compute_on_top_of_place_target", RuntimeError, "PROVIDER_CALL_FAILED"),
    ("compute_on_top_of_place_target", ValueError, "PROVIDER_CALL_FAILED"),
])
def test_provider_rejection_and_exception(phase, error, code, geometry, provenance, facts, fake_provider):
    getattr(fake_provider[0], phase).side_effect = error("injected provider rejection")
    result = execute(geometry, provenance, facts)
    assert result.failure_code == code and not result.action_success
    assert result.observations["exception_type"] == error.__name__


@pytest.mark.parametrize("target", [None, {},
    FakeTarget("other", (0.3, -0.2, 0.04), (0.3, -0.2, 0.1)),
    FakeTarget("support", (0, 0, 0), (0.3, -0.2, 0.1)),
    FakeTarget("support", (0.3, -0.2, 0.04), (0.3, -0.2, float("inf"))),
    FakeTarget("support", (0.3, -0.2, 0.04), (0.3, -0.2, float("nan")))])
def test_malformed_provider_result(target, geometry, provenance, facts, fake_provider):
    fake_provider[0].compute_on_top_of_place_target.return_value = target
    assert execute(geometry, provenance, facts).failure_code == "INVALID_PROVIDER_RESULT"


def test_immutable_configuration_result_and_bridge(geometry, provenance, facts, fake_provider):
    provider = adapter.RelationalPlaceTargetProvider(geometry, provenance)
    geometry["picked_object_height_m"] = 999
    result = provider.execute(adapter.SKILL_NAME, Goal("ON_TOP_OF", "picked", "support"), WorldState(facts))
    assert provider.geometry["picked_object_height_m"] == 0.04
    target = {"xyz": [1, 2, 3]}
    metrics = {"distance_m": 0.5}
    normalized = ProviderResult(True, target, metrics=metrics, provenance=provenance)
    observation = software_result_to_observation(normalized)
    target["xyz"][0] = 99
    metrics["distance_m"] = 99
    assert normalized.observations["xyz"] == (1, 2, 3)
    assert normalized.metrics["distance_m"] == 0.5
    assert observation.details["provider_metrics"]["distance_m"] == 0.5
    assert observation.state_updates == {} and observation.cost == 0
    assert observation.details["execution_cost"] == "NOT_VERIFIED"
    with pytest.raises(TypeError): result.observations["target"]["destination_object_id"] = "other"
    with pytest.raises(TypeError): provider.geometry["tabletop_z_m"] = 1


@pytest.mark.parametrize("broken", [False, True])
def test_bounded_loop_compatibility_without_goal_completion(broken, geometry, provenance, facts, fake_provider):
    if broken:
        fake_provider[0].compute_on_top_of_place_target.side_effect = RuntimeError("failure")
    result = make_loop(adapter.RelationalPlaceTargetProvider(geometry, provenance)).run(
        goal=Goal("ON_TOP_OF", "picked", "support"), initial_state=WorldState(facts))
    assert result.status == "ABORT" and not result.goal_satisfied
    assert result.total_steps == 1 and result.recovery_attempts == 0
    assert result.abort_reason == ("TERMINAL_FAILURE:PROVIDER_CALL_FAILED" if broken else "MAX_TOTAL_STEPS_EXCEEDED")
    assert result.final_state == WorldState(facts)
    assert result.trace[0].observed_result.action_success is (not broken)
    assert result.trace[0].observed_result.details["provider_provenance"]["source_commit"] == provenance.source_commit


@pytest.mark.parametrize("changes", [dict(source_repository="other"), dict(source_path="other.py"),
    dict(source_record_id="other"), dict(source_commit="UNKNOWN", artifact_snapshot_commit="UNKNOWN"),
    dict(raw_sha256="invalid")])
def test_provenance_rejects_wrong_capability_or_missing_commit(changes, geometry, provenance):
    with pytest.raises(ValueError):
        adapter.RelationalPlaceTargetProvider(geometry, replace(provenance, **changes))


def test_software_bridge_never_promotes_provider_facts_to_world_state():
    result = ProviderResult(True, {"on_top_of:picked:support": True, "goal:CANONICAL_READY": True})
    observation = software_result_to_observation(result)
    assert observation.action_success and observation.state_updates == {}
    assert observation.details["provider_observations"] == result.observations


def test_provider_result_failure_and_metrics_survive_bridge(provenance):
    result = ProviderResult(False, {"reason": "explicit rejection"}, "PROVIDER_CALL_FAILED",
                            {"diagnostic_count": 2.0}, provenance)
    observation = software_result_to_observation(result)
    assert observation.failure.code == "PROVIDER_CALL_FAILED"
    assert observation.terminal_failure and not observation.retryable
    assert observation.details["provider_metrics"] == {"diagnostic_count": 2.0}
    assert observation.cost == 0 and observation.state_updates == {}
