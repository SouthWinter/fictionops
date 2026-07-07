# FictionOps Known Limits

FictionOps is intentionally conservative. It helps maintain long-form fiction projects, but it does not make literary, legal, publishing, or autonomous-agent promises. This page records current limits so users, contributors, and external controllers do not confuse a passed workflow gate with a finished novel.

## Product Stage

FictionOps is still a pre-alpha local CLI. Command behavior is covered by tests and documented contracts, but the public API is not frozen as a 1.0 stable interface.

Current stability expectations:

- CLI commands should keep existing JSON keys whenever practical.
- New report fields should be added rather than replacing old meanings.
- File writes should continue to refuse accidental overwrites unless a command exposes and receives `--force`.
- Breaking changes before 1.0 must be documented in `CHANGELOG.md` and the CLI contract docs.

The detailed compatibility policy lives in [compatibility.md](compatibility.md).

## Literary Judgment

FictionOps does not judge whether prose is beautiful, publishable, emotionally true, or commercially viable. Audits can find maintenance risks such as missing information boundaries, repeated openings, flat chapter length, stale echoes, and incomplete character files.

Recommended mitigation:

- Treat audit output as evidence, not verdict.
- Keep human editorial judgment in retrospectives and decision logs.
- Record deliberate overrides when an audit warning is aesthetically correct to ignore.

## Model Behavior

FictionOps core does not call model providers. External runners may call OpenAI, local models, or other systems through `agent-exec`, but their output is staged and must be reviewed.

Known limits:

- Model quality, cost, latency, and provider availability are outside FictionOps control.
- The OpenAI runner example is an integration sample, not a managed provider SDK.
- External runners can leak or misuse context if the user writes them unsafely.

Recommended mitigation:

- Use `context-pack` budgets and task-specific scopes.
- Run external runners in dry-run or sandbox mode first.
- Keep API keys in environment variables, never project files.
- Inspect staged output with `agent-inbox` before applying anything.

## Context And Memory

FictionOps stores project memory in files, but it cannot guarantee that every human or agent has read the right file. A missing or stale table can make a report look cleaner than the story really is.

Known limits:

- `audit-info` and `audit-echoes` use structured tables and rough text scans, not full semantic understanding.
- Character, voice, and intelligence audits only know what is recorded in character memory.
- Long projects may contain old, duplicated, or deprecated notes that still need human sorting.

Recommended mitigation:

- Keep deprecated material in `99_archive/`.
- Run `doctor`, `review-gate`, and `book-gate` after major manual edits.
- Use `adopt-review` waivers only for conscious deferrals, not to hide unknowns.

## Migration

Migration tools diagnose and stage old material. They do not automatically understand a messy writing archive.

Known limits:

- `adopt` suggestions are heuristic.
- `import-plan --apply` moves only safe, unambiguous draft files.
- `adopt-review` can prove that known blockers are cleared or waived, but it cannot prove that the old project was conceptually migrated perfectly.

Recommended mitigation:

- Migrate into a separate initialized sandbox.
- Keep the source project read-only.
- Preserve `00_management/adopted_handoff/adopt_manifest.json`.
- Record waived blockers in `07_audits/adopt_review/waivers.json` with reasons.

## Publishing

FictionOps can export clean Markdown, metadata, manifests, EPUB files, and release gates. It does not guarantee marketplace compliance, copyright clearance, cover licensing, ISBN setup, printer requirements, or platform acceptance.

Recommended mitigation:

- Treat `release-gate` as a local package-readiness check.
- Run platform-specific validation outside FictionOps.
- Keep final upload credentials, tax/payment data, and marketplace accounts outside the project.

## Collaboration And Version Control

FictionOps uses ordinary files, which makes it friendly to Git and backups. It does not provide locking, multiplayer editing, merge resolution, or cloud sync.

Recommended mitigation:

- Use normal version control for shared projects.
- Avoid simultaneous edits to the same canon table.
- Record major structural decisions in `00_management/decision_log.md`.

## Security Boundary

FictionOps is not a security sandbox. It can run external commands through `agent-exec`, and those commands have the permissions of the user running them.

Recommended mitigation:

- Run only trusted external runners.
- Review runner scripts before passing sensitive context.
- Prefer dry runs before real model calls.
- Do not point FictionOps commands at directories you are not willing to audit.

## Recovery Expectations

FictionOps should make common mistakes visible, but recovery still requires human action.

Examples:

- If a generated report was overwritten with `--force`, restore it from version control or regenerate it.
- If a staged agent output is wrong, delete or archive that staging file and rerun `agent-inbox`.
- If a migration waiver was too broad, narrow its match fields and rerun `adopt-review`.
- If a release artifact is stale, rerun the relevant export and then rerun `release-gate`.

For step-by-step procedures, see [Recovery playbook](recovery.md).

The stable rule is: FictionOps should preserve the evidence trail. The author decides what becomes the book.
