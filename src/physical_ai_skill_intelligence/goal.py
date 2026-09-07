from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping

@dataclass(frozen=True)
class Goal:
    predicate: str
    subject: str | None = None
    reference: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def key(self) -> tuple:
        return (
            self.predicate,
            self.subject,
            self.reference,
            tuple(sorted(self.parameters.items())),
        )
