---
name: fictionops-writing-agent
description: Use when working in a FictionOps long-form writing project to write or revise chapters with AI, resume interrupted sessions, inspect persistent issues, run audits, prepare publishing, or collect dogfood evidence through the unified FictionOps agent runtime.
---

# FictionOps Writing Agent

Use the installed FictionOps CLI as the project harness. Prefer the unified stateful runtime; use lower-level bundle commands only for research/debugging or tasks not exposed by `fictionops agent`.

## First Checks

1. Locate the project root, active chapter/engine, and any existing run `session.json` before creating a new run.
2. Run `fictionops doctor <project> --book <book>` when structural health affects the task.
3. Use a real configured runner for normal writing. Echo/no-model runners are only for tests or recovery diagnosis.
4. Keep API keys in environment variables or a user-private env file outside the repository.

## Core Loop

1. Write: use `fictionops agent write <chapter> --engine <engine> ... --runner <command>`.
2. Revise: use `fictionops agent revise <chapter> ... --runner <command>`.
3. Recover: inspect `checkpoint.json`; use `fictionops agent resume <run-dir> ... --runner <command>` only when the checkpoint is resumable. Put `--runner` last.
4. Review: inspect the candidate, diff, verification, issue ledger, and token/cost budget. Never infer approval from model confidence.
5. Decide: record issue decisions with `agent issue`; run `agent accept <run-dir>` only after the user explicitly approves applying the verified candidate.
6. Verify and record: rerun relevant gates and retain meaningful acceptance/rejection evidence.

## Reference Routing

- For chapter drafting or revision, read `references/chapter-writing.md`.
- For audit and review-gate work, read `references/audit.md`.
- For end-to-end workflow sequencing, read `references/workflow.md`.
- For research, interview, or project-quality evidence, read `references/dogfood-metrics.md`.

## Guardrails

- Do not overwrite canon, outlines, or final manuscript files from raw model output.
- Do not call `agent accept` merely because a candidate is `ready_for_approval`; that state means eligible for author review, not accepted.
- Do not bypass stale source/artifact hashes or resume unsupported/cancelled checkpoints.
- Set call/runtime and, when telemetry is available, token/cost budgets for real API runs.
- Do not treat model confidence as acceptance. The user or a review gate must decide.
- Keep context packs small enough that the model sees only relevant canon, scene goals, information boundaries, and voice constraints.
- Preserve uncertainty: when a chapter depends on unknown canon, stage a question or TODO instead of inventing permanent truth.
