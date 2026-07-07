# Agent Evaluation Demo Report

This report is the first reproducible evidence record for the [Agent evaluation protocol](agent-evaluation.md). It uses the bundled `examples/demo_novel/` fixture and no real model API call.

The purpose is narrow: verify that FictionOps can act as a long-horizon agent workflow harness by preparing a bounded task, routing runner output into staging, surfacing review boundaries, and stopping a controller loop before unreviewed output reaches canon or manuscript files.

This report does **not** claim literary quality improvement or model superiority.

## Run Metadata

- Date: 2026-07-07
- Repository commit: `2888a06a9aa2d137833a129dcd9d5d1235e34cd9`
- Project fixture: `fictionops/examples/demo_novel/`, copied to a temporary directory before execution
- Model / runner:
  - `examples/agent_runner_echo.py` for the no-model staged-output path
  - `examples/agent_runner_openai_chat.py --dry-run --model demo-model` for provider-backed runner wiring without a network call
- Controller:
  - `examples/agent_controller_next.py`
  - `examples/agent_controller_loop.py`
- Task IDs covered: `T1`, `T2`, `T3`, `T4`, `T5`

## Commands

The fixture was copied to a temporary directory first, so the tracked demo project was not modified.

```bash
REPO=/path/to/fictionops-release-checkout
python "$REPO/fictionops/src/fictionops/cli.py" plan-chapter . --chapter 002 --force
python "$REPO/fictionops/src/fictionops/cli.py" scene-plan . --chapter 002 --format json
python "$REPO/fictionops/src/fictionops/cli.py" draft-brief . --chapter 002 --include-context-content --max-total-chars 4000 --format json
python "$REPO/fictionops/src/fictionops/cli.py" agent-run . --role draft-writer --chapter 002 --out-dir 00_management/agent_runs/ch_002_eval --force --format json
python "$REPO/fictionops/src/fictionops/cli.py" agent-exec 00_management/agent_runs/ch_002_eval --format json --runner python "$REPO/fictionops/examples/agent_runner_echo.py"
python "$REPO/fictionops/src/fictionops/cli.py" agent-inbox . --format json
python "$REPO/fictionops/src/fictionops/cli.py" doctor . --format json
python "$REPO/fictionops/examples/agent_controller_next.py" . --chapter 002 --no-text-scan --cli python "$REPO/fictionops/src/fictionops/cli.py" --format json
python "$REPO/fictionops/examples/agent_controller_loop.py" . --chapter 002 --no-text-scan --max-steps 3 --log 00_management/agent_runs/controller_eval.jsonl --cli python "$REPO/fictionops/src/fictionops/cli.py" --format json
python "$REPO/fictionops/src/fictionops/cli.py" agent-exec 00_management/agent_runs/ch_002_eval --force --format json --runner python "$REPO/fictionops/examples/agent_runner_openai_chat.py" --dry-run --model demo-model
python "$REPO/fictionops/src/fictionops/cli.py" agent-inbox . --format json
```

Implementation note: `agent-exec` treats everything after `--runner` as the runner command, so FictionOps options such as `--format json` must appear before `--runner`.

## Observed Results

### T1: Scoped Task Bundle

`agent-run` produced a task directory at:

```text
00_management/agent_runs/ch_002_eval
```

The run directory contained the expected trace files:

```text
request.json
prompt.md
context_pack.md
draft_brief.md
```

This satisfies the minimal trace requirement for a bounded writing-agent task.

### T2: Staged Runner Output

The echo runner completed with:

```text
returncode: 0
output_file: 00_management/agent_runs/ch_002_eval/output.md
```

`agent-inbox` then reported:

```text
status: ready_for_review
run_count: 1
ready_count: 1
awaiting_count: 0
needs_attention_count: 0
state: ready_for_review
role: draft-writer
task: draft
book: book_01
chapter: 002
output_chars: 499
issue_count: 0
```

The next actions were review-oriented rather than direct-write:

```text
Review the staged draft, then manually apply accepted text to `06_drafts/book_01/chapters/ch_002.md`.
Run `fictionops post-draft . --book book_01 --chapter 002` after applying accepted text.
Run `fictionops review-gate . --book book_01 --chapter 002` before broader revision.
```

### T3: Project Health After Staging

`doctor` reported:

```text
status: needs_attention
issue_counts: P1=0, P2=2, P3=15, P4=9, P5=0
agent_inbox.status: ready_for_review
agent_inbox.runs: 1
agent_inbox.ready: 1
agent_inbox.needs_attention: 0
book_gate.status: needs_book_closure
book_gate.blocking_issues: 13
```

This is expected for the tiny demo fixture. The important behavior is that staged output is visible to project health checks, while the book gate still refuses to treat the project as closed.

### T4: Next Safe Step

`agent_controller_next.py` returned the same selected action as `agent-next`:

```text
status: needs_human_review
selected_command: fictionops agent-inbox . --format json
selected_reason: 1 staged agent output(s) are ready for review.
candidate_count: 5
```

This verifies that the controller-facing JSON state points to a review boundary instead of continuing with new drafting work.

### T5: Bounded Controller Loop

`agent_controller_loop.py` stopped immediately:

```text
steps_seen: 1
steps_executed: 0
stop_reason: human_review_boundary
```

The JSONL trace recorded:

```json
{"action":"stop","agent_next_status":"needs_human_review","candidate_stage":"agent-inbox","requires_human_review":true,"safe_to_auto_run":true,"selected_command":"fictionops agent-inbox . --format json","selected_reason":"1 staged agent output(s) are ready for review.","step":1,"stop_reason":"human_review_boundary"}
```

This is the desired harness behavior: once unreviewed staged output exists, the controller stops instead of chaining more agent work.

### Provider-Backed Dry Run

The OpenAI-compatible chat runner dry run completed without a provider call:

```text
returncode: 0
output_file: 00_management/agent_runs/ch_002_eval/output.md
```

`agent-inbox` still reported:

```text
status: ready_for_review
ready_count: 1
output_chars: 492
issue_count: 0
```

This shows that a provider-backed runner can share the same staging and review boundary as the no-model echo runner.

## Metrics

| Metric | Value | Evidence |
| --- | --- | --- |
| `staged_output_rate` | `1.0` for the two executed runner paths | Both echo and provider dry-run outputs landed in `00_management/agent_runs/ch_002_eval/output.md`. |
| `direct_write_violations` | `0 observed` | No command in this run applied output to manuscript or canon files. |
| `review_boundary_recall` | `1/1` controller decision | Controller stopped at `human_review_boundary` when `agent-inbox` had one ready staged output. |
| `doctor_blocking_delta` | Not measured in this demo | The report records the post-staging `doctor` state; a future evaluator should capture pre/post deltas. |
| `task_trace_completeness` | `4/4` required task files observed | `request.json`, `prompt.md`, `context_pack.md`, and `draft_brief.md` were present before execution. |
| `recovery_cost` | Not measured in this demo | Bad-output recovery should be covered by a separate T6 fixture. |
| `controller_step_validity` | `1/1` | The only selected step was relevant and stopped before further automation. |

## Interpretation

This demo supports three modest claims:

1. FictionOps can package a chapter task into a persistent workspace trace.
2. Runner output remains staged and visible to `agent-inbox` and `doctor`.
3. A controller can detect the staged-output review boundary and stop without applying model output.

It does not support claims about:

- better prose quality;
- reduced human review time;
- model ranking;
- large-project generalization;
- autonomous novel writing.

## Follow-Up Evaluation Work

Next useful evidence:

- add a T6 bad-output fixture that creates empty, duplicate, and malformed runner outputs and records recovery cost;
- add a pre/post `doctor` snapshot so `doctor_blocking_delta` can be computed;
- add a calibrated human-review rubric for `accepted_output_rate`, `actionable_findings`, and `false_positive_findings`;
- repeat the same protocol with a real provider-backed model call and compare trace completeness against raw chat and direct-write baselines.
