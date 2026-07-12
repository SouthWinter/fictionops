# Workflow Reference

## Route The Task

| Request | Inspect first | Preferred action | Required stop |
| --- | --- | --- | --- |
| Write a new chapter | Engine, outline, adjacent chapters, active memory | `agent write` | Author review before accept |
| Revise an old chapter | Status, issues, chapter hash, guards | `agent revise` | Disputed or weakly grounded finding |
| Continue interrupted work | Session, checkpoint, budget | `agent resume` or `agent continue` | Stale/cancelled/unsupported state |
| Resolve disputed review | Packet, escalation, guards, source scope | Counterevidence workflow | Missing evidence or author decision |
| Compare teacher and API agent | Frozen task, hidden controls, trajectories | Benchmark/evidence workflow | Label leakage or non-comparable inputs |
| Publish | Gates, clean export, metadata, EPUB | Publishing cycle | Failed release gate |

## Chapter Cycle

1. Inspect status, checkpoint, chapter engine, and source hashes.
2. Run `fictionops agent write` with explicit call/runtime and, when available, token/cost budgets.
3. Inspect `candidate.md`, `changes.diff`, verification, issues, context manifest, and `model_budget.json`.
4. Resume only a supported checkpoint; do not replay completed model phases manually.
5. Show the author material changes and unresolved risks.
6. Apply only after explicit approval with `fictionops agent accept`.

## Revision Cycle

1. Separate user-reported issues, deterministic audit hits, reviewer findings, and author guards.
2. Run comprehensive revision unless the user deliberately limits scope.
3. Preserve original finding, verifier verdict, effective verdict, and issue lifecycle as distinct records.
4. Escalate `needs_counterevidence`; do not send it directly to the reviser.
5. Prefer a bounded local repair after a narrow candidate regression; stop byte-identical retries.
6. Waive, reject, reopen, or accept only with an explicit author reason.

## Publishing Cycle

1. Run `export-clean`.
2. Run `audit-publish`, `export-metadata`, `export-manifest`, and `export-epub`.
3. Run `audit-epub` and `release-gate`.
4. Record concrete release evidence; do not infer external publication from local artifacts.
