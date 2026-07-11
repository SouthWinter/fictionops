# Workflow Reference

## AI-Native Chapter Cycle

1. Inspect existing sessions/checkpoints plus `doctor` and the chapter engine.
2. Run `fictionops agent write` with a real runner and explicit budgets.
3. Review `candidate.md`, `changes.diff`, `verification.v1.json`, `issues.after.json`, and `model_budget.json`.
4. Resume a supported interrupted phase with `fictionops agent resume`; never replay completed phases manually.
5. Apply only after explicit author approval with `fictionops agent accept`.

## Revision Cycle

1. Identify concrete problems through the persistent issue ledger, audits, or user notes.
2. Run `fictionops agent revise`; default to comprehensive review unless the user deliberately scopes a style-only pass.
3. Inspect before/after issue identity, semantic invariants, and any targeted retry evidence.
4. Waive/reject/reopen issues only with an explicit author reason.

## Publishing Cycle

1. Run `export-clean`.
2. Run `audit-publish`, `export-metadata`, `export-manifest`, and `export-epub`.
3. Run `audit-epub` and `release-gate`.
4. Record release evidence when publishing or dry-running a package.
