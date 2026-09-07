from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable
from .provenance import Provenance

@dataclass(frozen=True)
class ExperienceRecord:
    goal_predicate: str
    state_context: dict[str, Any]
    skill_name: str
    success: bool
    cost: float = 0.0
    failure_code: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    provenance: Provenance | None = None

    def validate(self) -> None:
        if not self.goal_predicate:
            raise ValueError("goal_predicate is required")
        if not self.skill_name:
            raise ValueError("skill_name is required")
        if self.cost < 0:
            raise ValueError("cost must be >= 0")
        if self.provenance is not None:
            self.provenance.validate()

class ExperienceStore:
    def __init__(self, records: Iterable[ExperienceRecord] = ()):
        self._records: list[ExperienceRecord] = []
        for record in records:
            self.add(record)

    def add(self, record: ExperienceRecord) -> None:
        record.validate()
        self._records.append(record)

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
        for record in self._records:
            if record.goal_predicate != goal_predicate:
                continue
            if record.state_context != state_context:
                continue
            if skill_name is not None and record.skill_name != skill_name:
                continue
            out.append(record)
        return tuple(out)
