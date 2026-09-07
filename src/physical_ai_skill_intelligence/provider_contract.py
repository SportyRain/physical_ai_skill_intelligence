from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, Any
from ._integrity import snapshot_mapping, snapshot
from .goal import Goal
from .state import WorldState

@dataclass(frozen=True)
class ProviderResult:
    action_success: bool
    observations: Mapping[str, Any]
    failure_code: str | None = None
    metrics: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", snapshot_mapping(self.observations))
        object.__setattr__(self, "metrics", snapshot(self.metrics))
        if type(self.action_success) is not bool:
            raise ValueError("action_success must be bool")
        if self.action_success and self.failure_code is not None:
            raise ValueError("successful provider result cannot carry failure_code")
        if not self.action_success and not self.failure_code:
            raise ValueError("failed provider result requires failure_code")

class SkillProvider(Protocol):
    def execute(self, skill_name: str, goal: Goal, state: WorldState) -> ProviderResult:
        ...

# This file defines only the boundary.
# Robot motion/perception implementations must remain in external providers.
