from __future__ import annotations
from .goal import Goal
from .state import WorldState

def goal_satisfied(goal: Goal, state: WorldState) -> bool:
    if goal.predicate == "ON_TOP_OF":
        return state.get(f"on_top_of:{goal.subject}:{goal.reference}") is True
    if goal.predicate == "AT":
        return state.get(f"at:{goal.subject}:{goal.reference}") is True
    if goal.predicate == "INSERTED":
        return state.get(f"inserted:{goal.subject}:{goal.reference}") is True
    return state.get(f"goal:{goal.predicate}") is True
