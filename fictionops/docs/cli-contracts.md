# FictionOps CLI Contracts

This is the English contract reference for the current CLI. The fuller command-by-command reference remains the Chinese document: [cli-contracts.zh-CN.md](cli-contracts.zh-CN.md). This file exists so external contributors can understand the stable behavior FictionOps promises before reading the deeper Chinese reference.

For version-stage compatibility, additive-change rules, breaking-change definitions, and controller guidance, see [compatibility.md](compatibility.md).

## General Contract

All FictionOps commands follow these rules:

- Commands operate on ordinary project files. There is no hidden database.
- Read-only audit commands must not mutate project files unless an explicit `--out` path is provided.
- Commands that write files must refuse to overwrite existing files unless they expose and receive `--force`, or unless the command has a deliberately narrow safe-replacement option.
- JSON output is intended for controllers and tests. Markdown output is intended for humans.
- CLI failures should exit non-zero and write a short actionable error to stderr.
- Commands should preserve user-written manuscript and canon files unless the user explicitly asks for a write operation.
- Agent-facing commands must not save real API keys.
- FictionOps core must not call a model unless a future command explicitly says that it does. In 0.1.0, model execution is delegated to external runners through `agent-exec`.

## Command Groups

The current CLI exposes 60 MVP commands:

| Group | Commands | Contract Summary |
| --- | --- | --- |
| Migration | `adopt`, `adopt-review`, `adopt-plan`, `import-plan` | Diagnose and stage migration from an existing project without modifying the source directory; explicit migration waivers may defer known blockers without deleting the audit record. |
| Project setup | `init`, `new-book`, `new-chapter` | Create standard folders and starter files; avoid overwrites unless forced. |
| Chapter planning | `plan-chapter`, `scene-plan`, `draft-brief` | Turn book-outline material into chapter engines, scene plans, and task briefs without writing prose. |
| Draft closure | `post-draft`, `review-gate`, `book-gate`, `retrospective` | Check whether draft, chapter, and book memory are ready for the next step. |
| Audits | `audit-plan`, `stats`, `scan-words`, `check-tables`, `audit-wave`, `audit-style`, `review-workflow`, `audit-continuity`, `audit-echoes`, `audit-info`, `audit-characters` | Report structure, prose-pattern, review workflow, continuity, information, echo, and character-memory issues. |
| Agent workflow | `agent`, `setup-ai`, `model-config`, `context-pack`, `agent-prompt`, `agent-connect`, `eval-agent`, `agent-smoke`, `agent-run`, `agent-exec`, `agent-inbox`, `agent-memory`, `agent-revise-workflow`, `agent-write-workflow`, `agent-accept-revision`, `write-chapter`, `revise-chapter`, `audit-chapter`, `agent-session`, `agent-next`, `audit-agent-workflow`, `workflow-plan`, `revision-plan` | Use one stateful product entry or the lower-level research interface to retrieve memory, run causal simulation and adversarial review, draft/revise/verify chapters, explicitly accept hash-matched candidates, and preserve human authority over manuscript/canon changes. |
| Publishing | `export-clean`, `audit-publish`, `publish-copy`, `export-metadata`, `export-manifest`, `export-epub`, `audit-epub`, `release-gate` | Generate and audit clean manuscript, metadata, manifest, EPUB, and final release readiness. |
| Package release governance | `audit-release-evidence`, `audit-dogfood-cycle`, `audit-stability-window`, `audit-stable-core` | Audit FictionOps package release-trial, sustained dogfood-cycle, stability-window, and aggregate stable-core evidence so empty templates, too-short evidence windows, or unfinished drafts cannot close release or 1.0 milestones; stable-core JSON also exposes structured `action_items` for the remaining evidence lanes. |
| Reporting | `doctor`, `report` | Aggregate project health into human-readable or machine-readable reports. |

## Read/Write Boundaries

| Command Type | Writes By Default | Notes |
| --- | --- | --- |
| `adopt` | No | `--copy-to` writes into a separate initialized sandbox and leaves the source project untouched. |
| `adopt-review`, `audit-*`, `stats`, `doctor`, `book-gate`, `release-gate` | No | These are reporting commands unless `--out` is passed; `audit-release-evidence`, `audit-dogfood-cycle`, `audit-stability-window`, and `audit-stable-core` are read-only and have no write mode. |
| `init`, `new-book`, `new-chapter` | Yes | They create project scaffolds and must not overwrite user files without `--force`. |
| `plan-chapter` | Yes | It fills a chapter engine from an outline while preserving existing fields unless forced. |
| `scene-plan`, `draft-brief`, `workflow-plan`, `revision-plan`, `publish-copy` | No | They write only when `--out` is passed. |
| `agent-connect` | Yes | It writes a connector handshake kit with a manifest, environment example, smoke commands, and adapter stub. It does not call a model or store credentials. |
| `eval-agent` | Optional | It copies a project fixture to a temporary directory, runs a no-network evaluation chain, and writes a report only when `--out` is passed. It does not modify the source fixture or call a provider. |
| `agent-smoke` | Yes | It writes a smoke task bundle, runs the connector adapter through `agent-exec`, and leaves staged output for `agent-inbox`; it does not apply output to manuscript or canon. |
| `agent-run` | Optional | It can write a task bundle to `--out-dir`, but it does not call a model. |
| `agent-exec` | Yes | It runs an external command for an existing task bundle and saves stdout as staged output. It does not apply that output. |
| `agent-revise-workflow` | Optional | It packages a source chapter plus a review-workflow report; with `--runner`, it produces a staged candidate, diff, before/after audits, targeted retry evidence, and static/semantic verification. |
| `agent-write-workflow` | Optional | It compiles project-aware context, calls a chapter planner, drafts a new chapter, evaluates eight semantic dimensions, performs bounded targeted rewrites, and stages retrospective/canon-sync suggestions. |
| `agent-accept-revision` | Yes, explicitly | It applies only a `ready_for_approval` candidate and refuses stale source or post-verification candidate changes by comparing SHA-256 hashes. |
| `write-chapter`, `revise-chapter`, `audit-chapter` | Optional | They prepare a staged task bundle and only execute a model or external command when `--runner` is provided; returned output still goes through `agent-inbox`. |
| `agent-session` | Yes | It writes a session ledger under `00_management/agent_sessions/` that tracks planned chapter write/revise/audit runs and next review actions. It does not execute a runner or apply output. |
| `agent-inbox`, `agent-next`, `audit-agent-workflow`, `model-config` without `--write` | No | They inspect or report state. |
| `setup-ai` | Yes | It writes `00_management/model_config.json` and an API-key-free `00_management/ai_runner.env.example`. It records environment variable names only, never raw keys, and does not call a provider. |
| `model-config --write` | Yes | It records provider/model names and an environment-variable name for the key, not the key value. |
| `export-clean`, `export-metadata`, `export-manifest`, `export-epub` | Yes | They generate publish artifacts and refuse unsafe overwrites unless forced. |

## Agent Safety Contract

FictionOps treats agent output as staged evidence, not as authority.

- `context-pack` scopes the files that an agent may read.
- `agent-prompt` defines role, task, limits, and output contract.
- `agent-connect` writes a connector manifest, environment example, smoke commands, and adapter stub for long-lived external integrations.
- `eval-agent` runs a reproducible T1-T5 harness smoke on a temporary copy and reports whether staged output, inbox review, and controller stop behavior remain intact.
- `agent-smoke` proves the connector staging boundary by chaining `audit-agent-workflow`, `agent-run`, `agent-exec`, and `agent-inbox` with the no-network adapter.
- `agent-smoke --force` may overwrite only the current smoke run's own bundle/output; unrelated staged agent outputs still stop the smoke chain.
- `agent-run` packages the prompt, request metadata, context pack, and optional draft brief.
- `agent-exec` may call an external model runner, but FictionOps itself only passes stdin and captures stdout.
- A runner may emit one `FICTIONOPS_RUNNER_RECEIPT:` JSON line on stderr using schema `fictionops.runner_receipt.v1`. FictionOps validates and stores provider/model/request-id, token usage, and optional cost telemetry without mixing metadata into staged stdout. Runners without a receipt remain supported.
- `agent-inbox` checks whether returned output is present, unique, and ready for review.
- `agent write|revise|resume|status|accept|continue` is the unified product surface over the same runtime. `agent status` is read-only and aggregates session states, author actions, persistent issues, token usage, and cost. `continue --execute` may run only selected R0 maintenance such as rebuilding a stale derived memory index; approval, budget changes, failed candidates, and canon-sync suggestions remain human boundaries. `agent issues` reads the persistent cross-session issue ledger; `agent issue` records explicit author waive/reject/reopen decisions with a required reason.
- `agent continue` consumes the pure `select_agent_policy(state, evidence, budget, authority)` decision layer. Policy outputs name the action, risk level, required authority, and whether execution is permitted; model output cannot grant itself author authority.
- Each write/revision run appends `trajectory.jsonl` steps with schema `fictionops.agent_trajectory_step.v1`, covering runtime/control events, attributed context, model calls and telemetry, state transitions, evidence, and authority.
- `agent benchmark` runs repeated `raw`, `rag`, `full`, `no_memory`, `no_guard`, and `no_contract` review conditions through one runner without exposing fixture answers. `agent failure-lab` injects bounded state, artifact, budget, receipt, reviewer, and story-contract failures in temporary workspaces and reports detection, recovery, and protected-hash outcomes.
- Write/revision sessions persist `checkpoint.json` at phase boundaries with source and artifact hashes. `agent cancel` records an explicit reason, makes the checkpoint non-resumable, and refuses duplicate cancellation or cancellation after apply. `agent resume RUN_DIR --runner ...` validates the session, source, engine, and checkpoint artifacts before starting a fresh budget segment. It resumes write sessions from `context_ready`, `causal_ready`, `plan_ready`, or `draft_ready`, and revision sessions from `context_ready`, `review_ready`, or `verification_ready`, without replaying completed model phases. The runner command must be last because it consumes the remaining CLI arguments. Unsupported, cancelled, stale, or tampered checkpoints are refused.
- `agent-revise-workflow` packages a chapter, review-workflow report, and revision contract for a model-backed revision runner; after execution it creates a persistent session, issue snapshots, diff, before/after audits, at most the configured targeted retries, and a model-backed semantic invariant check. `--max-model-calls` (default 12) and `--max-runtime-seconds` (default 1800) are hard controller budgets recorded in `model_budget.json`; optional `--max-total-tokens`, `--max-cost`, and `--cost-currency` stop before the next call once receipt-backed cumulative usage reaches the threshold. It never applies the revised text automatically.
- `agent-revise-workflow` defaults to a project-aware six-dimension pre-review covering continuity, character, information boundaries, foreshadowing, chapter function, and prose/reader experience. `--review-scope style` retains the narrower prose-pattern path for smoke tests or deliberately limited work.
- `agent-write-workflow` accepts a missing target chapter or generated placeholder, but refuses substantive existing prose. It requires a chapter engine, creates a model-backed causal simulation, structured quantity/time/object fact ledger, and execution plan, then drafts either the full chapter or separate state-aware scenes with `--scene-by-scene`. Failed scene evidence is routed back only to matched scenes when possible. `--max-model-calls` (default 32) and `--max-runtime-seconds` (default 3600) stop before an over-budget runner call and record `model_budget.json`. It reaches `ready_for_approval` only after all blocking checks pass.
- `agent-accept-revision` is the explicit R3 authority boundary. It applies only a verified candidate, checks both source and candidate hashes, writes `acceptance.json`, and atomically replaces the source file. It has no stale-source override.
- `write-chapter`, `revise-chapter`, and `audit-chapter` compose the staged agent workflow for common writing tasks while preserving the same review boundary.
- `agent-session` persists the intended multi-step workflow and reads staged run state, but it still stops at `agent-inbox` review boundaries.
- `setup-ai` may generate provider setup files and suggested commands, but it must not store raw API keys or make a model call.
- `agent-next` recommends a safe next command for an external controller, but it does not execute it. When the target is a FictionOps package checkout, it selects from stable-core governance action items instead of legacy-project migration.
- `audit-agent-workflow` checks whether the project is ready for manual, runner, controller, or model-runner integration before a runner/controller is connected; with `--connector <name>`, it also validates the connector kit manifest, required files, smoke commands, and safety flags. When the target is a FictionOps package checkout and the level is `controller`, it reports package-governance evidence from `agent-next` and stops at human-review boundaries rather than recommending project adoption.

Package-release evidence commands are also read-only governance gates. `audit-release-evidence` may return `ready=true` only for accepted external evidence with a GitHub Actions run, artifact hashes, a named reviewer, explicit passing smoke results, and either TestPyPI URLs plus a clean install command or a recorded TestPyPI skip reason and acceptor.

The safe path is:

```text
context-pack / draft-brief
  -> agent-connect
  -> agent-smoke
  -> agent-run
  -> external runner or human collaborator
  -> agent-inbox
  -> post-draft / review-gate / revision-plan
  -> human decision before manuscript or canon changes
```

Any automation that lets a model directly overwrite canon or manuscript files is outside the FictionOps 0.1.0 safety contract.

## Migration Waiver Contract

`adopt-review` and `adopt-plan` may load `07_audits/adopt_review/waivers.json` by default, or an explicit file passed with `--waivers`.

- A waiver file is JSON, either a list or an object with a `waivers` list.
- Each waiver must include a non-empty `reason`.
- Each waiver must match at least one of `source`, `code`, `subject`, or `path`; provided fields must equal the corresponding issue fields.
- Waived issues are excluded from active `issue_count`, active `blocking_issue_count`, check counts, and `adopt-plan` tasks.
- Reports keep `total_issue_count`, `waived_issue_count`, `waiver_file`, and `waivers` so the human decision remains auditable.
- Waivers do not override physical import-queue state. If files remain in `06_drafts/import_queue/`, `adopt-review` must still return `needs_import_sorting`.

## Output Stability

JSON reports are intended to be stable enough for tests and simple controllers. Existing keys should not be removed casually. When a report needs to grow, prefer adding keys rather than changing old meanings.

Markdown reports are allowed to be more readable and less machine-stable. They should still include enough command suggestions and status labels for a human to know the next step.

External controllers should follow the compatibility policy: ignore unknown JSON keys, stop on missing expected keys, and treat unknown statuses as human-review boundaries.

## Package Contract

A release candidate should prove:

- CLI help exposes every MVP command.
- `compileall` succeeds for `src/fictionops` and `examples`.
- The full unittest suite passes.
- wheel and sdist build successfully.
- wheel contains CLI modules, agent modules, entry points, and packaged templates.
- sdist contains source, docs, examples, root templates, tests, and workflow docs.
- installing the wheel in a clean virtual environment supports `fictionops --version`, `python -m fictionops --version`, `fictionops init`, `fictionops doctor`, and representative agent commands.
