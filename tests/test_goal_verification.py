from physical_ai_skill_intelligence import Goal, WorldState
from physical_ai_skill_intelligence.goal_verification import goal_satisfied

def test_action_success_does_not_imply_goal_success():
    goal = Goal("ON_TOP_OF", "red", "blue")
    state = WorldState({"last_action_success": True})
    assert goal_satisfied(goal, state) is False

def test_world_relation_can_verify_goal():
    goal = Goal("ON_TOP_OF", "red", "blue")
    state = WorldState({"on_top_of:red:blue": True})
    assert goal_satisfied(goal, state) is True
