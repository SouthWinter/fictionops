# Workflow Reference

## AI-Native Chapter Cycle

1. Inspect current state with `agent-next`, `doctor`, and the book/chapter outline.
2. Build a task bundle with `draft-brief`, `context-pack`, or `agent-run`.
3. Execute with a real model runner, such as `examples/agent_runner_openai_chat.py`, configured through environment variables.
4. Stage results under the FictionOps agent run directory.
5. Review staged outputs through `agent-inbox`.
6. Apply accepted changes and run post-draft or review gates.

## Revision Cycle

1. Identify concrete problems through audits or user notes.
2. Use `revision-plan` or `workflow-plan` to separate structural fixes from prose fixes.
3. Ask the runner for a scoped patch or rewrite plan.
4. Keep rejected alternatives in notes only when they explain a future constraint.

## Publishing Cycle

1. Run `export-clean`.
2. Run `audit-publish`, `export-metadata`, `export-manifest`, and `export-epub`.
3. Run `audit-epub` and `release-gate`.
4. Record release evidence when publishing or dry-running a package.
