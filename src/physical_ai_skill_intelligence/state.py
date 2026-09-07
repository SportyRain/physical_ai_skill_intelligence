from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class WorldState:
    facts: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = UNKNOWN) -> Any:
        return self.facts.get(key, default)

    def satisfies(self, requirements: dict[str, Any]) -> bool:
        for key, required in requirements.items():
            actual = self.get(key)
            if actual == UNKNOWN:
                return False
            if actual != required:
                return False
        return True

    def context(self, keys: tuple[str, ...]) -> dict[str, Any]:
        return {key: self.get(key) for key in keys}
