# Physical AI Skill Intelligence

Clean-room base for **physical decision intelligence**.

This project does **not** implement robot motion, visual servoing, planning, IK/FK,
trajectory execution, camera drivers, or robot-specific manipulation.

## Core question

> Given a Goal, Current World State, Candidate Skills, and Past Physical Experience,
> which skill/strategy should be selected next, and why?

```text
Goal
+
World State
+
Candidate Skills
+
Past Experience
        |
        v
Outcome Estimation
        |
        v
Decision / Ranking
        |
        v
Existing Skill Provider
        |
        v
Observed Outcome
        |
        v
New Experience
```

## Existing robot repositories

Existing UR3 projects are treated as **STABLE SKILL PROVIDERS**.
They may evolve independently when necessary, but this repository does not copy their
control/perception implementations.

## DO_NOT_REIMPLEMENT

- Universal Robots ROS 2 Driver
- ros2_control
- MoveIt 2 / MoveIt Servo
- IK / FK / Jacobian
- trajectory execution
- camera drivers
- robot-specific visual servoing
- robot-specific pick/place implementation
- robot-specific peg-in-hole controllers

## OUR_CUSTOM_VALUE

- Goal representation
- World-state representation
- Skill capability contracts
- Experience/provenance representation
- Outcome estimation interface
- Experience-conditioned ranking
- Explainable decision output
- Offline evaluation/regression boundary

## Verification scope of v0.1.0

This base verifies only software-level behavior.

It does **not** claim:
- real UR3 integration
- repeatable performance improvement
- self-learning
- a novel learning algorithm

Run:

```bash
python -m pytest
python -m physical_ai_skill_intelligence.cli demo
```
