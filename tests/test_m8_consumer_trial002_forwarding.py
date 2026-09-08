"""Trial002 consumer forwarding tests; software-only, no provider/ROS execution."""

import pytest

from physical_ai_skill_intelligence import m8_trial002 as runner
from test_m8_trial002 import FakeProvider, run


def test_trial002_forwards_runtime_budgets_and_cancel_callback(tmp_path, monkeypatch):
    cancel_requested = lambda: False
    record, _ = run(
        tmp_path,
        monkeypatch,
        motion_timeout_s=7.0,
        operation_timeout_s=11.0,
        cleanup_timeout_s=4.0,
        settle_error_mm=0.75,
        cancel_requested=cancel_requested,
    )

    kwargs = FakeProvider.calls[0][2]
    assert kwargs["motion_timeout_s"] == 7.0
    assert kwargs["operation_timeout_s"] == 11.0
    assert kwargs["cleanup_timeout_s"] == 4.0
    assert kwargs["settle_error_mm"] == 0.75
    assert kwargs["cancel_requested_callback"] is cancel_requested
    assert record["configured_motion_timeout_s"] == 7.0
    assert record["configured_operation_timeout_s"] == 11.0
    assert record["configured_cleanup_timeout_s"] == 4.0
    assert record["cancel_callback_supplied"] is True


def test_trial002_without_cancel_callback_preserves_none(tmp_path, monkeypatch):
    record, _ = run(tmp_path, monkeypatch)
    assert FakeProvider.calls[0][2]["cancel_requested_callback"] is None
    assert record["cancel_callback_supplied"] is False


def test_invalid_cancel_callback_fails_before_provider_construction(tmp_path, monkeypatch):
    FakeProvider.calls = []
    monkeypatch.setattr(runner, "RealUr3PositiveAxis5mmProvider", FakeProvider)
    with pytest.raises(ValueError, match="cancel_requested"):
        runner.run_trial002_positive_axis_5mm(
            trial_id="M8_TRIAL002_CANCEL_INVALID",
            axis="Z",
            physical_ai_commit="1" * 40,
            provider_commit="2" * 40,
            provider_raw_sha256="a" * 64,
            provider_related_sources_sha256={
                path: "b" * 64 for path in runner.REQUIRED_RELATED_SOURCE_PATHS
            },
            provider_repository="/tmp/provider",
            output_path=tmp_path / "invalid.json",
            cancel_requested=True,
        )
    assert FakeProvider.calls == []
