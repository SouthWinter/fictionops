# FictionOps Agent Protocol

FictionOps lets AI agents participate in a long-form fiction workflow without turning the project into an unbounded chat transcript. The core idea is simple: agents receive scoped inputs, produce staged outputs, and humans decide what becomes manuscript or canon.

The Chinese protocol is the fuller reference: [agent-protocol.zh-CN.md](agent-protocol.zh-CN.md).

## What FictionOps Is

FictionOps is not a single autonomous novelist. It is an agentic workflow harness: a file structure, CLI, context packer, task bundler, runner bridge, inbox, and gate system that lets a human author and one or more agents share the same long-form project without losing canon, scope, or review order.

Use three levels when describing an integration:

- Level 1, AI-assisted workflow: a human chooses the next task, then uses `context-pack`, `agent-prompt`, or `agent-run` to hand a bounded job to a model or collaborator.
- Level 2, agentic workflow: scripts or an external controller read FictionOps JSON output, select the next safe command, run audits, and return staged output for review.
- Level 3, autonomous writing agent: an external controller may advance many tasks, but FictionOps still requires staged outputs, project gates, and human authority before manuscript or canon changes are accepted.

The current package supports Level 1 directly and provides the primitives for Level 2. Level 3 belongs outside the core package unless its controller preserves the same safety contract. For the short answer to whether an AI-connected FictionOps setup counts as an agent workflow, see [Agent workflow positioning](agent-workflow.md). For concrete wiring patterns, see [Agent integration guide](agent-integration.md). For the stdin/stdout, runner, and controller boundary expected from external tools, see [Agent connector contract](agent-connector-contract.md).

## Boundaries

An agent may help with:

- project handoff;
- outline and chapter planning;
- information-boundary checks;
- character memory checks;
- prose-pattern audits;
- staged draft or review output;
- release preparation.

An agent must not:

- overwrite manuscript or canon files without explicit human action;
- treat outdated notes as canon;
- reveal future secrets to a current chapter;
- flatten every character into the same intelligence pattern;
- turn every ambiguity into explanation;
- store API keys in project files.

## Recommended Roles

| Role | Main Input | Main Output |
| --- | --- | --- |
| `architect` | series outline, book outline, endpoints | structure advice and irreversible-event checks |
| `canon-keeper` | canon tables, drafts, decision log | conflict report and sync suggestions |
| `character-auditor` | arcs, voice profiles, chapters | character drift findings |
| `info-boundary-auditor` | information table, chapter text | early-reveal and knowledge-boundary findings |
| `foreshadowing-auditor` | echo table, chapters | plant/echo/payoff gap report |
| `chapter-planner` | book outline, previous chapter, canon | chapter engine and scene order |
| `draft-writer` | chapter engine, voice, info limits | staged draft text |
| `style-auditor` | chapter text | repeated-pattern and freshness findings |
| `publisher` | clean Markdown, metadata, checklist | publish artifacts and copy suggestions |

## Prepare A Model Boundary

`model-config` records provider and model names. It does not store real key values.

```bash
fictionops model-config my-novel \
  --provider openai \
  --planning-model planner \
  --drafting-model writer \
  --audit-model auditor \
  --api-key-env OPENAI_API_KEY \
  --write
```

The `api_key_env` value is the name of an environment variable. The key itself stays outside the project.

## Prepare A Task Bundle

Use `agent-run` to create a bounded task directory:

```bash
fictionops agent-run my-novel \
  --role draft-writer \
  --book book_01 \
  --chapter 001 \
  --out-dir 00_management/agent_runs/ch_001
```

The run directory contains:

- `README.md`: human-readable task summary;
- `request.json`: machine-readable role, task, book, chapter, safety policy, provider, and model;
- `prompt.md`: role prompt and output contract;
- `context_pack.md`: scoped project context;
- `draft_brief.md`: present for chapter drafting tasks.

`agent-run` is prepare-only. It does not call a model.

## Execute An External Runner

Use `agent-exec` when you already have a local model script, remote-model wrapper, or agent CLI:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python run_model.py
```

FictionOps sends the task bundle to the runner on stdin. The runner should write only the staged result to stdout. FictionOps saves stdout to `output.md` and writes `execution.json`.

The repository includes a no-model smoke runner:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python fictionops/examples/agent_runner_echo.py
```

Use it to confirm the pipe before replacing the echo body with a real model call.

The repository also includes a generic OpenAI-compatible Chat Completions runner for providers such as DeepSeek, Qwen/DashScope compatible mode, Kimi/Moonshot, GLM/Zhipu, Doubao/Volcengine Ark, SiliconFlow, and local OpenAI-compatible servers. The v1 runner supports provider presets, explicit `.env` files, dry-run reports, and output-length guards.

First run it without network access:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --dry-run \
  --provider deepseek \
  --model deepseek-chat
```

Then, after reviewing the boundary, run it with a real model and the provider key set outside the project:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --provider deepseek \
  --model deepseek-chat \
  --max-output-chars 12000
```

The example uses the Chat Completions `/chat/completions` endpoint and appends that path to the resolved base URL. For providers without presets, pass `--api-key-env` and `--base-url` explicitly. For provider starting points, see [Model providers](model-providers.md).

The repository also includes an OpenAI Responses API runner example. It is still external to FictionOps core: it reads the API key from the environment, receives the agent bundle on stdin, writes staged Markdown to stdout, and never applies output to manuscript or canon files.

First run it without network access:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
```

Then, after reviewing the boundary, run it with a real model and `OPENAI_API_KEY` set:

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --model your-model
```

You can also set `FICTIONOPS_OPENAI_MODEL` instead of passing `--model`. The example uses the OpenAI Responses API `/v1/responses` endpoint; if OpenAI changes provider behavior, update the external runner rather than weakening FictionOps' staged-output contract.

## Review Returned Output

After a runner or human collaborator writes staged output, use:

```bash
fictionops agent-inbox my-novel
fictionops agent-inbox my-novel/00_management/agent_runs/ch_001 --format json
```

`agent-inbox` checks whether the run has a valid request and exactly one non-empty staged output. It reports:

- `awaiting_output`: no output yet;
- `ready_for_review`: one usable output exists;
- `needs_attention`: damaged request, empty output, or multiple output candidates.

Ready output still needs human review and later gates such as `post-draft`, `review-gate`, or `revision-plan`.

## Select The Next Safe Step

Use `agent-next` when an external controller needs a machine-readable next command:

```bash
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
```

It reads project health, import queues, agent inbox state, optional chapter state, and publish gates, then returns `selected_command`, `selected_reason`, candidate actions, and evidence. It does not execute the command. This is the Level 2 controller boundary: automation may choose the next safe FictionOps command, but staged outputs and canon/manuscript changes still need gates and human authority. If the target is the FictionOps package checkout itself, `agent-next` reads stable-core governance action items instead of treating the tool repository as a legacy novel project.

`audit-agent-workflow <package-checkout> --level controller` follows the same package-governance boundary. It should report `fictionops_package: true`, surface the selected stable-core stage, and return `needs_human_review` when the remaining action requires external release, dogfood, or stability-window evidence that a controller must not fabricate.

The repository includes a no-model controller example:

```bash
python fictionops/examples/agent_controller_next.py my-novel --chapter 001 --cli fictionops
```

When running from a source checkout without installation, pass the source CLI as the command prefix:

```bash
python fictionops/examples/agent_controller_next.py my-novel --chapter 001 --cli python fictionops/src/fictionops/cli.py
```

For a multi-step no-model loop, use `agent_controller_loop.py`. It repeatedly calls `agent-next`, executes only candidates marked safe and not requiring human review, writes an optional JSONL log, and stops before staged output or manuscript/canon authority boundaries:

```bash
python fictionops/examples/agent_controller_loop.py my-novel --chapter 001 --max-steps 3 --log 00_management/agent_runs/controller_loop.jsonl --cli fictionops
```

## Human Override

FictionOps treats agents as collaborators, not final authorities. Human decisions may override audit suggestions for aesthetic, structural, or long-arc reasons. Important overrides should be recorded in the decision log or relevant retrospective so the next human or agent does not reopen the same question blindly.
