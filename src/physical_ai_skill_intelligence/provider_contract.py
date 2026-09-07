from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any
from .goal import Goal
from .state import WorldState

@dataclass(frozen=True)
class ProviderResult:
    action_success: bool
    observations: dict[str, Any]
    failure_code: str | None = None
    metrics: dict[str, float] | None = None

class SkillProvider(Protocol):
    def execute(self, skill_name: str, goal: Goal, state: WorldState) -> ProviderResult:
        ...

# This file defines only the boundary.
# Robot motion/perception implementations must remain in external providers.
