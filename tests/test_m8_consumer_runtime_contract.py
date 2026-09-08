"""M8 consumer-only runtime contract tests; no ROS or physical execution."""
from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

from physical_ai_skill_intelligence.adapters import real_ur3_free_space as adapter
from physical_ai_skill_intelligence.goal import Goal
from physical_ai_skill_intelligence.provenance import Provenance
from physical_ai_skill_intelligence.provider_observation import software_result_to_observation
from physical_ai_skill_intelligence.state import WorldState


PROVIDER_COMMIT = "025c6330e207c990afe103088c206feb0ac3dc7a"


def provenance():
    return Provenance(
        source_repository=adapter.PROVIDER_REPOSITORY,
        source_commit=PROVIDER_COMMIT,
        source_path=adapter.SOURCE_PATH,
        source_record_id=adapter.PROVIDER_CALLABLE,
        raw_sha256="a" * 64,
        schema_version="M8_CONSUMER_TEST_V1",
        importer_version="TEST",
        artifact_snapshot_commit=PROVIDER_COMMIT,
        experiment_runtime_commit=PROVIDER_COMMIT,
    )


def goal():
    return Goal(
        predicate=adapter.GOAL_PREDICATE,
        subject=adapter.GOAL_SUBJECT,
        reference=None,
        parameters={"axis": "Z"},
    )


@dataclass(frozen=True)
class ExtendedProviderResult:
    status: str
    axis: str = "Z"
    requested_translation_m: float = 0.005
    command_published: bool = True
    command_acceptance: str = "NOT_VERIFIED"
    provider_completed: bool = True
    settled: bool = True
    timed_out: bool = False
    initial_tcp_base_m: tuple[float, float, float] | None = (0.2, -0.08, 0.14)
    target_tcp_base_m: tuple[float, float, float] | None = (0.2, -0.08, 0.145)
    final_tcp_base_m: tuple[float, float, float] | None = (0.2, -0.08, 0.1449)
    observed_axis_translation_m: float | None = 0.0049
    observed_translation_norm_m: float | None = 0.0049
    final_error_mm: float | None = 0.1
    motion_elapsed_s: float = 0.3
    final_fpc_state: str = "inactive"
    servo_paused: bool = True
    operation_elapsed_s: float = 0.4
    cleanup_elapsed_s: float = 0.1
    wall_clock_elapsed_s: float = 0.5
    configured_operation_timeout_s: float = 30.0
    configured_cleanup_timeout_s: float = 15.0
    configured_wall_clock_limit_s: float = 45.0
    termination_reason: str = "SETTLED"
    cancel_requested: bool = False
    cancel_completed: bool = False
    cleanup_completed: bool = True


def extended_result(status="PASS"):
    base = ExtendedProviderResult(status=status)
    if status == "TIMEOUT":
        return replace(
            base,
            settled=False,
            timed_out=True,
            observed_axis_translation_m=0.002,
            observed_translation_norm_m=0.002,
            final_error_mm=3.0,
            termination_reason="OPERATION_TIMEOUT",
        )
    if status == "CANCELLED":
        return replace(
            base,
            settled=False,
            observed_axis_translation_m=0.001,
            observed_translation_norm_m=0.001,
            final_error_mm=4.0,
            termination_reason="CANCEL_REQUESTED",
            cancel_requested=True,
            cancel_completed=True,
        )
    if status == "BLOCKED_EXECUTION_REQUIRED":
        return replace(
            base,
            command_published=False,
            settled=False,
            initial_tcp_base_m=None,
            target_tcp_base_m=None,
            final_tcp_base_m=None,
            observed_axis_translation_m=None,
            observed_translation_norm_m=None,
            final_error_mm=None,
            motion_elapsed_s=0.0,
            operation_elapsed_s=0.0,
            cleanup_elapsed_s=0.0,
            wall_clock_elapsed_s=0.0,
            termination_reason="BLOCKED_EXECUTION_REQUIRED",
        )
    return base


def install_extended_provider(monkeypatch, result, calls=None):
    def execute_positive_axis_5mm(
        axis,
        *,
        execute=False,
        motion_timeout_sec=12.0,
        settle_error_mm=1.0,
        operation_timeout_sec=30.0,
        cleanup_timeout_sec=15.0,
        cancel_requested=None,
    ):
        if calls is not None:
            calls.append(
                (
                    axis,
                    dict(
                        execute=execute,
                        motion_timeout_sec=motion_timeout_sec,
                        settle_error_mm=settle_error_mm,
                        operation_timeout_sec=operation_timeout_sec,
                        cleanup_timeout_sec=cleanup_timeout_sec,
                        cancel_requested=cancel_requested,
                    ),
                )
            )
        return result

    provider = SimpleNamespace(
        FreeSpaceTranslationResult=ExtendedProviderResult,
        execute_positive_axis_5mm=execute_positive_axis_5mm,
    )
    monkeypatch.setattr(adapter, "import_module", lambda _: provider)
    monkeypatch.setattr(
        adapter,
        "attest_provider_source",
        lambda *args, **kwargs: {
            "status": "VERIFIED",
            "source_repository": adapter.PROVIDER_REPOSITORY,
            "source_commit": PROVIDER_COMMIT,
            "module": adapter.PROVIDER_MODULE,
            "callable": adapter.PROVIDER_CALLABLE,
            "sources": {adapter.SOURCE_PATH: "a" * 64},
        },
    )


def execute(monkeypatch, result, **provider_kwargs):
    install_extended_provider(monkeypatch, result)
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/synthetic/provider", **provider_kwargs
    )
    return provider.execute(adapter.SKILL_NAME, goal(), WorldState())


def test_extended_pass_propagates_timeouts_elapsed_and_termination(monkeypatch):
    calls = []
    install_extended_provider(monkeypatch, extended_result("PASS"), calls)
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/synthetic/provider"
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is True
    assert calls[0][1]["operation_timeout_sec"] == 30.0
    assert calls[0][1]["cleanup_timeout_sec"] == 15.0
    assert calls[0][1]["cancel_requested"] is None
    assert result.runtime_contract.configured_timeout_s == 12.0
    assert result.runtime_contract.configured_operation_timeout_s == 30.0
    assert result.runtime_contract.configured_cleanup_timeout_s == 15.0
    assert result.runtime_contract.configured_wall_clock_limit_s == 45.0
    assert result.runtime_contract.provider_timeout == "NOT_VERIFIED"
    assert result.runtime_contract.provider_cancel == "NOT_VERIFIED"
    assert result.runtime_contract.wall_clock_bound == "NOT_VERIFIED"
    assert result.runtime_result.termination_reason == "SETTLED"
    assert result.runtime_result.operation_elapsed_s == pytest.approx(0.4)
    assert result.runtime_result.cleanup_elapsed_s == pytest.approx(0.1)
    assert result.runtime_result.wall_clock_elapsed_s == pytest.approx(0.5)
    assert result.metrics["wall_clock_elapsed_s"] == pytest.approx(0.5)
    assert result.runtime_result.physical_stop_verified == "NOT_VERIFIED"

    bridged = software_result_to_observation(result).details["runtime_result"]
    assert bridged["termination_reason"] == "SETTLED"
    assert bridged["wall_clock_elapsed_s"] == pytest.approx(0.5)
    assert bridged["physical_stop_verified"] == "NOT_VERIFIED"


def test_timeout_is_preserved_without_promoting_timeout_verification(monkeypatch):
    result = execute(monkeypatch, extended_result("TIMEOUT"))
    assert result.action_success is False
    assert result.failure_code == "TIMEOUT"
    assert result.runtime_result.timed_out is True
    assert result.runtime_result.termination_reason == "OPERATION_TIMEOUT"
    assert result.runtime_result.cleanup_completed is True
    assert result.runtime_contract.provider_timeout == "NOT_VERIFIED"
    assert result.runtime_contract.wall_clock_bound == "NOT_VERIFIED"


def test_timeout_with_incomplete_cleanup_fails_closed(monkeypatch):
    provider_result = replace(
        extended_result("TIMEOUT"),
        cleanup_completed=False,
        final_fpc_state="active",
        servo_paused=False,
    )
    result = execute(monkeypatch, provider_result)
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"
    assert result.observations["provider_result"]["cleanup_completed"] is False
    assert result.runtime_result.cleanup_completed is False
    assert result.runtime_result.physical_stop_verified == "NOT_VERIFIED"


def test_cancel_completed_normalizes_only_to_software_acknowledgement(monkeypatch):
    result = execute(monkeypatch, extended_result("CANCELLED"))
    assert result.action_success is False
    assert result.failure_code == "CANCELLED"
    assert result.runtime_result.cancel_requested is True
    assert result.runtime_result.cancel_acknowledged is True
    assert result.runtime_result.cleanup_completed is True
    assert result.runtime_result.physical_stop_verified == "NOT_VERIFIED"
    assert result.runtime_contract.provider_cancel == "NOT_VERIFIED"


def test_cancel_acknowledgement_and_cleanup_completion_remain_distinct(monkeypatch):
    provider_result = replace(extended_result("CANCELLED"), cleanup_completed=False)
    result = execute(monkeypatch, provider_result)
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"
    assert result.runtime_result.cancel_requested is True
    assert result.runtime_result.cancel_acknowledged is True
    assert result.runtime_result.cleanup_completed is False
    assert result.runtime_result.physical_stop_verified == "NOT_VERIFIED"
    assert result.observations["provider_result"]["cleanup_completed"] is False


def test_contradictory_cancel_result_fails_closed_and_preserves_raw_evidence(monkeypatch):
    provider_result = replace(
        extended_result("CANCELLED"), cancel_requested=False, cancel_completed=True
    )
    result = execute(monkeypatch, provider_result)
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"
    assert result.observations["provider_result"]["cancel_requested"] is False
    assert result.observations["provider_result"]["cancel_completed"] is True
    assert result.runtime_result.physical_stop_verified == "NOT_VERIFIED"


def test_pass_with_incomplete_cleanup_fails_closed(monkeypatch):
    result = execute(
        monkeypatch, replace(extended_result("PASS"), cleanup_completed=False)
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"
    assert result.observations["provider_result"]["cleanup_completed"] is False


def test_runtime_configuration_mismatch_fails_closed(monkeypatch):
    result = execute(
        monkeypatch,
        replace(extended_result("TIMEOUT"), configured_wall_clock_limit_s=999.0),
    )
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_legacy_pass_and_timeout_contract_remain_accepted(monkeypatch):
    from test_real_ur3_free_space_adapter import (
        FakeProviderResult,
        fake_result,
    )

    calls = []

    def legacy_execute_positive_axis_5mm(
        axis, *, execute=False, motion_timeout_sec=12.0, settle_error_mm=1.0
    ):
        calls.append((axis, execute, motion_timeout_sec, settle_error_mm))
        return current_result[0]

    provider = SimpleNamespace(
        FreeSpaceTranslationResult=FakeProviderResult,
        execute_positive_axis_5mm=legacy_execute_positive_axis_5mm,
    )
    monkeypatch.setattr(adapter, "import_module", lambda _: provider)
    monkeypatch.setattr(
        adapter,
        "attest_provider_source",
        lambda *args, **kwargs: {"status": "VERIFIED"},
    )

    consumer = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/synthetic/provider"
    )
    current_result = [fake_result("PASS")]
    passed = consumer.execute(adapter.SKILL_NAME, goal(), WorldState())
    assert passed.action_success is True
    assert passed.runtime_contract.configured_operation_timeout_s is None
    assert passed.runtime_result.timed_out is False
    assert passed.runtime_result.cancel_acknowledged is None

    current_result[0] = fake_result("TIMEOUT")
    timed_out = consumer.execute(adapter.SKILL_NAME, goal(), WorldState())
    assert timed_out.failure_code == "TIMEOUT"
    assert timed_out.runtime_result.timed_out is True
    assert timed_out.runtime_result.termination_reason == "UNKNOWN"
    assert calls == [
        ("Z", False, 12.0, 1.0),
        ("Z", False, 12.0, 1.0),
    ]


def test_partial_extended_provider_api_fails_before_provider_call(monkeypatch):
    called = False

    def partial_execute_positive_axis_5mm(
        axis, *, execute=False, motion_timeout_sec=12.0,
        settle_error_mm=1.0, operation_timeout_sec=30.0,
    ):
        nonlocal called
        called = True
        return extended_result("PASS")

    provider = SimpleNamespace(
        FreeSpaceTranslationResult=ExtendedProviderResult,
        execute_positive_axis_5mm=partial_execute_positive_axis_5mm,
    )
    monkeypatch.setattr(adapter, "import_module", lambda _: provider)
    monkeypatch.setattr(
        adapter,
        "attest_provider_source",
        lambda *args, **kwargs: {"status": "VERIFIED"},
    )
    consumer = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/synthetic/provider"
    )
    result = consumer.execute(adapter.SKILL_NAME, goal(), WorldState())
    assert result.failure_code == "PROVIDER_RUNTIME_CONTRACT_UNSUPPORTED"
    assert called is False
