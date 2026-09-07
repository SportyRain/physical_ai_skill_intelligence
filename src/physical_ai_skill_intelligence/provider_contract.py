from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, Any
from ._integrity import snapshot_mapping, snapshot, finite_number
from .cost import OBSERVED_COST, validate_cost_semantics
from .goal import Goal
from .state import WorldState
from .provenance import Provenance


@dataclass(frozen=True)
class ProviderCost:
    """Explicit provider measurement or configuration, never inferred from metrics.

    An observed value requires a metric unit and a provider evidence reference.
    This declares cost evidence, not a verified physical outcome. UNKNOWN has no
    numeric value; only observed costs may use the experience conversion gate.
    """
    value: float | None = None
    semantics: str = "UNKNOWN"
    unit: str = "UNKNOWN"
    evidence_reference: str = "UNKNOWN"

    def __post_init__(self):
        validate_cost_semantics(self.semantics, self.unit)
        if self.semantics == "UNKNOWN":
            if self.value is not None or self.unit != "UNKNOWN":
                raise ValueError("unknown cost must have no value or unit")
        else:
            finite_number(self.value, "provider cost")
            if self.unit.strip() in {"UNKNOWN", "NOT_VERIFIED", "UNRESOLVED"}:
                raise ValueError("known cost requires an explicit metric unit")
        if self.semantics == OBSERVED_COST:
            if (not isinstance(self.evidence_reference, str)
                    or self.evidence_reference.strip() in {
                        "", "UNKNOWN", "NOT_VERIFIED", "UNRESOLVED"}):
                raise ValueError("observed cost requires provider evidence")

    def observed_experience_fields(self) -> dict:
        """Refuse to persist missing measurements or limits as observed cost."""
        if self.semantics != OBSERVED_COST:
            raise ValueError("provider cost is not observed")
        return {"cost": self.value, "cost_semantics": self.semantics,
                "cost_unit": self.unit}


@dataclass(frozen=True)
class ProviderRuntimeContract:
    """Declarations only; no timer, cancellation or runtime execution machinery.

    M8 must supply provider API identities and evidence for the timeout scope,
    cancellation acknowledgement AND completed stop, and an end-to-end monotonic
    bound including observation and cleanup. A configured duration, wait expiry,
    cancel request, or thread join alone verifies none of these guarantees.
    """
    configured_wall_clock_limit_s: float | None = None
    configured_timeout_s: float | None = None
    timeout_api: str = "UNKNOWN"
    timeout_scope: str = "UNKNOWN"
    cancel_api: str = "UNKNOWN"
    cancel_completion_semantics: str = "UNKNOWN"
    wall_clock_bound: str = field(default="NOT_VERIFIED", init=False)
    provider_timeout: str = field(default="NOT_VERIFIED", init=False)
    provider_cancel: str = field(default="NOT_VERIFIED", init=False)

    def __post_init__(self):
        for name in ("configured_wall_clock_limit_s", "configured_timeout_s"):
            if getattr(self, name) is not None:
                finite_number(getattr(self, name), name, positive=True)
        for name in ("timeout_api", "timeout_scope", "cancel_api", "cancel_completion_semantics"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be explicit or UNKNOWN")


@dataclass(frozen=True)
class ProviderResult:
    """Provider declarations, not adapter-invented failure-code policy.

    Known retryability needs an operation-scoped provider evidence reference;
    merely accepting that reference does not verify the real provider semantics.
    The M7 geometry adapter supplies neither retryability nor physical cost.
    """
    action_success: bool
    observations: Mapping[str, Any]
    failure_code: str | None = None
    metrics: Mapping[str, float] | None = None
    provenance: Provenance | None = None
    failure_retryability: str = "unknown"
    failure_semantics_reference: str = "UNKNOWN"
    cost: ProviderCost = field(default_factory=ProviderCost)
    runtime_contract: ProviderRuntimeContract = field(default_factory=ProviderRuntimeContract)

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", snapshot_mapping(self.observations))
        object.__setattr__(self, "metrics", snapshot(self.metrics))
        if type(self.action_success) is not bool:
            raise ValueError("action_success must be bool")
        if self.action_success and self.failure_code is not None:
            raise ValueError("successful provider result cannot carry failure_code")
        if not self.action_success and not self.failure_code:
            raise ValueError("failed provider result requires failure_code")
        if self.failure_retryability not in {"retryable", "terminal", "unknown"}:
            raise ValueError("unsupported failure retryability")
        if self.action_success and self.failure_retryability != "unknown":
            raise ValueError("successful result cannot carry failure retryability")
        if self.failure_retryability != "unknown":
            if (not isinstance(self.failure_semantics_reference, str)
                    or self.failure_semantics_reference.strip() in {
                        "", "UNKNOWN", "NOT_VERIFIED", "UNRESOLVED"}):
                raise ValueError("known retryability requires provider semantic evidence")
        if not isinstance(self.cost, ProviderCost):
            raise ValueError("explicit ProviderCost required")
        if not isinstance(self.runtime_contract, ProviderRuntimeContract):
            raise ValueError("explicit ProviderRuntimeContract required")
        if self.provenance is not None:
            self.provenance.validate()

class SkillProvider(Protocol):
    def execute(self, skill_name: str, goal: Goal, state: WorldState) -> ProviderResult:
        ...

# This file defines only the boundary.
# Robot motion/perception implementations must remain in external providers.
