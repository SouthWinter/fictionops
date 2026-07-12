---
name: fictionops-writing-agent
description: Govern long-form fiction work in a FictionOps project. Use when Codex needs to inspect or maintain project memory; plan, write, review, revise, or recover chapters; resolve counterevidence; prepare publishing; or act as a reference teacher that produces evidence-grounded trajectories for comparison with an API agent.
---

# FictionOps Writing Agent

Use FictionOps as the state, evidence, and authority harness. Act as a capable reference policy, not as the source of literary truth. Treat explicit author decisions and active project canon as higher authority than model preference.

## Start From State

1. Locate the project root, target chapter, chapter engine or outline, and existing `session.json`, `checkpoint.json`, and issue state.
2. Run `fictionops agent status <project> --format json` when prior runs may exist. Run `fictionops doctor <project> --book <book>` when structural health affects the task.
3. Classify the request before acting:
   - New prose: read `references/chapter-writing.md` and `references/workflow.md`.
   - Existing-prose review or revision: read `references/audit.md` and `references/workflow.md`.
   - Disputed findings or blocked evidence: read `references/counterevidence.md`.
   - Teacher/student comparison or research evidence: read `references/teacher-mode.md` and `references/dogfood-metrics.md`.
   - Publishing: read the publishing section in `references/workflow.md`.
4. Do not call a model when the user asks only for analysis, planning, or a bounded deterministic audit.

## Follow The Teacher Loop

1. **Observe:** identify current state, unresolved issues, source hashes, budgets, and authority boundaries.
2. **Retrieve:** select the smallest sufficient evidence at the same scale as the claim. Record paths, authority, and selection reasons.
3. **Plan:** state the intended state transition and acceptance checks. Keep alternatives when the choice is uncertain.
4. **Execute:** prefer `fictionops agent write|revise|resume|continue` over reconstructing lower-level calls. Put `--runner` last.
5. **Verify:** inspect candidate, diff, issue lifecycle, deterministic gates, semantic verification, and runner telemetry. Never infer correctness from model confidence.
6. **Countercheck:** test the strongest plausible reason not to revise. Route insufficient evidence through counterevidence instead of forcing a verdict.
7. **Stop:** stop at stale state, exhausted budget, unsupported recovery, unresolved canon, or author-owned acceptance.
8. **Record:** preserve `trajectory.jsonl`, context manifests, receipts, diffs, verification artifacts, and the human decision. When acting as teacher, add the decision summary required by `references/teacher-mode.md`.

## Respect Authority

Apply this order when sources conflict:

1. Explicit current author decision and active `G-*` author guard.
2. Accepted canon, current manuscript state, and approved continuity records.
3. Current outline, chapter engine, information-release plan, and character memory.
4. Retrieved supporting material and prior unaccepted drafts.
5. Model inference or aesthetic preference.

Let deterministic gates block unsafe transitions, but do not let a gate invent literary intent. Ask the author when two same-rank authoritative sources conflict.

## Use Governed Actions

- Write with `fictionops agent write <chapter> --engine <engine> ... --runner <command>`.
- Revise with `fictionops agent revise <chapter> ... --runner <command>`; keep comprehensive review unless the user explicitly requests style-only scope.
- Recover with `fictionops agent resume <run-dir> ... --runner <command>` only after validating a resumable checkpoint.
- Observe the next action with `fictionops agent continue <project>` before using `--execute`; only R0 actions may execute automatically.
- Record author issue decisions with `fictionops agent issue` and a reason.
- Apply a verified chapter only after explicit author approval with `fictionops agent accept <run-dir>`.

Use a real configured runner for normal AI work. Use echo/no-model runners only for tests and recovery diagnosis. Keep API keys in environment variables or a private env file outside the repository.

## Preserve The Boundary

- Stage model output; never copy raw model prose directly into canon or final manuscript files.
- Treat `ready_for_approval` as eligibility for author review, not acceptance.
- Refuse stale hashes, unsupported or cancelled checkpoints, and silent budget expansion.
- Preserve uncertainty. Mark a question or stop when evidence cannot establish canon.
- Do not turn a teacher decision into benchmark ground truth without author confirmation or an independent deterministic check.
- Keep expected labels, hidden controls, and teacher conclusions out of student prompts and held-out evaluation inputs.
