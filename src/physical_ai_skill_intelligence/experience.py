from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Iterable
from .provenance import Provenance
from ._integrity import snapshot_mapping, snapshot, finite_number
from .cost import validate_cost_semantics
from .state import UNKNOWN

NOT_VERIFIED = "NOT_VERIFIED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ExperienceRecord:
    # Compatibility fields used by the clean-room v0.1.0 estimator.
    goal_predicate: str
    state_context: Mapping[str, Any]
    skill_name: str
    success: bool
    cost: float = 0.0
    failure_code: str | None = None
    metrics: Mapping[str, Any] = field(default_factory=dict)
    provenance: Provenance | None = None

    # Semantically explicit physical-experience identity.
    experience_id: str = UNKNOWN
    experiment_id: str = UNKNOWN
    trial_id: str = UNKNOWN
    attempt_id: str = UNKNOWN

    # Meaning-preserving normalized fields.
    goal_semantics: Mapping[str, Any] = field(default_factory=dict)
    state_before: Mapping[str, Any] = field(default_factory=dict)
    state_after: Mapping[str, Any] = field(default_factory=dict)
    object_identity: Any = UNKNOWN
    target_identity: Any = UNKNOWN
    scene_context: Mapping[str, Any] = field(default_factory=dict)
    strategy_name: str = UNKNOWN
    planned_action: Mapping[str, Any] = field(default_factory=dict)
    accepted_action: Mapping[str, Any] = field(default_factory=dict)
    executed_action: Mapping[str, Any] = field(default_factory=dict)
    physical_outcome: Mapping[str, Any] = field(default_factory=dict)
    task_success: bool | str = UNKNOWN
    action_success: bool | str = UNKNOWN
    failure_attribution: Any = UNKNOWN
    recovery_action: Any = UNKNOWN
    timestamp: Any = UNKNOWN
    source_schema_version: str = UNKNOWN
    identity_required: bool = False

    cost_semantics: str = UNKNOWN
    cost_unit: str = UNKNOWN

    def __post_init__(self) -> None:
        for name in (
            "state_context", "metrics", "scene_context", "goal_semantics",
            "state_before", "state_after", "planned_action", "accepted_action",
            "executed_action", "physical_outcome",
        ):
            object.__setattr__(self, name, snapshot_mapping(getattr(self, name)))
        for name in ("object_identity", "target_identity", "failure_attribution",
                     "recovery_action", "timestamp"):
            object.__setattr__(self, name, snapshot(getattr(self, name)))
        finite_number(self.cost, "cost")
        validate_cost_semantics(self.cost_semantics, self.cost_unit)

    def validate(self) -> None:
        if not self.goal_predicate:
            raise ValueError("goal_predicate is required")
        if not self.skill_name:
            raise ValueError("skill_name is required")
        if not isinstance(self.success, bool):
            raise ValueError("success must be bool")
        finite_number(self.cost, "cost")
        validate_cost_semantics(self.cost_semantics, self.cost_unit)
        if isinstance(self.task_success, bool) and self.task_success != self.success:
            raise ValueError("success compatibility field must equal verified task_success")
        if self.provenance is not None:
            self.provenance.validate()
        if self.identity_required:
            required = {
                "experience_id": self.experience_id,
                "experiment_id": self.experiment_id,
                "trial_id": self.trial_id,
                "source_schema_version": self.source_schema_version,
            }
            missing = [
                name
                for name, value in required.items()
                if value in (None, "", UNKNOWN, NOT_VERIFIED, UNRESOLVED)
            ]
            if missing:
                raise ValueError(f"missing required experience identity: {', '.join(missing)}")
            if self.provenance is None:
                raise ValueError("imported experience requires provenance")

    def identity_key(self) -> str | None:
        if self.experience_id in (None, "", UNKNOWN, NOT_VERIFIED, UNRESOLVED):
            return None
        return self.experience_id


class ExperienceStore:
    def __init__(self, records: Iterable[ExperienceRecord] = ()):
        self._records: list[ExperienceRecord] = []
        self._by_identity: dict[str, ExperienceRecord] = {}
        for record in records:
            self.add(record)

    def add(self, record: ExperienceRecord) -> bool:
        record.validate()
        key = record.identity_key()
        if key is not None:
            existing = self._by_identity.get(key)
            if existing is not None:
                if existing != record:
                    raise ValueError(f"conflicting duplicate experience_id: {key}")
                return False
            self._by_identity[key] = record
        self._records.append(record)
        return True

    def add_many(self, records: Iterable[ExperienceRecord]) -> int:
        return sum(1 for record in records if self.add(record))

    def all(self) -> tuple[ExperienceRecord, ...]:
        return tuple(self._records)

    def exact_context(
        self,
        *,
        goal_predicate: str,
        state_context: dict[str, Any],
        skill_name: str | None = None,
    ) -> tuple[ExperienceRecord, ...]:
        out = []
        state_context = snapshot_mapping(state_context)
        for record in self._records:
            if record.goal_predicate != goal_predicate:
                continue
            # Deliberately exact: UNKNOWN is a literal value, never a wildcard.
            if record.state_context != state_context:
                continue
            if skill_name is not None and record.skill_name != skill_name:
                continue
            out.append(record)
        return tuple(out)
