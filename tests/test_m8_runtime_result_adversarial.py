from dataclasses import replace

import pytest

from test_m8_consumer_runtime_contract import execute, extended_result


def test_pass_with_timeout_termination_reason_fails_closed(monkeypatch):
    result = execute(
        monkeypatch,
        replace(extended_result("PASS"), termination_reason="OPERATION_TIMEOUT"),
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"
    assert "termination_reason" in result.observations["invalid_provider_result_reason"]


def test_timeout_with_settled_termination_reason_fails_closed(monkeypatch):
    result = execute(
        monkeypatch,
        replace(extended_result("TIMEOUT"), termination_reason="SETTLED"),
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_cancel_with_settled_termination_reason_fails_closed(monkeypatch):
    result = execute(
        monkeypatch,
        replace(extended_result("CANCELLED"), termination_reason="SETTLED"),
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_blocked_with_nonblocked_termination_reason_fails_closed(monkeypatch):
    result = execute(
        monkeypatch,
        replace(
            extended_result("BLOCKED_EXECUTION_REQUIRED"),
            termination_reason="SETTLED",
        ),
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_wall_clock_smaller_than_operation_plus_cleanup_fails_closed(monkeypatch):
    result = execute(
        monkeypatch,
        replace(
            extended_result("PASS"),
            operation_elapsed_s=0.4,
            cleanup_elapsed_s=0.2,
            wall_clock_elapsed_s=0.5,
        ),
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"
    assert "wall_clock_elapsed_s" in result.observations["invalid_provider_result_reason"]


def test_cleanup_elapsed_beyond_configured_cleanup_budget_fails_closed(monkeypatch):
    result = execute(
        monkeypatch,
        replace(
            extended_result("PASS"),
            operation_elapsed_s=0.4,
            cleanup_elapsed_s=16.0,
            wall_clock_elapsed_s=16.4,
        ),
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"
    assert "cleanup_elapsed_s" in result.observations["invalid_provider_result_reason"]
