# Agent Connector Contract

This contract is for anyone wiring a model runner, IDE agent, local automation, or external controller to FictionOps.

FictionOps core remains model-free. A connector may call a model, select safe commands, or produce draft/review material, but it must preserve the staged-output boundary.

## Stable Connector Shape

```text
FictionOps project
  -> fictionops agent-connect connector kit
  -> fictionops agent-run / context-pack / agent-prompt / draft-brief
  -> agent run directory
  -> external connector
  -> staged output.md plus execution.json
  -> fictionops agent-inbox / gates / human decision
```

The connector is outside the core package. The project files are the source of truth.

## Connector Kit Contract

`fictionops agent-connect` creates a durable handshake directory for an external integration. It does not call a model, store a real key, execute a controller, or apply staged output.

The kit contains:

| File | Owner | Purpose |
| --- | --- | --- |
| `connector_manifest.json` | FictionOps | Machine-readable connector mode, provider/model metadata, allowed commands, forbidden actions, smoke commands, and safety flags. |
| `.env.example` | FictionOps | Environment-variable names only; never real secrets. |
| `smoke_commands.md` | FictionOps | Commands proving the staging boundary before a real model is trusted. |
| `README.md` | FictionOps | Human-readable connector instructions. |
| `runner_adapter.py` | FictionOps | No-network smoke-test adapter that can be replaced by a real model wrapper. |

## Runner Contract

A runner is any command passed to `fictionops agent-exec --runner ...`.

It must:

- read the full bundle from stdin;
- write exactly one proposed staged result to stdout;
- write diagnostics, progress, and provider logs to stderr;
- exit nonzero when no usable staged result should be saved;
- keep API keys outside the project, usually through environment variables;
- avoid editing `03_characters/`, `04_structure/`, `05_canon/`, `06_drafts/`, `08_publish/`, or other project files directly.

It may:

- call a hosted model, local model, IDE assistant, or custom agent framework;
- read `request.json`, `prompt.md`, `context_pack.md`, and optional `draft_brief.md` from stdin;
- include short self-check notes in stdout when the role prompt asks for them;
- use `model-config` metadata to choose a provider or model.

It must not:

- apply its own output to manuscript or canon;
- store real credentials in `request.json`, `execution.json`, or project Markdown;
- treat missing context as permission to invent canon;
- bypass `agent-inbox`, `post-draft`, `review-gate`, `book-gate`, or `release-gate`.

## Controller Contract

A controller is an external loop that calls `fictionops agent-next --format json`.

It may execute a selected command only when all of these are true:

- the candidate is marked safe by FictionOps;
- the command does not apply staged model output;
- the command does not overwrite manuscript, canon, credentials, or release artifacts;
- the same command is not repeating without changing project evidence;
- no human-review boundary has been reported.

It must stop when:

- `agent-next` reports a review boundary;
- `agent-inbox` has ready staged output;
- migration is blocked by ambiguous imports or unwaived repair groups;
- publish or release steps require external credentials, service state, or human confirmation;
- the next action is a placeholder, unknown command, or a command outside FictionOps' safe list.

## Required Files

An `agent-run` directory should contain:

| File | Owner | Purpose |
| --- | --- | --- |
| `request.json` | FictionOps | Machine-readable role, task, project scope, model metadata, and safety contract. |
| `prompt.md` | FictionOps | Human-readable role prompt and output rules. |
| `context_pack.md` | FictionOps | Scoped project context for the task. |
| `draft_brief.md` | FictionOps | Present for chapter-drafting tasks. |
| `output.md` | Connector through `agent-exec` | Staged result for review. |
| `execution.json` | FictionOps | Runner command, exit code, output path, and safety metadata. |

External connectors should ignore unknown JSON keys and prefer named keys over positional assumptions.

## Minimal Smoke Test

Before using a real model:

```bash
fictionops agent-connect my-novel --name local-runner --mode runner
fictionops agent-smoke my-novel --connector local-runner
```

That single smoke command runs the connector kit's no-network adapter through `audit-agent-workflow`, `agent-run`, `agent-exec`, and `agent-inbox`. The expanded manual path is:

```bash
fictionops agent-connect my-novel --name local-runner --mode runner

fictionops agent-run my-novel \
  --role draft-writer \
  --book book_01 \
  --chapter 001 \
  --out-dir my-novel/00_management/agent_runs/ch_001

fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_echo.py

fictionops agent-inbox my-novel/00_management/agent_runs/ch_001 --format json
```

The smoke is successful when `agent-inbox` reports one ready staged output and no damaged request, empty output, or multiple-output issue.

## OpenAI-Compatible Chat Example

The repository includes `examples/agent_runner_openai_chat.py` as a generic provider-backed runner for OpenAI-compatible Chat Completions APIs. It is useful for DeepSeek, Qwen/DashScope compatible mode, Kimi/Moonshot, GLM/Zhipu, Doubao/Volcengine Ark, SiliconFlow, local servers, and similar providers. The v1 runner supports provider presets, explicit `.env` files, dry-run reports, and output-length guards.

Dry-run first:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --dry-run \
  --provider deepseek \
  --model deepseek-chat
```

Then run with a real key only from the environment:

```bash
set DEEPSEEK_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --provider deepseek \
  --model deepseek-chat \
  --max-output-chars 12000
```

For providers without a preset, pass `--api-key-env` and `--base-url` explicitly. For local no-auth servers, use `--provider local-openai`.

## OpenAI Responses Example

The repository includes `examples/agent_runner_openai_responses.py` as a provider-backed runner example. It is still a connector, not FictionOps core.

Dry-run first:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
```

Then run with a real key only from the environment:

```bash
set OPENAI_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --model your-model
```

## Acceptance Evidence

A connector integration is ready to be trusted only when it leaves evidence:

- a task bundle exists;
- the connector can run a no-network smoke;
- real credentials are absent from project files;
- staged output is visible to `agent-inbox`;
- later FictionOps gates still decide whether the output can enter manuscript, canon, or release artifacts;
- external run IDs or URLs are recorded when a milestone depends on service state.

This is the line between a casual AI writing session and an auditable FictionOps agent workflow.
