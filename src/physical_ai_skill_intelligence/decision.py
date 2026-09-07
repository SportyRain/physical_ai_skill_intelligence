from __future__ import annotations
from dataclasses import dataclass
from .goal import Goal
from .state import WorldState
from .skill import SkillSpec
from .outcome import EmpiricalOutcomeEstimator

@dataclass(frozen=True)
class Decision:
    selected_skill: str
    score: float
    expected_success: float
    evidence_count: int
    reason: str
    ranking: tuple[tuple[str, float], ...]

class DecisionEngine:
    def __init__(
        self,
        estimator: EmpiricalOutcomeEstimator,
        *,
        context_keys: tuple[str, ...],
        cost_weight: float = 0.02,
        uncertainty_weight: float = 0.00,
    ):
        self.estimator = estimator
        self.context_keys = context_keys
        self.cost_weight = cost_weight
        self.uncertainty_weight = uncertainty_weight

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
        for skill in candidates:
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
            rows.append((skill, est, score))

        rows.sort(key=lambda row: (-row[2], row[0].name))
        best_skill, best_est, best_score = rows[0]
        ranking = tuple((row[0].name, row[2]) for row in rows)
        reason = (
            f"goal={goal.predicate}; context={context}; "
            f"skill={best_skill.name}; evidence_count={best_est.evidence_count}; "
            f"p_success={best_est.success_probability:.6f}; "
            f"mean_cost={best_est.mean_cost:.6f}; score={best_score:.6f}"
        )
        return Decision(
            selected_skill=best_skill.name,
            score=best_score,
            expected_success=best_est.success_probability,
            evidence_count=best_est.evidence_count,
            reason=reason,
            ranking=ranking,
        )
