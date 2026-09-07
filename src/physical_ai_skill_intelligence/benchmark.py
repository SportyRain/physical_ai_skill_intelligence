from __future__ import annotations
from dataclasses import dataclass

from .decision import Decision, DecisionEngine
from .experience import ExperienceRecord, ExperienceStore
from .goal import Goal
from .outcome import EmpiricalOutcomeEstimator
from .skill import SkillSpec
from .state import WorldState


@dataclass(frozen=True)
class DecisionBenchmarkResult:
    without_relevant_experience: Decision
    with_relevant_real_experience: Decision
    selection_changed: bool
    estimate_changed: bool
    evidence_count: int


def run_push_decision_benchmark(
    records: tuple[ExperienceRecord, ...],
) -> DecisionBenchmarkResult:
    if len(records) < 2:
        raise ValueError("benchmark requires multiple real Push experiences")
    context = records[0].state_context
    if any(record.state_context != context for record in records):
        raise ValueError("benchmark records must have exactly identical context")

    skill_names = (
        "goal_directed_continuous_push/nominal_baseline",
        "goal_directed_continuous_push/experience_adapted",
    )
    if {record.skill_name for record in records} != set(skill_names):
        raise ValueError("benchmark requires both nominal and adapted candidate strategies")

    goal = Goal(
        "RELATIVE_DISPLACEMENT",
        subject="puck",
        reference="relative_goal",
        parameters={
            "direction": context["direction"],
            "relative_goal_displacement_m": context["relative_goal_displacement_m"],
        },
    )
    state = WorldState(context)
    skills = [
        SkillSpec(skill_names[0], ("RELATIVE_DISPLACEMENT",), provider="ur3_visual_servoing"),
        SkillSpec(skill_names[1], ("RELATIVE_DISPLACEMENT",), provider="ur3_visual_servoing"),
    ]
    context_keys = tuple(context.keys())

    def decide(store: ExperienceStore) -> Decision:
        return DecisionEngine(
            EmpiricalOutcomeEstimator(store),
            context_keys=context_keys,
            ranking_mode="lexicographic_success_then_cost",
        ).rank(goal=goal, state=state, skills=skills)

    without = decide(ExperienceStore())
    with_real = decide(ExperienceStore(records))
    estimate_changed = any(
        before.expected_success != after.expected_success
        or before.evidence_count != after.evidence_count
        or before.mean_cost != after.mean_cost
        for before, after in zip(without.candidates, with_real.candidates)
    )
    return DecisionBenchmarkResult(
        without_relevant_experience=without,
        with_relevant_real_experience=with_real,
        selection_changed=without.selected_skill != with_real.selected_skill,
        estimate_changed=estimate_changed,
        evidence_count=sum(candidate.evidence_count for candidate in with_real.candidates),
    )
