# Dogfood Cycle Evidence

This file records the sustained real-project dogfood cycle required before FictionOps can claim the 1.0 stable-core milestone. It is not the original 0.2 migration closure log; it is the later maintenance-cycle proof that the migrated project can keep using FictionOps without silent contract drift.

## Evidence Rules

- Record a cycle after the 0.2 migration closure, not the initial migration itself.
- Include the project or sandbox path, version or commit range, commands exercised, before/after gate states, compatibility notes, recovery notes, and final decision.
- Name the actual book/project slice, chapter range, focused tasks, AI/agent runner path, and human review boundary. A cycle that only says "maintenance" or "smoke" is not specific enough.
- Use `YYYY-MM-DD` for start/end dates; the end date must not be earlier than the start date, and the cycle must cover at least 7 calendar days.
- Exercise at least three command paths; a one-command or two-command smoke is not enough for accepted 1.0 dogfood evidence.
- The command coverage must name at least three recognized FictionOps CLI commands, such as `adopt-review`, `adopt-plan`, `import-plan`, `doctor`, `report`, or `context-pack`; vague labels are not enough.
- Accepted sustained evidence must include a day-by-day ledger with at least a start checkpoint and a close checkpoint. The seven-day window proves recovery and continuation across time; it is not a reason to stretch one day's work across a week.
- Do not mark the cycle `accepted` unless `import_queue_files` and `blocking_issue_count` are both `0`, the final status is ready/complete, and any compatibility-sensitive behavior changes have an explicit note.
- Do not mark the cycle `accepted` without a named human reviewer.
- Use [Dogfood cycle close runbook](dogfood-cycle-close-runbook.md) when the real close date arrives.
- Run `fictionops audit-dogfood-cycle . --file <filled-cycle.md>` before using the record as 1.0 evidence.

## Dogfood Cycle Template

Copy this section for each sustained cycle.

```markdown
## Dogfood Cycle Evidence

- Cycle ID:
- Project / sandbox:
- Start date:
- End date:
- Version / commit range:
- Scope:
- Book / chapter scope:
- Focused tasks:
- Commands exercised:
- AI workflow evidence:
- Human review boundary:
- Day-by-day ledger:
- Initial adopt-review status:
- Final adopt-review status:
- import_queue_files:
- blocking_issue_count:
- Waiver count:
- Compatibility notes:
- Recovery notes:
- Decision: accepted / deferred / failed
- Reviewer:

### Summary

- What stayed stable:
- What changed:
- Regression tests added:
- Docs updated:
- Follow-up:
```

## Active Cycle

- Cycle ID: dogfood-2026-07-private-maintenance
- Project / sandbox: private migrated long-form fiction sandbox; local path and story content redacted from the public repository
- Start date: 2026-07-07
- End date: 2026-07-14
- Version / commit range: 3e0703f..cycle-close
- Scope: sustained post-migration maintenance pass covering project health, context packaging, review gates, and agent-harness evidence after the 0.2 migration closure
- Book / chapter scope: Book 01 (`book_01`, first book of the private long-form fiction sandbox), full structural pass over `ch_001` to `ch_033`, focused prose/review passes on `ch_007`, `ch_010`, `ch_012`, `ch_013`, `ch_014`, `ch_026`, `ch_027`, and `ch_028`; agent/eval smoke used `ch_002`, and real multi-role runner review covered the high-risk load-bearing chapter `ch_010`
- Focused tasks: repair active project memory tables, align Book 01 outline/draft/chapter-engine inventory, separate active echo tracking from imported retrospective material, triage reader-experience signals, apply bounded prose maintenance to selected chapters, and run a Book 01 publish-chain smoke check
- Commands exercised: adopt-review, doctor, context-pack, report, audit-info, audit-characters, revision-plan, eval-agent
- AI workflow evidence: `eval-agent` was run on `ch_002`, and the agent harness stopped at the human-review boundary with staged output remaining quarantined. On 2026-07-10, real OpenAI-compatible DeepSeek runner checkpoints were added in the private sandbox for `book_01/ch_002` using `audit-chapter --role info-boundary-auditor`: the first proved the API runner boundary, and the second completed a bounded information-boundary review. The same real runner was then used on the high-risk load-bearing chapter `book_01/ch_010` with five review roles: `architect`, `character-auditor`, `info-boundary-auditor`, `style-auditor`, and `foreshadowing-auditor`. Model output was staged in agent run directories, `agent-inbox` reported `ready_for_review`, no manuscript or canon file was overwritten, and a private aggregate review record was written for human review. The public evidence does not claim autonomous direct-writing.
- Human review boundary: style/wave/word signals were converted into a reader-experience memo and targeted review before prose edits; staged agent output remained in the inbox/review path and no source overwrite was allowed during diagnostics
- Day-by-day ledger: 2026-07-07 day-one checkpoint: baseline audit, project-memory repairs, Book 01 outline sync, echo/continuity cleanup, reader-experience triage, bounded prose passes, and publish-chain smoke; 2026-07-10 AI runner checkpoints: real DeepSeek `audit-chapter` reviews for `book_01/ch_002`, including one complete bounded information-boundary review, followed by a five-role comprehensive review of the high-risk load-bearing chapter `book_01/ch_010`; staged output ready for human review, no source overwrite; 2026-07-14 close checkpoint: pending rerun of the same command family and human review before any accepted decision
- Initial adopt-review status: baseline_pending_on_private_sandbox
- Final adopt-review status: deferred_until_cycle_close
- import_queue_files: 0
- blocking_issue_count: 0
- Waiver count: 0
- Compatibility notes: Active cycle opened on 2026-07-07. No compatibility claim is made until the minimum seven-calendar-day window has elapsed and the private sandbox is rechecked at close.
- Recovery notes: Recovery behavior to verify during the cycle: no source overwrite during diagnostics, staged agent output remains quarantined, and generated reports refuse unsafe overwrite without `--force`.
- Decision: deferred
- Reviewer: maintainer pending final review

### Summary

- What stayed stable: 2026-07-07 checkpoint passed the staging boundary and migration-readiness checks: `adopt-review` returned `ready=true` with `blocking_issue_count=0`, and `eval-agent` returned `pass` with the controller stopping at the human-review boundary. The first maintenance repair made the active information-release table parseable: `audit-info` moved to `item_count=8` and `issues=0` in the private sandbox checkpoint. The second maintenance repair made the active character-memory layer parseable: `audit-characters` moved to `character_count=8`, `arc_count=8`, `index_count=8`, `intelligence_count=8`, `voice_count=8`, and `issues=0`. The third maintenance repair cleaned active table hygiene without fabricating filled content: active table issues moved to `0`, and the private sandbox `revision-plan` task count dropped from `595` to `152`. The fourth maintenance repair aligned the active Book 01 outline with the draft inventory: `audit-plan` moved to `planned_chapters=33`, `chapter_files=33`, `engine_files=33`, `synced_engines=33`, and `issues=0`, and the private sandbox `revision-plan` task count dropped to `119`. The fifth maintenance repair separated active echo tracking from imported retrospective material: `audit-echoes` moved to `table_files=1`, `thread_count=3`, `issues=0`; continuity template issues moved to `0`; the private sandbox doctor report reached `P2=0`; and the private sandbox `revision-plan` task count dropped to `18`, all style/wave/word-scan prompts. The sixth maintenance review converted those remaining style, wave, and word-scan prompts into a private reader-experience memo rather than automated prose rewrites; no structural `P2` issues reappeared. The seventh maintenance review classified high-priority chapters before revision and produced a bounded private edit order, proving the workflow can separate raw frequency warnings from human prose decisions. The eighth maintenance pass applied a bounded private prose edit to the first targeted cluster and reran style/wave checks; no new pacing issue was introduced. The ninth maintenance pass applied a bounded private prose edit to the court-density cluster and reran style/wave checks; no new pacing issue was introduced. The tenth maintenance pass applied a bounded private prose edit to the first-blood sequence and reran style/wave/word checks; no new pacing issue was introduced. The eleventh maintenance pass completed the high-priority reader-experience prose sequence with a bounded private light read and reran style/wave/word checks; no new pacing category was introduced. The twelfth maintenance pass ran a private publish-chain smoke check: clean Markdown, metadata, manifest, and EPUB artifacts were generated, and book/release gates reported ready with no blocking issues.
- What changed: `eval-agent` was added before the cycle opened; watch whether it affects existing agent workflow contracts.
- Regression tests added: `test_eval_agent_generates_reproducible_agent_harness_report` plus CLI, package, and CI smoke coverage for `eval-agent`.
- Docs updated: Agent evaluation protocol, CLI guides, command contracts, testing guide, README, and promotion kit mention `eval-agent`.
- Follow-up: Day-one private-sandbox checkpoint files were written under `07_audits/dogfood_cycle/2026-07-07/` in the local migrated novel sandbox, including after-repair `audit-info`, `audit-characters`, `audit-plan`, `audit-echoes`, `audit-continuity`, `check-tables`, `doctor`, and `revision-plan` snapshots. Rerun the same command family on or after 2026-07-14, then update final status, decision, reviewer, and any compatibility/recovery notes from the real maintenance window.

## Acceptance Decision

Use one of:

- `accepted`: the sustained cycle completed, migration queues and blockers are closed, compatibility/recovery notes are current, and the record passes `audit-dogfood-cycle`.
- `deferred`: the repository has local migration evidence, but no sustained post-closure dogfood cycle is complete yet.
- `failed`: the cycle exposed a real regression or contract drift that needs a fix, tests, and a new cycle.
