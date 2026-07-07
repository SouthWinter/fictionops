# FictionOps

Languages: English | [Chinese](README.zh-CN.md)

FictionOps is a file-based operating system and API-backed workflow harness for long-form fiction planning, drafting, auditing, migration, and publishing. It is not a one-click novel generator and it is not an autonomous writing agent. Its job is to help a writer keep a large story maintainable: structure, canon, information boundaries, character memory, prose-pattern audits, handoff context, model/API task bundles, staged outputs, and release artifacts all live in ordinary files.

The current package is Chinese-first and local-first. It uses Markdown, YAML, JSON, and EPUB files, and the CLI does not call a model by itself. External runners may call OpenAI, local model servers, or other APIs; external controllers may turn those calls into an agentic loop.

## Start Here

Install from the GitHub source checkout today:

```bash
python -m pip install "git+https://github.com/SouthWinter/fictionops.git#subdirectory=fictionops"
```

After the first formal PyPI release, the intended install command is:

```bash
python -m pip install fictionops
```

Create a tiny project:

```bash
fictionops init my-novel --title "My Novel"
fictionops new-book my-novel --book book_01 --title "Book One"
fictionops new-chapter my-novel --book book_01 --chapter 001 --title "Chapter One"
fictionops plan-chapter my-novel --book book_01 --chapter 001
fictionops draft-brief my-novel --book book_01 --chapter 001
fictionops doctor my-novel --book book_01
```

For the shorter onboarding guide, see [Getting started](docs/getting-started.md). For model/API setup, see [Model providers](docs/model-providers.md).

## Repository Contents

```text
fictionops/
  pyproject.toml
  LICENSE
  CHANGELOG.md
  CONTRIBUTING.md
  CONTRIBUTING.zh-CN.md
  README.md
  README.zh-CN.md
  src/fictionops/
    adopt.py
    adopt_review.py
    cli.py
    core.py
    doctor.py
    report.py
    templates/
  docs/
    getting-started.md
    getting-started.zh-CN.md
    cli.md
    cli.zh-CN.md
    cli-contracts.md
    agent-protocol.md
    agent-protocol.zh-CN.md
    agent-connector-contract.md
    agent-connector-contract.zh-CN.md
    agent-workflow.md
    agent-workflow.zh-CN.md
    agent-evaluation.md
    agent-evaluation.zh-CN.md
    agent-evaluation-demo-report.md
    migration.md
    testing.md
    release.md
    compatibility.md
    compatibility.zh-CN.md
    known-limits.md
    known-limits.zh-CN.md
    recovery.md
    recovery.zh-CN.md
    tutorial-demo.md
    cli-contracts.zh-CN.md
    agent-integration.md
    agent-integration.zh-CN.md
    model-providers.md
    model-providers.zh-CN.md
    completion-audit-0.1.0.zh-CN.md
    roadmap.md
    roadmap.zh-CN.md
    milestone-status.md
    milestone-status.zh-CN.md
    stable-core-remaining-checklist.md
    stable-core-remaining-checklist.zh-CN.md
    end-to-end-migration-publish.md
    dogfood-legacy-adopt.zh-CN.md
    pypi-release.zh-CN.md
    release-checklist.zh-CN.md
    release-notes-0.1.0.zh-CN.md
    testing.zh-CN.md
  examples/
    agent_controller_next.py
    agent_controller_loop.py
    agent_runner_echo.py
    agent_runner_openai_chat.py
    agent_runner_openai_responses.py
    demo_novel/
    legacy_novel_source/
  tests/
    test_cli.py
```

## Documentation

- [CLI guide](docs/cli.md)
- [Getting started](docs/getting-started.md)
- [Getting started, Chinese reference](docs/getting-started.zh-CN.md)
- [CLI usage, Chinese reference](docs/cli.zh-CN.md)
- [CLI contracts](docs/cli-contracts.md)
- [CLI contracts, Chinese reference](docs/cli-contracts.zh-CN.md)
- [Agent protocol](docs/agent-protocol.md)
- [Agent protocol, Chinese reference](docs/agent-protocol.zh-CN.md)
- [Agent connector contract](docs/agent-connector-contract.md)
- [Agent connector contract, Chinese reference](docs/agent-connector-contract.zh-CN.md)
- [Agent integration guide](docs/agent-integration.md)
- [Agent integration guide, Chinese reference](docs/agent-integration.zh-CN.md)
- [Model providers](docs/model-providers.md)
- [Model providers, Chinese reference](docs/model-providers.zh-CN.md)
- [Agent workflow positioning](docs/agent-workflow.md)
- [Agent workflow positioning, Chinese reference](docs/agent-workflow.zh-CN.md)
- [Research positioning](docs/research-positioning.md)
- [Research positioning, Chinese reference](docs/research-positioning.zh-CN.md)
- [Agent evaluation protocol](docs/agent-evaluation.md)
- [Agent evaluation protocol, Chinese reference](docs/agent-evaluation.zh-CN.md)
- [Evaluation plan](docs/evaluation-plan.md)
- [Evaluation plan, Chinese reference](docs/evaluation-plan.zh-CN.md)
- [Agent evaluation demo report](docs/agent-evaluation-demo-report.md)
- [Interview brief for agent research discussions](docs/interview-brief.md)
- [Interview brief, Chinese reference](docs/interview-brief.zh-CN.md)
- [Migration guide](docs/migration.md)
- [Promotion kit](docs/promotion-kit.md)
- [Promotion kit, Chinese reference](docs/promotion-kit.zh-CN.md)
- [Demo tutorial](docs/tutorial-demo.md)
- [Two-minute demo script](docs/two-minute-demo.md)
- [Two-minute demo script, Chinese reference](docs/two-minute-demo.zh-CN.md)
- [Testing guide](docs/testing.md)
- [Release guide](docs/release.md)
- [0.1.1 release candidate plan](docs/release-candidate-0.1.1.md)
- [0.1.1 release candidate plan, Chinese reference](docs/release-candidate-0.1.1.zh-CN.md)
- [Release trial evidence](docs/release-trial-evidence.md)
- [Release trial evidence, Chinese reference](docs/release-trial-evidence.zh-CN.md)
- [Compatibility policy](docs/compatibility.md)
- [Compatibility policy, Chinese reference](docs/compatibility.zh-CN.md)
- [Known limits](docs/known-limits.md)
- [Known limits, Chinese reference](docs/known-limits.zh-CN.md)
- [Recovery playbook](docs/recovery.md)
- [Recovery playbook, Chinese reference](docs/recovery.zh-CN.md)
- [Testing guide, Chinese reference](docs/testing.zh-CN.md)
- [Release checklist, Chinese reference](docs/release-checklist.zh-CN.md)
- [PyPI release guide, Chinese reference](docs/pypi-release.zh-CN.md)
- [0.1.0 release notes](docs/release-notes-0.1.0.zh-CN.md)
- [0.1.1 release notes](docs/release-notes-0.1.1.md)
- [0.1.0 completion audit](docs/completion-audit-0.1.0.zh-CN.md)
- [Roadmap](docs/roadmap.md)
- [Roadmap, Chinese reference](docs/roadmap.zh-CN.md)
- [Milestone status ledger](docs/milestone-status.md)
- [Milestone status ledger, Chinese reference](docs/milestone-status.zh-CN.md)
- [Stable core remaining checklist](docs/stable-core-remaining-checklist.md)
- [Stable core remaining checklist, Chinese reference](docs/stable-core-remaining-checklist.zh-CN.md)
- [Stable core audit](docs/stable-core-audit.md)
- [Stable core audit, Chinese reference](docs/stable-core-audit.zh-CN.md)
- [End-to-end migration and publishing case](docs/end-to-end-migration-publish.md)
- [Dogfood case study: maintaining a million-character novel](docs/dogfood-case-study.md)
- [Dogfood case study, Chinese reference](docs/dogfood-case-study.zh-CN.md)
- [Real-project adopt dogfood report](docs/dogfood-legacy-adopt.zh-CN.md)
- [Sustained dogfood cycle evidence](docs/dogfood-cycle-evidence.md)
- [Sustained dogfood cycle evidence, Chinese reference](docs/dogfood-cycle-evidence.zh-CN.md)
- [Stability window evidence](docs/stability-window-evidence.md)
- [Stability window evidence, Chinese reference](docs/stability-window-evidence.zh-CN.md)
- [Legacy migration example](examples/legacy_novel_source/README.md)
- [Contribution guide](CONTRIBUTING.md)
- [Contribution guide, Chinese reference](CONTRIBUTING.zh-CN.md)
- [Changelog](CHANGELOG.md)
- [MIT License](LICENSE)

## CLI Quick Start

The current CLI includes fifty-one MVP commands:

`adopt`, `adopt-review`, `adopt-plan`, `import-plan`, `init`, `new-book`, `new-chapter`, `plan-chapter`, `scene-plan`, `draft-brief`, `post-draft`, `review-gate`, `book-gate`, `audit-plan`, `retrospective`, `stats`, `scan-words`, `check-tables`, `audit-wave`, `audit-style`, `audit-continuity`, `audit-echoes`, `audit-info`, `audit-characters`, `agent-prompt`, `agent-connect`, `eval-agent`, `agent-smoke`, `agent-run`, `agent-exec`, `agent-inbox`, `agent-next`, `audit-agent-workflow`, `model-config`, `context-pack`, `workflow-plan`, `revision-plan`, `doctor`, `report`, `export-clean`, `audit-publish`, `publish-copy`, `export-metadata`, `export-manifest`, `export-epub`, `audit-epub`, `release-gate`, `audit-release-evidence`, `audit-dogfood-cycle`, `audit-stability-window`, and `audit-stable-core`.

From the repository root:

```bash
python fictionops/src/fictionops/cli.py --help
python fictionops/src/fictionops/cli.py adopt existing-novel --out adopt_report.md
python fictionops/src/fictionops/cli.py init migrated-novel --title "Migrated Novel"
python fictionops/src/fictionops/cli.py adopt existing-novel --copy-to migrated-novel --format json
python fictionops/src/fictionops/cli.py adopt-review migrated-novel --format json
python fictionops/src/fictionops/cli.py adopt-plan migrated-novel --out 07_audits/adopt_review/plan.md
python fictionops/src/fictionops/cli.py adopt-plan migrated-novel --write-groups 07_audits/adopt_review/repair_groups
python fictionops/src/fictionops/cli.py import-plan migrated-novel --out 07_audits/adopt_review/import_plan.md
python fictionops/src/fictionops/cli.py import-plan migrated-novel --apply --create-scaffolds --replace-placeholder-targets
python fictionops/src/fictionops/cli.py doctor migrated-novel --book book_01
python fictionops/src/fictionops/cli.py agent-connect migrated-novel --name local-runner --mode runner
python fictionops/src/fictionops/cli.py eval-agent examples/demo_novel --chapter 002 --out docs/agent-evaluation-smoke.md
python fictionops/src/fictionops/cli.py agent-smoke migrated-novel --connector local-runner
python fictionops/src/fictionops/cli.py audit-agent-workflow migrated-novel --level runner --connector local-runner
python fictionops/src/fictionops/cli.py release-gate migrated-novel --book book_01
python fictionops/src/fictionops/cli.py audit-release-evidence . --file docs/release-trial-evidence.md
python fictionops/src/fictionops/cli.py audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md
python fictionops/src/fictionops/cli.py audit-stability-window . --file docs/stability-window-evidence.md
python fictionops/src/fictionops/cli.py audit-stable-core .
```

For a shorter onboarding path, start with [Getting started](docs/getting-started.md). For OpenAI-compatible providers such as DeepSeek, Qwen/DashScope, Kimi/Moonshot, GLM/Zhipu, Doubao/Volcengine Ark, SiliconFlow, local model servers, and OpenAI Chat Completions, see [Model providers](docs/model-providers.md).

Installed usage:

```bash
python -m pip install ./fictionops
fictionops --version
fictionops init my-novel --title "My Novel"
fictionops doctor my-novel --book book_01
```

## Migration Workflow

`adopt` scans an existing writing directory, maps legacy files into FictionOps layers, suggests migration phases and target paths, and can copy candidate files into a separate initialized FictionOps sandbox with `--copy-to`. The source project remains read-only. Copy runs also write `00_management/adopted_handoff/adopt_manifest.json` so later cleanup tools can see the original source paths.

`adopt-review` reviews that migration sandbox after copying. It aggregates `doctor`, `audit-info`, `audit-characters`, and `book-gate`, then flags migration-specific blockers such as unsorted files still sitting in `06_drafts/import_queue/`.

`adopt-plan` turns those review findings into a prioritized migration cleanup checklist, with grouped repair phases so hundreds of migration findings can be handled as coherent batches before drilling into individual tasks. With `--write-groups`, it writes an index and one Markdown workfile per repair group for handoff to a person or agent.

Migration waivers can be recorded in `07_audits/adopt_review/waivers.json` or passed with `--waivers`. They defer explicitly reviewed blockers from active issue counts and `adopt-plan` tasks while preserving the decision record; unsorted files in `06_drafts/import_queue/` still have to be cleared before the sandbox can leave `needs_import_sorting`.

`import-plan` inspects `06_drafts/import_queue/`, uses the adopt manifest when present, suggests book/chapter targets, flags ambiguous rows, and can move only unambiguous files when `--apply` is passed. With `--apply --create-scaffolds`, it also creates missing chapter engines and retrospectives for moved chapters without overwriting existing files. With `--replace-placeholder-targets`, it may replace only generated placeholder chapter targets.

The repository also includes a tiny legacy source folder at `examples/legacy_novel_source/`. It is not a FictionOps project; it exists so users can run the migration chain end to end in a safe sandbox.

## Validation

The 0.1.0 pre-alpha evidence is tracked in the release docs. External release-trial evidence should be recorded with [Release trial evidence](docs/release-trial-evidence.md) so GitHub Actions runs, artifacts, optional TestPyPI URLs, smoke results, and final decisions have one durable place. The publish workflow also uploads a separate workflow-generated release trial evidence draft artifact; it is deliberately kept out of the wheel/sdist distribution artifact. Current local validation target:

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

The test suite currently covers 51 CLI commands and 129 regression tests, including source and built-wheel installation smoke tests, wheel and source-distribution content checks, template sync checks, release governance checks, release evidence auditing, sustained dogfood-cycle auditing, stability-window auditing, stable-core auditing, English documentation coverage, runnable demo and migration examples, the real-project `adopt` dogfood entry point, `adopt --copy-to`, copy-path collision disambiguation, `adopt-review`, migration waivers, `adopt-plan`, `import-plan`, `agent-connect`, `eval-agent`, `agent-smoke`, `agent-run`, `agent-exec`, `agent-inbox`, `agent-next`, `audit-agent-workflow`, the no-model controller loop example, the OpenAI-compatible Chat Completions runner dry-run path, and the OpenAI Responses runner dry-run path. `audit-stable-core --format json` also emits structured `action_items` so a maintainer or controller can see the remaining evidence files, audit commands, and acceptance criteria without treating the plan as proof.

## Positioning

FictionOps is best understood as a workflow and toolkit for long-form fiction continuity, planning, revision, and publishing. It should protect uncertainty, silence, misreading, emotional residue, character-specific intelligence, delayed understanding, and living prose.

When connected to an external model API through a runner, the setup is an API-backed AI workflow. When an external controller also reads project state, chooses next steps, calls runners, and stops at review gates, the whole setup becomes an agentic workflow. FictionOps core remains the harness: it scopes context, packages tasks, receives staged outputs, and runs gates; API calls, model execution, and controller loops live outside the core. `audit-agent-workflow` is the preflight gate for checking that boundary before connecting a runner or controller. See [Agent workflow positioning](docs/agent-workflow.md).

For concrete wiring patterns, including manual chat use, external runners, OpenAI-compatible Chat Completions runner dry runs, OpenAI Responses runner dry runs, and controller loops, see [Agent integration guide](docs/agent-integration.md).

If the workflow makes the novel feel too neat, the workflow should bend. The story comes first.
