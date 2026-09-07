"""One software geometry capability, implementing the existing SkillProvider.

Geometry is explicit immutable configuration; destination observations come from
WorldState.objects[goal.reference]. No hardware dimensions or observations are
inferred. Success means a target was computed, never that placement occurred.
The caller supplies pinned provenance and a configurable Git repository path.
Runtime loaded source identity is checked before provider constructors/calls.
"""
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib import import_module
from math import isfinite

from .._integrity import snapshot_mapping
from ..goal import Goal
from ..provenance import Provenance, validate_commit
from ..provider_contract import ProviderResult
from ..state import WorldState
from ._source_attestation import attest_provider_source

SKILL_NAME = "COMPUTE_ON_TOP_OF_PLACE_TARGET"
PROVIDER_REPOSITORY = "SportyRain/ur3_visual_servoing"
PROVIDER_MODULE = "ur3_visual_servoing.task.relational_pick_place"
PROVIDER_CALLABLE = "compute_on_top_of_place_target"
SOURCE_PATH = "src/ur3_visual_servoing/task/relational_pick_place.py"
GEOMETRY_FIELDS = frozenset({
    "tabletop_z_m", "picked_object_height_m", "destination_object_height_m",
    "destination_support_radius_m", "support_margin_m", "z_tolerance_m",
})


def _number(value):
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError("required finite numeric value")


def _identity(value):
    if (not isinstance(value, str) or not value.strip() or value != value.strip()
            or value in {"UNKNOWN", "NOT_VERIFIED"} or ":" in value):
        raise ValueError("required explicit identity")


def _vector(value, length):
    if not isinstance(value, (tuple, list)) or len(value) != length:
        raise ValueError("invalid coordinate vector")
    for coordinate in value:
        _number(coordinate)


@dataclass(frozen=True)
class RelationalPlaceTargetProvider:
    geometry: Mapping[str, float]
    provenance: Provenance
    provider_repository: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "geometry", snapshot_mapping(self.geometry))
        self.provenance.validate()
        validate_commit(self.provenance.artifact_snapshot_commit,
                        "artifact_snapshot_commit", allow_unknown=False)
        if (self.provenance.source_repository != PROVIDER_REPOSITORY
                or self.provenance.source_path != SOURCE_PATH
                or self.provenance.source_record_id != PROVIDER_CALLABLE):
            raise ValueError("provenance must identify the exact software capability")

    def _result(self, success, *, failure_code=None, observations=None, metrics=None,
                runtime_identity=None):
        return ProviderResult(
            success,
            {"capability_id": f"{PROVIDER_MODULE}.{PROVIDER_CALLABLE}",
             "capability_kind": "SOFTWARE_TARGET_COMPUTATION",
             "runtime_provider_identity": runtime_identity or {"status": "NOT_VERIFIED"},
             **(observations or {})},
            failure_code, metrics, self.provenance,
        )

    def execute(self, skill_name: str, goal: Goal, state: WorldState) -> ProviderResult:
        if skill_name != SKILL_NAME:
            return self._result(False, failure_code="UNSUPPORTED_CAPABILITY")
        try:
            if not isinstance(goal, Goal) or not isinstance(state, WorldState):
                raise ValueError("Goal and WorldState required")
            if goal.predicate != "ON_TOP_OF" or goal.parameters:
                raise ValueError("only an unparameterized ON_TOP_OF goal is supported")
            _identity(goal.subject)
            _identity(goal.reference)
            if goal.subject == goal.reference:
                raise ValueError("subject and destination must differ")
            if set(self.geometry) != GEOMETRY_FIELDS:
                raise ValueError("all and only explicit geometry fields required")
            for value in self.geometry.values():
                _number(value)
            objects = state.get("objects")
            if not isinstance(objects, Mapping):
                raise ValueError("explicit objects mapping required")
            destination = objects[goal.reference]
            if not isinstance(destination, Mapping) or set(destination) != {
                "label", "confidence", "bbox_xyxy", "base_xyz_m"
            }:
                raise ValueError("all and only destination observation fields required")
            _identity(destination["label"])
            _number(destination["confidence"])
            if not 0 <= destination["confidence"] <= 1:
                raise ValueError("confidence outside [0, 1]")
            _vector(destination["base_xyz_m"], 3)
            _vector(destination["bbox_xyxy"], 4)
        except Exception as exc:
            return self._result(False, failure_code="INVALID_PROVIDER_INPUT",
                                observations={"exception_type": type(exc).__name__})

        try:
            provider = import_module(PROVIDER_MODULE)
            scene = import_module("ur3_visual_servoing.vision.scene_objects")
        except ImportError as exc:
            return self._result(False, failure_code="PROVIDER_UNAVAILABLE",
                                observations={"exception_type": type(exc).__name__})
        except Exception as exc:
            return self._result(False, failure_code="PROVIDER_CALL_FAILED",
                                observations={"exception_type": type(exc).__name__})

        try:
            runtime_identity = attest_provider_source(
                provider, self.provenance, self.provider_repository,
                PROVIDER_MODULE, PROVIDER_CALLABLE,
            )
        except Exception as exc:
            return self._result(False, failure_code="RUNTIME_PROVIDER_IDENTITY_UNVERIFIED",
                                observations={"exception_type": type(exc).__name__})

        try:
            # Provider-owned input validation includes support margin/radius and
            # bbox bounds. These constructors perform no geometry planning.
            geometry = provider.OnTopOfGeometry(**self.geometry)
            observed = scene.SceneObject(
                object_id=goal.reference, label=destination["label"],
                confidence=destination["confidence"],
                bbox=scene.BBox2D(*destination["bbox_xyxy"]),
                base_xyz_m=destination["base_xyz_m"],
            )
        except (ValueError, TypeError) as exc:
            return self._result(False, failure_code="INVALID_PROVIDER_INPUT",
                                observations={"exception_type": type(exc).__name__},
                                runtime_identity=runtime_identity)
        except Exception as exc:
            return self._result(False, failure_code="PROVIDER_CALL_FAILED",
                                observations={"exception_type": type(exc).__name__},
                                runtime_identity=runtime_identity)

        try:
            target = provider.compute_on_top_of_place_target(observed, geometry)
        except Exception as exc:
            return self._result(False, failure_code="PROVIDER_CALL_FAILED",
                                observations={"exception_type": type(exc).__name__},
                                runtime_identity=runtime_identity)
        try:
            if not isinstance(target, provider.ObjectRelativePlaceTarget):
                raise ValueError("unexpected provider result type")
            if target.destination_object_id != goal.reference:
                raise ValueError("provider destination identity mismatch")
            _vector(target.source_destination_xyz_m, 3)
            _vector(target.picked_object_center_xyz_m, 3)
            if tuple(target.source_destination_xyz_m) != tuple(destination["base_xyz_m"]):
                raise ValueError("provider source observation mismatch")
            # Preserve the provider target unchanged. No placement math or state
            # updates here; even finite inputs can yield nonfinite outputs.
            return self._result(True, observations={"target": asdict(target)}, metrics={},
                                runtime_identity=runtime_identity)
        except Exception as exc:
            return self._result(False, failure_code="INVALID_PROVIDER_RESULT",
                                observations={"exception_type": type(exc).__name__},
                                runtime_identity=runtime_identity)
