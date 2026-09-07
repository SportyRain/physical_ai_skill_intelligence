from physical_ai_skill_intelligence import WorldState, UNKNOWN

def test_unknown_is_not_a_wildcard_for_preconditions():
    state = WorldState({"robot_ready": True})
    assert state.get("vision_ready") == UNKNOWN
    assert state.satisfies({"vision_ready": True}) is False
