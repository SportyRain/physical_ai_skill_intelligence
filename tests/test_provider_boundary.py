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


def test_provider_imports_are_only_in_adapter_layer():
    import ast
    root = Path(__file__).parents[1] / "src" / "physical_ai_skill_intelligence"
    forbidden = {"ur3_visual_servoing", "rclpy", "moveit", "ur_robot_driver",
                 "ros2_control", "trajectory_msgs", "geometry_msgs", "sensor_msgs"}
    for path in root.rglob("*.py"):
        is_adapter = "adapters" in path.relative_to(root).parts
        for node in ast.walk(ast.parse(path.read_text())):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            elif isinstance(node, ast.Call):
                function = node.func
                name = function.id if isinstance(function, ast.Name) else getattr(function, "attr", "")
                if name in {"import_module", "__import__"} and node.args:
                    if not is_adapter:
                        assert isinstance(node.args[0], ast.Constant), path
                    if isinstance(node.args[0], ast.Constant):
                        modules = [node.args[0].value]
            for module in modules:
                base = module.split(".")[0]
                assert base not in forbidden or (is_adapter and base == "ur3_visual_servoing"), path


def test_production_source_has_no_local_repository_paths():
    root = Path(__file__).parents[1] / "src"
    for path in root.rglob("*.py"):
        content = path.read_text()
        assert "/home/rosystem" not in content, path
        assert "../ur3_visual_servoing" not in content, path


def test_core_and_adapter_import_without_loading_external_provider():
    import subprocess
    import sys
    root = Path(__file__).parents[1] / "src"
    code = '''
import sys
sys.path.insert(0, sys.argv[1])
import physical_ai_skill_intelligence
import physical_ai_skill_intelligence.adapters.relational_place
import physical_ai_skill_intelligence.provider_observation
assert not any(name == 'ur3_visual_servoing' or name.startswith('ur3_visual_servoing.') for name in sys.modules)
'''
    subprocess.run([sys.executable, "-I", "-c", code, str(root)], check=True)
