# Changelog

All notable changes to FictionOps will be documented in this file.

The project uses semantic versioning while the CLI contracts are still small enough to audit by hand.

## [0.1.1] - 2026-07-07

### Added

- GitHub root README with concise positioning, quickstart commands, model/API integration notes, documentation links, roadmap, citation, and license pointers.
- Root `LICENSE` and `CITATION.cff` for GitHub project presentation and citation support.
- Quickstart terminal preview SVG included in the source distribution.
- Promotion kit docs with GitHub Release, Show HN, community post, Chinese article, and demo-script drafts.
- Quickstart/onboarding issue template.
- 0.1.1 release-candidate plan explaining why the current public package candidate should not reuse the earlier 0.1.0 TestPyPI artifact.
- Draft API Agent thin server under `integrations/api-agent/server.py`, wrapping `agent-run`, `agent-exec`, `agent-inbox`, and human decisions behind a local HTTP adapter.

### Changed

- Package metadata now includes project URLs and expanded keywords.
- CI and publish distribution checks include the newer onboarding docs, provider docs, chat runner example, and quickstart preview asset.
- Public-facing release and promotion copy now targets 0.1.1 as the recommended PyPI/TestPyPI candidate after the 0.1.0 MVP proof.

## [0.1.0] - 2026-07-05

### Added

- Legacy writing directory adoption diagnostics with `adopt`, including migration phases, suggested target paths, and conservative copy-to-sandbox migration.
- Migration sandbox review with `adopt-review`, aggregating doctor, information-boundary, character, and book-gate signals after `adopt --copy-to`.
- Explicit migration waivers for `adopt-review` and `adopt-plan`, allowing human-reviewed blockers to be deferred without removing their audit trail.
- Migration cleanup planning with `adopt-plan`, turning adopt-review findings into prioritized tasks, grouped repair phases, and optional per-group Markdown workfiles for large migrations.
- Import queue sorting plans with `import-plan`, including conservative book/chapter inference, optional safe moves for unambiguous draft files, companion chapter scaffold creation, and explicit generated-placeholder replacement.
- Project skeleton generation with `init`.
- Book and chapter scaffolding with `new-book` and `new-chapter`.
- Chapter engine synchronization from book outlines with `plan-chapter`.
- Scene skeleton generation from chapter engines with `scene-plan`.
- Task-ready drafting briefs from scene plans and scoped context with `draft-brief`.
- Post-draft gate checks for chapter drafts, engines, retrospectives, and sync items with `post-draft`.
- Single-chapter review gate aggregation across post-draft, continuity, information, character, echo, style, and wave checks with `review-gate`.
- Book-level closing gate aggregation across plan, retrospective, revision, table structure, word-scan, and wave checks with `book-gate`.
- General word and watch-term scanning with `scan-words`.
- General Markdown table structure checking with `check-tables`.
- Plan, retrospective, continuity, style, echo, and stats audits.
- Project health summary with `doctor`.
- Markdown/JSON health report export with `report`.
- Clean Markdown publishing export with `export-clean`.
- Clean Markdown publishing audit with `audit-publish`.
- Publish-copy drafting for editable synopsis, tag, and keyword candidates with `publish-copy`.
- Word-scan and Markdown table summaries in `doctor`, `report`, `revision-plan`, and book/review workflows.
- Publish audit integration in `doctor` and `report`.
- Publish checklist metadata export with `export-metadata`.
- Publish metadata integration in `doctor` and `report`.
- Publish package manifest export with `export-manifest`.
- Publish manifest integration in `doctor` and `report`.
- Styled EPUB export with `export-epub`.
- EPUB package checks in `doctor` and `report`.
- Styled EPUB output with optional cover-image packaging.
- Standalone EPUB package audit with `audit-epub`.
- Final release gate aggregation across book closure, publish, metadata, manifest, and EPUB checks with `release-gate`.
- Package release evidence auditing with `audit-release-evidence`, checking that 0.4 release-trial records are filled, externally grounded, and accepted before milestone closure.
- Sustained real-project dogfood-cycle auditing with `audit-dogfood-cycle`, checking that 1.0 dogfood evidence is filled, post-migration, ready, and compatibility-aware before stable-core closure.
- Stability-window evidence auditing with `audit-stability-window`, checking elapsed compatibility proof independently before aggregate stable-core closure.
- Stable-core evidence aggregation with `audit-stable-core`, checking release evidence, sustained dogfood, stability-window evidence, local governance files, and milestone claims before 1.0 closure.
- Chapter length wave audit with `audit-wave`.
- Chapter wave summary integration in `doctor` and `report`.
- Information boundary audit with `audit-info`.
- Information boundary summary integration in `doctor` and `report`.
- Character arc and voice-profile audit with `audit-characters`.
- Character audit integration in `doctor`, `report`, and `revision-plan`.
- Role-specific agent prompt rendering with `agent-prompt`.
- Agent connector handshake kits with `agent-connect`, including manifest, environment example, smoke commands, and adapter stub.
- Prepare-only agent task bundles with `agent-run`, combining prompt, scoped context, model config metadata, and optional draft brief without calling a model.
- External runner bridge with `agent-exec`, sending prepared bundles to user-provided commands and saving stdout as staged output without applying it.
- Minimal `examples/agent_runner_echo.py` runner showing how external agents receive FictionOps bundles over stdin and return staged stdout.
- OpenAI Responses API runner example with a no-network dry-run mode, showing a concrete model-backed `agent-exec` integration while keeping FictionOps core model-free.
- OpenAI-compatible Chat Completions runner example and provider setup docs for DeepSeek, Qwen/DashScope, Kimi/Moonshot, GLM/Zhipu, Doubao/Volcengine Ark, SiliconFlow, OpenAI Chat Completions, and local compatible servers.
- Agent output inbox auditing with `agent-inbox`, checking staged runner outputs without applying them.
- Agent next-step selection with `agent-next`, giving external controllers a read-only command recommendation without executing it.
- Agent workflow preflight auditing with `audit-agent-workflow`, checking manual, runner, controller, and model-runner readiness before connecting external automation.
- Minimal `examples/agent_controller_next.py` controller showing how to consume `agent-next` JSON without applying changes.
- No-model multi-step `examples/agent_controller_loop.py` controller showing how to execute only safe commands and stop at review boundaries.
- Agent integration guide documenting manual chat use, external runners, OpenAI Responses runner dry runs, and controller-loop wiring.
- Getting started and model-provider guides documenting shorter onboarding paths and model/API setup without adding provider SDKs to FictionOps core.
- Agent connector contract documenting the stable stdin/stdout runner boundary, controller stop rules, required task files, and smoke-test evidence for external agent integrations.
- Agent inbox summaries in `doctor` and `report` when agent run directories exist.
- Local model provider config reporting with `model-config`.
- Model provider configuration summary integration in `doctor` and `report`.
- Book-gate and release-gate milestone summaries in `doctor` and `report` without double-counting underlying audit issues.
- Scoped agent context packs with `context-pack`.
- Handoff context packs now include model config, character memory, canon state, revision plans, and gate reports.
- Context packs, draft briefs, and agent prompts now support total embedded-content budgets for long projects.
- Runnable `examples/demo_novel` project and demo tutorial for the outline-to-brief workflow.
- Runnable `examples/legacy_novel_source` project for safe old-project migration practice.
- English entry documentation for the core CLI, agent protocol, and demo tutorial.
- English CLI contract entry documentation for command groups, read/write boundaries, agent safety, and packaging expectations.
- English migration, testing, release, and contribution guides for external contributor onboarding.
- English end-to-end migration and publishing case covering legacy adoption, import sorting, clean Markdown, metadata, manifest, EPUB, and release-gate evidence.
- Roadmap and acceptance matrix for 0.2 migration dogfood, 0.3 controller orchestration, release trials, documentation parity, and 1.0 stability.
- Real long-form `adopt` dogfood report documenting a million-character-scale legacy project scan.
- GitHub Actions CI plus issue and pull request templates for open-source maintenance.
- Manual PyPI/TestPyPI publish workflow using trusted publishing, plus release documentation for credential isolation and rollback handling.
- Release trial evidence template for recording GitHub Actions run URLs, artifact hashes, optional TestPyPI URLs, install smoke results, rollback notes, and the final accepted/deferred/failed decision.
- Workflow-generated release trial evidence draft artifact in the publish workflow, kept separate from wheel/sdist artifacts so package publishing receives only distribution files.
- 0.1.0 release notes and completion audit documenting verified scope, validation results, and known boundaries.
- Known-limits documentation covering literary judgment, model behavior, context, migration, publishing, collaboration, security, and recovery boundaries.
- Recovery playbook documenting common damaged states, triage commands, safe regeneration, migration cleanup, agent-output recovery, publish-artifact recovery, and controller-loop stop rules.
- Compatibility policy documenting version stages, stable surfaces, additive changes, breaking changes, deprecation path, and controller guidance.
- Milestone status ledger mapping roadmap milestones to current evidence and remaining external or real-project proof.
- Stable core audit mapping the 1.0 requirements to current local evidence, external blockers, sustained dogfood needs, and compatibility-time requirements.
- Staged workflow checklist generation with `workflow-plan`.
- Audit-to-revision task planning with `revision-plan`.
- Packaged templates for installed CLI use.
- Source distribution manifest covering Chinese docs, examples, root templates, tests, and workflow documentation.
- Wheel and source-distribution content checks in local tests and CI.
- GitHub CI and publish workflow distribution checks now cover current agent integration, compatibility, known-limits, OpenAI runner, and controller-loop artifacts.
- GitHub CI and publish workflow now install the built wheel in a clean virtual environment and run CLI smoke commands before artifact upload or publishing.
- Built-wheel clean-virtual-environment install smoke test for release readiness.
- Modern SPDX-style license metadata for current setuptools builds.
- Release smoke and installation smoke tests.
- `python -m fictionops` module entrypoint for installed packages.

### Notes

- This is a pre-alpha MVP intended to prove the file-based workflow and CLI contracts.
- English docs now cover the core external onboarding path, while deep methodology remains Chinese-first until the workflow stabilizes.
