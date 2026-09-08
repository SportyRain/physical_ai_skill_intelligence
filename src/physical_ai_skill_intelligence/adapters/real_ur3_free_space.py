"""M8 adapter for one source-attested real UR3 +5 mm free-space action.

This adapter owns no ROS, controller, planner, retry, recovery, timeout, or
cancellation machinery. It validates the narrow Physical AI request, attests
the caller-pinned provider source immediately before the call, invokes the
provider's existing bounded action, and preserves the provider result without
inventing WorldState updates or broader motion capability.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from importlib import import_module
from inspect import signature
from math import isclose, isfinite
from typing import Any

from ..goal import Goal
from ..provenance import Provenance, validate_commit
from ..provider_contract import (
    ProviderResult,
    ProviderRuntimeContract,
    ProviderRuntimeResult,
)
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
DEFAULT_OPERATION_TIMEOUT_S = 30.0
DEFAULT_CLEANUP_TIMEOUT_S = 15.0
DEFAULT_SETTLE_ERROR_MM = 1.0
_EXTENDED_RUNTIME_PARAMETERS = frozenset(
    {"operation_timeout_sec", "cleanup_timeout_sec", "cancel_requested"}
)
_EXTENDED_RUNTIME_RESULT_FIELDS = frozenset(
    {
        "operation_elapsed_s",
        "cleanup_elapsed_s",
        "wall_clock_elapsed_s",
        "configured_operation_timeout_s",
        "configured_cleanup_timeout_s",
        "configured_wall_clock_limit_s",
        "termination_reason",
        "cancel_requested",
        "cleanup_completed",
    }
)
_TERMINATION_REASONS_BY_STATUS = {
    "PASS": frozenset({"SETTLED"}),
    "TIMEOUT": frozenset({"MOTION_SETTLE_TIMEOUT", "OPERATION_TIMEOUT"}),
    "CANCELLED": frozenset({"CANCEL_REQUESTED", "CANCELLED_BEFORE_RUNTIME"}),
    "BLOCKED_EXECUTION_REQUIRED": frozenset(
        {"EXECUTION_BLOCKED", "BLOCKED_EXECUTION_REQUIRED"}
    ),
}
_ELAPSED_TOLERANCE_S = 1e-6


def _positive(value: Any, name: str) -> float:
    if type(value) not in (int, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be a finite positive number")
    return float(value)


def _nonnegative(value: Any, name: str) -> float:
    if type(value) not in (int, float) or not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a finite nonnegative number")
    return float(value)


def _legacy_runtime_contract(timeout_s: float) -> ProviderRuntimeContract:
    return ProviderRuntimeContract(
        configured_timeout_s=timeout_s,
        timeout_api=f"{PROVIDER_MODULE}:_RosRuntime.move",
        timeout_scope="motion settle loop only; startup and cleanup excluded",
        cancel_api="UNKNOWN",
        cancel_completion_semantics="UNKNOWN",
    )


def _extended_runtime_contract(
    motion_timeout_s: float,
    operation_timeout_s: float,
    cleanup_timeout_s: float,
) -> ProviderRuntimeContract:
    return ProviderRuntimeContract(
        configured_wall_clock_limit_s=operation_timeout_s + cleanup_timeout_s,
        configured_timeout_s=motion_timeout_s,
        configured_operation_timeout_s=operation_timeout_s,
        configured_cleanup_timeout_s=cleanup_timeout_s,
        timeout_api=f"{PROVIDER_MODULE}:{PROVIDER_CALLABLE}",
        timeout_scope=(
            "provider operation deadline covers startup and motion; cleanup has a "
            "separate deadline; configured wall-clock limit is operation+cleanup"
        ),
        cancel_api=f"{PROVIDER_MODULE}:{PROVIDER_CALLABLE}(cancel_requested)",
        cancel_completion_semantics=(
            "provider cancel_completed/cancel_acknowledged is normalized only as "
            "software cancel acknowledgement; cleanup_completed and "
            "physical_stop_verified remain separate"
        ),
    )


def _supports_extended_runtime(provider_callable: Any) -> bool:
    parameters = signature(provider_callable).parameters
    present = _EXTENDED_RUNTIME_PARAMETERS.intersection(parameters)
    if present and present != _EXTENDED_RUNTIME_PARAMETERS:
        raise ValueError("provider exposes only a partial extended runtime API")
    return present == _EXTENDED_RUNTIME_PARAMETERS


def _normalize_runtime_result(
    payload: Mapping[str, Any],
    *,
    extended_runtime: bool,
) -> ProviderRuntimeResult:
    if not extended_runtime:
        return ProviderRuntimeResult(timed_out=payload["timed_out"])

    missing = _EXTENDED_RUNTIME_RESULT_FIELDS.difference(payload)
    if missing:
        raise ValueError("extended runtime result fields are incomplete")
    if "cancel_acknowledged" not in payload and "cancel_completed" not in payload:
        raise ValueError("cancel acknowledgement is missing")

    cancel_acknowledged = payload.get("cancel_acknowledged")
    if "cancel_completed" in payload:
        cancel_completed = payload["cancel_completed"]
        if type(cancel_completed) is not bool:
            raise ValueError("cancel_completed must be explicit boolean")
        if cancel_acknowledged is None:
            cancel_acknowledged = cancel_completed
        elif cancel_acknowledged is not cancel_completed:
            raise ValueError("cancel acknowledgement fields contradict each other")

    for name in ("cancel_requested", "cleanup_completed"):
        if type(payload[name]) is not bool:
            raise ValueError(f"{name} must be explicit boolean")
    if type(cancel_acknowledged) is not bool:
        raise ValueError("cancel acknowledgement must be explicit boolean")

    termination_reason = payload["termination_reason"]
    if (
        not isinstance(termination_reason, str)
        or termination_reason.strip() in {"", "UNKNOWN", "NOT_VERIFIED", "UNRESOLVED"}
    ):
        raise ValueError("extended runtime result requires termination_reason")

    return ProviderRuntimeResult(
        termination_reason=termination_reason,
        timed_out=payload["timed_out"],
        cancel_requested=payload["cancel_requested"],
        cancel_acknowledged=cancel_acknowledged,
        cleanup_completed=payload["cleanup_completed"],
        operation_elapsed_s=_nonnegative(
            payload["operation_elapsed_s"], "operation_elapsed_s"
        ),
        cleanup_elapsed_s=_nonnegative(
            payload["cleanup_elapsed_s"], "cleanup_elapsed_s"
        ),
        wall_clock_elapsed_s=_nonnegative(
            payload["wall_clock_elapsed_s"], "wall_clock_elapsed_s"
        ),
    )


def _validate_extended_runtime_semantics(
    payload: Mapping[str, Any],
    runtime_result: ProviderRuntimeResult,
) -> None:
    status = str(payload["status"])
    allowed_reasons = _TERMINATION_REASONS_BY_STATUS[status]
    if runtime_result.termination_reason not in allowed_reasons:
        raise ValueError(
            f"{status} contradicts termination_reason={runtime_result.termination_reason}"
        )

    operation_elapsed = runtime_result.operation_elapsed_s
    cleanup_elapsed = runtime_result.cleanup_elapsed_s
    wall_clock_elapsed = runtime_result.wall_clock_elapsed_s
    if operation_elapsed is None or cleanup_elapsed is None or wall_clock_elapsed is None:
        raise ValueError("extended runtime elapsed evidence is incomplete")
    if wall_clock_elapsed + _ELAPSED_TOLERANCE_S < operation_elapsed + cleanup_elapsed:
        raise ValueError(
            "wall_clock_elapsed_s is smaller than operation+cleanup elapsed evidence"
        )

    cleanup_limit = _positive(
        payload["configured_cleanup_timeout_s"], "configured_cleanup_timeout_s"
    )
    if cleanup_elapsed > cleanup_limit + _ELAPSED_TOLERANCE_S:
        raise ValueError("cleanup_elapsed_s exceeds configured cleanup timeout")


@dataclass(frozen=True)
class RealUr3PositiveAxis5mmProvider:
    """Thin Physical AI boundary over the provider's exact +5 mm action."""

    provenance: Provenance
    provider_repository: str | None = None
    execute_real: bool = False
    motion_timeout_s: float = DEFAULT_MOTION_TIMEOUT_S
    operation_timeout_s: float = DEFAULT_OPERATION_TIMEOUT_S
    cleanup_timeout_s: float = DEFAULT_CLEANUP_TIMEOUT_S
    settle_error_mm: float = DEFAULT_SETTLE_ERROR_MM
    cancel_requested_callback: Callable[[], bool] | None = None

    def __post_init__(self) -> None:
        if type(self.execute_real) is not bool:
            raise ValueError("execute_real must be boolean")
        _positive(self.motion_timeout_s, "motion_timeout_s")
        _positive(self.operation_timeout_s, "operation_timeout_s")
        _positive(self.cleanup_timeout_s, "cleanup_timeout_s")
        _positive(self.settle_error_mm, "settle_error_mm")
        if self.cancel_requested_callback is not None and not callable(
            self.cancel_requested_callback
        ):
            raise ValueError("cancel_requested_callback must be callable or None")
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
        runtime_contract: ProviderRuntimeContract | None = None,
        runtime_result: ProviderRuntimeResult | None = None,
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
            runtime_contract=runtime_contract
            or _legacy_runtime_contract(float(self.motion_timeout_s)),
            runtime_result=runtime_result or ProviderRuntimeResult(),
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
            extended_runtime = _supports_extended_runtime(
                provider.execute_positive_axis_5mm
            )
        except Exception as exc:
            return self._result(
                False,
                failure_code="PROVIDER_RUNTIME_CONTRACT_UNSUPPORTED",
                observations={"exception_type": type(exc).__name__},
                runtime_identity=runtime_identity,
            )

        if self.cancel_requested_callback is not None and not extended_runtime:
            return self._result(
                False,
                failure_code="PROVIDER_RUNTIME_CONTRACT_UNSUPPORTED",
                observations={"cancel_requested": "UNSUPPORTED_BY_PROVIDER_API"},
                runtime_identity=runtime_identity,
            )

        runtime_contract = (
            _extended_runtime_contract(
                float(self.motion_timeout_s),
                float(self.operation_timeout_s),
                float(self.cleanup_timeout_s),
            )
            if extended_runtime
            else _legacy_runtime_contract(float(self.motion_timeout_s))
        )

        call_kwargs: dict[str, Any] = {
            "execute": self.execute_real,
            "motion_timeout_sec": float(self.motion_timeout_s),
            "settle_error_mm": float(self.settle_error_mm),
        }
        if extended_runtime:
            call_kwargs.update(
                operation_timeout_sec=float(self.operation_timeout_s),
                cleanup_timeout_sec=float(self.cleanup_timeout_s),
                cancel_requested=self.cancel_requested_callback,
            )

        try:
            provider_result = provider.execute_positive_axis_5mm(axis, **call_kwargs)
        except Exception as exc:
            return self._result(
                False,
                failure_code="PROVIDER_CALL_FAILED",
                observations={"exception_type": type(exc).__name__},
                runtime_identity=runtime_identity,
                runtime_contract=runtime_contract,
            )

        payload: dict[str, Any] | None = None
        runtime_result = ProviderRuntimeResult()
        try:
            if not isinstance(provider_result, provider.FreeSpaceTranslationResult):
                raise ValueError("unexpected provider result type")
            payload = asdict(provider_result)
            if payload["axis"] != axis or payload["requested_translation_m"] != 0.005:
                raise ValueError("provider result escaped the +5 mm capability bound")
            if payload["status"] not in {
                "PASS",
                "TIMEOUT",
                "CANCELLED",
                "BLOCKED_EXECUTION_REQUIRED",
            }:
                raise ValueError("unexpected provider status")
            if type(payload["provider_completed"]) is not bool:
                raise ValueError("provider completion must be explicit")
            if type(payload["command_published"]) is not bool:
                raise ValueError("command publication must be explicit")
            if (
                type(payload["settled"]) is not bool
                or type(payload["timed_out"]) is not bool
            ):
                raise ValueError("provider termination flags must be explicit")
            if payload["status"] == "CANCELLED" and not extended_runtime:
                raise ValueError("legacy runtime contract cannot report CANCELLED")

            runtime_result = _normalize_runtime_result(
                payload,
                extended_runtime=extended_runtime,
            )

            if extended_runtime:
                for name, expected in (
                    (
                        "configured_operation_timeout_s",
                        float(self.operation_timeout_s),
                    ),
                    (
                        "configured_cleanup_timeout_s",
                        float(self.cleanup_timeout_s),
                    ),
                    (
                        "configured_wall_clock_limit_s",
                        float(self.operation_timeout_s)
                        + float(self.cleanup_timeout_s),
                    ),
                ):
                    actual = _positive(payload[name], name)
                    if not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9):
                        raise ValueError(
                            f"{name} contradicts requested runtime contract"
                        )
                _validate_extended_runtime_semantics(payload, runtime_result)

            status = payload["status"]
            if not payload["provider_completed"]:
                raise ValueError("returned provider result must be completed")
            if status == "PASS":
                if (
                    not payload["command_published"]
                    or not payload["settled"]
                    or payload["timed_out"]
                ):
                    raise ValueError("PASS contradicts provider termination flags")
            elif status == "TIMEOUT":
                if not payload["timed_out"] or payload["settled"]:
                    raise ValueError("TIMEOUT contradicts provider termination flags")
            elif status == "CANCELLED":
                if payload["timed_out"] or payload["settled"]:
                    raise ValueError("CANCELLED contradicts provider termination flags")
                if (
                    runtime_result.cancel_requested is not True
                    or runtime_result.cancel_acknowledged is not True
                ):
                    raise ValueError(
                        "CANCELLED requires requested and acknowledged cancel"
                    )
            elif status == "BLOCKED_EXECUTION_REQUIRED":
                if (
                    payload["command_published"]
                    or payload["timed_out"]
                    or payload["settled"]
                ):
                    raise ValueError("blocked result contradicts execution flags")

            if extended_runtime and status in {"PASS", "TIMEOUT", "CANCELLED"}:
                if runtime_result.cleanup_completed is not True:
                    raise ValueError(f"{status} requires completed cleanup")
                if payload["command_published"] and (
                    payload["final_fpc_state"] != "inactive"
                    or payload["servo_paused"] is not True
                ):
                    raise ValueError(
                        "post-command terminal result requires completed safe cleanup"
                    )

            if extended_runtime and status != "CANCELLED":
                if runtime_result.cancel_requested or runtime_result.cancel_acknowledged:
                    raise ValueError("non-cancel status carries cancel evidence")
        except Exception as exc:
            invalid_observations: dict[str, Any] = {
                "exception_type": type(exc).__name__,
                "invalid_provider_result_reason": str(exc),
            }
            if payload is not None:
                invalid_observations["provider_result"] = payload
            return self._result(
                False,
                failure_code="INVALID_PROVIDER_RESULT",
                observations=invalid_observations,
                runtime_identity=runtime_identity,
                runtime_contract=runtime_contract,
                runtime_result=runtime_result,
            )

        observations = {
            "provider_result": payload,
            "command_accepted": payload["command_acceptance"],
            "provider_completed": payload["provider_completed"],
            "actual_tcp_motion_observation": {
                "initial_tcp_base_m": payload["initial_tcp_base_m"],
                "target_tcp_base_m": payload["target_tcp_base_m"],
                "final_tcp_base_m": payload["final_tcp_base_m"],
                "observed_axis_translation_m": payload[
                    "observed_axis_translation_m"
                ],
                "observed_translation_norm_m": payload[
                    "observed_translation_norm_m"
                ],
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
            "operation_elapsed_s",
            "cleanup_elapsed_s",
            "wall_clock_elapsed_s",
        ):
            if name not in payload:
                continue
            value = payload[name]
            if type(value) in (int, float) and isfinite(value):
                metrics[name] = float(value)

        success = bool(
            payload["status"] == "PASS"
            and payload["command_published"]
            and payload["provider_completed"]
            and payload["settled"]
            and not payload["timed_out"]
            and payload["final_fpc_state"] == "inactive"
            and payload["servo_paused"] is True
            and payload["observed_axis_translation_m"] is not None
            and (
                not extended_runtime
                or runtime_result.cleanup_completed is True
            )
        )
        if success:
            return self._result(
                True,
                observations=observations,
                metrics=metrics,
                runtime_identity=runtime_identity,
                runtime_contract=runtime_contract,
                runtime_result=runtime_result,
            )

        return self._result(
            False,
            failure_code=str(payload["status"]),
            observations=observations,
            metrics=metrics,
            runtime_identity=runtime_identity,
            runtime_contract=runtime_contract,
            runtime_result=runtime_result,
        )