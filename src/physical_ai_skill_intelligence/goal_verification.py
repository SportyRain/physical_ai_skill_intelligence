from __future__ import annotations
from .goal import Goal
from .state import WorldState


def goal_satisfied(goal: Goal, state: WorldState) -> bool:
    # No evaluator currently interprets parameters. Never erase their identity.
    if goal.parameters:
        return False
    if goal.predicate in {"ON_TOP_OF", "AT", "INSERTED"}:
        # The legacy relation fact format uses ':' as a delimiter.
        if any(not isinstance(value, str) or not value or ":" in value
               for value in (goal.subject, goal.reference)):
            return False
        return state.get(f"{goal.predicate.lower()}:{goal.subject}:{goal.reference}") is True
    # Explicit global evaluator: subject/reference variants are unsupported.
    if goal.predicate == "CANONICAL_READY" and goal.subject is None and goal.reference is None:
        return state.get("goal:CANONICAL_READY") is True
    return False
