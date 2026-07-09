# API Agent Adapter

This directory sketches a platform-neutral contract for external AI agents that want to use FictionOps as a long-form writing harness.

The current files are a contract draft, not a production web server. They define how a controller, hosted agent, IDE extension, or web app could talk to FictionOps without depending on Codex-specific behavior.

## Shape

- `openapi.yaml` defines the first HTTP surface.
- `schemas/` contains reusable JSON Schemas for goals, sessions, and staged outputs.
- `examples/` contains minimal request/response examples.

## Design Principles

- AI APIs are expected for normal use; no-model flows are only for smoke tests and recovery.
- The API should produce staged outputs, not silently mutate final manuscript files.
- Human-governed acceptance is the default decision mode.
- Provider credentials belong in deployment secrets, not in project files.

## Typical Flow

1. Create a session with a writing goal.
2. Ask the agent to write, revise, or audit a chapter.
3. Receive staged outputs plus metrics and review requirements.
4. Submit a human decision: accept, reject, or request revision.
5. Run FictionOps audits before applying or publishing.
