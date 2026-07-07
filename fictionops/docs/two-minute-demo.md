# FictionOps Two-Minute Demo Script

This is a short recording or live-demo script. For the longer walkthrough, use [Demo tutorial](tutorial-demo.md).

You do not have to record it yourself to make the project usable. The script is useful in three modes:

- Live demo: run the commands while explaining the boundary.
- Terminal recording: capture the same sequence as GIF, MP4, or asciinema.
- Interview walkthrough: describe the commands without running them.

## Setup

From a source checkout:

```bash
cd fictionops/examples/demo_novel
```

If FictionOps is installed, use `fictionops`. From a source checkout without installation, replace `fictionops` with:

```bash
python ../../src/fictionops/cli.py
```

The commands below use `fictionops` for readability.

## 0:00 - Position The Problem

Say:

> FictionOps is not an autonomous novelist. It is a file-based workflow harness for long fiction: canon, outlines, information boundaries, task bundles, staged model output, audits, and publishing gates.

Show:

```bash
fictionops doctor . --book book_01
```

Expected point: the demo project is small on purpose, and `doctor` surfaces maintenance signals rather than pretending everything is complete.

## 0:20 - Turn Outline Into A Chapter Work Surface

Say:

> First, I sync the book outline into the chapter engine. This gives the chapter a local pressure, desire, obstacle, change, remainder, viewpoint, kind, and target length.

Run:

```bash
fictionops plan-chapter . --chapter 002 --force
```

Expected point: FictionOps prepares structured writing work from ordinary Markdown files.

## 0:40 - Build A Scoped Draft Brief

Say:

> For a million-character project, the model should not receive the whole book. It should receive a scoped brief: scene needs, canon, information boundaries, echoes, and voice notes within a context budget.

Run:

```bash
fictionops draft-brief . --chapter 002 --include-context-content --max-total-chars 4000
```

Expected point: the CLI creates a bounded writing brief instead of dumping all project memory into a prompt.

## 1:00 - Prepare An Agent Bundle

Say:

> Now I prepare an agent task bundle. This is still not giving a model direct write access to the manuscript. It is packaging a task, context, and constraints.

Run:

```bash
fictionops agent-run . --role draft-writer --chapter 002 --out-dir 00_management/agent_runs/ch_002_two_minute_demo --force
```

Expected point: the bundle is a reviewable file artifact, not an invisible chat state.

## 1:20 - Execute A No-Model Runner

Say:

> This echo runner stands in for any external API or agent wrapper. A real runner can call OpenAI, DeepSeek, Qwen, a local server, or another controller, but FictionOps only accepts staged output.

Run:

```bash
fictionops agent-exec 00_management/agent_runs/ch_002_two_minute_demo --force --runner python ../../examples/agent_runner_echo.py
```

Expected point: runner output is captured as a staged artifact and receipt.

## 1:40 - Inspect The Inbox

Say:

> The output lands in an inbox. Human review, gates, and explicit application remain outside the runner boundary.

Run:

```bash
fictionops agent-inbox . --format json
```

Expected point: the workflow is API-backed and can become agentic with a controller, but FictionOps itself keeps the review boundary visible.

## 1:55 - Close With The Boundary

Say:

> The important part is not that the tool writes prose for you. The important part is that it makes a long novel maintainable: scoped context, visible handoffs, staged AI output, audits, release artifacts, and repeatable project state.

Optional final command:

```bash
fictionops doctor . --book book_01
```

## Recording Notes

For a simple terminal transcript on PowerShell:

```powershell
Start-Transcript .\fictionops-two-minute-demo.txt
# run the demo commands
Stop-Transcript
```

For an asciinema recording:

```bash
asciinema rec fictionops-two-minute-demo.cast
# run the demo commands
exit
```

Keep the recording honest: if `doctor` reports gaps, say that the demo project is intentionally small and the gaps are exactly what the audit layer is supposed to expose.
