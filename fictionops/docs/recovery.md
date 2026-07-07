# Recovery Playbook

This playbook covers common FictionOps mistakes and damaged states. It is intentionally procedural: find the symptom, preserve evidence, run the smallest safe command, and stop before making the damage worse.

FictionOps is file-based. Recovery should favor ordinary backups, version control, explicit reports, and re-running generated artifacts over silent repair.

## Recovery Rules

Before fixing anything:

1. Preserve the current project folder or commit it to version control.
2. Prefer read-only commands first: `doctor`, `report`, `adopt-review`, `book-gate`, `release-gate`, `agent-inbox`.
3. Do not use `--force` until you know which generated file you are replacing.
4. Do not let an external model edit `03_characters/`, `04_structure/`, `05_canon/`, or `06_drafts/` directly.
5. Record deliberate human decisions in `00_management/decision_log.md`, the relevant retrospective, or a waiver file.

## Quick Triage

```bash
fictionops doctor my-novel --book book_01 --format json
fictionops report my-novel --book book_01 --format json
fictionops workflow-plan my-novel --stage all --book book_01
```

Use those outputs to decide which section below applies.

## Generated Report Was Overwritten

Symptom:

- A Markdown report, context pack, draft brief, or gate report was replaced with bad content.

Do:

```bash
fictionops doctor my-novel --format json
```

If the file is generated and no human-only notes were stored inside it, regenerate it with the same command and `--force`. Examples:

```bash
fictionops context-pack my-novel --task handoff --out 00_management/context/handoff.md --force
fictionops review-gate my-novel --chapter 001 --out 07_audits/review_gate/ch_001.md --force
fictionops release-gate my-novel --book book_01 --out 07_audits/release_gate/book_01.md --force
```

If the overwritten file contained human notes, restore it from version control or backup first. Do not regenerate over it again.

## Draft Or Canon File Was Accidentally Edited

Symptom:

- A chapter, character file, information table, or structure file changed unexpectedly.

Do:

```bash
fictionops audit-continuity my-novel --book book_01 --format json
fictionops audit-info my-novel --book book_01 --format json
fictionops audit-characters my-novel --format json
```

Then compare against version control or a backup. FictionOps does not silently reconstruct prose or canon. Restore the last trusted version, then rerun:

```bash
fictionops review-gate my-novel --chapter 001 --format json
fictionops book-gate my-novel --book book_01 --format json
```

Stop if the restored state conflicts with later chapters. That is an editorial decision, not an automatic recovery.

## Agent Output Is Wrong Or Unsafe

Symptom:

- `agent-exec` wrote an unusable `output.md`;
- `agent-inbox` reports multiple outputs, empty output, or a damaged request;
- a model response includes future secrets or direct file-edit instructions.

Do:

```bash
fictionops agent-inbox my-novel --format json
```

Then:

- archive or delete the bad staged output;
- keep `request.json`, `prompt.md`, and `execution.json` when you need an audit trail;
- rerun `agent-inbox`;
- rerun `agent-exec` only after fixing the runner or prompt boundary.

Do not paste unsafe output directly into manuscript or canon. If you decide to use part of it, record the human decision and rerun the relevant gate.

## Import Queue Is Stuck

Symptom:

- `adopt-review` reports `needs_import_sorting`;
- files remain under `06_drafts/import_queue/`.

Do:

```bash
fictionops import-plan my-novel --format json
fictionops import-plan my-novel --out 07_audits/adopt_review/import_plan.md
```

Only apply safe moves after reviewing the plan:

```bash
fictionops import-plan my-novel --apply --create-scaffolds --format json
```

Use `--replace-placeholder-targets` only for generated placeholder chapter targets. If a real chapter target already exists, leave it for manual review.

After applying:

```bash
fictionops adopt-review my-novel --format json
```

If ambiguous files remain, move them manually only after deciding their book/chapter targets.

## Migration Waiver Was Too Broad

Symptom:

- `adopt-review` looks cleaner than expected;
- important issues disappeared after adding `07_audits/adopt_review/waivers.json`.

Do:

1. Open the waiver file.
2. Narrow each waiver by adding `source`, `code`, `subject`, or `path`.
3. Keep a human-readable `reason`.
4. Rerun:

```bash
fictionops adopt-review my-novel --format json
fictionops adopt-plan my-novel --format json
```

Waivers defer known work. They should not hide unknown work, and they never clear physical `import_queue` files.

## Publish Artifact Is Missing Or Stale

Symptom:

- `audit-publish`, `audit-epub`, `doctor`, or `release-gate` reports missing, stale, or hash-mismatched artifacts.

Do:

```bash
fictionops export-clean my-novel --book book_01 --force --format json
fictionops audit-publish my-novel --book book_01 --format json
fictionops export-metadata my-novel --book book_01 --force --format json
fictionops export-manifest my-novel --book book_01 --force --format json
fictionops export-epub my-novel --book book_01 --force --format json
fictionops audit-epub my-novel --book book_01 --format json
fictionops release-gate my-novel --book book_01 --format json
```

Use `--force` here only because these are generated publish artifacts. Do not treat a passing `release-gate` as marketplace acceptance.

## Controller Repeats The Same Step

Symptom:

- an external controller keeps selecting the same command;
- no project evidence changes between loop iterations.

Do:

```bash
fictionops agent-next my-novel --book book_01 --format json
```

Then inspect the controller log. A safe controller should stop on repeated suggestions. If it does not, disable the controller and run the selected command manually. Do not keep looping blindly.

## When To Stop

Stop automatic recovery and ask for human review when:

- the next action would modify manuscript, canon, credentials, or release uploads;
- two valid story states conflict and both have later consequences;
- a migration file has multiple plausible chapter targets;
- a waiver would silence an issue you do not understand;
- a model output changes facts, timelines, or information boundaries.

The recovery goal is not to make every gate green quickly. It is to preserve the evidence trail until the author can make a real decision.
