from __future__ import annotations
from dataclasses import dataclass
from .experience import ExperienceStore

@dataclass(frozen=True)
class OutcomeEstimate:
    success_probability: float
    evidence_count: int
    mean_cost: float
    uncertainty: float
    method: str = "empirical_beta_baseline"

class EmpiricalOutcomeEstimator:
    """Simple inspectable baseline. Not a novel learning algorithm."""

    def __init__(self, store: ExperienceStore, *, alpha: float = 1.0, beta: float = 1.0):
        if alpha <= 0 or beta <= 0:
            raise ValueError("alpha and beta must be > 0")
        self.store = store
        self.alpha = alpha
        self.beta = beta

    def estimate(
        self,
        *,
        goal_predicate: str,
        state_context: dict,
        skill_name: str,
    ) -> OutcomeEstimate:
        records = self.store.exact_context(
            goal_predicate=goal_predicate,
            state_context=state_context,
            skill_name=skill_name,
        )
        n = len(records)
        successes = sum(1 for r in records if r.success)
        p = (successes + self.alpha) / (n + self.alpha + self.beta)
        mean_cost = sum(r.cost for r in records) / n if n else 0.0
        # Conservative, inspectable proxy; decreases as evidence grows.
        uncertainty = 1.0 / (n + 1.0)
        return OutcomeEstimate(
            success_probability=p,
            evidence_count=n,
            mean_cost=mean_cost,
            uncertainty=uncertainty,
        )
