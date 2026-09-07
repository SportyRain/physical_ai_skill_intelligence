"""M8 adapter for one source-attested real UR3 +5 mm free-space action.

This adapter owns no ROS, controller, planner, retry, recovery, timeout, or
cancellation machinery.  It validates the narrow Physical AI request, attests
the caller-pinned provider source immediately before the call, invokes the
provider's existing bounded action, and preserves the provider result without
inventing WorldState updates or broader motion capability.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib import import_module
from math import isfinite
from typing import Any

from ..goal import Goal
from ..provenance import Provenance, validate_commit
from ..provider_contract import ProviderResult, ProviderRuntimeContract
from ..state import WorldState
from ._source_attestation import attest_provider_source


SKILL_NAME = "REAL_UR3_POSITIVE_AXIS_5MM_TRANSLATION"
GOAL_PREDICATE = "TRANSLATE_POSITIVE_AXIS_5MM"
GOAL_SUBJECT = "UR3_TCP"
VALID_AXES = frozenset({"X", "Y", "Z"})

PROVIDER_REPOSITORY = "SportyRain/ur3_visual_servoing"
PROVIDER_MODULE = "ur3_visual_servoing.runtime.real_free_space_translation"
PROVIDER_CALLABLE = "execute_positive_axis_5mm"
SOURCE_PATH = "src/ur3_visual_servoing/runtime/real_free_space_translation.py"

DEFAULT_MOTION_TIMEOUT_S = 12.0
DEFAULT_SETTLE_ERROR_MM = 1.0


def _positive(value: Any, name: str) -> float:
    if type(value) not in (int, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be a finite positive number")
    return float(value)


def _runtime_contract(timeout_s: float) -> ProviderRuntimeContract:
    return ProviderRuntimeContract(
        configured_timeout_s=timeout_s,
        timeout_api=f"{PROVIDER_MODULE}:_RosRuntime.move",
        timeout_scope="motion settle loop only; startup and cleanup excluded",
        cancel_api="UNKNOWN",
        cancel_completion_semantics="UNKNOWN",
    )


@dataclass(frozen=True)
class RealUr3PositiveAxis5mmProvider:
    """Thin Physical AI boundary over the provider's exact +5 mm action."""

    provenance: Provenance
    provider_repository: str | None = None
    execute_real: bool = False
    motion_timeout_s: float = DEFAULT_MOTION_TIMEOUT_S
    settle_error_mm: float = DEFAULT_SETTLE_ERROR_MM

    def __post_init__(self) -> None:
        if type(self.execute_real) is not bool:
            raise ValueError("execute_real must be boolean")
        _positive(self.motion_timeout_s, "motion_timeout_s")
        _positive(self.settle_error_mm, "settle_error_mm")
        self.provenance.validate()
        validate_commit(
            self.provenance.artifact_snapshot_commit,
            "artifact_snapshot_commit",
            allow_unknown=False,
        )
        if (
            self.provenance.source_repository != PROVIDER_REPOSITORY
            or self.provenance.source_path != SOURCE_PATH
            or self.provenance.source_record_id != PROVIDER_CALLABLE
        ):
            raise ValueError("provenance must identify the exact real UR3 capability")

    def _result(
        self,
        success: bool,
        *,
        failure_code: str | None = None,
        observations: Mapping[str, Any] | None = None,
        metrics: Mapping[str, float] | None = None,
        runtime_identity: Mapping[str, Any] | None = None,
    ) -> ProviderResult:
        return ProviderResult(
            action_success=success,
            observations={
                "capability_id": f"{PROVIDER_MODULE}.{PROVIDER_CALLABLE}",
                "capability_kind": "REAL_UR3_BOUNDED_FREE_SPACE_TRANSLATION",
                "runtime_provider_identity": runtime_identity
                or {"status": "NOT_VERIFIED"},
                **(dict(observations) if observations else {}),
            },
            failure_code=failure_code,
            metrics=metrics,
            provenance=self.provenance,
            runtime_contract=_runtime_contract(float(self.motion_timeout_s)),
        )

    def execute(self, skill_name: str, goal: Goal, state: WorldState) -> ProviderResult:
        if skill_name != SKILL_NAME:
            return self._result(False, failure_code="UNSUPPORTED_CAPABILITY")

        try:
            if not isinstance(goal, Goal) or not isinstance(state, WorldState):
                raise ValueError("Goal and WorldState required")
            if goal.predicate != GOAL_PREDICATE:
                raise ValueError("unsupported goal predicate")
            if goal.subject != GOAL_SUBJECT or goal.reference is not None:
                raise ValueError("goal must identify only UR3_TCP")
            if set(goal.parameters) != {"axis"}:
                raise ValueError("goal parameters must contain exactly axis")
            axis = goal.parameters["axis"]
            if not isinstance(axis, str) or axis not in VALID_AXES:
                raise ValueError("axis must be exactly X, Y, or Z")
        except Exception as exc:
            return self._result(
                False,
                failure_code="INVALID_PROVIDER_INPUT",
                observations={"exception_type": type(exc).__name__},
            )

        try:
            provider = import_module(PROVIDER_MODULE)
        except ImportError as exc:
            return self._result(
                False,
                failure_code="PROVIDER_UNAVAILABLE",
                observations={"exception_type": type(exc).__name__},
            )
        except Exception as exc:
            return self._result(
                False,
                failure_code="PROVIDER_CALL_FAILED",
                observations={"exception_type": type(exc).__name__},
            )

        try:
            runtime_identity = attest_provider_source(
                provider,
                self.provenance,
                self.provider_repository,
                PROVIDER_MODULE,
                PROVIDER_CALLABLE,
            )
        except Exception as exc:
            return self._result(
                False,
                failure_code="RUNTIME_PROVIDER_IDENTITY_UNVERIFIED",
                observations={"exception_type": type(exc).__name__},
            )

        try:
            provider_result = provider.execute_positive_axis_5mm(
                axis,
                execute=self.execute_real,
                motion_timeout_sec=float(self.motion_timeout_s),
                settle_error_mm=float(self.settle_error_mm),
            )
        except Exception as exc:
            return self._result(
                False,
                failure_code="PROVIDER_CALL_FAILED",
                observations={"exception_type": type(exc).__name__},
                runtime_identity=runtime_identity,
            )

        try:
            if not isinstance(provider_result, provider.FreeSpaceTranslationResult):
                raise ValueError("unexpected provider result type")
            payload = asdict(provider_result)
            if payload["axis"] != axis or payload["requested_translation_m"] != 0.005:
                raise ValueError("provider result escaped the +5 mm capability bound")
            if payload["status"] not in {
                "PASS",
                "TIMEOUT",
                "BLOCKED_EXECUTION_REQUIRED",
            }:
                raise ValueError("unexpected provider status")
            if type(payload["provider_completed"]) is not bool:
                raise ValueError("provider completion must be explicit")
            if type(payload["command_published"]) is not bool:
                raise ValueError("command publication must be explicit")
            if type(payload["settled"]) is not bool or type(payload["timed_out"]) is not bool:
                raise ValueError("provider termination flags must be explicit")
        except Exception as exc:
            return self._result(
                False,
                failure_code="INVALID_PROVIDER_RESULT",
                observations={"exception_type": type(exc).__name__},
                runtime_identity=runtime_identity,
            )

        observations = {
            "provider_result": payload,
            "command_accepted": payload["command_acceptance"],
            "provider_completed": payload["provider_completed"],
            "actual_tcp_motion_observation": {
                "initial_tcp_base_m": payload["initial_tcp_base_m"],
                "target_tcp_base_m": payload["target_tcp_base_m"],
                "final_tcp_base_m": payload["final_tcp_base_m"],
                "observed_axis_translation_m": payload["observed_axis_translation_m"],
                "observed_translation_norm_m": payload["observed_translation_norm_m"],
                "settled": payload["settled"],
            },
            "final_runtime_state": {
                "forward_position_controller": payload["final_fpc_state"],
                "servo_paused": payload["servo_paused"],
            },
        }

        metrics: dict[str, float] = {}
        for name in (
            "observed_axis_translation_m",
            "observed_translation_norm_m",
            "final_error_mm",
            "motion_elapsed_s",
        ):
            value = payload[name]
            if type(value) in (int, float) and isfinite(value):
                metrics[name] = float(value)

        success = bool(
            payload["status"] == "PASS"
            and payload["provider_completed"]
            and payload["settled"]
            and not payload["timed_out"]
            and payload["final_fpc_state"] == "inactive"
            and payload["servo_paused"] is True
            and payload["observed_axis_translation_m"] is not None
        )
        if success:
            return self._result(
                True,
                observations=observations,
                metrics=metrics,
                runtime_identity=runtime_identity,
            )

        return self._result(
            False,
            failure_code=str(payload["status"]),
            observations=observations,
            metrics=metrics,
            runtime_identity=runtime_identity,
        )
