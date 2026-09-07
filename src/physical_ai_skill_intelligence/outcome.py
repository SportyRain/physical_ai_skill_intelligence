from __future__ import annotations
from dataclasses import dataclass
from .experience import ExperienceStore
from ._integrity import finite_number
from .cost import observed_cost
from .provenance import Provenance


@dataclass(frozen=True)
class OutcomeEstimate:
    success_probability: float
    evidence_count: int
    mean_cost: float
    uncertainty: float
    method: str = "empirical_beta_baseline"
    successes: int = 0
    failures: int = 0
    evidence_ids: tuple[str, ...] = ()
    provenance_trace: tuple[Provenance, ...] = ()
    cost_evidence_count: int = 0
    cost_unit: str = "UNKNOWN"


class EmpiricalOutcomeEstimator:
    """Simple inspectable baseline. Not a novel learning algorithm."""

    def __init__(self, store: ExperienceStore, *, alpha: float = 1.0, beta: float = 1.0):
        finite_number(alpha, "alpha", positive=True)
        finite_number(beta, "beta", positive=True)
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
        failures = n - successes
        scale = max(n, self.alpha, self.beta)
        p = (successes / scale + self.alpha / scale) / (n / scale + self.alpha / scale + self.beta / scale)
        mean_cost, cost_count, cost_unit = observed_cost(records)
        uncertainty = 1.0 / (n + 1.0)
        evidence_ids = tuple(
            r.experience_id if r.identity_key() is not None else f"LEGACY:{i}"
            for i, r in enumerate(records)
        )
        trace = tuple(r.provenance for r in records if r.provenance is not None)
        return OutcomeEstimate(
            success_probability=p,
            evidence_count=n,
            mean_cost=mean_cost,
            cost_evidence_count=cost_count,
            cost_unit=cost_unit,
            uncertainty=uncertainty,
            method="explicit_beta_prior_no_evidence" if n == 0 else "empirical_beta_baseline",
            successes=successes,
            failures=failures,
            evidence_ids=evidence_ids,
            provenance_trace=trace,
        )
