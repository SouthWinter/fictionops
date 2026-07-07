# Stable Core Audit

This audit tracks whether FictionOps is ready to call itself a 1.0 stable core. It is intentionally stricter than the local test suite: tests can prove current behavior, but 1.0 also needs release evidence and time-tested compatibility.

Current result: **not complete**.

Machine-checkable aggregate gate: run `fictionops audit-stability-window . --file docs/stability-window-evidence.md --format json`, then run `fictionops audit-stable-core . --format json`. The aggregate command must report `ready=true` before this document and the milestone ledger can honestly mark 1.0 complete. Its JSON also includes structured `action_items` for external runners or human maintainers; those items are a handoff plan, not proof that the work has happened.

Execution handoff: use `docs/stable-core-remaining-checklist.md` for the concrete 1.0 remaining execution checklist. That checklist separates local maintenance from the external release, dogfood, and stability evidence that must happen before this audit can close.

## Evidence Matrix

| Requirement | Current Evidence | Status | Remaining Proof |
| --- | --- | --- | --- |
| Command names and core JSON keys are stable | `docs/cli-contracts.md`, `docs/compatibility.md`, CLI help coverage, JSON parsing tests, controller guidance. | Locally strong | Needs a compatibility window where changes are tracked without silent contract drift. |
| Compatibility policy is maintained | `docs/compatibility.md`, `docs/compatibility.zh-CN.md`, `CHANGELOG.md`, release notes, release governance tests. | Locally strong | Future behavior changes must continue updating these records. |
| Unsafe overwrites are consistently refused | Regression tests cover no-overwrite behavior across CLI report/output commands, staged agent output, package artifacts, and project scaffolding. | Locally strong | Keep adding no-overwrite tests for new write commands. |
| Release gates catch stale or missing publish artifacts | `release-gate`, `audit-publish`, `export-metadata`, `export-manifest`, `export-epub`, `audit-epub`, and tests for missing/stale/invalid artifacts. | Locally strong | Continue using these gates before every publish attempt. |
| Agent workflows remain staged and auditable | `agent-connect`, `agent-smoke`, `agent-run`, `agent-exec`, `agent-inbox`, `agent-next`, `examples/agent_controller_loop.py`, `docs/agent-connector-contract.md`, and controller tests. | Locally strong | Real model/controller integrations remain optional but must preserve staged output and review gates. |
| Migration from messy legacy projects has sustained real-project proof | `docs/dogfood-legacy-adopt.zh-CN.md` records 0.2 closure, and `docs/dogfood-cycle-evidence.md` plus `audit-dogfood-cycle` define the sustained-cycle evidence gate. | Partially proven | 1.0 still needs a filled accepted post-closure maintenance cycle that passes `audit-dogfood-cycle`. |
| Recovery paths remain current | `docs/recovery.md`, `docs/recovery.zh-CN.md`, known-limits docs, compatibility policy, release evidence tests. | Locally strong | Recovery docs must be updated whenever commands can create, repair, regenerate, or invalidate durable state. |
| Package release evidence exists outside the local checkout | Local wheel/sdist builds, CI/publish workflows, accepted `docs/release-trial-evidence.md`, GitHub Actions run `28837872185`, TestPyPI `fictionops==0.1.0`, clean venv install smoke, and `audit-release-evidence` reporting `ready=true`. | Complete with external evidence | Keep future release trials recorded with real run URLs, package hashes, install smoke, reviewer, and decision. |
| Stable behavior over time | Milestone ledger, compatibility policy, release notes, regression tests, `docs/stability-window-evidence.md`, `audit-stability-window`, and `audit-stable-core`. | Not yet provable | Needs an accepted stability-window record showing elapsed real use without undocumented breaking changes. |

## Current Local Conclusion

The local repository has enough evidence to say:

- 0.1.0 pre-alpha MVP is locally complete.
- 0.2 migration dogfood is locally complete.
- 0.3 no-model controller orchestration is locally complete.
- 0.4 release trial is complete with accepted external evidence.
- 0.5 documentation parity is locally complete.
- 1.0 stable core is not complete.

## 1.0 Blockers

Do not mark 1.0 complete until all of these are true:

1. At least one sustained real-project dogfood cycle after the 0.2 migration closure is recorded and passes `audit-dogfood-cycle`.
2. Compatibility-sensitive behavior has stayed stable across that cycle, or every breaking change has an explicit migration path, recorded in `docs/stability-window-evidence.md` and passing `audit-stability-window`.
3. Recovery docs remain current with all commands that create, repair, regenerate, publish, or invalidate durable project state.
4. `fictionops audit-stable-core .` reports `ready=true`.

## Action Item Contract

`audit-stable-core --format json` exposes one action item for each 1.0 evidence lane:

- `local-foundation`: local governance files, workflows, docs, and tests exist.
- `release-trial-evidence`: external package release evidence is filled and accepted.
- `sustained-dogfood-cycle`: a real post-migration maintenance cycle is filled and accepted.
- `stability-window`: elapsed compatibility behavior is filled and accepted.
- `stable-core-ledger`: stable-core and milestone docs honestly claim completion after the evidence is ready.

Action item statuses such as `external_required` or `docs_update_required` are instructions for the next actor. They must not be treated as evidence. The linked audit command in each item is the acceptance test.

## Audit Rule

If a future change touches CLI command names, required arguments, core JSON keys, overwrite behavior, package contents, release flow, agent staging, or recovery paths, update this audit together with compatibility docs, milestone status, release notes, and tests.
