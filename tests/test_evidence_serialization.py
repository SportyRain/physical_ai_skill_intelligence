import json
from dataclasses import asdict

import pytest

from physical_ai_skill_intelligence.evidence_serialization import to_jsonable
from physical_ai_skill_intelligence.provider_contract import ProviderResult


def test_mappingproxy_provider_result_reproduces_old_failure_and_serializes_safely():
    result = ProviderResult(
        action_success=False,
        observations={
            "provider_result": {
                "status": "TIMEOUT",
                "command_published": True,
                "provider_completed": True,
                "timed_out": True,
                "initial_tcp_base_m": (0.20, -0.08, 0.14),
                "final_tcp_base_m": (0.20, -0.08, 0.142),
            },
            "final_runtime_state": {
                "forward_position_controller": "inactive",
                "servo_paused": True,
            },
        },
        failure_code="TIMEOUT",
        metrics={"motion_elapsed_s": 12.0},
    )

    # Trial001 used dataclasses.asdict on ProviderResult after immutable snapshots
    # had converted mappings into MappingProxyType. Preserve that regression.
    with pytest.raises(TypeError, match="mappingproxy"):
        asdict(result)

    payload = to_jsonable(result)
    encoded = json.dumps(payload, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["action_success"] is False
    assert decoded["failure_code"] == "TIMEOUT"
    assert decoded["observations"]["provider_result"]["timed_out"] is True
    assert decoded["observations"]["provider_result"]["initial_tcp_base_m"] == [
        0.20,
        -0.08,
        0.14,
    ]
    assert decoded["observations"]["final_runtime_state"] == {
        "forward_position_controller": "inactive",
        "servo_paused": True,
    }
    assert decoded["metrics"]["motion_elapsed_s"] == 12.0
    assert decoded["runtime_contract"]["provider_timeout"] == "NOT_VERIFIED"
    assert decoded["runtime_contract"]["provider_cancel"] == "NOT_VERIFIED"
    assert decoded["runtime_contract"]["wall_clock_bound"] == "NOT_VERIFIED"


def test_serializer_does_not_mutate_immutable_provider_result():
    result = ProviderResult(
        action_success=False,
        observations={"nested": {"value": 1}},
        failure_code="TEST_FAILURE",
    )

    payload = to_jsonable(result)
    payload["observations"]["nested"]["value"] = 99

    assert result.observations["nested"]["value"] == 1


def test_serializer_fails_closed_on_nonfinite_or_unsupported_values():
    with pytest.raises(ValueError, match="finite"):
        to_jsonable(float("nan"))

    with pytest.raises(TypeError, match="unsupported evidence value type"):
        to_jsonable(object())

    with pytest.raises(TypeError, match="mapping keys must be strings"):
        to_jsonable({1: "bad"})
