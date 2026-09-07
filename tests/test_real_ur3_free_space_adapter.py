from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from physical_ai_skill_intelligence.adapters import real_ur3_free_space as adapter
from physical_ai_skill_intelligence.goal import Goal
from physical_ai_skill_intelligence.provenance import Provenance
from physical_ai_skill_intelligence.state import WorldState


PROVIDER_COMMIT = "8733c1f0a1172200d5a0b42a3fea4cd76bc4bcc2"


def provenance(**overrides):
    values = dict(
        source_repository=adapter.PROVIDER_REPOSITORY,
        source_commit=PROVIDER_COMMIT,
        source_path=adapter.SOURCE_PATH,
        source_record_id=adapter.PROVIDER_CALLABLE,
        raw_sha256="a" * 64,
        schema_version="M8_TEST_V1",
        importer_version="TEST",
        artifact_snapshot_commit=PROVIDER_COMMIT,
        experiment_runtime_commit=PROVIDER_COMMIT,
    )
    values.update(overrides)
    return Provenance(**values)


def goal(axis="Z"):
    return Goal(
        predicate=adapter.GOAL_PREDICATE,
        subject=adapter.GOAL_SUBJECT,
        reference=None,
        parameters={"axis": axis},
    )


@dataclass(frozen=True)
class FakeProviderResult:
    status: str
    axis: str
    requested_translation_m: float
    command_published: bool
    command_acceptance: str
    provider_completed: bool
    settled: bool
    timed_out: bool
    initial_tcp_base_m: tuple[float, float, float] | None
    target_tcp_base_m: tuple[float, float, float] | None
    final_tcp_base_m: tuple[float, float, float] | None
    observed_axis_translation_m: float | None
    observed_translation_norm_m: float | None
    final_error_mm: float | None
    motion_elapsed_s: float
    final_fpc_state: str
    servo_paused: bool
    operation_elapsed_s: float
    cleanup_elapsed_s: float
    wall_clock_elapsed_s: float
    configured_operation_timeout_s: float
    configured_cleanup_timeout_s: float
    configured_wall_clock_limit_s: float
    termination_reason: str
    cancel_requested: bool
    cancel_completed: bool
    cleanup_completed: bool


def fake_result(status="BLOCKED_EXECUTION_REQUIRED", axis="Z", **overrides):
    if status == "PASS":
        values = dict(
            status=status,
            axis=axis,
            requested_translation_m=0.005,
            command_published=True,
            command_acceptance="NOT_VERIFIED",
            provider_completed=True,
            settled=True,
            timed_out=False,
            initial_tcp_base_m=(0.20, -0.08, 0.14),
            target_tcp_base_m=(0.20, -0.08, 0.145),
            final_tcp_base_m=(0.20, -0.08, 0.14486),
            observed_axis_translation_m=0.00486,
            observed_translation_norm_m=0.00486,
            final_error_mm=0.14,
            motion_elapsed_s=0.31,
            final_fpc_state="inactive",
            servo_paused=True,
            operation_elapsed_s=0.80,
            cleanup_elapsed_s=0.10,
            wall_clock_elapsed_s=0.90,
            configured_operation_timeout_s=30.0,
            configured_cleanup_timeout_s=15.0,
            configured_wall_clock_limit_s=45.0,
            termination_reason="SETTLED",
            cancel_requested=False,
            cancel_completed=False,
            cleanup_completed=True,
        )
    elif status == "TIMEOUT":
        values = dict(
            status=status,
            axis=axis,
            requested_translation_m=0.005,
            command_published=True,
            command_acceptance="NOT_VERIFIED",
            provider_completed=True,
            settled=False,
            timed_out=True,
            initial_tcp_base_m=(0.20, -0.08, 0.14),
            target_tcp_base_m=(0.20, -0.08, 0.145),
            final_tcp_base_m=(0.20, -0.08, 0.142),
            observed_axis_translation_m=0.002,
            observed_translation_norm_m=0.002,
            final_error_mm=3.0,
            motion_elapsed_s=12.0,
            final_fpc_state="inactive",
            servo_paused=True,
            operation_elapsed_s=12.4,
            cleanup_elapsed_s=0.2,
            wall_clock_elapsed_s=12.6,
            configured_operation_timeout_s=30.0,
            configured_cleanup_timeout_s=15.0,
            configured_wall_clock_limit_s=45.0,
            termination_reason="MOTION_SETTLE_TIMEOUT",
            cancel_requested=False,
            cancel_completed=False,
            cleanup_completed=True,
        )
    elif status == "CANCELLED":
        values = dict(
            status=status,
            axis=axis,
            requested_translation_m=0.005,
            command_published=True,
            command_acceptance="NOT_VERIFIED",
            provider_completed=True,
            settled=False,
            timed_out=False,
            initial_tcp_base_m=(0.20, -0.08, 0.14),
            target_tcp_base_m=(0.20, -0.08, 0.145),
            final_tcp_base_m=(0.20, -0.08, 0.141),
            observed_axis_translation_m=0.001,
            observed_translation_norm_m=0.001,
            final_error_mm=4.0,
            motion_elapsed_s=0.15,
            final_fpc_state="inactive",
            servo_paused=True,
            operation_elapsed_s=0.30,
            cleanup_elapsed_s=0.10,
            wall_clock_elapsed_s=0.40,
            configured_operation_timeout_s=30.0,
            configured_cleanup_timeout_s=15.0,
            configured_wall_clock_limit_s=45.0,
            termination_reason="CANCEL_REQUESTED",
            cancel_requested=True,
            cancel_completed=True,
            cleanup_completed=True,
        )
    else:
        values = dict(
            status=status,
            axis=axis,
            requested_translation_m=0.005,
            command_published=False,
            command_acceptance="NOT_VERIFIED",
            provider_completed=True,
            settled=False,
            timed_out=False,
            initial_tcp_base_m=None,
            target_tcp_base_m=None,
            final_tcp_base_m=None,
            observed_axis_translation_m=None,
            observed_translation_norm_m=None,
            final_error_mm=None,
            motion_elapsed_s=0.0,
            final_fpc_state="NOT_APPLICABLE",
            servo_paused=True,
            operation_elapsed_s=0.0,
            cleanup_elapsed_s=0.0,
            wall_clock_elapsed_s=0.0,
            configured_operation_timeout_s=30.0,
            configured_cleanup_timeout_s=15.0,
            configured_wall_clock_limit_s=45.0,
            termination_reason="EXECUTION_BLOCKED",
            cancel_requested=False,
            cancel_completed=False,
            cleanup_completed=True,
        )
    values.update(overrides)
    return FakeProviderResult(**values)


def install_fake_provider(monkeypatch, result, calls=None):
    def execute_positive_axis_5mm(axis, **kwargs):
        if calls is not None:
            calls.append((axis, kwargs))
        return result

    provider = SimpleNamespace(
        FreeSpaceTranslationResult=FakeProviderResult,
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


def test_constructor_requires_exact_provider_capability():
    with pytest.raises(ValueError, match="exact real UR3 capability"):
        adapter.RealUr3PositiveAxis5mmProvider(
            provenance(source_record_id="other")
        )


def test_constructor_validates_new_runtime_bounds_and_cancel_callable():
    for kwargs in (
        {"operation_timeout_s": 0.0},
        {"cleanup_timeout_s": -1.0},
        {"cancel_requested": True},
    ):
        with pytest.raises(ValueError):
            adapter.RealUr3PositiveAxis5mmProvider(provenance(), **kwargs)


def test_unsupported_skill_fails_without_provider_import():
    provider = adapter.RealUr3PositiveAxis5mmProvider(provenance())
    result = provider.execute("OTHER", goal(), WorldState())
    assert result.action_success is False
    assert result.failure_code == "UNSUPPORTED_CAPABILITY"


def test_invalid_axis_fails_before_provider_call():
    provider = adapter.RealUr3PositiveAxis5mmProvider(provenance())
    result = provider.execute(adapter.SKILL_NAME, goal("-Z"), WorldState())
    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_INPUT"


def test_dry_run_passes_bounded_contract_and_preserves_block(monkeypatch):
    calls = []
    install_fake_provider(monkeypatch, fake_result(), calls)
    cancel = lambda: False
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(),
        provider_repository="/tmp/provider",
        execute_real=False,
        motion_timeout_s=12.0,
        operation_timeout_s=30.0,
        cleanup_timeout_s=15.0,
        settle_error_mm=1.0,
        cancel_requested=cancel,
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert calls == [(
        "Z",
        {
            "execute": False,
            "motion_timeout_sec": 12.0,
            "operation_timeout_sec": 30.0,
            "cleanup_timeout_sec": 15.0,
            "settle_error_mm": 1.0,
            "cancel_requested": cancel,
        },
    )]
    assert result.action_success is False
    assert result.failure_code == "BLOCKED_EXECUTION_REQUIRED"
    assert result.observations["provider_completed"] is True
    assert result.observations["provider_result"]["command_published"] is False
    assert result.runtime_contract.configured_timeout_s == 30.0
    assert result.runtime_contract.configured_wall_clock_limit_s == 45.0
    assert "startup + motion" in result.runtime_contract.timeout_scope
    assert "cancel_requested=callable" in result.runtime_contract.cancel_api
    assert result.runtime_contract.provider_timeout == "NOT_VERIFIED"
    assert result.runtime_contract.provider_cancel == "NOT_VERIFIED"
    assert result.runtime_contract.wall_clock_bound == "NOT_VERIFIED"


def test_pass_requires_observed_settle_safe_cleanup_and_bounded_evidence(monkeypatch):
    install_fake_provider(monkeypatch, fake_result("PASS"))
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider", execute_real=True
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is True
    assert result.failure_code is None
    assert result.observations["provider_result"]["status"] == "PASS"
    assert result.observations["actual_tcp_motion_observation"]["settled"] is True
    assert result.observations["final_runtime_state"] == {
        "forward_position_controller": "inactive",
        "servo_paused": True,
    }
    assert result.observations["termination"]["cleanup_completed"] is True
    assert result.observations["termination"]["wall_clock_elapsed_s"] == 0.90
    assert result.metrics["observed_axis_translation_m"] == pytest.approx(0.00486)
    assert result.metrics["wall_clock_elapsed_s"] == pytest.approx(0.90)
    assert result.observations["command_accepted"] == "NOT_VERIFIED"


def test_timeout_is_bounded_provider_failure_not_success(monkeypatch):
    install_fake_provider(monkeypatch, fake_result("TIMEOUT"))
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider", execute_real=True
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is False
    assert result.failure_code == "TIMEOUT"
    assert result.observations["provider_completed"] is True
    assert result.observations["provider_result"]["timed_out"] is True
    assert result.observations["termination"]["cleanup_completed"] is True
    assert result.observations["final_runtime_state"]["forward_position_controller"] == "inactive"
    assert result.runtime_contract.provider_timeout == "NOT_VERIFIED"


def test_cancelled_is_terminal_failure_only_after_safe_cleanup(monkeypatch):
    install_fake_provider(monkeypatch, fake_result("CANCELLED"))
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider", execute_real=True
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is False
    assert result.failure_code == "CANCELLED"
    assert result.observations["termination"]["cancel_requested"] is True
    assert result.observations["termination"]["cancel_completed"] is True
    assert result.observations["termination"]["cleanup_completed"] is True
    assert result.observations["final_runtime_state"] == {
        "forward_position_controller": "inactive",
        "servo_paused": True,
    }


def test_cancelled_without_completed_cancel_is_rejected(monkeypatch):
    install_fake_provider(
        monkeypatch, fake_result("CANCELLED", cancel_completed=False)
    )
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider", execute_real=True
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_post_command_timeout_without_safe_cleanup_is_rejected(monkeypatch):
    install_fake_provider(
        monkeypatch,
        fake_result("TIMEOUT", cleanup_completed=False, final_fpc_state="active"),
    )
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider", execute_real=True
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_wall_clock_overrun_is_rejected_instead_of_being_trusted(monkeypatch):
    install_fake_provider(
        monkeypatch,
        fake_result("PASS", wall_clock_elapsed_s=45.001),
    )
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider", execute_real=True
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_inconsistent_wall_clock_configuration_is_rejected(monkeypatch):
    install_fake_provider(
        monkeypatch,
        fake_result("PASS", configured_wall_clock_limit_s=44.0),
    )
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider", execute_real=True
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert result.action_success is False
    assert result.failure_code == "INVALID_PROVIDER_RESULT"


def test_attestation_failure_fails_closed_before_provider_call(monkeypatch):
    provider_module = SimpleNamespace(
        FreeSpaceTranslationResult=FakeProviderResult,
        execute_positive_axis_5mm=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("provider call must not run")
        ),
    )
    monkeypatch.setattr(adapter, "import_module", lambda _: provider_module)
    monkeypatch.setattr(
        adapter,
        "attest_provider_source",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("identity mismatch")),
    )
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(), provider_repository="/tmp/provider"
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())
    assert result.action_success is False
    assert result.failure_code == "RUNTIME_PROVIDER_IDENTITY_UNVERIFIED"
