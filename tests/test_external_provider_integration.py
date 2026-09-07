"""Opt-in real Git source tests. No vendored provider and no worktree imports.

Set M7_PROVIDER_REPOSITORY to a local clone containing PROVIDER_COMMIT. Tests
read committed blobs into pytest's temporary directory and verify every imported
provider source against that commit. A missing opt-in is SKIPPED, never VERIFIED.
"""
import hashlib
import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from physical_ai_skill_intelligence.adapters import relational_place as adapter
from physical_ai_skill_intelligence import Goal, WorldState
from physical_ai_skill_intelligence.provenance import Provenance, SourceArtifact
from physical_ai_skill_intelligence.provider_observation import software_result_to_observation
from test_relational_place_provider import facts, geometry, make_loop  # shared synthetic inputs

PROVIDER_COMMIT = "dd12a75bbe55df65ce8112fe4fd6fdf2c903eb9f"


@pytest.fixture(scope="module")
def committed_snapshot(tmp_path_factory):
    repository = os.environ.get("M7_PROVIDER_REPOSITORY")
    if repository is None:
        pytest.skip("M7_PROVIDER_REPOSITORY required for real committed provider integration")
    root = tmp_path_factory.mktemp("m7_committed_provider")
    def git(*args):
        return subprocess.check_output(["git", "-C", repository, *args])
    assert git("rev-parse", f"{PROVIDER_COMMIT}^{{commit}}").decode().strip() == PROVIDER_COMMIT
    files = git("ls-tree", "-r", "--name-only", PROVIDER_COMMIT,
                "src/ur3_visual_servoing").decode().splitlines()
    assert adapter.SOURCE_PATH in files
    digests = {}
    for name in files:
        # Trusted Git paths still must stay within the temporary snapshot.
        target = root / name
        assert target.resolve().is_relative_to(root.resolve())
        raw = git("show", f"{PROVIDER_COMMIT}:{name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o444)
        digests[name] = hashlib.sha256(raw).hexdigest()
    return root, digests


@pytest.fixture
def real_provider(committed_snapshot, monkeypatch):
    root, digests = committed_snapshot
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.syspath_prepend(str(root / "src"))
    for name in tuple(sys.modules):
        if name == "ur3_visual_servoing" or name.startswith("ur3_visual_servoing."):
            monkeypatch.delitem(sys.modules, name)
    importlib.invalidate_caches()
    provider = importlib.import_module(adapter.PROVIDER_MODULE)
    loaded = []
    for name, module in tuple(sys.modules.items()):
        if name == "ur3_visual_servoing" or name.startswith("ur3_visual_servoing."):
            path = Path(module.__file__).resolve()
            assert path.is_relative_to(root.resolve())
            relative = path.relative_to(root).as_posix()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digests[relative]
            loaded.append(SourceArtifact(relative, digests[relative]))
    provenance = Provenance(
        adapter.PROVIDER_REPOSITORY, PROVIDER_COMMIT, adapter.SOURCE_PATH,
        adapter.PROVIDER_CALLABLE, digests[adapter.SOURCE_PATH], "m7-software-call-v1",
        importer_version="m7-adapter-v1",
        related_sources=tuple(item for item in loaded if item.source_path != adapter.SOURCE_PATH),
        # This is software source integration, not a physical experiment.
        experiment_runtime_commit="NOT_VERIFIED",
    )
    yield provider, provenance
    for name in tuple(sys.modules):
        if name == "ur3_visual_servoing" or name.startswith("ur3_visual_servoing."):
            del sys.modules[name]


def test_real_committed_callable_normalization_and_bounded_loop(
        real_provider, geometry, facts, record_property):
    provider, provenance = real_provider
    scene = importlib.import_module("ur3_visual_servoing.vision.scene_objects")
    observed = scene.SceneObject("support", "support", 0.9, scene.BBox2D(10, 20, 30, 40),
                                 (0.3, -0.2, 0.04))
    direct = provider.compute_on_top_of_place_target(observed, provider.OnTopOfGeometry(**geometry))
    boundary = adapter.RelationalPlaceTargetProvider(geometry, provenance)
    goal, state = Goal("ON_TOP_OF", "picked", "support"), WorldState(facts)
    normalized = boundary.execute(adapter.SKILL_NAME, goal, state)
    assert normalized.action_success and normalized.failure_code is None
    target = normalized.observations["target"]
    assert target["picked_object_center_xyz_m"] == direct.picked_object_center_xyz_m
    assert target["picked_object_center_xyz_m"] == (0.3, -0.2, 0.1)
    assert target["source_destination_xyz_m"] == direct.source_destination_xyz_m
    assert target["destination_object_id"] == direct.destination_object_id
    assert normalized.provenance.artifact_snapshot_commit == PROVIDER_COMMIT
    assert normalized.provenance.experiment_runtime_commit == "NOT_VERIFIED"
    observation = software_result_to_observation(normalized)
    assert observation.state_updates == {}
    assert observation.details["provider_provenance"]["related_sources"]
    result = make_loop(boundary).run(goal=goal, initial_state=state)
    assert result.status == "ABORT" and result.abort_reason == "MAX_TOTAL_STEPS_EXCEEDED"
    assert result.trace[0].decision.selected_skill == adapter.SKILL_NAME
    assert result.trace[0].observed_result.action_success
    assert not result.goal_satisfied and result.final_state == state
    assert result.total_steps == 1 and result.recovery_attempts == 0
    for name, value in {
        "PROVIDER_REPOSITORY": adapter.PROVIDER_REPOSITORY,
        "PROVIDER_COMMIT": PROVIDER_COMMIT,
        "PROVIDER_MODULE": adapter.PROVIDER_MODULE,
        "PROVIDER_CALLABLE": adapter.PROVIDER_CALLABLE,
        "PROVIDER_SOURCE_SHA256": provenance.raw_sha256,
    }.items():
        record_property(name, value)
        print(f"{name} = {value}")


@pytest.mark.parametrize("field,value", [
    ("picked_object_height_m", 0), ("picked_object_height_m", -1),
    ("destination_object_height_m", 0), ("destination_support_radius_m", 0),
    ("support_margin_m", -0.001), ("support_margin_m", 0.05),
    ("support_margin_m", 0.06), ("z_tolerance_m", 0),
])
def test_real_provider_input_rejection(real_provider, geometry, facts, field, value, monkeypatch):
    provider, provenance = real_provider
    geometry[field] = value
    def must_not_call(*args):
        pytest.fail("rejected constructor input must not reach target computation")
    monkeypatch.setattr(provider, "compute_on_top_of_place_target", must_not_call)
    result = adapter.RelationalPlaceTargetProvider(geometry, provenance).execute(
        adapter.SKILL_NAME, Goal("ON_TOP_OF", "picked", "support"), WorldState(facts))
    assert not result.action_success and result.failure_code == "INVALID_PROVIDER_INPUT"


def test_real_bbox_rejection(real_provider, geometry, facts):
    _, provenance = real_provider
    facts["objects"]["support"]["bbox_xyxy"] = [1, 1, 0, 0]
    result = adapter.RelationalPlaceTargetProvider(geometry, provenance).execute(
        adapter.SKILL_NAME, Goal("ON_TOP_OF", "picked", "support"), WorldState(facts))
    assert result.failure_code == "INVALID_PROVIDER_INPUT"


def test_real_finite_input_overflow_rejected_as_invalid_result(real_provider, geometry, facts):
    _, provenance = real_provider
    geometry.update(tabletop_z_m=1.7e308, destination_object_height_m=1.7e308)
    result = adapter.RelationalPlaceTargetProvider(geometry, provenance).execute(
        adapter.SKILL_NAME, Goal("ON_TOP_OF", "picked", "support"), WorldState(facts))
    assert not result.action_success and result.failure_code == "INVALID_PROVIDER_RESULT"
