# FictionOps Integrations

This directory holds adapter drafts for turning the FictionOps file-based harness into AI-native writing workflows.

FictionOps core should stay stable and local: it owns project structure, task packages, staged outputs, audits, and review gates. Integrations own how an AI system enters that harness.

## Adapters

- `codex-skill/` packages FictionOps as a Codex Skill. It is optimized for an agent already working inside a local writing repository.
- `api-agent/` sketches a platform-neutral API contract for external controllers, web apps, or hosted agent services.

Both adapters share the same principle: AI can propose, draft, revise, and audit, but manuscript and canon changes should pass through staged outputs and human-governed acceptance.

## Boundary

- Keep secrets outside this repository. Use environment variables or external secret stores.
- Treat echo/no-model runners as smoke-test tools only.
- Prefer real model APIs for dogfood and evaluation when provider credentials are available.
- Keep adapter-specific ergonomics here; keep reusable CLI behavior in `src/fictionops/`.
