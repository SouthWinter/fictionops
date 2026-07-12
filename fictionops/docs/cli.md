# FictionOps CLI Guide

FictionOps is a local, file-based stateful agent and toolkit for long-form fiction projects. `fictionops agent ...` delegates model calls to an explicit runner; lower-level CLI commands remain deterministic and can run without a model.

The Chinese CLI guide remains the most detailed reference: [cli.zh-CN.md](cli.zh-CN.md). This English guide covers the core workflow, command groups, and safety boundaries.

## Install Or Run From Source

From a source checkout:

```bash
python fictionops/src/fictionops/cli.py --help
python fictionops/src/fictionops/cli.py init my-novel --title "My Novel"
```

After local installation:

```bash
python -m pip install ./fictionops
fictionops --version
python -m fictionops --version
```

Most commands accept `--format json` for script or agent use. Write commands do not overwrite existing files unless they expose and receive `--force`.

## Command Groups

### Migration

Use these commands when adopting an existing writing folder:

```bash
fictionops adopt existing-novel --out adopt_report.md
fictionops init migrated-novel --title "Migrated Novel"
fictionops adopt existing-novel --copy-to migrated-novel --format json
fictionops adopt-review migrated-novel --format json
fictionops adopt-plan migrated-novel --out 07_audits/adopt_review/plan.md
fictionops import-plan migrated-novel --out 07_audits/adopt_review/import_plan.md
```

- `adopt` scans source files without modifying them.
- `adopt --copy-to` copies candidate files into an initialized FictionOps sandbox and writes an adopt manifest.
- `adopt-review` checks the sandbox after copying.
- `adopt-plan` turns review findings into prioritized cleanup groups.
- `import-plan` sorts safe draft files from `06_drafts/import_queue/` into book/chapter folders only when `--apply` is provided.

### Project Scaffolding

```bash
fictionops init my-novel --title "My Novel"
fictionops new-book my-novel --book book_02 --title "Book Two"
fictionops new-chapter my-novel --book book_01 --chapter 002 --title "Chapter Two"
```

These commands create the standard project layout, book outlines, chapter drafts, chapter engines, and retrospective files.

### Chapter Preparation

```bash
fictionops plan-chapter my-novel --book book_01 --chapter 002
fictionops scene-plan my-novel --book book_01 --chapter 002
fictionops draft-brief my-novel --book book_01 --chapter 002 --include-context-content --max-total-chars 4000
```

- `plan-chapter` syncs fields from a book outline into a chapter engine.
- `scene-plan` turns a chapter engine into scene-level pressure and change.
- `draft-brief` builds a task-ready writing brief with scoped context.

### Post-Draft Review

```bash
fictionops post-draft my-novel --book book_01 --chapter 002
fictionops review-gate my-novel --book book_01 --chapter 002
fictionops revision-plan my-novel --book book_01
```

Use these commands after a chapter exists. They check whether the chapter has a matching engine, retrospective, information boundaries, character memory, echo signals, style risks, and next revision tasks.

### Audits

```bash
fictionops stats my-novel
fictionops scan-words my-novel --watch "not,never"
fictionops check-tables my-novel --all
fictionops audit-wave my-novel
fictionops audit-style my-novel
fictionops audit-continuity my-novel
fictionops audit-echoes my-novel
fictionops audit-info my-novel
fictionops audit-characters my-novel
```

Audits are maintenance signals, not literary quality scores. They help find missing tables, flat chapter lengths, repeated prose patterns, leaked information, and incomplete character memory.

### Agent Workflow

```bash
fictionops model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor --write
fictionops setup-ai my-novel --provider deepseek --model deepseek-chat
fictionops context-pack my-novel --task draft --book book_01 --chapter 001
fictionops agent-prompt my-novel --role draft-writer --book book_01 --chapter 001
fictionops agent-connect my-novel --name local-runner --mode runner
fictionops eval-agent fictionops/examples/demo_novel --chapter 002 --out agent-evaluation-smoke.md
fictionops agent-smoke my-novel --connector local-runner
fictionops agent-run my-novel --role draft-writer --book book_01 --chapter 001 --out-dir 00_management/agent_runs/ch_001
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python fictionops/examples/agent_runner_echo.py
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
fictionops agent-inbox my-novel
fictionops write-chapter my-novel --book book_01 --chapter 001 --runner python fictionops/examples/agent_runner_openai_chat.py --model your-model
fictionops revise-chapter my-novel --book book_01 --chapter 001
fictionops audit-chapter my-novel --book book_01 --chapter 001
fictionops agent-session my-novel --book book_01 --chapter 001 --goal "Draft, revise, and audit chapter 001."
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
fictionops audit-agent-workflow my-novel --level runner --connector local-runner
```

FictionOps prepares connector handshakes, bounded inputs, staged-output checks, safe next-command suggestions, reproducible harness smoke reports, and preflight audits before agent integration. `setup-ai` is the guided first-run path for OpenAI-compatible providers: it writes model metadata and an API-key-free env example. `write-chapter`, `revise-chapter`, and `audit-chapter` are AI-first orchestration commands over the same staged `agent-run` / `agent-exec` / `agent-inbox` contract; `agent-session` records a multi-step session ledger that ties those runs together without applying model output. It does not store API keys or apply model output to the manuscript automatically. `eval-agent` runs on a temporary fixture copy and uses an internal no-network runner; real model calls still go through explicit runners and produce staged output. See [agent-protocol.md](agent-protocol.md), [agent-integration.md](agent-integration.md), and [agent-evaluation.md](agent-evaluation.md).

### Book And Release Gates

```bash
fictionops book-gate my-novel --book book_01
fictionops export-clean my-novel --book book_01
fictionops audit-publish my-novel --book book_01
fictionops publish-copy my-novel --book book_01
fictionops export-metadata my-novel --book book_01
fictionops export-manifest my-novel --book book_01
fictionops export-epub my-novel --book book_01
fictionops audit-epub my-novel --book book_01
fictionops release-gate my-novel --book book_01
```

This path moves a book from draft maintenance to clean Markdown, editable copy, metadata, manifest, EPUB, and final release readiness.

### Package Release Governance

```bash
fictionops audit-release-evidence . --file docs/release-trial-evidence.md
fictionops audit-release-evidence . --file release-trial-evidence-0.1.0.md --format json
fictionops audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md
fictionops audit-stability-window . --file docs/stability-window-evidence.md
fictionops audit-stable-core .
```

These commands are for FictionOps package and stable-core governance, not for a novel project release. They check whether release-trial evidence has real external GitHub Actions proof, artifact hashes, install smoke results, and an `accepted` decision; whether sustained dogfood-cycle evidence is filled and covers at least 7 calendar days; whether stability-window evidence is accepted after at least 7 calendar days of real elapsed use and, for local Markdown references, points to release/dogfood evidence that passes its own audit; and whether the 1.0 stable-core gate has release, dogfood, and stability-window proof before the milestone is closed.

## Safety Rules

- Source migration scans are read-only unless an explicit copy or apply flag is used.
- Generated reports do not overwrite existing files without `--force`.
- Agent commands produce staging files and receipts; they do not apply output to canon or chapters.
- JSON output is intended for automation. Markdown output is intended for humans.
- The project state stays in ordinary files so writers can inspect and revise it directly.
