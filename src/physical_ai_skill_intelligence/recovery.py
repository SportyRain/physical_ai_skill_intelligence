from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Iterable

from ._integrity import snapshot_mapping, snapshot, finite_number
from .cost import validate_cost_semantics, observed_cost
from .goal import Goal
from .provenance import Provenance
from .state import UNKNOWN, WorldState


@dataclass(frozen=True)
class FailureState:
    """Observed failure presented to the recovery decision layer."""

    code: str
    attribution: Any = UNKNOWN
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", snapshot_mapping(self.details))
        object.__setattr__(self, "attribution", snapshot(self.attribution))
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("failure code is required")


@dataclass(frozen=True)
class RecoverySpec:
    """High-level recovery option supplied by an existing skill provider."""

    name: str
    failure_codes: tuple[str, ...]
    preconditions: Mapping[str, Any] = field(default_factory=dict)
    provider: str = "UNKNOWN"
    nominal_cost: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "preconditions", snapshot_mapping(self.preconditions))
        object.__setattr__(self, "failure_codes", tuple(self.failure_codes))
        self.validate()

    def validate(self) -> None:
        if not self.name:
            raise ValueError("recovery name is required")
        if not self.failure_codes:
            raise ValueError("recovery failure_codes must be explicit")
        finite_number(self.nominal_cost, "nominal_cost")

    def supports_failure(self, failure_code: str) -> bool:
        # Deliberately exact: neither UNKNOWN nor a missing list is a wildcard.
        return failure_code in self.failure_codes


@dataclass(frozen=True)
class RecoveryExperienceRecord:
    """One explicitly recovery-labelled outcome observation."""

    goal_predicate: str
    state_context: Mapping[str, Any]
    failure_code: str
    failure_attribution: Any
    recovery_action: str
    recovery_success: bool
    cost: float = 0.0
    experience_id: str = UNKNOWN
    provenance: Provenance | None = None
    metrics: Mapping[str, Any] = field(default_factory=dict)

    cost_semantics: str = UNKNOWN
    cost_unit: str = UNKNOWN

    def __post_init__(self) -> None:
        for name in ("state_context", "metrics"):
            object.__setattr__(self, name, snapshot_mapping(getattr(self, name)))
        object.__setattr__(self, "failure_attribution", snapshot(self.failure_attribution))
        finite_number(self.cost, "cost")
        validate_cost_semantics(self.cost_semantics, self.cost_unit)

    def validate(self) -> None:
        if not self.goal_predicate:
            raise ValueError("goal_predicate is required")
        if not self.failure_code:
            raise ValueError("failure_code is required")
        if not self.recovery_action:
            raise ValueError("recovery_action is required")
        if not isinstance(self.recovery_success, bool):
            raise ValueError("recovery_success must be bool")
        finite_number(self.cost, "cost")
        validate_cost_semantics(self.cost_semantics, self.cost_unit)
        if self.provenance is not None:
            self.provenance.validate()


class RecoveryExperienceStore:
    def __init__(self, records: Iterable[RecoveryExperienceRecord] = ()):
        self._records: list[RecoveryExperienceRecord] = []
        self._by_identity: dict[str, RecoveryExperienceRecord] = {}
        for record in records:
            self.add(record)

    def add(self, record: RecoveryExperienceRecord) -> bool:
        record.validate()
        key = None if record.experience_id == UNKNOWN else record.experience_id
        if key is not None:
            existing = self._by_identity.get(key)
            if existing is not None:
                if existing != record:
                    raise ValueError(f"conflicting duplicate recovery experience_id: {key}")
                return False
            self._by_identity[key] = record
        self._records.append(record)
        return True

    def exact_context(
        self,
        *,
        goal_predicate: str,
        state_context: dict[str, Any],
        failure: FailureState,
        recovery_action: str | None = None,
    ) -> tuple[RecoveryExperienceRecord, ...]:
        failure.validate()
        rows = []
        state_context = snapshot_mapping(state_context)
        for record in self._records:
            if record.goal_predicate != goal_predicate:
                continue
            if record.state_context != state_context:
                continue
            if record.failure_code != failure.code:
                continue
            if record.failure_attribution != failure.attribution:
                continue
            if recovery_action is not None and record.recovery_action != recovery_action:
                continue
            rows.append(record)
        return tuple(rows)


@dataclass(frozen=True)
class RecoveryOutcomeEstimate:
    success_probability: float
    evidence_count: int
    mean_cost: float
    uncertainty: float
    method: str
    successes: int
    failures: int
    evidence_ids: tuple[str, ...]
    provenance_trace: tuple[Provenance, ...]
    cost_evidence_count: int = 0
    cost_unit: str = UNKNOWN


class EmpiricalRecoveryOutcomeEstimator:
    """Inspectable Beta-prior baseline for recovery outcomes."""

    def __init__(
        self,
        store: RecoveryExperienceStore,
        *,
        alpha: float = 1.0,
        beta: float = 1.0,
    ):
        finite_number(alpha, "alpha", positive=True)
        finite_number(beta, "beta", positive=True)
        self.store = store
        self.alpha = alpha
        self.beta = beta

    def estimate(
        self,
        *,
        goal_predicate: str,
        state_context: dict[str, Any],
        failure: FailureState,
        recovery_action: str,
    ) -> RecoveryOutcomeEstimate:
        rows = self.store.exact_context(
            goal_predicate=goal_predicate,
            state_context=state_context,
            failure=failure,
            recovery_action=recovery_action,
        )
        n = len(rows)
        successes = sum(1 for row in rows if row.recovery_success)
        failures = n - successes
        scale = max(n, self.alpha, self.beta)
        probability = (successes / scale + self.alpha / scale) / (n / scale + self.alpha / scale + self.beta / scale)
        mean_cost, cost_count, cost_unit = observed_cost(rows)
        evidence_ids = tuple(
            row.experience_id if row.experience_id != UNKNOWN else f"LEGACY:{i}"
            for i, row in enumerate(rows)
        )
        trace = tuple(row.provenance for row in rows if row.provenance is not None)
        return RecoveryOutcomeEstimate(
            success_probability=probability,
            evidence_count=n,
            mean_cost=mean_cost,
            cost_evidence_count=cost_count,
            cost_unit=cost_unit,
            uncertainty=1.0 / (n + 1.0),
            method=(
                "explicit_beta_prior_no_recovery_evidence"
                if n == 0
                else "empirical_recovery_beta_baseline"
            ),
            successes=successes,
            failures=failures,
            evidence_ids=evidence_ids,
            provenance_trace=trace,
        )


@dataclass(frozen=True)
class RecoveryCandidateDecision:
    recovery_action: str
    expected_success: float
    evidence_count: int
    mean_cost: float
    uncertainty: float
    evidence_ids: tuple[str, ...]
    estimator_method: str
    provenance_trace: tuple[Provenance, ...]
    cost_evidence_count: int = 0
    cost_unit: str = UNKNOWN


@dataclass(frozen=True)
class RecoveryDecision:
    selected_recovery: str
    failure_code: str
    reason: str
    candidates: tuple[RecoveryCandidateDecision, ...]


class RecoveryDecisionEngine:
    """Rank existing high-level recovery options for one observed failure."""

    def __init__(
        self,
        estimator: EmpiricalRecoveryOutcomeEstimator,
        *,
        context_keys: tuple[str, ...],
    ):
        self.estimator = estimator
        self.context_keys = context_keys

    def rank(
        self,
        *,
        goal: Goal,
        state: WorldState,
        failure: FailureState,
        recoveries: list[RecoverySpec],
    ) -> RecoveryDecision:
        failure.validate()
        context = state.context(self.context_keys)
        applicable = []
        for order, recovery in enumerate(recoveries):
            recovery.validate()
            if not recovery.supports_failure(failure.code):
                continue
            if not state.satisfies(recovery.preconditions):
                continue
            estimate = self.estimator.estimate(
                goal_predicate=goal.predicate,
                state_context=context,
                failure=failure,
                recovery_action=recovery.name,
            )
            applicable.append((order, recovery, estimate))

        if not applicable:
            raise RuntimeError("NO_APPLICABLE_RECOVERY")

        if len({row[2].cost_unit for row in applicable if row[2].cost_evidence_count}) > 1:
            raise ValueError("INCOMPATIBLE_COST_UNITS")

        applicable.sort(
            key=lambda row: (
                -row[2].success_probability,
                row[2].mean_cost + row[1].nominal_cost,
                row[2].uncertainty,
                row[0],
            )
        )
        _, selected, selected_estimate = applicable[0]
        candidates = tuple(
            RecoveryCandidateDecision(
                recovery_action=recovery.name,
                expected_success=estimate.success_probability,
                evidence_count=estimate.evidence_count,
                mean_cost=estimate.mean_cost,
                cost_evidence_count=estimate.cost_evidence_count,
                cost_unit=estimate.cost_unit,
                uncertainty=estimate.uncertainty,
                evidence_ids=estimate.evidence_ids,
                estimator_method=estimate.method,
                provenance_trace=estimate.provenance_trace,
            )
            for _, recovery, estimate in applicable
        )
        reason = (
            f"goal={goal.predicate}; failure={failure.code}; "
            f"failure_attribution={failure.attribution}; context={context}; "
            f"selected={selected.name}; evidence_count={selected_estimate.evidence_count}; "
            f"p_recovery_success={selected_estimate.success_probability:.6f}; "
            f"mean_cost={selected_estimate.mean_cost:.6f}; "
            f"uncertainty={selected_estimate.uncertainty:.6f}; "
            f"cost_evidence_count={selected_estimate.cost_evidence_count}; "
            f"cost_unit={selected_estimate.cost_unit}; "
            f"evidence_ids={selected_estimate.evidence_ids}"
        )
        return RecoveryDecision(
            selected_recovery=selected.name,
            failure_code=failure.code,
            reason=reason,
            candidates=candidates,
        )
