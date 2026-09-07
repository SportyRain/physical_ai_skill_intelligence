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


def fake_result(status="BLOCKED_EXECUTION_REQUIRED", axis="Z"):
    if status == "PASS":
        return FakeProviderResult(
            status,
            axis,
            0.005,
            True,
            "NOT_VERIFIED",
            True,
            True,
            False,
            (0.20, -0.08, 0.14),
            (0.20, -0.08, 0.145),
            (0.20, -0.08, 0.14486),
            0.00486,
            0.00486,
            0.14,
            0.31,
            "inactive",
            True,
        )
    if status == "TIMEOUT":
        return FakeProviderResult(
            status,
            axis,
            0.005,
            True,
            "NOT_VERIFIED",
            True,
            False,
            True,
            (0.20, -0.08, 0.14),
            (0.20, -0.08, 0.145),
            (0.20, -0.08, 0.142),
            0.002,
            0.002,
            3.0,
            12.0,
            "inactive",
            True,
        )
    return FakeProviderResult(
        status,
        axis,
        0.005,
        False,
        "NOT_VERIFIED",
        True,
        False,
        False,
        None,
        None,
        None,
        None,
        None,
        None,
        0.0,
        "NOT_APPLICABLE",
        True,
    )


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


def test_dry_run_preserves_provider_block_and_runtime_declaration(monkeypatch):
    calls = []
    install_fake_provider(monkeypatch, fake_result(), calls)
    provider = adapter.RealUr3PositiveAxis5mmProvider(
        provenance(),
        provider_repository="/tmp/provider",
        execute_real=False,
        motion_timeout_s=12.0,
        settle_error_mm=1.0,
    )
    result = provider.execute(adapter.SKILL_NAME, goal(), WorldState())

    assert calls == [(
        "Z",
        {"execute": False, "motion_timeout_sec": 12.0, "settle_error_mm": 1.0},
    )]
    assert result.action_success is False
    assert result.failure_code == "BLOCKED_EXECUTION_REQUIRED"
    assert result.observations["provider_completed"] is True
    assert result.observations["provider_result"]["command_published"] is False
    assert result.runtime_contract.configured_timeout_s == 12.0
    assert result.runtime_contract.timeout_scope == (
        "motion settle loop only; startup and cleanup excluded"
    )
    assert result.runtime_contract.provider_timeout == "NOT_VERIFIED"
    assert result.runtime_contract.provider_cancel == "NOT_VERIFIED"
    assert result.runtime_contract.wall_clock_bound == "NOT_VERIFIED"


def test_pass_requires_observed_settle_and_safe_cleanup(monkeypatch):
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
    assert result.metrics["observed_axis_translation_m"] == pytest.approx(0.00486)
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
    assert result.observations["final_runtime_state"]["forward_position_controller"] == "inactive"
    assert result.runtime_contract.provider_timeout == "NOT_VERIFIED"


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
