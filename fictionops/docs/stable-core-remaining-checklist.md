# FictionOps 1.0 Stable Core Remaining Checklist

Current conclusion: the local foundation is in place and the external release trial has been accepted, but 1.0 cannot be closed. `fictionops audit-stable-core . --format json` should continue to return `not_ready` until the sustained dogfood and stability-window evidence lanes are filled with real records and pass their audits.

This checklist answers the execution question: what real work remains between the current repository and 1.0. It is not evidence by itself, and it does not replace `docs/stable-core-audit.md` or the machine audit commands.

The current execution status is recorded in `docs/stable-core-remaining-execution.zh-CN.md`. If the execution environment, GitHub Actions run, TestPyPI state, or real dogfood cycle changes, update that status record first, then use this checklist to close each lane.

## 0. Current State

| Item | Status | Notes |
| --- | --- | --- |
| Local governance files, tests, CLI, docs, workflows | Complete | `local-foundation` is complete; continue local hardening only when a real regression is found. |
| Release-trial evidence | Complete | Accepted external evidence is recorded in `docs/release-trial-evidence.md`; GitHub Actions run `28849146871`; TestPyPI `fictionops==0.1.1`; `audit-release-evidence` returns `ready=true`. |
| Sustained dogfood cycle | Missing | Needs at least 7 calendar days of real post-0.2 project maintenance records. |
| Stability window | Missing | Needs compatibility evidence after release and dogfood records exist. |
| Milestone ledger closure | Missing | Can only happen after `audit-stable-core` returns `ready=true`. |

## 1. Stop Spending 1.0 Time Here

Unless a real regression appears, do not spend the main 1.0 effort on:

- expanding the CLI surface;
- adding more empty template fields;
- repeatedly proving local wheel/sdist builds;
- re-running release-trial work that already has accepted external evidence;
- treating `audit-stability-window` hardening as the main task;
- using local smoke tests, generated drafts, or empty evidence templates as substitutes for elapsed external evidence.

Local hardening can continue as maintenance, but it is no longer the main 1.0 blocker.

## 2. Phase A: External Release Trial

Goal: close the external evidence gap for the 0.4 release trial.

Status: **complete**.

Accepted evidence:

- GitHub Actions run: `https://github.com/SouthWinter/fictionops/actions/runs/28849146871`
- TestPyPI project: `https://test.pypi.org/project/fictionops/`
- TestPyPI version: `https://test.pypi.org/project/fictionops/0.1.1/`
- Evidence file: `docs/release-trial-evidence.md`
- Decision: `accepted`

Acceptance command:

```bash
fictionops audit-release-evidence . --file docs/release-trial-evidence.md --format json
```

Done means:

- `ready=true`;
- `decision=accepted`;
- `blocking_issue_count=0`;
- the evidence is not an empty template or unreviewed workflow draft;
- release notes include the real run id or URL.

## 3. Phase B: Sustained Dogfood Cycle

Goal: prove that after the 0.2 migration closure, a real long-form project can keep using FictionOps for maintenance instead of only completing one migration demo.

This is now the next active 1.0 lane.

Steps:

1. Choose a real migrated project or equivalent maintenance sandbox.
2. Record start and end times covering at least 7 calendar days after the 0.2 closure.
3. Exercise at least 3 recognized FictionOps CLI commands, preferably across categories such as `adopt-review`, `adopt-plan`, `import-plan`, `doctor`, `report`, `context-pack`, and `revision-plan`.
4. Record initial and final project states, including `ready`, `import_queue_files`, `blocking_issue_count`, waivers, deferred items, and recovery actions.
5. Record compatibility issues, recovery-path issues, and human decisions from the cycle.
6. Fill `docs/dogfood-cycle-evidence.md`.

Acceptance command:

```bash
fictionops audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md --format json
```

Done means:

- `ready=true`;
- the cycle covers at least 7 calendar days;
- command coverage uses recognized FictionOps commands;
- the final state has no unexplained migration blockers;
- the decision is accepted.

## 4. Phase C: Stability Window

Goal: prove that stable surfaces did not drift silently over real elapsed time; if a breaking change happened, each one has an explicit migration path.

Start this only after the sustained dogfood cycle is accepted.

Steps:

1. After release-trial and dogfood evidence pass, record a stability window covering at least 7 calendar days.
2. Track command names, required arguments, core JSON keys, default no-overwrite behavior, package contents, release flow, agent staging boundaries, and recovery paths.
3. If local Markdown evidence is referenced, it must stay inside the audited checkout and the referenced release/dogfood evidence must pass its own audit.
4. If URL evidence is referenced, it must be a complete `https://...` URL pointing to a concrete run, artifact, release, dogfood, or stability record. Do not use generic home-page links.
5. Fill `docs/stability-window-evidence.md`.

Acceptance command:

```bash
fictionops audit-stability-window . --file docs/stability-window-evidence.md --format json
```

Done means:

- `ready=true`;
- the window covers at least 7 calendar days;
- release and dogfood references are real and auditable;
- there are no undocumented breaking changes;
- the decision is accepted.

## 5. Phase D: Close The 1.0 Ledger

Goal: after all external evidence lanes pass, update the 1.0 state honestly.

Steps:

1. Run the aggregate audit:

```bash
fictionops audit-stable-core . --format json
```

2. If the aggregate result is `ready_needs_docs_update`, update:

- `docs/stable-core-audit.md`
- `docs/stable-core-audit.zh-CN.md`
- `docs/milestone-status.md`
- `docs/milestone-status.zh-CN.md`
- `docs/roadmap.md`
- `docs/roadmap.zh-CN.md`
- relevant release notes and changelog entries

3. Re-run full local validation and package builds.
4. Run `fictionops audit-stable-core . --format json` again.

Final done means:

- `ready=true`;
- `status=ready`;
- `blocking_issue_count=0`;
- every `action_items` entry is complete;
- docs do not blur external evidence, templates, and plans.

## 6. Responsibility Table

| Item | Primary Actor | Local Acceptance Command | Evidence File | Can Codex Do It Alone? |
| --- | --- | --- | --- | --- |
| Local foundation maintenance | Codex | `python -m unittest discover -s fictionops/tests -v` | Tests, workflows, docs | Yes, but only for real regressions. |
| Release-trial evidence | Maintainer + Codex assist | `audit-release-evidence` | `docs/release-trial-evidence.md` | Complete for the current 0.1.1 trial. Future trials still need external run evidence. |
| Sustained dogfood cycle | Maintainer + Codex assist | `audit-dogfood-cycle` | `docs/dogfood-cycle-evidence.md` | Not fully. It needs a real project and elapsed time. |
| Stability window | Maintainer + Codex audit | `audit-stability-window` | `docs/stability-window-evidence.md` | Not fully. It needs real elapsed time. |
| 1.0 ledger closure | Codex + maintainer review | `audit-stable-core` | stable-core, milestone, roadmap, release notes | Yes after evidence exists. |

## 7. Stop Conditions

Do not mark accepted, and do not close 1.0, if any of these are true:

- the evidence file is still a template;
- the evidence is only a workflow-generated draft with no human review;
- dogfood or stability spans fewer than 7 calendar days;
- a URL points to a generic homepage instead of a concrete run, artifact, release, or evidence page;
- a local reference points outside the audited checkout;
- any one of release, dogfood, or stability does not pass its audit command.

## 8. Next Single Action

The next action that truly advances 1.0 is: start or continue a sustained post-migration dogfood cycle from a real migrated project or equivalent maintenance sandbox, record at least 7 calendar days of maintenance, fill `docs/dogfood-cycle-evidence.md`, and make `audit-dogfood-cycle` return `ready=true`.

If that real cycle is not available yet, keep 1.0 open. Do not treat more local hardening as 1.0 completion progress.
