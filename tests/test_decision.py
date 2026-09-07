from physical_ai_skill_intelligence import (
    Goal, WorldState, SkillSpec,
    ExperienceRecord, ExperienceStore,
    EmpiricalOutcomeEstimator, DecisionEngine
)

def build_engine(records):
    return DecisionEngine(
        EmpiricalOutcomeEstimator(ExperienceStore(records)),
        context_keys=("vision_quality", "previous_grasp"),
    )

def skills():
    return [
        SkillSpec("direct_pick_place", ("ON_TOP_OF",), provider="ur3_visual_servoing"),
        SkillSpec("visual_servo_then_pick", ("ON_TOP_OF",), provider="ur3_visual_servoing"),
    ]

def test_deterministic_baseline_without_experience():
    engine = build_engine([])
    goal = Goal("ON_TOP_OF", "red", "blue")
    state = WorldState({"vision_quality": "GOOD", "previous_grasp": "FAILED"})
    a = engine.rank(goal=goal, state=state, skills=skills())
    b = engine.rank(goal=goal, state=state, skills=skills())
    assert a == b
    assert a.selected_skill == "direct_pick_place"

def test_experience_can_change_selection():
    ctx = {"vision_quality": "GOOD", "previous_grasp": "FAILED"}
    records = [
        ExperienceRecord("ON_TOP_OF", ctx, "direct_pick_place", False, cost=1.0),
        ExperienceRecord("ON_TOP_OF", ctx, "direct_pick_place", False, cost=1.0),
        ExperienceRecord("ON_TOP_OF", ctx, "visual_servo_then_pick", True, cost=1.0),
        ExperienceRecord("ON_TOP_OF", ctx, "visual_servo_then_pick", True, cost=1.0),
        ExperienceRecord("ON_TOP_OF", ctx, "visual_servo_then_pick", True, cost=1.0),
    ]
    engine = build_engine(records)
    decision = engine.rank(
        goal=Goal("ON_TOP_OF", "red", "blue"),
        state=WorldState(ctx),
        skills=skills(),
    )
    assert decision.selected_skill == "visual_servo_then_pick"
    assert decision.evidence_count == 3
    assert "evidence_count=3" in decision.reason

def test_preconditions_filter_candidate():
    engine = DecisionEngine(
        EmpiricalOutcomeEstimator(ExperienceStore()),
        context_keys=("vision_ready",),
    )
    decision = engine.rank(
        goal=Goal("AT", "object", "target"),
        state=WorldState({"vision_ready": False}),
        skills=[
            SkillSpec("needs_vision", ("AT",), {"vision_ready": True}),
            SkillSpec("safe_fallback", ("AT",), {}),
        ],
    )
    assert decision.selected_skill == "safe_fallback"
