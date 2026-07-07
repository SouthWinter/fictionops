# Agent Integration Guide

This guide shows how to connect an external model API, runner, or controller to FictionOps without letting model output silently overwrite manuscript or canon files.

FictionOps core is the workflow harness. A runner may be a simple API wrapper, a local script, an IDE tool, or a model service client; a controller may turn those calls into an agentic loop. For the compact interface contract that external runners and controllers should follow, see [Agent connector contract](agent-connector-contract.md).

## Integration Levels

| Level | Use When | FictionOps Commands | Who Applies Output |
| --- | --- | --- | --- |
| Manual chat helper | A writer wants to paste scoped context into ChatGPT, Claude, a local model, or another assistant. | `context-pack`, `agent-prompt`, `draft-brief` | Human |
| External runner | A script, API wrapper, or model service client can read stdin and write stdout. | `agent-connect`, `agent-smoke`, `agent-run`, `agent-exec`, `agent-inbox` | Human, after review |
| Controller loop | A script should choose and run safe FictionOps commands. | `agent-connect`, `agent-next`, `examples/agent_controller_loop.py` | Human at review boundaries |
| Provider-backed runner | A runner calls OpenAI, a local server, or another provider. | `model-config`, `agent-connect`, `agent-exec`, runner script | Human, after review |

The stable rule is: **external runners and controllers may produce staged output; they do not directly edit manuscript or canon.**

## Files And Data Flow

```text
project files
  -> agent-connect connector kit
  -> context-pack / agent-prompt / draft-brief
  -> agent-run task directory
  -> external runner or controller
  -> staged output in 00_management/agent_runs/
  -> agent-inbox / post-draft / review-gate / book-gate
  -> human decision
```

The task directory is the contract between FictionOps and the external runner or controller:

- `request.json` is the machine-readable task envelope.
- `prompt.md` is the role prompt and output contract.
- `context_pack.md` is the scoped project context.
- `draft_brief.md` exists when the task is chapter-drafting oriented.
- `output.md` is staged runner output, written by `agent-exec`.
- `execution.json` records the runner command, exit code, and output path.

`agent-connect` can also write a longer-lived connector kit under `00_management/agent_connectors/<name>/`. That kit contains `connector_manifest.json`, `.env.example`, `smoke_commands.md`, `README.md`, and a no-network `runner_adapter.py` stub for first smoke tests.

```bash
fictionops agent-connect my-novel --name openai-runner --mode model-runner
fictionops agent-smoke my-novel --connector openai-runner --dry-run
```

Use `agent-smoke` before a real model call when you want a single local proof that the connector kit, adapter, task bundle, staged output, and inbox boundary fit together. A passed smoke test proves the staging boundary, not model quality.

## Pattern 1: Manual Chat Or API Use

Use this when the model is accessed through a chat UI or any API/tool that does not have a runner script yet.

```bash
fictionops context-pack my-novel --task draft --book book_01 --chapter 001 --out context.md
fictionops agent-prompt my-novel --role draft-writer --book book_01 --chapter 001 --out prompt.md
fictionops draft-brief my-novel --book book_01 --chapter 001 --out brief.md
```

Give those files to the assistant manually. When the assistant returns text, paste it into a staging file or review it by hand. Do not treat chat output as canon until later gates pass.

## Pattern 2: External Runner

Use this when your model API call, local tool, or assistant can be wrapped as a command that reads stdin and writes stdout.

```bash
fictionops agent-run my-novel \
  --role draft-writer \
  --book book_01 \
  --chapter 001 \
  --out-dir my-novel/00_management/agent_runs/ch_001

fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_echo.py

fictionops agent-inbox my-novel/00_management/agent_runs/ch_001 --format json
```

Runner contract:

- read the full bundle from stdin;
- write only the proposed staged result to stdout;
- write diagnostics to stderr when needed;
- do not edit project files directly;
- exit nonzero when no usable staged output should be saved.

This makes it easy to plug in a local script, a hosted model wrapper, an IDE assistant, or a custom orchestration framework.

## Pattern 3: OpenAI Responses Runner

The repository includes an example runner for the OpenAI Responses API. It is intentionally outside FictionOps core.

Dry run first:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
```

Then run with a real provider only after setting the API key outside the project:

```bash
set OPENAI_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --model your-model
```

`model-config` may record which environment variable to use, but it must not store the key value.

```bash
fictionops model-config my-novel \
  --provider openai \
  --planning-model planner \
  --drafting-model writer \
  --audit-model auditor \
  --api-key-env OPENAI_API_KEY \
  --write
```

## Pattern 4: Controller Loop

Use this when an external controller should decide the next safe command from project evidence.

```bash
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
fictionops audit-agent-workflow my-novel --level controller --book book_01 --chapter 001 --connector openai-runner
```

For a no-model loop demo:

```bash
python fictionops/examples/agent_controller_loop.py my-novel \
  --chapter 001 \
  --max-steps 3 \
  --log my-novel/00_management/agent_runs/controller_loop.jsonl \
  --cli fictionops
```

The controller should stop when:

- `agent-next` reports a human-review boundary;
- an agent output is ready for review;
- the next command would overwrite manuscript or canon;
- migration state requires manual sorting or waivers;
- the same command is repeatedly suggested without progress.

## Safety Checklist

Before calling a real model or controller:

- `fictionops audit-agent-workflow <project> --level runner`, `--level controller`, or `--level model-runner` reports `ready`.
- If a connector kit is used, `fictionops audit-agent-workflow <project> --level <level> --connector <name>` reports `ready` and validates the connector manifest, safety flags, smoke commands, and required files.
- `fictionops agent-smoke <project> --connector <name>` can run the no-network adapter into `agent-inbox` before any real provider call.
- The project is initialized and has `project.yml`.
- The task has a bounded book/chapter or explicit audit scope.
- API keys live in environment variables, not project files.
- The runner writes staged output only.
- `agent-inbox` can see exactly one non-empty candidate output.
- Later gates such as `post-draft`, `review-gate`, `book-gate`, or `release-gate` still run before acceptance.
- Human decisions are recorded in decision logs or retrospectives when they override audit advice.

## What Not To Do

Do not connect a model, API runner, or controller by giving it write access to `06_drafts/`, `05_canon/`, or `04_structure/` and asking it to edit files directly. That may be useful for private experiments, but it is outside the FictionOps safety contract and cannot be treated as an auditable FictionOps workflow.
