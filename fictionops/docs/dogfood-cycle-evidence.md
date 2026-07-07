# Dogfood Cycle Evidence

This file records the sustained real-project dogfood cycle required before FictionOps can claim the 1.0 stable-core milestone. It is not the original 0.2 migration closure log; it is the later maintenance-cycle proof that the migrated project can keep using FictionOps without silent contract drift.

## Evidence Rules

- Record a cycle after the 0.2 migration closure, not the initial migration itself.
- Include the project or sandbox path, version or commit range, commands exercised, before/after gate states, compatibility notes, recovery notes, and final decision.
- Use `YYYY-MM-DD` for start/end dates; the end date must not be earlier than the start date, and the cycle must cover at least 7 calendar days.
- Exercise at least three command paths; a one-command or two-command smoke is not enough for accepted 1.0 dogfood evidence.
- The command coverage must name at least three recognized FictionOps CLI commands, such as `adopt-review`, `adopt-plan`, `import-plan`, `doctor`, `report`, or `context-pack`; vague labels are not enough.
- Do not mark the cycle `accepted` unless `import_queue_files` and `blocking_issue_count` are both `0`, the final status is ready/complete, and any compatibility-sensitive behavior changes have an explicit note.
- Do not mark the cycle `accepted` without a named human reviewer.
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
- Commands exercised:
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
- Commands exercised: adopt-review, doctor, context-pack, report, audit-info, audit-characters, revision-plan, eval-agent
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

- What stayed stable: To be recorded after the cycle closes.
- What changed: `eval-agent` was added before the cycle opened; watch whether it affects existing agent workflow contracts.
- Regression tests added: `test_eval_agent_generates_reproducible_agent_harness_report` plus CLI, package, and CI smoke coverage for `eval-agent`.
- Docs updated: Agent evaluation protocol, CLI guides, command contracts, testing guide, README, and promotion kit mention `eval-agent`.
- Follow-up: Rerun `audit-dogfood-cycle` on or after 2026-07-14, then update final status, decision, reviewer, and any compatibility/recovery notes from the real maintenance window.

## Acceptance Decision

Use one of:

- `accepted`: the sustained cycle completed, migration queues and blockers are closed, compatibility/recovery notes are current, and the record passes `audit-dogfood-cycle`.
- `deferred`: the repository has local migration evidence, but no sustained post-closure dogfood cycle is complete yet.
- `failed`: the cycle exposed a real regression or contract drift that needs a fix, tests, and a new cycle.
