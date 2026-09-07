from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class SkillSpec:
    name: str
    goal_predicates: tuple[str, ...] = ()
    preconditions: dict[str, object] = field(default_factory=dict)
    provider: str = "UNKNOWN"
    nominal_cost: float = 0.0

    def supports_goal(self, predicate: str) -> bool:
        return not self.goal_predicates or predicate in self.goal_predicates
