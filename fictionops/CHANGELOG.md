# Changelog

## Unreleased

- Added state-aware scene-by-scene drafting and evidence-guided scene rewriting for new chapters.
- Added deterministic story fact ledgers for quantities, timelines, and coded object-state transitions.
- Added bounded JSON/schema repair for causal simulation, planning, adversarial review, and evaluation.
- Added strict scene-target budget normalization, under/over-length repair, and candidate-grounded review evidence checks.
- Added evidence-routed selective scene rewriting so unaffected scenes remain byte-for-byte unchanged during retries.
- Added hard model-call and wall-clock budgets with a persistent `model_budget.json` ledger for write and revision workflows.
- Added versioned runner telemetry receipts for provider/model/request ids, token usage, explicit-price cost estimates, cumulative resume accounting, and pre-next-call token/cost budget stops.
- Added the unified `fictionops agent write|revise|accept|continue` product entry and a session-aware safe continuation controller.
- Added a persistent cross-session issue ledger with stable identity, duplicate merging, automatic reopen, verified/accepted transitions, and explicit author waive/reject/reopen decisions.
- Added three anonymous high-risk semantic review fixtures for information boundaries, character voice, and prose/reader experience.
- Added a reproducible raw-vs-RAG-vs-workflow review baseline harness over the anonymous high-risk fixtures.
- Added a validated installable Codex skill and a versioned `fictionops.api` v1 facade shared by the HTTP adapter and canonical runtime.
- Added phase checkpoints with source/artifact hashes, explicit auditable session cancellation, and checkpoint-aware `agent resume` for safe write/revision phases without replaying completed model calls.
- Added revision resume from `verification_ready` and a read-only `agent status` author workbench for project-wide sessions, issues, usage, and cost.
- Added a unified attributed `trajectory.jsonl`, an explicit pure controller policy, repeated raw/RAG/full/ablation experiments, and a seven-scenario failure-injection lab with protected-hash checks.
- Added an interview-ready research case, architecture, reproducible evidence, and 3-minute/10-minute technical scripts grounded in real DeepSeek failures.
- Added Benchmark v2 with opaque prompt ids, memory-only positives, preservation negatives, confusion-matrix metrics, replayable DeepSeek evidence, and condition-isolated blind-review packets.
- Added an independent preservation verifier for comprehensive old-chapter revision, with deterministic self-abstention withdrawal, model-backed uphold/withdraw/counterevidence decisions, and separate original/effective issue artifacts.
- Added a project-level author guard registry with stable ids, explicit set/retire history, run snapshots, and verifier authority restricted to active author-authored guards.
- Recorded a focused DeepSeek guard-id dogfood showing scoped authorized withdrawal without suppressing the benchmark's true repetition finding.
- Added anonymous counterevidence packet export and strict annotation scoring, with private control keys, issue-level evaluability boundaries, repair-harm ratings, and human-effort metrics.
- Recorded a real DeepSeek dogfood run that completed the full workflow and correctly withheld approval from a structurally valid but stylistically weak candidate.

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
- AI-first `write-chapter`, `revise-chapter`, and `audit-chapter` commands that compose staged `agent-run`, optional `agent-exec`, and `agent-inbox` workflows.
- `agent-session` command for durable multi-step AI writing session ledgers across chapter write, revise, and audit runs.
- `setup-ai` command for guided OpenAI-compatible provider setup, safe model config generation, and API-key-free runner env examples.
- Closed-loop `agent-revise-workflow` runtime with source manifests, persistent session/events, structured before/after issues, unified diffs, static checks, model-backed semantic invariant verification, and bounded targeted retries.
- `agent-accept-revision` command for explicit atomic application of verified candidates with source/candidate SHA-256 checks and stale-source refusal.
- Agent system design documenting the controller loop, memory layers, risk levels, chapter state machine, and implementation priorities.
- Project-aware context compiler for custom and standard novel layouts, with adjacent-chapter discovery, entity-linked character memory, authority labels, hashes, reasons, and bounded context budgets.
- Comprehensive old-chapter review covering continuity, character, information boundaries, foreshadowing, chapter function, and prose/reader experience before revision.
- Closed-loop `agent-write-workflow` covering model-backed chapter planning, drafting, eight-dimension evaluation, targeted rewrite, retrospective drafting, canon-sync suggestions, and safe acceptance of previously absent target files.

### Changed

- Package metadata now includes project URLs and expanded keywords.
- CI and publish distribution checks include the newer onboarding docs, provider docs, chat runner example, and quickstart preview asset.
- Public-facing release and promotion copy now targets 0.1.1 as the recommended PyPI/TestPyPI candidate after the 0.1.0 MVP proof.
- Real-model revision dogfood now feeds the static P1/P2 issue ledger into comprehensive review and semantic verification, preserves role-diverse project context under tight budgets, and rejects token-level fixes that leave material chapter-wide prose clusters unresolved.
- Comprehensive reviewer output gets one bounded schema-repair retry when an otherwise useful model response is malformed; both the original and repaired outputs remain in the evidence bundle.
- Metaphor auditing now treats common Chinese explicit comparison markers as one family, records per-marker distribution and dominance, and routes implicit metaphor, literal likeness, register fit, and image precision to semantic review instead of rewarding mechanical synonym rotation.
- Draft evaluation now checks every planned preserve/forbidden constraint by stable ID and blocks acceptance when any explicit constraint fails, even if broad semantic dimensions pass.
- Revision verification now cross-checks P1/P2 review claims against required static metric deltas, preventing a model's self-reported fix from overriding unchanged counts or severity.
- Chapter-title verification now reads explicit engine headings such as `# Chapter 5 "Title"` before falling back to target filenames.
- Added typed, rebuildable project memory with source authority, hashes, line ranges, scoped retrieval, explicit author preferences, and acceptance-event history through `agent-memory`.
- Added model-backed pre-draft causal simulation, explicit chapter contracts, and per-scene entry/exit state handoffs to the closed-loop chapter writer.
- Added an independent adversarial reviewer that checks continuity, character/knowledge, prose/reader experience, every explicit constraint, and every expected scene state before semantic evaluation.
- Added deterministic story-contract checks for prohibited conclusions, suspicious forbidden-viewpoint scenes, constrained formal passages, and paragraph-rhythm evidence.
- Hash-guarded acceptance now records accepted manuscript events and invalidates the memory cache without automatically promoting model suggestions into canon or author preferences.
- Chapter plans are now checked against causal viewpoint whitelists, forbidden viewpoints, theme questions, and forbidden conclusions before prose generation, with one bounded plan-only repair.
- The OpenAI-compatible Chat runner now retries only transient transport failures, HTTP 429, and HTTP 5xx with bounded exponential backoff.

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
