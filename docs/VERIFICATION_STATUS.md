# Verification Status

The canonical current claim ledger is [VERIFICATION_REPORT.txt](../VERIFICATION_REPORT.txt).
Current test counts and commands are in [TEST_RESULTS.txt](../TEST_RESULTS.txt).
This index intentionally does not maintain a second independent claim table.

M1–M6 and M6.1 are closed at the M7 base commit, per the current task's authority.
M7 software provider integration passed reviewer audit and is closed on `main`.
The approved commit `5d7581275c7af6ee9f9c0773bf04ea5e290083f2` was merged and pushed by fast-forward only.

```text
AUTHORITATIVE_BRANCH = main
M7_REVIEW = PASS
M7_STATUS = CLOSED
```

See [M7 verification](MILESTONE_7_VERIFICATION.md)
for the exact committed provider source, input contract, actual callable tests,
and the limits of the software result. Finalization changes documentation only; M7.1, M8, and real UR3 work are not started.

The existing M5 runtime recovery evidence remains historical preserved evidence;
M7 performs no robot execution or runtime recovery. Real UR3 execution/adapter,
real recovery adapter, timeout/cancel/wall-clock bounds, decision superiority,
and learning claims remain NOT_VERIFIED as recorded in the canonical ledger.
`RUNTIME_PROVIDER_SOURCE_ATTESTATION`, `REAL_PROVIDER_FAILURE_RETRYABILITY`, and
`REAL_PROVIDER_COST` also remain NOT_VERIFIED. Software source tests do not
establish runtime source attestation, physical failure retryability, or cost.

Milestone reports M1–M6.1 describe their historical verification runs. Their
historical counts and pending-review statements are not current status overrides.
