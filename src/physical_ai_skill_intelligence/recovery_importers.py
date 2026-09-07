from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .experience import UNKNOWN
from .provenance import Provenance, SourceArtifact, validate_commit, runtime_commit
from ._evidence_paths import contained_path, validate_raw_paths
from .cost import OBSERVED_COST
from .recovery import RecoveryExperienceRecord

RECOVERY_IMPORTER_VERSION = "ur3_visual_servoing_recovery_evidence_v2"
SOURCE_REPOSITORY = "SportyRain/ur3_visual_servoing"
RUN_MANIFEST_SCHEMA = "UNVERSIONED_RUN_MANIFEST"
READY_RECOVERY_GOAL = "CANONICAL_READY"
READY_STALE_FAILURE_CODE = "PA-READY-818"
READY_STALE_FAILURE_ATTRIBUTION = "NONCANONICAL_CONTROLLER_ACTIVE"
READY_STALE_RECOVERY_ACTION = "CLEAN_STALE_FORCE_PASSTHROUGH"


class RecoveryEvidenceImportError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RecoveryEvidenceImportError(f"failed to read evidence: {path}") from exc


def _load_json_bytes(data: bytes, *, source: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecoveryEvidenceImportError(f"corrupt JSON evidence: {source}") from exc
    if not isinstance(payload, dict):
        raise RecoveryEvidenceImportError(f"evidence JSON must be an object: {source}")
    return payload


def _required(payload: Mapping[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or value == "":
        raise RecoveryEvidenceImportError(f"missing required identity: {key}")
    return value


def _parse_assignment(text: str, name: str) -> Any:
    match = re.search(rf"^{re.escape(name)}\s*=\s*(.+)$", text, re.MULTILINE)
    if not match:
        return UNKNOWN
    raw = match.group(1).strip()
    try:
        return ast.literal_eval(raw)
    except Exception:
        return raw


def _section(text: str, name: str) -> str:
    marker = f"=== {name} ==="
    start = text.find(marker)
    if start < 0:
        raise RecoveryEvidenceImportError(f"missing raw evidence section: {name}")
    start += len(marker)
    end = text.find("\n=== ", start)
    return text[start:] if end < 0 else text[start:end]


def _section_json(text: str, name: str) -> dict[str, Any]:
    section = _section(text, name)
    start = section.find("{")
    if start < 0:
        raise RecoveryEvidenceImportError(
            f"missing JSON object in raw evidence section: {name}"
        )
    try:
        value, _ = json.JSONDecoder().raw_decode(section[start:])
    except json.JSONDecodeError as exc:
        raise RecoveryEvidenceImportError(
            f"malformed JSON in raw evidence section: {name}"
        ) from exc
    if not isinstance(value, dict):
        raise RecoveryEvidenceImportError(
            f"raw evidence section JSON must be an object: {name}"
        )
    return value


def _controller_states(text: str, name: str) -> dict[str, str]:
    section = _section(text, name)
    states: dict[str, str] = {}
    for line in section.splitlines():
        match = re.match(
            r"^(\S+_controller)\s+\S+\s+(active|inactive)\s*$",
            line.strip(),
        )
        if match:
            states[match.group(1)] = match.group(2)
    required = {
        "forward_position_controller",
        "scaled_joint_trajectory_controller",
        "passthrough_trajectory_controller",
        "force_mode_controller",
        "freedrive_mode_controller",
    }
    if set(states) != required:
        raise RecoveryEvidenceImportError(
            f"incomplete controller state evidence in section: {name}"
        )
    return states


@dataclass(frozen=True)
class Ur3VisualServoingRecoveryEvidenceImporter:
    """Read-only importer for explicit tracked real recovery evidence only."""

    provider_commit: str
    source_repository: str = SOURCE_REPOSITORY

    def __post_init__(self) -> None:
        validate_commit(self.provider_commit, "provider_commit", allow_unknown=False)

    def import_run_manifest(
        self,
        run_path: str | Path,
        *,
        provider_root: str | Path | None = None,
    ) -> tuple[RecoveryExperienceRecord, ...]:
        path = Path(run_path).absolute()
        root = Path(provider_root).resolve() if provider_root is not None else path.parents[2].resolve()
        path = contained_path(root, path, RecoveryEvidenceImportError)
        manifest_raw = _read(path)
        manifest = _load_json_bytes(manifest_raw, source=str(path))
        experiment_id = str(_required(manifest, "experiment_id"))
        repository = str(_required(manifest, "repository"))
        if repository != self.source_repository:
            raise RecoveryEvidenceImportError(
                f"unexpected source repository: {repository} != {self.source_repository}"
            )
        milestone = str(_required(manifest, "milestone"))
        if milestone != "CANONICAL_READY_STALE_FORCE_PASSTHROUGH_AUTO_CLEANUP":
            raise RecoveryEvidenceImportError(
                f"unsupported recovery evidence family: {milestone}"
            )
        manifest_rel = path.relative_to(root).as_posix()
        return self._import_ready_stale_cleanup_recovery(
            manifest=manifest,
            manifest_raw=manifest_raw,
            manifest_rel=manifest_rel,
            root=root,
            experiment_id=experiment_id,
        )

    def _import_ready_stale_cleanup_recovery(
        self,
        *,
        manifest: Mapping[str, Any],
        manifest_raw: bytes,
        manifest_rel: str,
        root: Path,
        experiment_id: str,
    ) -> tuple[RecoveryExperienceRecord, ...]:
        raw_evidence = manifest.get("raw_evidence")
        if not isinstance(raw_evidence, list) or len(raw_evidence) != 1:
            raise RecoveryEvidenceImportError(
                "READY stale-cleanup recovery requires exactly one tracked raw transcript"
            )
        transcript_rel = str(raw_evidence[0])
        if not transcript_rel.startswith("evidence/logs/"):
            raise RecoveryEvidenceImportError(
                "recovery raw evidence must be a tracked evidence/logs path"
            )
        validate_raw_paths(root, raw_evidence, RecoveryEvidenceImportError)
        transcript_raw = _read(contained_path(root, root / transcript_rel, RecoveryEvidenceImportError))
        try:
            transcript = transcript_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RecoveryEvidenceImportError(
                "recovery raw transcript is not UTF-8"
            ) from exc

        metrics = manifest.get("metrics")
        verified = manifest.get("verified")
        if not isinstance(metrics, dict) or not isinstance(verified, list):
            raise RecoveryEvidenceImportError("recovery manifest fields are malformed")

        required_verified = {
            "check-only READY detects the stale pair as PA-READY-818 without mutating controller state",
            "READY --execute cleans the exact stale pair and returns PA-000",
            "passthrough_trajectory_controller and force_mode_controller are inactive after cleanup",
            "final check-only READY returns PA-000",
        }
        if not required_verified.issubset(set(str(item) for item in verified)):
            raise RecoveryEvidenceImportError(
                "recovery manifest is missing required explicit verification"
            )

        if transcript.count("=== EXECUTE AUTO CLEANUP ===") != 1:
            raise RecoveryEvidenceImportError(
                "expected exactly one recovery execution in raw transcript"
            )
        if _parse_assignment(transcript, "HAS_STALE_CLEANUP") is not True:
            raise RecoveryEvidenceImportError(
                "raw transcript does not identify stale cleanup support"
            )
        if _parse_assignment(transcript, "STALE_PAIR_REPRODUCED") != "YES":
            raise RecoveryEvidenceImportError(
                "raw transcript does not reproduce the exact stale pair"
            )

        failure_payload = _section_json(transcript, "CHECK-ONLY MUST FAIL CLOSED")
        execute_payload = _section_json(transcript, "EXECUTE AUTO CLEANUP")
        final_payload = _section_json(transcript, "FINAL READY")
        failure_states = _controller_states(transcript, "STALE PAIR CONFIRM")
        post_states = _controller_states(transcript, "POST CONTROLLERS")

        if failure_payload != {
            "code": READY_STALE_FAILURE_CODE,
            "first_blocker": READY_STALE_FAILURE_ATTRIBUTION,
            "mode": "CHECK_ONLY",
            "next_action": "LEAVE_CONTROLLER_UNCHANGED",
            "physical_action": "NO",
            "ready": False,
            "status": "BUSY",
        }:
            raise RecoveryEvidenceImportError(
                "raw recovery failure payload is not the supported PA-READY-818 state"
            )
        if execute_payload.get("code") != "PA-000" or execute_payload.get("ready") is not True:
            raise RecoveryEvidenceImportError(
                "raw recovery execute result is not READY/PA-000"
            )
        if execute_payload.get("mode") != "EXECUTE" or execute_payload.get("physical_action") != "YES":
            raise RecoveryEvidenceImportError("raw recovery execute semantics are malformed")
        if _parse_assignment(_section(transcript, "EXECUTE AUTO CLEANUP"), "EXEC_RC") != 0:
            raise RecoveryEvidenceImportError("raw recovery execution did not return zero")
        if final_payload.get("code") != "PA-000" or final_payload.get("ready") is not True:
            raise RecoveryEvidenceImportError("raw final READY check did not pass")
        if _parse_assignment(_section(transcript, "FINAL READY"), "FINAL_RC") != 0:
            raise RecoveryEvidenceImportError("raw final READY check returned nonzero")
        if "program_running=True" not in _section(transcript, "POST PROGRAM"):
            raise RecoveryEvidenceImportError(
                "raw transcript does not preserve program_running=true"
            )

        expected_failure_states = {
            "forward_position_controller": "inactive",
            "scaled_joint_trajectory_controller": "inactive",
            "passthrough_trajectory_controller": "active",
            "force_mode_controller": "active",
            "freedrive_mode_controller": "inactive",
        }
        expected_post_states = {name: "inactive" for name in expected_failure_states}
        if failure_states != expected_failure_states:
            raise RecoveryEvidenceImportError(
                "raw stale controller state does not match supported recovery context"
            )
        if post_states != expected_post_states:
            raise RecoveryEvidenceImportError(
                "raw post-recovery controller state is not canonical inactive"
            )

        if manifest.get("result") != "PASS" or manifest.get("physical_action") is not True:
            raise RecoveryEvidenceImportError(
                "manifest does not identify a real passing recovery execution"
            )
        manifest_checks = {
            "stale_pair_reproduced": True,
            "check_only_code": READY_STALE_FAILURE_CODE,
            "execute_code": "PA-000",
            "execute_rc": 0,
            "post_program_running": True,
            "post_passthrough_trajectory_controller": "inactive",
            "post_force_mode_controller": "inactive",
            "final_ready_code": "PA-000",
            "final_rc": 0,
        }
        for key, expected in manifest_checks.items():
            if metrics.get(key) != expected:
                raise RecoveryEvidenceImportError(f"manifest/raw recovery mismatch: {key}")

        state_context = {
            "experience_family": "READY_STALE_FORCE_PASSTHROUGH_RECOVERY",
            **failure_states,
        }
        transcript_artifact = SourceArtifact(transcript_rel, _sha256(transcript_raw))
        provenance = Provenance(
            source_repository=self.source_repository,
            source_commit=self.provider_commit,
            artifact_snapshot_commit=self.provider_commit,
            experiment_runtime_commit=runtime_commit(manifest.get("commit")),
            source_path=manifest_rel,
            source_record_id=experiment_id,
            raw_sha256=_sha256(manifest_raw),
            schema_version=RUN_MANIFEST_SCHEMA,
            importer_version=RECOVERY_IMPORTER_VERSION,
            related_sources=(transcript_artifact,),
        )
        provenance.validate()

        record = RecoveryExperienceRecord(
            goal_predicate=READY_RECOVERY_GOAL,
            state_context=state_context,
            failure_code=READY_STALE_FAILURE_CODE,
            failure_attribution=READY_STALE_FAILURE_ATTRIBUTION,
            recovery_action=READY_STALE_RECOVERY_ACTION,
            recovery_success=True,
            cost=1.0,
            cost_semantics=OBSERVED_COST,
            cost_unit="RECOVERY_EXECUTION_COUNT",
            experience_id=f"{self.source_repository}:{experiment_id}:RECOVERY",
            provenance=provenance,
            metrics={
                "recovery_execution_count": 1,
                "cost_semantics": "RECOVERY_EXECUTION_COUNT",
                "failure_payload": failure_payload,
                "execute_payload": execute_payload,
                "final_payload": final_payload,
                "controller_state_before_recovery": failure_states,
                "controller_state_after_recovery": post_states,
                "experiment_id": experiment_id,
                "timestamp": manifest.get("timestamp", UNKNOWN),
                "source_schema_version": RUN_MANIFEST_SCHEMA,
                "manifest_commit": manifest.get("commit", UNKNOWN),
                "manifest_branch": manifest.get("branch", UNKNOWN),
                "manifest_gate": manifest.get("gate", UNKNOWN),
            },
        )
        record.validate()
        return (record,)
