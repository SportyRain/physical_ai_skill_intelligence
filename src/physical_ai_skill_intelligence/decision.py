from __future__ import annotations
from dataclasses import dataclass
from ._integrity import finite_number
from .goal import Goal
from .state import WorldState
from .skill import SkillSpec
from .outcome import EmpiricalOutcomeEstimator
from .provenance import Provenance


@dataclass(frozen=True)
class CandidateDecision:
    skill_name: str
    expected_success: float
    evidence_count: int
    mean_cost: float
    uncertainty: float
    evidence_ids: tuple[str, ...]
    estimator_method: str
    provenance_trace: tuple[Provenance, ...]
    score: float
    cost_evidence_count: int = 0
    cost_unit: str = "UNKNOWN"


@dataclass(frozen=True)
class Decision:
    selected_skill: str
    score: float
    expected_success: float
    evidence_count: int
    reason: str
    ranking: tuple[tuple[str, float], ...]
    candidates: tuple[CandidateDecision, ...] = ()
    ranking_mode: str = "weighted"


class DecisionEngine:
    def __init__(
        self,
        estimator: EmpiricalOutcomeEstimator,
        *,
        context_keys: tuple[str, ...],
        cost_weight: float = 0.02,
        uncertainty_weight: float = 0.00,
        ranking_mode: str = "weighted",
    ):
        if ranking_mode not in {"weighted", "lexicographic_success_then_cost"}:
            raise ValueError("unsupported ranking_mode")
        finite_number(cost_weight, "cost_weight")
        finite_number(uncertainty_weight, "uncertainty_weight")
        self.estimator = estimator
        self.context_keys = context_keys
        self.cost_weight = cost_weight
        self.uncertainty_weight = uncertainty_weight
        self.ranking_mode = ranking_mode

    def rank(
        self,
        *,
        goal: Goal,
        state: WorldState,
        skills: list[SkillSpec],
    ) -> Decision:
        context = state.context(self.context_keys)
        candidates = [
            s for s in skills
            if s.supports_goal(goal.predicate) and state.satisfies(s.preconditions)
        ]
        if not candidates:
            raise RuntimeError("NO_APPLICABLE_SKILL")

        rows = []
        for order, skill in enumerate(candidates):
            est = self.estimator.estimate(
                goal_predicate=goal.predicate,
                state_context=context,
                skill_name=skill.name,
            )
            score = (
                est.success_probability
                - self.cost_weight * (est.mean_cost + skill.nominal_cost)
                - self.uncertainty_weight * est.uncertainty
            )
            rows.append((order, skill, est, score))

        if len({row[2].cost_unit for row in rows if row[2].cost_evidence_count}) > 1:
            raise ValueError("INCOMPATIBLE_COST_UNITS")

        if self.ranking_mode == "lexicographic_success_then_cost":
            # Preserve input order only as the final deterministic tie-break.
            rows.sort(
                key=lambda row: (
                    -row[2].success_probability,
                    row[2].mean_cost + row[1].nominal_cost,
                    row[2].uncertainty,
                    row[0],
                )
            )
        else:
            rows.sort(key=lambda row: (-row[3], row[1].name))

        _, best_skill, best_est, best_score = rows[0]
        ranking = tuple((row[1].name, row[3]) for row in rows)
        details = tuple(
            CandidateDecision(
                skill_name=row[1].name,
                expected_success=row[2].success_probability,
                evidence_count=row[2].evidence_count,
                mean_cost=row[2].mean_cost,
                cost_evidence_count=row[2].cost_evidence_count,
                cost_unit=row[2].cost_unit,
                uncertainty=row[2].uncertainty,
                evidence_ids=row[2].evidence_ids,
                estimator_method=row[2].method,
                provenance_trace=row[2].provenance_trace,
                score=row[3],
            )
            for row in rows
        )
        reason = (
            f"goal={goal.predicate}; context={context}; "
            f"ranking_mode={self.ranking_mode}; skill={best_skill.name}; "
            f"evidence_count={best_est.evidence_count}; "
            f"p_success={best_est.success_probability:.6f}; "
            f"mean_cost={best_est.mean_cost:.6f}; uncertainty={best_est.uncertainty:.6f}; "
            f"cost_evidence_count={best_est.cost_evidence_count}; "
            f"cost_unit={best_est.cost_unit}; "
            f"evidence_ids={best_est.evidence_ids}; score={best_score:.6f}"
        )
        return Decision(
            selected_skill=best_skill.name,
            score=best_score,
            expected_success=best_est.success_probability,
            evidence_count=best_est.evidence_count,
            reason=reason,
            ranking=ranking,
            candidates=details,
            ranking_mode=self.ranking_mode,
        )
