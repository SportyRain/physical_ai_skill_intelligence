from physical_ai_skill_intelligence import ExperienceRecord, ExperienceStore

def test_context_matching_is_exact():
    store = ExperienceStore([
        ExperienceRecord("AT", {"visibility": "GOOD"}, "skill_a", True),
        ExperienceRecord("AT", {"visibility": "GOOD", "moved": False}, "skill_a", True),
    ])
    rows = store.exact_context(
        goal_predicate="AT",
        state_context={"visibility": "GOOD"},
        skill_name="skill_a",
    )
    assert len(rows) == 1

def test_unknown_is_literal_not_wildcard_in_experience_context():
    store = ExperienceStore([
        ExperienceRecord("AT", {"object_id": "UNKNOWN"}, "skill_a", True),
    ])
    assert store.exact_context(
        goal_predicate="AT",
        state_context={"object_id": "puck-1"},
        skill_name="skill_a",
    ) == ()
