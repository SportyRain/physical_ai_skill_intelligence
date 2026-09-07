from pathlib import Path

def test_no_robot_control_dependencies_in_core():
    root = Path(__file__).parents[1] / "src" / "physical_ai_skill_intelligence"
    text = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*.py"))
    forbidden = [
        "rclpy",
        "moveit",
        "ur_robot_driver",
        "ros2_control",
        "trajectory_msgs",
        "geometry_msgs",
        "sensor_msgs",
    ]
    for token in forbidden:
        assert token not in text.lower()
