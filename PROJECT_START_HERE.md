# Physical AI Skill Intelligence — Start Here

This repository's latest authoritative `main` is the shared project source of
truth for Reviewer GPT, Execution GPT, Research GPT, Codex, agents, and people.
The workflow lives in this repository; it does not depend on external ChatGPT
Project Instructions, Knowledge files, or chat memory.

Before substantial project work, inspect the latest repository state and read:

1. [VERIFICATION_REPORT.txt](VERIFICATION_REPORT.txt)
2. [docs/VERIFICATION_STATUS.md](docs/VERIFICATION_STATUS.md)
3. [docs/PROJECT_HISTORY.md](docs/PROJECT_HISTORY.md)

## Authority

- `VERIFICATION_REPORT.txt` = authoritative current verification claim ledger.
- `docs/VERIFICATION_STATUS.md` = current milestone / gate state.
- `docs/PROJECT_HISTORY.md` = chronological decision history: what changed, why,
  evidence, unresolved items, and next gate.

Git commit history and preserved experiments/manifests provide underlying
provenance. Historical reports and test counts describe their recorded snapshots;
they cannot override the current claim ledger. If source, historical reports,
and current claims differ, report the discrepancy with commit evidence instead
of silently reconciling it or inferring a new verification status.

## Continuity

Do not restart project reasoning from scratch because this is a new GPT, chat,
or agent session. Preserve and respect existing:

- VERIFIED, NOT_VERIFIED, UNKNOWN, and UNRESOLVED;
- DO_NOT_REIMPLEMENT boundaries;
- rejected/superseded approaches;
- milestone closures;
- evidence provenance;
- the current next gate.

Do not silently upgrade a claim without supporting repository or physical
evidence. Provider software success does not establish physical task success.

## GitHub-first rule

Before proposing or implementing substantial work:

1. Inspect latest authoritative `main` at
   [SportyRain/physical_ai_skill_intelligence](https://github.com/SportyRain/physical_ai_skill_intelligence/tree/main).
2. Read the current verification/status/history at that same commit.
3. Inspect relevant source/tests/evidence and record the inspected commit SHA.
4. Continue from the current project state instead of rebuilding prior reasoning.

With a local checkout, inspect `git status --short --branch` first. On a clean
checkout, synchronize with `git switch main` and `git pull --ff-only`, then record
`git rev-parse HEAD`. Verify the live remote with
`git ls-remote origin refs/heads/main`; a cached `origin/main` alone does not prove
freshness. If the remote advances, refresh the relevant context before proceeding.
Preserve dirty changes and divergent work: do not reset, discard, force-push, or
rewrite history to synchronize. Inspect remote source separately when switching
would disrupt work, and state the relationship of the working branch to main.

Without a shell, use GitHub access to inspect main and then read the documents
and relevant files at its resolved SHA. If remote access is unavailable, request
the exact SHA and required repository outputs from the user, continue independent
analysis, and state that freshness is unconfirmed until evidence arrives. A local
download or previous conversation is not proof of latest main. Repository rules
make the entry point discoverable; an external GPT must actually read it for the
workflow to apply.

## Live robot collaboration

If live Ubuntu/UR3/sensor/device/runtime access is required but unavailable to the
current GPT/agent, do not stop merely because direct access is unavailable.

If the user can perform the operation:

- provide exact commands, minimal execution steps, and required observations;
- ask the user to return the actual output, state, logs, and evidence;
- continue the next verification Gate from that evidence;
- continue source investigation, analysis, judgment, and command preparation
  independently where possible.

Do not mark the result VERIFIED before actual evidence exists. Existing scope,
execution authorization, and physical safety gates still apply.

## History maintenance

Update `docs/PROJECT_HISTORY.md` when:

- a milestone closes;
- a verification gate materially changes;
- an important architecture/project boundary is decided;
- a NOT_VERIFIED/UNKNOWN claim materially changes;
- an important approach fails or is rejected;
- new evidence changes the project's next direction.

Do not log routine formatting or minor refactors. Append decisions chronologically;
do not rewrite historical entries except for explicit, evidence-backed factual
corrections. Preserve superseded decisions and explain what superseded them.

`VERIFICATION_REPORT.txt` remains authoritative for verification claims.
History must never override the claim ledger.
