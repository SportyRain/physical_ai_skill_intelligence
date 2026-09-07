import pytest
from physical_ai_skill_intelligence import ExperienceRecord, ExperienceStore

def test_negative_cost_rejected():
    with pytest.raises(ValueError):
        ExperienceStore([ExperienceRecord("AT", {}, "skill", True, cost=-1)])
