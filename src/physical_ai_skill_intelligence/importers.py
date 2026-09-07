from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .experience import ExperienceRecord, UNKNOWN
from .provenance import Provenance, SourceArtifact

IMPORTER_VERSION = "ur3_visual_servoing_evidence_v1"
SOURCE_REPOSITORY = "SportyRain/ur3_visual_servoing"
RUN_MANIFEST_SCHEMA = "UNVERSIONED_RUN_MANIFEST"


class EvidenceImportError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvidenceImportError(f"failed to read evidence: {path}") from exc


def _load_json_bytes(data: bytes, *, source: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceImportError(f"corrupt JSON evidence: {source}") from exc
    if not isinstance(payload, dict):
        raise EvidenceImportError(f"evidence JSON must be an object: {source}")
    return payload


def _required(payload: Mapping[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or value == "":
        raise EvidenceImportError(f"missing required identity: {key}")
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


def _parse_push_summary_jsons(text: str) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(payload, dict)
            and "attempt_count" in payload
            and "first_commanded_push_distance_m" in payload
            and "status" in payload
        ):
            summaries.append(payload)
    if len(summaries) != 2:
        raise EvidenceImportError(
            f"expected exactly two real Push trial summaries, got {len(summaries)}"
        )
    return summaries


@dataclass(frozen=True)
class Ur3VisualServoingEvidenceImporter:
    """Read-only deterministic importer for tracked provider evidence snapshots."""

    provider_commit: str
    source_repository: str = SOURCE_REPOSITORY

    def import_run_manifest(
        self,
        run_path: str | Path,
        *,
        provider_root: str | Path | None = None,
    ) -> tuple[ExperienceRecord, ...]:
        path = Path(run_path)
        root = Path(provider_root) if provider_root is not None else path.parents[2]
        raw = _read(path)
        manifest = _load_json_bytes(raw, source=str(path))
        experiment_id = str(_required(manifest, "experiment_id"))
        repository = str(_required(manifest, "repository"))
        if repository != self.source_repository:
            raise EvidenceImportError(
                f"unexpected source repository: {repository} != {self.source_repository}"
            )
        milestone = str(_required(manifest, "milestone"))
        source_rel = path.relative_to(root).as_posix()

        if milestone == "REAL_GOAL_DIRECTED_CONTINUOUS_PUSH_INTER_TRIAL_LEARNING":
            return self._import_push(
                manifest=manifest,
                manifest_raw=raw,
                manifest_rel=source_rel,
                root=root,
                experiment_id=experiment_id,
            )
        if milestone == "REAL_UR3_PICK_PLACE_FIRST_RUN":
            return self._import_pick_place(
                manifest=manifest,
                manifest_raw=raw,
                manifest_rel=source_rel,
                experiment_id=experiment_id,
            )
        raise EvidenceImportError(f"unsupported evidence family: {milestone}")

    def _base_provenance(
        self,
        *,
        manifest: Mapping[str, Any],
        manifest_raw: bytes,
        manifest_rel: str,
        source_record_id: str,
        related: tuple[SourceArtifact, ...] = (),
    ) -> Provenance:
        provenance = Provenance(
            source_repository=self.source_repository,
            source_commit=self.provider_commit,
            source_path=manifest_rel,
            source_record_id=source_record_id,
            raw_sha256=_sha256(manifest_raw),
            schema_version=RUN_MANIFEST_SCHEMA,
            importer_version=IMPORTER_VERSION,
            related_sources=related,
        )
        provenance.validate()
        return provenance

    def _import_push(
        self,
        *,
        manifest: Mapping[str, Any],
        manifest_raw: bytes,
        manifest_rel: str,
        root: Path,
        experiment_id: str,
    ) -> tuple[ExperienceRecord, ...]:
        raw_evidence = manifest.get("raw_evidence")
        if not isinstance(raw_evidence, list) or not raw_evidence:
            raise EvidenceImportError("Push manifest is missing raw_evidence links")

        readback_rel = next(
            (str(p) for p in raw_evidence if "experience_readback" in str(p)), None
        )
        if readback_rel is None:
            raise EvidenceImportError("Push experience readback link is missing")
        readback_raw = _read(root / readback_rel)
        try:
            readback = readback_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvidenceImportError("Push experience readback is not UTF-8") from exc

        context_raw = _parse_assignment(readback, "CONTEXT_KEY")
        if not isinstance(context_raw, dict):
            raise EvidenceImportError("Push CONTEXT_KEY is missing or malformed")

        metrics = manifest.get("metrics")
        verified = manifest.get("verified")
        if not isinstance(metrics, dict) or not isinstance(verified, list):
            raise EvidenceImportError("Push manifest fields are malformed")
        if metrics.get("action_changed_from_trial1") is not True:
            raise EvidenceImportError("Push manifest does not explicitly verify action change")
        if "TRIAL2_EXPERIENCE_LOADED_TO_CHANGE_FIRST_ACTION" not in verified:
            raise EvidenceImportError("Push manifest does not verify experience-conditioned Trial 2")

        direction = metrics.get("direction", UNKNOWN)
        relative_goal = metrics.get("relative_goal_displacement_m", UNKNOWN)
        tolerance = metrics.get("goal_tolerance_m", UNKNOWN)
        if not isinstance(tolerance, (int, float)) or tolerance < 0:
            raise EvidenceImportError("invalid Push goal tolerance")

        context = {
            "experience_family": "GOAL_DIRECTED_CONTINUOUS_PUSH",
            "direction": direction,
            "relative_goal_displacement_m": relative_goal,
            "goal_tolerance_m": tolerance,
            "provider_experience_context": context_raw,
            "object_identity": UNKNOWN,
            "target_identity": UNKNOWN,
            "scene_identity": UNKNOWN,
        }
        related = (SourceArtifact(readback_rel, _sha256(readback_raw)),)
        strategies = ("nominal_baseline", "experience_adapted")
        skill_names = (
            "goal_directed_continuous_push/nominal_baseline",
            "goal_directed_continuous_push/experience_adapted",
        )

        out: list[ExperienceRecord] = []
        for idx in (1, 2):
            attempt_count = metrics.get(f"trial{idx}_attempt_count")
            final_error = metrics.get(f"trial{idx}_final_goal_error_m")
            first_action = metrics.get(f"trial{idx}_first_action_m")
            if not isinstance(attempt_count, int) or attempt_count <= 0:
                raise EvidenceImportError(f"invalid Push trial{idx}_attempt_count")
            if not isinstance(final_error, (int, float)) or final_error < 0:
                raise EvidenceImportError(f"invalid Push trial{idx}_final_goal_error_m")
            if not isinstance(first_action, (int, float)) or first_action <= 0:
                raise EvidenceImportError(f"invalid Push trial{idx}_first_action_m")

            # Explicit, inspectable derivation from two raw manifest metrics.
            # This is intentionally recorded in physical_outcome; it is not a silent guess.
            task_success = float(final_error) <= float(tolerance)
            effective_action = (
                metrics.get("nominal_baseline_push_distance_m", UNKNOWN)
                if idx == 1
                else metrics.get("trial2_effective_push_distance_m", UNKNOWN)
            )
            trial_id = f"{experiment_id}:TRIAL_{idx}"
            experience_id = f"{self.source_repository}:{experiment_id}:TRIAL_{idx}"
            record = ExperienceRecord(
                goal_predicate="RELATIVE_DISPLACEMENT",
                state_context=dict(context),
                skill_name=skill_names[idx - 1],
                success=task_success,
                cost=float(attempt_count),
                failure_code=None if task_success else "FINAL_GOAL_ERROR_EXCEEDS_TOLERANCE",
                metrics={
                    "attempt_count": attempt_count,
                    "final_goal_error_m": final_error,
                    "first_commanded_push_distance_m": first_action,
                    "effective_push_distance_m": effective_action,
                    "hard_max_push_distance_m": metrics.get("hard_max_push_distance_m", UNKNOWN),
                    "cost_semantics": "ATTEMPT_COUNT",
                },
                provenance=self._base_provenance(
                    manifest=manifest,
                    manifest_raw=manifest_raw,
                    manifest_rel=manifest_rel,
                    source_record_id=experiment_id,
                    related=related,
                ),
                experience_id=experience_id,
                experiment_id=experiment_id,
                trial_id=trial_id,
                attempt_id=UNKNOWN,
                goal_semantics={
                    "predicate": "RELATIVE_DISPLACEMENT",
                    "direction": direction,
                    "relative_goal_displacement_m": relative_goal,
                    "goal_tolerance_m": tolerance,
                },
                state_before={"object_xy_m": UNKNOWN, "target_xy_m": UNKNOWN},
                state_after={"object_xy_m": UNKNOWN},
                object_identity=UNKNOWN,
                target_identity=UNKNOWN,
                scene_context={
                    "provider_experience_context": context_raw,
                    "physical_action": manifest.get("physical_action", UNKNOWN),
                    "source_record_commit": manifest.get("commit", UNKNOWN),
                    "source_record_branch": manifest.get("branch", UNKNOWN),
                    "source_record_gate": manifest.get("gate", UNKNOWN),
                    "raw_evidence_refs": tuple(str(x) for x in raw_evidence),
                },
                strategy_name=strategies[idx - 1],
                planned_action={
                    "nominal_baseline_push_distance_m": metrics.get(
                        "nominal_baseline_push_distance_m", UNKNOWN
                    ),
                    "effective_push_distance_m": effective_action,
                },
                accepted_action={"first_commanded_push_distance_m": first_action},
                executed_action={"actual_tcp_first_action_m": UNKNOWN},
                physical_outcome={
                    "final_goal_error_m": final_error,
                    "task_success_derivation": "FINAL_GOAL_ERROR_LE_GOAL_TOLERANCE",
                },
                task_success=task_success,
                action_success=UNKNOWN,
                failure_attribution=UNKNOWN,
                recovery_action=UNKNOWN,
                timestamp=manifest.get("timestamp", UNKNOWN),
                source_schema_version=RUN_MANIFEST_SCHEMA,
                identity_required=True,
            )
            record.validate()
            out.append(record)
        return tuple(out)

    def _import_pick_place(
        self,
        *,
        manifest: Mapping[str, Any],
        manifest_raw: bytes,
        manifest_rel: str,
        experiment_id: str,
    ) -> tuple[ExperienceRecord, ...]:
        metrics = manifest.get("metrics")
        verified = manifest.get("verified")
        if not isinstance(metrics, dict) or not isinstance(verified, list):
            raise EvidenceImportError("Pick/Place manifest fields are malformed")

        success_statement = "physical Place outcome confirmed successful by the user"
        if success_statement not in verified:
            raise EvidenceImportError("Pick/Place task success is not explicitly verified")
        task_success = True

        runtime_status = metrics.get("runtime_final_status", UNKNOWN)
        action_success: bool | str
        if runtime_status == "SUCCESS":
            action_success = True
        elif runtime_status == "FAILURE":
            action_success = False
        else:
            action_success = UNKNOWN

        trial_id = experiment_id
        experience_id = f"{self.source_repository}:{experiment_id}"
        attempt_count = metrics.get("max_pick_attempts", 0)
        if not isinstance(attempt_count, int) or attempt_count < 0:
            raise EvidenceImportError("invalid Pick/Place max_pick_attempts")
        place_xyz = [
            metrics.get("place_x_m", UNKNOWN),
            metrics.get("place_y_m", UNKNOWN),
            metrics.get("place_z_m", UNKNOWN),
        ]
        context = {
            "experience_family": "PICK_PLACE",
            "target_hue": metrics.get("target_hue", UNKNOWN),
            "place_xyz_m": place_xyz,
            "physical_action": manifest.get("physical_action", UNKNOWN),
            "object_identity": UNKNOWN,
            "target_identity": UNKNOWN,
            "scene_identity": UNKNOWN,
        }
        record = ExperienceRecord(
            goal_predicate="PICK_AND_PLACE",
            state_context=context,
            skill_name="pick_place/real_runtime",
            success=task_success,
            cost=float(attempt_count),
            failure_code=(
                None
                if action_success is True
                else str(metrics.get("runtime_final_reason", UNKNOWN))
            ),
            metrics={**metrics, "cost_semantics": "MAX_PICK_ATTEMPTS"},
            provenance=self._base_provenance(
                manifest=manifest,
                manifest_raw=manifest_raw,
                manifest_rel=manifest_rel,
                source_record_id=trial_id,
            ),
            experience_id=experience_id,
            experiment_id=experiment_id,
            trial_id=trial_id,
            attempt_id=UNKNOWN,
            goal_semantics={
                "predicate": "PICK_AND_PLACE",
                "place_xyz_m": place_xyz,
            },
            state_before={"object_pose": UNKNOWN},
            state_after={"object_pose": UNKNOWN},
            object_identity=UNKNOWN,
            target_identity=UNKNOWN,
            scene_context={
                "target_hue": metrics.get("target_hue", UNKNOWN),
                "source_record_commit": manifest.get("commit", UNKNOWN),
                "source_record_branch": manifest.get("branch", UNKNOWN),
                "source_record_gate": manifest.get("gate", UNKNOWN),
                "raw_evidence_refs": tuple(str(x) for x in manifest.get("raw_evidence", ())),
            },
            strategy_name="real_pick_place_runtime",
            planned_action={"place_xyz_m": place_xyz},
            accepted_action={"pick_attachment_state": metrics.get("pick_attachment_state", UNKNOWN)},
            executed_action={"vacuum_release_and_retreat": "VERIFIED"},
            physical_outcome={
                "task_outcome": "SUCCESS_CONFIRMED_BY_USER",
                "runtime_final_status": runtime_status,
                "runtime_final_reason": metrics.get("runtime_final_reason", UNKNOWN),
            },
            task_success=task_success,
            action_success=action_success,
            failure_attribution=UNKNOWN,
            recovery_action=UNKNOWN,
            timestamp=manifest.get("timestamp", UNKNOWN),
            source_schema_version=RUN_MANIFEST_SCHEMA,
            identity_required=True,
        )
        record.validate()
        return (record,)
