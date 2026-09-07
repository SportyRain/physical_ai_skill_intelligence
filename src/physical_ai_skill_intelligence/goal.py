from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping
from ._integrity import snapshot_mapping, identity_key

@dataclass(frozen=True)
class Goal:
    predicate: str
    subject: str | None = None
    reference: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameters", snapshot_mapping(self.parameters))

    def key(self) -> tuple:
        return (
            self.predicate,
            self.subject,
            self.reference,
            identity_key(self.parameters),
        )
