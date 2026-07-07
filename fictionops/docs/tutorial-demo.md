# FictionOps Demo Tutorial

This tutorial uses `examples/demo_novel/` to show the smallest useful FictionOps loop: sync outline data, build a scene plan, prepare a draft brief, create an agent task bundle, run the no-model echo runner, and inspect project health.

The Chinese version is here: [tutorial-demo.zh-CN.md](tutorial-demo.zh-CN.md).

## 1. Enter The Demo Project

From the repository root:

```bash
cd fictionops/examples/demo_novel
```

If FictionOps is installed:

```bash
fictionops doctor . --book book_01
```

From the source checkout without installation:

```bash
python ../../src/fictionops/cli.py doctor . --book book_01
```

The commands below use `fictionops`. Replace it with `python ../../src/fictionops/cli.py` when running directly from source.

## 2. Sync The Book Outline Into A Chapter Engine

Chapter 2 is intentionally left ready for outline sync:

```bash
fictionops plan-chapter . --chapter 002 --force
```

This reads `04_structure/book_outlines/book_01_outline.md` and fills the matching chapter engine with pressure, desire, obstacle, change, remainder, viewpoint, kind, and target length.

## 3. Build A Scene Plan

```bash
fictionops scene-plan . --chapter 002
```

`scene-plan` does not write prose. It turns the chapter engine into scene-level work so a writer or agent can see what each scene must change.

## 4. Build A Draft Brief

```bash
fictionops draft-brief . --chapter 002 --include-context-content --max-total-chars 4000
```

The draft brief combines scene work, scoped context, information boundaries, echo tables, voice notes, and writing constraints. The total context budget matters for very large novels.

## 5. Create A Handoff Pack

```bash
fictionops context-pack . --task handoff --no-content
```

The handoff pack lists the files a new collaborator should read first: handoff log, decision log, outline, canon tables, character notes, information boundaries, echo tables, reports, revision plans, and gates when present.

## 6. Prepare And Execute A Demo Agent Run

Create a prepare-only agent bundle:

```bash
fictionops agent-run . --role draft-writer --chapter 002 --out-dir 00_management/agent_runs/ch_002_demo --force
```

Run the no-model echo runner from the repository root path. If you are still inside `fictionops/examples/demo_novel`, use:

```bash
fictionops agent-exec 00_management/agent_runs/ch_002_demo --runner python ../../examples/agent_runner_echo.py
```

To test the OpenAI Responses runner boundary without network access:

```bash
fictionops agent-exec 00_management/agent_runs/ch_002_demo --force --runner python ../../examples/agent_runner_openai_responses.py --dry-run --model your-model
```

Then inspect the staged output:

```bash
fictionops agent-inbox . --format json
```

This confirms the agent pipe. A real integration can replace the echo runner with a model or agent wrapper that reads stdin and writes staged Markdown to stdout; the OpenAI example does that through `agent-exec` while keeping output staged.

## 7. Ask A Demo Controller For The Next Step

The repository also includes a tiny Level 2 controller example. It calls `agent-next`, prints the selected command, and stops before executing anything:

```bash
python ../../examples/agent_controller_next.py . --chapter 002 --no-text-scan --cli fictionops
```

When running directly from source, point it at the source CLI:

```bash
python ../../examples/agent_controller_next.py . --chapter 002 --no-text-scan --cli python ../../src/fictionops/cli.py
```

For a no-model loop that can execute safe commands and stop at review boundaries:

```bash
python ../../examples/agent_controller_loop.py . --chapter 002 --no-text-scan --max-steps 3 --log 00_management/agent_runs/controller_loop.jsonl --cli fictionops
```

This demonstrates the controller boundary: automation can choose a safe next command, while staged output still waits for inbox review, gates, and human approval.

## 8. Run A Health Check

```bash
fictionops doctor . --book book_01 --format json
```

The demo project is intentionally tiny, so `doctor` will report maintenance gaps. That is expected. The point is to show how FictionOps exposes structure, continuity, information, character, agent-output, and release signals from ordinary project files.
