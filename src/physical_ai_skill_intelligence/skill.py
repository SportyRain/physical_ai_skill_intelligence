from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from ._integrity import snapshot_mapping, finite_number

@dataclass(frozen=True)
class SkillSpec:
    name: str
    goal_predicates: tuple[str, ...] = ()
    preconditions: Mapping[str, object] = field(default_factory=dict)
    provider: str = "UNKNOWN"
    nominal_cost: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "preconditions", snapshot_mapping(self.preconditions))
        object.__setattr__(self, "goal_predicates", tuple(self.goal_predicates))
        finite_number(self.nominal_cost, "nominal_cost")

    def supports_goal(self, predicate: str) -> bool:
        return predicate in self.goal_predicates
