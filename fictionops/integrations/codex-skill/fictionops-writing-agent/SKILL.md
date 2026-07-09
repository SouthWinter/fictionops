---
name: fictionops-writing-agent
description: Use when working inside a FictionOps long-form writing project to run AI-native chapter writing, revision, audit, publishing-prep, dogfood, and staged human-review workflows through the FictionOps CLI and model/API runners.
---

# FictionOps Writing Agent

Use FictionOps as the project harness. Keep manuscript and canon edits reviewable: generate task packages, run or call a model runner, stage outputs, inspect the inbox, then apply accepted changes deliberately.

## First Checks

1. Confirm the current project is a FictionOps project by locating `project.yml` or the standard FictionOps folders.
2. Run `fictionops doctor <project> --book <book>` when project health matters before drafting.
3. Prefer a real OpenAI-compatible provider when credentials are available. Use echo/no-model runners only for smoke tests, CI, or debugging.
4. Never place API keys in project files. Use environment variables such as `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, or provider-specific equivalents.

## Core Loop

1. Prepare: run `model-config`, `agent-next`, `scene-plan`, or `draft-brief` as needed.
2. Package: run `agent-run` or `context-pack` to create a bounded task.
3. Execute: run `agent-exec` with a configured runner, or hand the task to an external model/API controller.
4. Review: run `agent-inbox`, inspect staged outputs, then apply only accepted material.
5. Verify: run relevant audits such as `review-gate`, `audit-continuity`, `audit-info`, `audit-characters`, `audit-style`, or `doctor`.
6. Record: update retrospective or dogfood evidence when the workflow produces a meaningful acceptance/rejection decision.

## Reference Routing

- For chapter drafting or revision, read `references/chapter-writing.md`.
- For audit and review-gate work, read `references/audit.md`.
- For end-to-end workflow sequencing, read `references/workflow.md`.
- For research, interview, or project-quality evidence, read `references/dogfood-metrics.md`.

## Guardrails

- Do not overwrite canon, outlines, or final manuscript files from raw model output.
- Do not treat model confidence as acceptance. The user or a review gate must decide.
- Keep context packs small enough that the model sees only relevant canon, scene goals, information boundaries, and voice constraints.
- Preserve uncertainty: when a chapter depends on unknown canon, stage a question or TODO instead of inventing permanent truth.
