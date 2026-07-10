# FictionOps Milestone Status

This ledger records what the current repository proves against the roadmap. It is stricter than a feature list: a milestone is only complete when current files, tests, workflows, or release records prove the required behavior.

Status meanings:

- **Complete locally:** repository evidence proves the milestone without external service state.
- **Complete with external evidence:** repository evidence plus a recorded external run or service record proves the milestone.
- **Partially proven:** important evidence exists, but at least one required acceptance item is still missing.
- **Externally blocked:** repository-side work exists, but completion depends on GitHub Actions, TestPyPI, PyPI, or real-project state that cannot be faked in the repository.
- **Not complete:** implementation or proof is still materially incomplete.

## Summary

| Milestone | Status | Current Evidence | Remaining Evidence |
| --- | --- | --- | --- |
| 0.1.0 Pre-Alpha MVP | Complete locally | `docs/completion-audit-0.1.0.zh-CN.md`, `docs/release-notes-0.1.0.zh-CN.md`, 138 tests, wheel/sdist builds, source and built-wheel install smoke tests. | External release record if publishing is chosen. |
| 0.2.0 Migration Dogfood | Complete locally | Real-project dogfood log, `adopt --copy-to`, `adopt-review`, `adopt-plan`, `import-plan`, migration waivers, import queue clearing path, grouped repair files, and 0.2 closure rerun with `ready: true`, `import_queue_files: 0`, `blocking_issue_count: 0`, and no blocking repair groups. | Further canon normalization remains normal project work, not a migration milestone blocker. |
| 0.3.0 Agent Controller | Complete locally | `examples/agent_controller_loop.py`, `agent-next`, `agent-exec`, `agent-inbox`, `docs/agent-connector-contract.md`, JSONL controller logs, tests for safe execution, review boundaries, placeholders, migration states, repeated suggestions, and publish-stage command handling. | Real model/controller integration is optional and remains outside core unless it preserves staged outputs and gates. |
| 0.4.0 Release Trial | Complete with external evidence | GitHub Actions publish run `28849146871`, TestPyPI package `fictionops==0.1.1`, `docs/release-trial-evidence.md`, distribution artifact hashes, clean TestPyPI install smoke, and `audit-release-evidence` returning `ready=true`. | None for the release-trial milestone. |
| 0.5.0 Documentation Parity Pass | Complete locally | English docs for CLI, contracts, migration, agent protocol, agent workflow, agent integration, testing, release, compatibility, known limits, contribution, demo, legacy migration example, and `docs/end-to-end-migration-publish.md`. | Full translation of every Chinese design note remains intentionally out of scope for this milestone. |
| 0.6.0 AI Provider Onboarding | Partially proven | OpenAI-compatible Chat runner v1, provider presets, model-provider docs, dry-run paths, `setup-ai`, API-key-free env examples, and tests proving preset/env-file wiring plus no raw-key storage. | AI-first README quickstart and a documented real-call path as the default user story. |
| 0.7.0 Writing Agent Commands | Partially proven | AI-first `write-chapter`, `revise-chapter`, `audit-chapter`, and `agent-session` commands now wrap staged agent task creation, optional runner execution, inbox checks, and durable session ledgers with tests. | Richer command telemetry and real provider dogfood. |
| 0.8.0 Agent Runtime Dogfood | Not complete | Private real-project workflow dogfood exists, but it mostly proves project maintenance and publishing infrastructure rather than measured AI-agent contribution. | A real AI-assisted writing dogfood report with model/provider, tasks, accepted/rejected output, useful/noisy findings, time saved, review cost, and recovery notes. |
| 1.0.0 Stable Core | Not complete | `docs/stable-core-audit.md`, compatibility policy, known-limits docs, recovery playbook, command contracts, broad test suite, no-overwrite behavior, staged agent workflow, release gates, accepted TestPyPI release-trial evidence, real-project dogfood evidence, `docs/dogfood-cycle-evidence.md`, `docs/stability-window-evidence.md`, `audit-dogfood-cycle`, `audit-stability-window`, and `audit-stable-core`. | Filled sustained real-project dogfood cycle, accepted stability-window evidence, stable core contracts over time, and proof that recovery paths remain current as behavior changes. |

## 0.2 Migration Dogfood Detail

The repository proves the migration chain can scan a million-character-scale legacy project, copy candidate files into an initialized sandbox, disambiguate target collisions, sort import queues, replace generated placeholder targets only when explicitly requested, and turn migration review findings into grouped repair work.

The 0.2 closure rerun in `docs/dogfood-legacy-adopt.zh-CN.md` records a real sandbox at `C:\Users\z\Documents\story\legacy_fictionops_02_closure_sandbox`. After import sorting and explicit waivers for author-only canon normalization, `adopt-review` reported `ready: true`, `import_queue_files: 0`, `blocking_issue_count: 0`, and `waived_issue_count: 31`; `adopt-plan` reported 501 remaining normal maintenance tasks, 14 repair groups, and no blocking repair groups.

This does **not** claim the migrated novel is editorially finished. It proves the migration milestone: old material can leave the import queue, known migration blockers can be repaired or consciously deferred, and the project can move into normal FictionOps work.

## 0.3 Agent Controller Detail

This milestone is locally satisfied for the controller-safety scope described in the roadmap. The no-model loop proves the controller boundary; later AI-native milestones must make real model APIs the default product path. The controller can:

- call `agent-next`;
- follow the external connector contract for runner and controller boundaries;
- execute commands only when candidates are marked safe;
- write JSONL logs;
- stop at staged agent output;
- stop on placeholder commands;
- stop on repeated suggestions;
- avoid editing manuscript or canon directly;
- handle migration-only states and publish-stage command inspection.

This is not a claim that FictionOps is an autonomous novelist. It proves controller orchestration while preserving staged output and review gates. It also does not complete the AI-native roadmap; 0.6-0.8 now track provider onboarding, writing-agent commands, and real AI dogfood.

## 0.4 Release Trial Detail

The repository now has strong pre-release evidence:

- local full test suite;
- local source install smoke;
- local built-wheel clean venv smoke;
- CI build/content checks;
- publish workflow build/content checks;
- CI and publish workflow built-wheel smoke before artifact upload or publishing;
- Trusted Publishing setup path;
- a `fictionops-release-trial-evidence-<version>` artifact generated by the publish workflow, kept separate from the distribution artifact so PyPI/TestPyPI receive only wheel and sdist files;
- `audit-release-evidence`, which rejects empty templates, unfinished generated drafts, invalid run URLs, invalid hashes, missing install smoke fields, and non-accepted decisions;
- `docs/release-trial-evidence.md`, which defines where to record the GitHub Actions run URL, artifact names and hashes, optional TestPyPI URLs, install smoke output, rollback notes, and final `accepted/deferred/failed` decision.

The external release-trial evidence now exists: GitHub Actions run `28849146871` built the distributions, published `fictionops==0.1.1` to TestPyPI through trusted publishing, and the accepted record in `docs/release-trial-evidence.md` includes artifact hashes plus clean install smoke results. The workflow-generated release trial evidence draft artifact remains part of the audit trail, but local tests, an empty template, or a generated draft still cannot replace a reviewed external record for future release trials.

## 0.5 Documentation Parity Detail

This milestone is locally satisfied for outside-contributor onboarding. English docs now provide:

- command and JSON contract entry points;
- migration and release guides;
- agent protocol, workflow positioning, connector contract, and integration guide;
- testing, compatibility, known-limits, and contribution guidance;
- a runnable demo tutorial;
- a legacy migration example;
- an end-to-end migration and publishing case that continues through clean Markdown, metadata, manifest, EPUB, and `release-gate`.

The Chinese methodology remains deeper and more literary. That is acceptable for this milestone because full translation of every Chinese design note is explicitly out of scope.

## 1.0 Stable Core Detail

The repository has several local stability ingredients: command contracts, compatibility policy, known-limits documentation, a recovery playbook, no-overwrite tests, staged agent boundaries, release gates, package smoke tests, accepted release-trial evidence, `audit-dogfood-cycle`, `audit-stability-window`, `docs/stability-window-evidence.md`, `audit-stable-core`, and the requirement-by-requirement matrix in `docs/stable-core-audit.md`. It still does **not** prove 1.0 readiness because stable-core status needs a filled sustained real-project dogfood cycle and accepted time-tested compatibility behavior.

Use `docs/stable-core-remaining-checklist.md` as the execution checklist for the remaining 1.0 work. It names the exact evidence lanes, acceptance commands, stop conditions, and which parts require a maintainer or external service state rather than more local implementation.

## How To Use This Ledger

Before marking a roadmap milestone complete:

1. Read the milestone row here.
2. Inspect the files, tests, workflows, or external records named as evidence.
3. Update this ledger, the roadmap, release notes, and completion audit together.
4. Add or update regression tests when a command, package artifact, or safety boundary becomes part of the evidence.
