# Dogfood Cycle Close Runbook

This runbook closes a sustained FictionOps dogfood cycle without pretending that a one-day maintenance pass is seven days of evidence. Use it when the cycle end date has actually arrived.

The current active cycle is `dogfood-2026-07-private-maintenance`, covering `2026-07-07` through `2026-07-14`. Do not mark it accepted before the close date and the close checkpoint both exist.

## Purpose

The close checkpoint must prove four things:

- The same real project or sandbox can still be inspected after elapsed time.
- The book/chapter scope is explicit.
- The AI/API runner or agent workflow path is documented.
- Model or tool output still stops at a human review boundary.

## Inputs

Before closing, collect:

- private sandbox path;
- current FictionOps commit;
- start checkpoint folder;
- close checkpoint folder;
- book id and chapter scope;
- focused tasks completed during the cycle;
- AI runner/controller evidence, if any;
- human reviewer name or handle.

## Close-Day Commands

Run these from the release repository, replacing `<sandbox>` with the private project path and `<date>` with the close date.

```bash
fictionops adopt-review <sandbox> --format json
fictionops doctor <sandbox> --book book_01 --format json
fictionops audit-info <sandbox> --format json
fictionops audit-characters <sandbox> --format json
fictionops audit-plan <sandbox> --book book_01 --format json
fictionops audit-echoes <sandbox> --format json
fictionops audit-continuity <sandbox> --format json
fictionops context-pack <sandbox> --task handoff --book book_01 --format json
fictionops revision-plan <sandbox> --book book_01 --format json
fictionops eval-agent <sandbox> --chapter 002 --format json
fictionops agent-inbox <sandbox> --format json
fictionops report <sandbox> --book book_01 --format json
```

If the cycle includes a real model/API call, also record the staged run path:

```bash
fictionops agent-run <sandbox> --role draft-writer --book book_01 --chapter <chapter> --out-dir <run-dir>
fictionops agent-exec <run-dir> --runner <runner-command>
fictionops agent-inbox <run-dir> --format json
```

Do not apply staged output directly to source files as part of the evidence. Human adoption belongs in the project work log, not in the runner command.

## Required Comparisons

Compare start and close checkpoints:

| Signal | Must Record |
| --- | --- |
| `adopt-review` | `ready`, `blocking_issue_count`, `import_queue_files` |
| `doctor` | priority counts and new blockers |
| `revision-plan` | task count and remaining categories |
| `audit-plan` | planned chapters, draft chapters, engine sync |
| `audit-info` | item count and issue count |
| `audit-characters` | character, arc, index, intelligence, and voice counts |
| `audit-echoes` / `audit-continuity` | issue counts |
| `eval-agent` / runner | pass/fail, staged output path, stop reason |
| publish gates, if run | blocking issue count |

## Update The Evidence File

Edit `docs/dogfood-cycle-evidence.md`:

- set `Final adopt-review status` to `ready`, `ready_for_project_work`, `complete`, or `completed` only if the close checkpoint supports it;
- keep `import_queue_files: 0` and `blocking_issue_count: 0` only if the close checkpoint supports those values;
- expand `Day-by-day ledger` with the real close checkpoint;
- update `Compatibility notes` with any changed command, JSON key, default behavior, runner contract, or recovery path;
- update `Recovery notes` with no-overwrite, inbox quarantine, and failed-run recovery observations;
- set `Decision: accepted` only after human review.

Then run:

```bash
fictionops audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md --format json
fictionops audit-stable-core . --format json
```

## Do Not Accept If

- the close date has not arrived;
- the close checkpoint was not rerun;
- book/chapter scope is vague;
- AI workflow evidence says only "no AI used";
- staged output did not stop for human review;
- command outputs show new P1/P2 blockers without explanation;
- `audit-dogfood-cycle` does not return `ready=true`.

## After Acceptance

Commit the evidence update with a message such as:

```bash
git commit -m "Accept sustained dogfood cycle evidence"
```

Then start the stability-window lane. The stability window should reference the accepted release evidence and accepted dogfood evidence; it should not start from a deferred dogfood cycle.
