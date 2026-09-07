import json

import pytest

from physical_ai_skill_intelligence import m8_trial002 as runner
from physical_ai_skill_intelligence.provider_contract import ProviderResult


PAI_COMMIT = "1" * 40
PROVIDER_COMMIT = "2" * 40
PROVIDER_SHA256 = "a" * 64
RELATED_SHA256 = {
    path: (hex(index + 11)[2:] * 64)[:64]
    for index, path in enumerate(runner.REQUIRED_RELATED_SOURCE_PATHS)
}


class FakeProvider:
    calls = []

    def __init__(self, provenance, **kwargs):
        self.provenance = provenance
        self.kwargs = kwargs
        type(self).calls.append(("init", provenance, kwargs))

    def execute(self, skill_name, goal, state):
        type(self).calls.append(("execute", skill_name, goal, state))
        return ProviderResult(
            action_success=False,
            observations={
                "provider_result": {
                    "status": "BLOCKED_EXECUTION_REQUIRED",
                    "command_published": False,
                    "provider_completed": True,
                    "timed_out": False,
                }
            },
            failure_code="BLOCKED_EXECUTION_REQUIRED",
            provenance=self.provenance,
        )


def run(tmp_path, monkeypatch, **overrides):
    FakeProvider.calls = []
    monkeypatch.setattr(runner, "RealUr3PositiveAxis5mmProvider", FakeProvider)
    values = dict(
        trial_id="M8_TRIAL002_DRYRUN",
        axis="Z",
        physical_ai_commit=PAI_COMMIT,
        provider_commit=PROVIDER_COMMIT,
        provider_raw_sha256=PROVIDER_SHA256,
        provider_related_sources_sha256=RELATED_SHA256,
        provider_repository="/tmp/provider",
        output_path=tmp_path / "trial.json",
    )
    values.update(overrides)
    return runner.run_trial002_positive_axis_5mm(**values), values


def test_trial002_defaults_fail_closed_and_writes_json(tmp_path, monkeypatch):
    record, values = run(tmp_path, monkeypatch)

    assert FakeProvider.calls[0][0] == "init"
    provenance = FakeProvider.calls[0][1]
    init_kwargs = FakeProvider.calls[0][2]
    assert init_kwargs["execute_real"] is False
    assert init_kwargs["motion_timeout_s"] == runner.DEFAULT_MOTION_TIMEOUT_S
    assert init_kwargs["operation_timeout_s"] == runner.DEFAULT_OPERATION_TIMEOUT_S
    assert init_kwargs["cleanup_timeout_s"] == runner.DEFAULT_CLEANUP_TIMEOUT_S
    assert init_kwargs["settle_error_mm"] == runner.DEFAULT_SETTLE_ERROR_MM
    assert init_kwargs["cancel_requested"] is None
    assert FakeProvider.calls[1][0] == "execute"
    assert tuple(item.source_path for item in provenance.related_sources) == (
        runner.REQUIRED_RELATED_SOURCE_PATHS
    )
    assert {
        item.source_path: item.raw_sha256 for item in provenance.related_sources
    } == RELATED_SHA256

    assert record["execute_real"] is False
    assert record["axis"] == "Z"
    assert record["requested_translation_m"] == 0.005
    assert record["serialization"] == "to_jsonable"
    assert record["provider_related_sources_sha256"] == RELATED_SHA256
    assert record["configured_motion_timeout_s"] == runner.DEFAULT_MOTION_TIMEOUT_S
    assert record["configured_operation_timeout_s"] == runner.DEFAULT_OPERATION_TIMEOUT_S
    assert record["configured_cleanup_timeout_s"] == runner.DEFAULT_CLEANUP_TIMEOUT_S
    assert record["cancel_callback_supplied"] is False
    assert record["result"]["failure_code"] == "BLOCKED_EXECUTION_REQUIRED"

    written = json.loads(values["output_path"].read_text(encoding="utf-8"))
    assert written["trial_id"] == "M8_TRIAL002_DRYRUN"
    assert written["physical_ai_commit"] == PAI_COMMIT
    assert written["provider_commit"] == PROVIDER_COMMIT
    assert written["provider_related_sources_sha256"] == RELATED_SHA256
    assert written["configured_operation_timeout_s"] == runner.DEFAULT_OPERATION_TIMEOUT_S
    assert written["configured_cleanup_timeout_s"] == runner.DEFAULT_CLEANUP_TIMEOUT_S
    assert written["cancel_callback_supplied"] is False
    assert written["result"]["observations"]["provider_result"][
        "provider_completed"
    ] is True


def test_trial002_path_calls_verified_serializer(tmp_path, monkeypatch):
    original = runner.to_jsonable
    seen = []

    def capture(value):
        seen.append(value)
        return original(value)

    monkeypatch.setattr(runner, "to_jsonable", capture)
    run(tmp_path, monkeypatch)

    assert len(seen) == 1
    assert isinstance(seen[0], ProviderResult)


def test_existing_output_blocks_before_provider_construction(tmp_path, monkeypatch):
    output = tmp_path / "trial.json"
    output.write_text("preserved\n", encoding="utf-8")

    class MustNotConstruct:
        def __init__(self, *args, **kwargs):
            raise AssertionError("provider must not be constructed")

    monkeypatch.setattr(
        runner,
        "RealUr3PositiveAxis5mmProvider",
        MustNotConstruct,
    )

    with pytest.raises(FileExistsError, match="already exists"):
        runner.run_trial002_positive_axis_5mm(
            trial_id="M8_TRIAL002",
            axis="Z",
            physical_ai_commit=PAI_COMMIT,
            provider_commit=PROVIDER_COMMIT,
            provider_raw_sha256=PROVIDER_SHA256,
            provider_related_sources_sha256=RELATED_SHA256,
            provider_repository="/tmp/provider",
            output_path=output,
        )

    assert output.read_text(encoding="utf-8") == "preserved\n"


def test_execute_real_requires_explicit_boolean(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="execute_real"):
        run(tmp_path, monkeypatch, execute_real=1)


def test_explicit_execute_real_is_forwarded_once(tmp_path, monkeypatch):
    record, _ = run(tmp_path, monkeypatch, execute_real=True)

    assert FakeProvider.calls[0][2]["execute_real"] is True
    assert len([item for item in FakeProvider.calls if item[0] == "execute"]) == 1
    assert record["execute_real"] is True


def test_termination_contract_inputs_are_forwarded_once_and_recorded(
    tmp_path, monkeypatch
):
    cancel = lambda: False
    record, _ = run(
        tmp_path,
        monkeypatch,
        execute_real=True,
        motion_timeout_s=4.0,
        operation_timeout_s=7.0,
        cleanup_timeout_s=3.0,
        settle_error_mm=0.8,
        cancel_requested=cancel,
    )

    kwargs = FakeProvider.calls[0][2]
    assert kwargs == {
        "provider_repository": "/tmp/provider",
        "execute_real": True,
        "motion_timeout_s": 4.0,
        "operation_timeout_s": 7.0,
        "cleanup_timeout_s": 3.0,
        "settle_error_mm": 0.8,
        "cancel_requested": cancel,
    }
    assert len([item for item in FakeProvider.calls if item[0] == "execute"]) == 1
    assert record["configured_motion_timeout_s"] == 4.0
    assert record["configured_operation_timeout_s"] == 7.0
    assert record["configured_cleanup_timeout_s"] == 3.0
    assert record["cancel_callback_supplied"] is True


def test_invalid_cancel_callback_fails_before_provider_construction(tmp_path, monkeypatch):
    FakeProvider.calls = []
    monkeypatch.setattr(runner, "RealUr3PositiveAxis5mmProvider", FakeProvider)

    with pytest.raises(ValueError, match="cancel_requested"):
        runner.run_trial002_positive_axis_5mm(
            trial_id="M8_TRIAL002",
            axis="Z",
            physical_ai_commit=PAI_COMMIT,
            provider_commit=PROVIDER_COMMIT,
            provider_raw_sha256=PROVIDER_SHA256,
            provider_related_sources_sha256=RELATED_SHA256,
            provider_repository="/tmp/provider",
            output_path=tmp_path / "bad_cancel.json",
            cancel_requested=True,
        )
    assert FakeProvider.calls == []


def test_bad_identity_inputs_fail_before_provider(tmp_path, monkeypatch):
    FakeProvider.calls = []
    monkeypatch.setattr(runner, "RealUr3PositiveAxis5mmProvider", FakeProvider)

    with pytest.raises(ValueError, match="physical_ai_commit"):
        runner.run_trial002_positive_axis_5mm(
            trial_id="M8_TRIAL002",
            axis="Z",
            physical_ai_commit="bad",
            provider_commit=PROVIDER_COMMIT,
            provider_raw_sha256=PROVIDER_SHA256,
            provider_related_sources_sha256=RELATED_SHA256,
            provider_repository="/tmp/provider",
            output_path=tmp_path / "bad1.json",
        )

    with pytest.raises(ValueError, match="provider_raw_sha256"):
        runner.run_trial002_positive_axis_5mm(
            trial_id="M8_TRIAL002",
            axis="Z",
            physical_ai_commit=PAI_COMMIT,
            provider_commit=PROVIDER_COMMIT,
            provider_raw_sha256="bad",
            provider_related_sources_sha256=RELATED_SHA256,
            provider_repository="/tmp/provider",
            output_path=tmp_path / "bad2.json",
        )

    incomplete = dict(RELATED_SHA256)
    incomplete.pop(next(iter(incomplete)))
    with pytest.raises(ValueError, match="exactly the required"):
        runner.run_trial002_positive_axis_5mm(
            trial_id="M8_TRIAL002",
            axis="Z",
            physical_ai_commit=PAI_COMMIT,
            provider_commit=PROVIDER_COMMIT,
            provider_raw_sha256=PROVIDER_SHA256,
            provider_related_sources_sha256=incomplete,
            provider_repository="/tmp/provider",
            output_path=tmp_path / "bad3.json",
        )

    extra = dict(RELATED_SHA256)
    extra["src/ur3_visual_servoing/unexpected.py"] = "f" * 64
    with pytest.raises(ValueError, match="exactly the required"):
        runner.run_trial002_positive_axis_5mm(
            trial_id="M8_TRIAL002",
            axis="Z",
            physical_ai_commit=PAI_COMMIT,
            provider_commit=PROVIDER_COMMIT,
            provider_raw_sha256=PROVIDER_SHA256,
            provider_related_sources_sha256=extra,
            provider_repository="/tmp/provider",
            output_path=tmp_path / "bad4.json",
        )

    assert FakeProvider.calls == []
