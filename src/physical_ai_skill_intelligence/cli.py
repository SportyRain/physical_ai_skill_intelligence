from __future__ import annotations
import argparse
from .goal import Goal
from .state import WorldState
from .skill import SkillSpec
from .experience import ExperienceRecord, ExperienceStore
from .outcome import EmpiricalOutcomeEstimator
from .decision import DecisionEngine

def demo() -> None:
    context = {"vision_quality": "GOOD", "previous_grasp": "FAILED"}
    store = ExperienceStore([
        ExperienceRecord("ON_TOP_OF", context, "direct_pick_place", False, cost=1.0),
        ExperienceRecord("ON_TOP_OF", context, "direct_pick_place", False, cost=1.0),
        ExperienceRecord("ON_TOP_OF", context, "visual_servo_then_pick", True, cost=1.5),
        ExperienceRecord("ON_TOP_OF", context, "visual_servo_then_pick", True, cost=1.5),
        ExperienceRecord("ON_TOP_OF", context, "visual_servo_then_pick", True, cost=1.5),
    ])
    engine = DecisionEngine(
        EmpiricalOutcomeEstimator(store),
        context_keys=("vision_quality", "previous_grasp"),
    )
    decision = engine.rank(
        goal=Goal("ON_TOP_OF", "red", "blue"),
        state=WorldState(context),
        skills=[
            SkillSpec("direct_pick_place", ("ON_TOP_OF",), provider="ur3_visual_servoing"),
            SkillSpec("visual_servo_then_pick", ("ON_TOP_OF",), provider="ur3_visual_servoing"),
        ],
    )
    print(decision.reason)
    print("ranking=", decision.ranking)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["demo"])
    args = parser.parse_args()
    if args.command == "demo":
        demo()

if __name__ == "__main__":
    main()
