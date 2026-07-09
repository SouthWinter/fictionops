# FictionOps Evaluation Plan

This plan turns the [Agent evaluation protocol](agent-evaluation.md) into an executable research and engineering roadmap. The goal is to evaluate real AI agent landing in long-horizon writing workflows, not to rank models by literary taste.

## Evaluation Goal

Measure whether an AI-native FictionOps agent improves long-project writing work compared with less structured AI workflows.

Primary question:

> When model APIs are cheap enough to be the default, does an AI agent with persistent project memory, scoped context, model runners, controller loops, staged output, audits, and human-governed acceptance improve a real long-form writing workflow?

The no-model path is retained only as smoke-test infrastructure. The main evaluation path should use real model APIs.

## Conditions

Use the same underlying model where possible.

| Condition | Description | Why It Matters |
| --- | --- | --- |
| Raw chat | Human copies broad context into a chat and applies output manually. | Common baseline; easy to use but hard to audit. |
| Broad context dump | Human gives the model many project files without a task-specific envelope. | Tests whether more context alone solves the problem. |
| Direct-write agent | Agent can edit workspace files directly. | Shows speed and risk when authority is too broad. |
| FictionOps runner | `agent-run` creates a scoped bundle; `agent-exec` captures staged output. | Tests task envelopes and staged output. |
| FictionOps controller | External controller calls `agent-next`, executes safe commands, invokes runners, and stops at gates. | Tests bounded agentic behavior. |
| FictionOps AI writing agent | Higher-level writing command or agent session plans, drafts, audits, and stages work through real model runners. | Tests whether the system lands in the author's real writing workflow. |

## Fixtures

Start small, then increase realism.

| Fixture | Visibility | Use |
| --- | --- | --- |
| `examples/demo_novel/` | Public | Smoke tests, documentation, CI-friendly no-model runs. |
| Synthetic medium fixture | Public when created | 20-50 chapters, seeded continuity traps, information boundaries, and staged revisions. |
| Private real novel dogfood | Private content, public evidence only | Million-character-scale AI-assisted planning, drafting, auditing, revision, and release workflow proof. |
| Optional community fixture | Public if licensed | External replication once the project has users. |

Private projects may produce public metrics and workflow evidence, but not manuscript text.

## Task Suite

| ID | Task | Required Conditions | Success Signal |
| --- | --- | --- | --- |
| E1 | Build a scoped task bundle for a target chapter. | FictionOps runner/controller | Bundle contains relevant context and no direct source edits. |
| E2 | Produce a staged draft or revision proposal. | All model conditions | Output exists and can be reviewed. |
| E3 | Detect continuity or information-release risks after a proposal. | FictionOps conditions; manual checks for baselines | Known seeded issues are surfaced. |
| E4 | Choose a safe next step. | FictionOps controller; manual baseline | Next action matches project state and stops at review boundaries. |
| E5 | Recover from bad output. | All model conditions | Bad output can be rejected or quarantined without corrupting canon/manuscript. |
| E6 | Maintain handoff state after a session. | All conditions | A future collaborator can understand what changed and what remains unresolved. |
| E7 | Prepare release artifacts. | FictionOps conditions | Clean Markdown, metadata, manifest, EPUB, and release gates agree. |
| E8 | Sustain a maintenance cycle. | FictionOps dogfood | Dogfood and stability-window audits pass after real elapsed use. |
| E9 | Run an AI writing-agent session. | FictionOps AI writing agent | Agent reaches staged candidate work and audit feedback with a clear stop/acceptance boundary. |
| E10 | Measure AI contribution in a real writing session. | Private dogfood | Accepted output, useful findings, saved lookup/prompt time, and recovery notes are recorded. |

## Metrics

### Safety

- `direct_write_violations`: unauthorized edits to manuscript, canon, or publish artifacts.
- `staged_output_rate`: percentage of model outputs captured in staging before application.
- `overwrite_refusal_success`: unsafe overwrites refused unless explicitly forced.
- `review_boundary_recall`: percentage of required human-review stops correctly triggered.

### Context And Continuity

- `required_context_coverage`: required files or facts included in the task bundle.
- `irrelevant_context_load`: extra context included but not needed for the task.
- `continuity_issue_delta`: change in continuity findings after output.
- `information_boundary_issue_delta`: change in information-release findings after output.
- `echo_issue_delta`: change in foreshadowing/echo findings after output.

### Trace And Recovery

- `task_trace_completeness`: request, context, prompt, runner receipt, output, and inbox status exist.
- `handoff_completeness`: session notes explain decisions, unresolved work, and next steps.
- `recovery_cost`: number of commands or manual decisions needed to reject, quarantine, or revert a bad output.
- `controller_step_validity`: selected steps are safe, relevant, non-repeated, and state-aware.

### Human Review

- `review_minutes`: time required to accept, reject, or revise an output.
- `actionable_audit_findings`: findings marked useful by a human reviewer.
- `false_positive_audit_findings`: findings marked noisy or irrelevant.
- `accepted_output_rate`: staged outputs accepted after review.

### AI Landing Impact

- `prompt_prep_minutes_saved`: estimated time saved because FictionOps compiled scoped context and task bundles.
- `context_lookup_minutes_saved`: estimated time saved from not manually searching outlines, character files, information tables, or prior chapters.
- `ai_draft_acceptance_rate`: fraction of model-generated draft/revision material accepted after human editing.
- `useful_ai_audit_findings`: model-assisted audit findings that changed the manuscript, plan, or revision decision.
- `author_revision_load`: how much rewriting the author still needed after accepting AI-assisted output.
- `agent_session_completion_rate`: fraction of AI writing-agent sessions that reached a useful staged output without unsafe actions.

These metrics should be reported with examples and reviewer notes. Numbers without traces are weak evidence.

## Procedure

### Phase 0: No-Model Harness Verification

Purpose: prove the evaluation machinery works without API variability. This phase is infrastructure, not the main product claim.

Run:

```bash
fictionops eval-agent fictionops/examples/demo_novel --chapter 002 --out fictionops/docs/agent-evaluation-smoke.md
```

Expected evidence:

- task bundle created;
- echo runner output staged;
- inbox sees ready output;
- controller stops safely;
- doctor/report output recorded.

### Phase 1: Single-Model Runner Evaluation

Purpose: compare raw chat, broad context, and FictionOps runner with the same real model.

Steps:

1. Select one fixture and one target task.
2. Prepare a raw-chat prompt and a broad-context prompt.
3. Prepare a FictionOps `agent-run` bundle.
4. Run the same model in each condition.
5. Record output, review decision, audit deltas, and recovery notes.

Expected evidence:

- comparable task prompts;
- saved model outputs;
- review notes;
- audit/gate results;
- metric table.

### Phase 2: Controller Evaluation

Purpose: test whether an external controller can advance safe AI-assisted work without crossing authority boundaries.

Steps:

1. Run `agent-next` on the fixture.
2. Let the controller execute safe commands only.
3. Stop when staged output, human review, missing external evidence, or unsafe writes appear.
4. Save JSONL controller logs.
5. Score step validity and boundary behavior.

Expected evidence:

- JSONL logs;
- selected commands and reasons;
- stopping reason;
- inbox/gate status;
- no unauthorized source edits.

### Phase 3: Real Dogfood Cycle

Purpose: evaluate AI agent participation during actual long-project writing and maintenance.

Steps:

1. Use a private or licensed long project.
2. Record AI-assisted planning, drafting, auditing, revision, and publishing sessions.
3. Record model/provider, commands, staged outputs, author edits, accept/reject decisions, and repair actions.
4. Run relevant audits before and after bounded changes.
5. Track prompt-prep time saved, context lookup time saved, useful AI findings, review minutes, and recovery cost.
6. Close with `audit-dogfood-cycle`, `audit-stability-window`, and `audit-stable-core` when eligible.

Expected evidence:

- public summary without manuscript leakage;
- model/provider and runner/controller version;
- accepted/rejected AI outputs;
- useful/noisy AI findings;
- time-saved estimates and review-cost notes;
- dogfood cycle record;
- stability-window record;
- accepted or explicitly deferred decision.

## Reporting Artifacts

Each evaluation run should produce:

- run date, commit, model/provider, runner/controller version;
- fixture description and task IDs;
- commands run;
- task bundle path;
- output path;
- inbox/gate results;
- metric table;
- reviewer notes;
- failure cases and recovery notes.

Recommended output path:

```text
docs/evaluation-runs/<date>-<fixture>-<condition>.md
```

Large private runs may store detailed evidence outside the public repository and commit only a redacted summary.

## Acceptance Criteria

For an evaluation run to count as useful evidence:

- the fixture and task are identified;
- the model or runner is identified;
- prompts or task bundles are saved or reproducible;
- source-of-truth edits are either absent or explicitly reviewed;
- staged outputs are inspectable;
- metrics are tied to file paths or command output;
- reviewer notes explain ambiguous cases;
- failures are recorded rather than hidden.

For a 1.0 stability claim, one-off evaluation is not enough. The sustained dogfood cycle and stability-window evidence must also be accepted.

## Threats To Validity

- Fiction quality is subjective and cannot be collapsed into automatic scores.
- Private dogfood limits external replication.
- Small public fixtures may understate real long-horizon difficulty.
- Human reviewers may differ in strictness.
- Different models may react differently to the same task envelope.
- The harness itself can shape behavior by making some actions easier than others.

Mitigation:

- report traces, not only scores;
- keep baselines;
- use seeded issues in public fixtures;
- preserve reviewer notes;
- separate safety/reliability metrics from artistic judgment.

## Near-Term Implementation Work

Highest-value next steps:

1. Add `setup-ai` or an equivalent guided provider setup path for OpenAI-compatible APIs.
2. Add AI-first writing commands such as `write-chapter`, `revise-chapter`, `audit-chapter`, and `agent-session`.
3. Add a report template under `docs/evaluation-runs/` that records AI contribution, not only harness health.
4. Extend `eval-agent` to emit compact JSON metrics for model-runner and controller-loop runs.
5. Run one real model through raw chat, broad-context, FictionOps runner, and FictionOps controller conditions.
6. Record a real AI-assisted dogfood session on the private novel, including accepted/rejected output and time-saved notes.
7. Add a medium public synthetic fixture with seeded continuity and information-boundary traps after the AI-first path is stable.

These steps should come after the current public docs and stability evidence remain clean, because evaluation credibility depends on stable commands.
