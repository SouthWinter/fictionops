# FictionOps Roadmap

This roadmap defines what "more complete" means after the 0.1.0 pre-alpha MVP. It is intentionally evidence-based: a milestone is not done because the idea exists; it is done when the repository contains commands, docs, tests, examples, or release records that prove the behavior.

## Current Baseline

0.1.0 proves a local, file-first workflow:

- project scaffolding;
- migration diagnostics and safe copy-to-sandbox;
- import queue planning and safe application;
- chapter planning, scene planning, and drafting briefs;
- post-draft, review, book, and release gates;
- information, character, echo, style, table, wave, and continuity audits;
- scoped context packs and prepare-only agent bundles;
- external runner bridge, staged agent inbox, next-step controller primitive, and agent integration guidance;
- clean Markdown, metadata, manifest, EPUB export, and EPUB audit;
- CI, release docs, compatibility and known-limits docs, package builds, and smoke tests.

The 0.1.0 completion evidence is tracked in [completion-audit-0.1.0.zh-CN.md](completion-audit-0.1.0.zh-CN.md). Current milestone-by-milestone status is tracked in [milestone-status.md](milestone-status.md), and the stricter 1.0 evidence matrix is tracked in [stable-core-audit.md](stable-core-audit.md).

## AI-Native Direction

The next product and research direction is **AI-native by default**. FictionOps should be presented and developed as a long-form writing agent system that assumes a model API is available. No-model paths remain valuable for CI, smoke tests, debugging, reproducibility, and offline fallback, but they are no longer the main value proposition.

The target user experience should move from "many CLI building blocks that can optionally call AI" toward "an AI agent embedded in a real writing workflow":

```text
story/project state
  -> agent observes the workspace
  -> scoped context is compiled
  -> model runner produces candidate work
  -> audits/gates provide feedback
  -> controller continues or stops at a review boundary
  -> author accepts, revises, or rejects
```

The AI agent should do useful writing work by default:

- plan chapters from book outlines, character memory, and information boundaries;
- draft candidate prose or revision proposals through an OpenAI-compatible runner;
- audit information leaks, character drift, continuity, echoes, prose patterns, and release readiness;
- prepare summaries, tags, metadata, clean Markdown, EPUB artifacts, and publish checklists;
- decide safe next steps through a controller loop;
- stop when aesthetic judgment, source-of-truth changes, credentials, publishing, or external evidence require human authority.

No-model echo runners should be documented as testing infrastructure, not the primary story. The primary story is AI agent landing in a real long-form writing pipeline.

## Milestone Matrix

| Milestone | Goal | Required Evidence | Not Required Yet |
| --- | --- | --- | --- |
| 0.2.0 Migration Dogfood | Prove a real long project can move from copied legacy material to normal FictionOps project work. | A dogfood log where `adopt-review` reaches `ready_for_project_work` or every remaining blocker is explicitly recorded in `07_audits/adopt_review/waivers.json`; migration repair groups closed or deferred; import queue empty; updated docs for lessons learned. | Cloud sync, web UI, automatic literary rewriting. |
| 0.3.0 Agent Controller | Prove a controller can run a multi-step loop while preserving staged outputs and gates. | `examples/agent_controller_loop.py` can call `agent-next`, execute safe read/write commands, stop on human-review boundaries, placeholder commands, repeated suggestions, and migration-only states, and record a JSONL run log; `docs/agent-integration.md` documents runner/controller wiring; tests cover non-destructive stopping behavior. | Direct model editing of manuscript/canon. |
| 0.4.0 Release Trial | Prove external installation and publishing workflow outside the local checkout. | GitHub Actions release flow run; TestPyPI publish record if publishing is chosen; clean venv install from built package; release notes updated with the external result. | Permanent PyPI release if the project is still pre-alpha. |
| 0.5.0 Documentation Parity Pass | Make English onboarding good enough for outside contributors. | English docs cover CLI contracts, migration, agent workflow, release, testing, demo, contribution, and the end-to-end migration/publishing case in `docs/end-to-end-migration-publish.md`. | Full translation of every Chinese design note. |
| 0.6.0 AI Provider Onboarding | Make real model API setup the default first-run path. | `setup-ai` or equivalent guided command; provider presets for OpenAI-compatible APIs; `.env.example`; dry-run and real-run docs; smoke tests proving API keys stay outside project files. | Web UI, hosted accounts, automatic billing management. |
| 0.7.0 Writing Agent Commands | Wrap the multi-command writing workflow into AI-first commands. | `write-chapter`, `revise-chapter`, `audit-chapter`, or equivalent orchestration commands that call planning, brief generation, model runner execution, inbox, and audits; tests for staged output and stop behavior. | Fully autonomous acceptance into manuscript/canon. |
| 0.8.0 Agent Runtime Dogfood | Prove the AI agent improves a real writing workflow, not just infrastructure. | A real-project AI dogfood report with model/provider, tasks, acceptance rate, useful findings, prompt-prep time saved, context lookup time saved, review cost, failure cases, and recovery notes. | Public manuscript text or automated literary scoring. |
| 1.0.0 Stable Core | Freeze stable command contracts for real writers and contributors. | Maintained compatibility policy; backward-compatibility notes; full local test suite; package release; maintained known-limits document; at least one sustained real-project dogfood cycle that passes `audit-dogfood-cycle`; accepted stability-window evidence that passes `audit-stability-window`; `audit-stable-core` returns ready. | Automated quality scoring or autonomous novel authorship. |

## 0.2.0 Acceptance Checklist

0.2.0 should focus on the real-project migration path rather than adding many new commands.

- Run the legacy-to-FictionOps chain on a substantial real project sandbox.
- Clear `import_queue` items; explicitly deferred blockers belong in `07_audits/adopt_review/waivers.json`, but unsorted draft files still keep the sandbox in `needs_import_sorting`.
- Fill enough information boundary, character memory, chapter engine, and retrospective files for `adopt-review` to stop reporting migration-only blockers.
- Record every manual decision that cannot be automated safely.
- Update migration docs with the rough edges found during dogfood.
- Add regression tests for any command behavior changed because of dogfood.

Exit condition:

```text
fictionops adopt-review <sandbox> --book <book_id> --format json
```

returns a state that is either ready for normal project work or contains only documented, consciously deferred issues.

## 0.3.0 Acceptance Checklist

0.3.0 should prove agent workflow orchestration without giving the model unchecked authority.

- Add a controller example that can run more than one step.
- Require controller logs for selected command, evidence, execution result, and stopping reason.
- Stop automatically when an agent output is ready for human review.
- Stop automatically before any manuscript/canon overwrite.
- Keep `agent-exec` output staged.
- Add tests for controller behavior on missing project, import queue, ready agent output, and publish gate states.

Exit condition: a contributor can run a local controller demo and see a complete, auditable loop that never silently edits manuscript or canon. The no-model demo is acceptable as a smoke test, but later milestones must use real model APIs as the default product path.

## 0.6.0 AI Provider Onboarding Checklist

0.6.0 should make AI setup feel like the normal entry point:

- Add a guided `setup-ai` path, or an equivalent documented command sequence, for OpenAI-compatible providers.
- Support at least OpenAI, DeepSeek, Qwen/DashScope, Kimi/Moonshot, GLM/Zhipu, Doubao/Volcengine Ark, SiliconFlow, and local OpenAI-compatible servers through presets or documented configuration.
- Write `.env.example` files that contain only variable names and placeholders, never secrets.
- Provide `--dry-run` and "real call" examples side by side.
- Make the README quickstart AI-first while moving echo/no-model usage to smoke-test sections.
- Add tests that prove real API keys are not written into project files, receipts, task bundles, docs, or generated reports.

Exit condition: a new user can configure a provider, run a dry run, run a real model call, inspect staged output, and understand where the human acceptance boundary is.

## 0.7.0 Writing Agent Commands Checklist

0.7.0 should hide routine command choreography behind AI-first writing commands:

- `write-chapter`: synchronize chapter plan, build scene/brief/context, call a drafting runner, save staged output, run inbox and basic audits.
- `revise-chapter`: read review/audit findings, construct a revision task bundle, call a model runner, and save a staged revision proposal.
- `audit-chapter`: call role-specific auditors for information boundaries, character drift, continuity, echoes, and prose patterns, then collect findings.
- `agent-session`: persist a multi-step chapter writing ledger across write/revise/audit runs, read staged output state, and stop at review boundaries.
- Future `agent-loop`: observe project state, select safe next steps, execute tools, call model runners, and remain bounded by the same review gates.
- Keep acceptance human-governed: the agent may produce candidate work and structured findings, but source-of-truth changes still require explicit adoption.

Exit condition: the normal user story becomes "ask FictionOps Agent to work on a chapter" rather than "manually compose five commands."

## 0.8.0 AI Agent Dogfood Checklist

0.8.0 should measure what the AI agent changed in the real writing workflow:

- Record at least one real chapter planning/drafting/revision session with a model runner.
- Record at least one AI-assisted audit session for information, character, continuity, echo, or prose freshness.
- Record at least one publish-preparation session where the agent helps with metadata, clean copy, or release checks.
- Track the model/provider, command chain, staged outputs, accepted/rejected outputs, review time, useful findings, noisy findings, recovery actions, and author notes.
- Compare against raw chat or manual workflow where possible.

Exit condition: the project can honestly claim not only that AI is connected, but that AI agent participation has been observed, reviewed, and measured in a real long-form writing workflow.

## 1.0.0 Stability Bar

FictionOps should not call itself 1.0 until the core writer workflow is boring in the best sense:

- command names and core JSON keys are stable;
- compatibility policy is maintained when commands, schemas, or controller-facing JSON change;
- unsafe overwrites are consistently refused;
- release gates catch stale or missing publish artifacts;
- agent workflows remain staged and auditable;
- migration from messy legacy projects has at least one sustained real-project proof that passes `audit-dogfood-cycle`;
- a stability window record is accepted, passes `audit-stability-window`, and `audit-stable-core` returns ready;
- docs explain both the happy path, known limits, and recovery from common mistakes through `docs/recovery.md`.

The detailed requirement-by-requirement 1.0 audit lives in [stable-core-audit.md](stable-core-audit.md). Treat that file and `fictionops audit-stable-core .` as the final checklist before changing the 1.0 milestone status.

## Explicit Non-Goals

These may become separate plugins or future experiments, but they are not required for the core roadmap:

- cloud database backend;
- multiplayer web application;
- automatic literary quality scoring;
- one-click autonomous novel generation;
- direct model writes into canon/manuscript without review gates.
