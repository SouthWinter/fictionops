# FictionOps Migration Guide

This guide explains how to bring an existing long-form fiction folder into FictionOps without damaging the source project.

The migration tools are conservative by design. They first diagnose, then copy into a sandbox, then plan cleanup, and only move draft files when the command is explicitly told to apply safe moves.

The repository includes a tiny runnable legacy source at `examples/legacy_novel_source/`. Use it when you want to test the migration workflow before touching a real project.

For a longer English case that continues from migration into clean Markdown, metadata, manifest, EPUB, and `release-gate`, see [End-to-end migration and publishing case](end-to-end-migration-publish.md).

## 1. Diagnose The Existing Folder

Run `adopt` against the old writing directory:

```bash
fictionops adopt existing-novel --out adopt_report.md
fictionops adopt existing-novel --format json
```

`adopt` is read-only. It scans Markdown, text, YAML, and JSON files, then maps candidates into FictionOps layers such as management, story seed, world, characters, structure, canon, drafts, audits, publish, and archive.

The report includes:

- file counts and text-size summaries;
- suggested FictionOps target paths;
- migration phases;
- risks such as missing `project.yml`, archive material, and mixed legacy folders;
- next actions.

## 2. Create A Clean Sandbox

Do not migrate directly into the old project. Create a separate FictionOps project:

```bash
fictionops init migrated-novel --title "Migrated Novel"
```

Then copy candidates into that sandbox:

```bash
fictionops adopt existing-novel --copy-to migrated-novel --format json
```

The source folder remains unchanged. The sandbox receives copied files, and FictionOps writes:

```text
00_management/adopted_handoff/adopt_manifest.json
```

The manifest preserves source paths and chosen target paths. Later migration tools use it to avoid guessing chapter ownership from copied file names alone.

## 3. Review The Sandbox

After copying, run:

```bash
fictionops adopt-review migrated-novel --format json
```

`adopt-review` aggregates normal project checks with migration-specific signals. It can report:

- `needs_import_sorting`: draft files still sit in `06_drafts/import_queue/`;
- `needs_migration_fixes`: files are placed, but project memory is still thin;
- `ready_for_project_work`: the sandbox can enter normal FictionOps work.

This command does not move or edit files.

If a remaining issue is a deliberate human decision rather than an active blocker, record it in:

```text
07_audits/adopt_review/waivers.json
```

or pass an explicit file:

```bash
fictionops adopt-review migrated-novel --waivers 07_audits/adopt_review/waivers.json
```

Waivers require a reason and match issues by one or more of `source`, `code`, `subject`, and `path`:

```json
{
  "waivers": [
    {
      "source": "audit-info",
      "code": "no_information_items",
      "reason": "Deferred until the first canon-normalization pass.",
      "owner": "author",
      "until": "0.2 dogfood"
    }
  ]
}
```

`adopt-review` still reports total, active, and waived issue counts. Waivers defer current blockers but do not erase the audit record. They also do not make unsorted files in `06_drafts/import_queue/` count as migrated; imported drafts still need to be sorted or removed from the queue.

## 4. Plan Cleanup

Convert review findings into prioritized work:

```bash
fictionops adopt-plan migrated-novel --out 07_audits/adopt_review/plan.md
fictionops adopt-plan migrated-novel --write-groups 07_audits/adopt_review/repair_groups
```

Large migrations may produce hundreds of issues. `adopt-plan` folds them into repair groups so a human or agent can work by phase: import sorting, structure cleanup, canon and information boundaries, character memory, retrospectives, table cleanup, and style or length review.

`adopt-plan` uses the same default waiver file as `adopt-review`, and also accepts `--waivers`. Explicitly waived issues are not converted into active cleanup tasks.

## 5. Sort Imported Drafts

If review reports `needs_import_sorting`, inspect:

```bash
fictionops import-plan migrated-novel --out 07_audits/adopt_review/import_plan.md
```

Only after checking the plan, apply safe moves:

```bash
fictionops import-plan migrated-novel --apply --create-scaffolds
```

Use placeholder replacement only when you want generated starter chapters to be replaced by imported draft files:

```bash
fictionops import-plan migrated-novel --apply --create-scaffolds --replace-placeholder-targets
```

`import-plan --apply` moves only unambiguous files whose targets are safe. Ambiguous chapter numbers, duplicate targets, and real existing targets stay in the import queue for human review.

## 6. Enter Normal FictionOps Work

After import sorting, run:

```bash
fictionops adopt-review migrated-novel
fictionops doctor migrated-novel --book book_01
fictionops workflow-plan migrated-novel --stage all
```

At this point the hard work is usually not file movement. It is filling durable project memory:

- information release tables;
- character arcs, intelligence profiles, and voice profiles;
- chapter engines;
- chapter retrospectives;
- foreshadowing echo tables;
- book retrospectives.

Migration succeeds when the old project becomes maintainable, not when every file has merely been copied.

## 7. Try The Included Legacy Example

From the repository root:

```bash
python fictionops/src/fictionops/cli.py adopt fictionops/examples/legacy_novel_source --format json
python fictionops/src/fictionops/cli.py init migrated-legacy --title "Migrated Legacy"
python fictionops/src/fictionops/cli.py adopt fictionops/examples/legacy_novel_source --copy-to migrated-legacy --format json
python fictionops/src/fictionops/cli.py adopt-review migrated-legacy --format json
python fictionops/src/fictionops/cli.py import-plan migrated-legacy --format json
python fictionops/src/fictionops/cli.py import-plan migrated-legacy --apply --create-scaffolds --replace-placeholder-targets --format json
python fictionops/src/fictionops/cli.py adopt-review migrated-legacy --format json
```

Expected shape:

- the first review reports `needs_import_sorting`;
- `import-plan` finds one ready chapter and one generated placeholder target;
- applying the plan moves two draft files into `06_drafts/book_01/chapters/`;
- the next review reports zero import-queue files and moves on to ordinary migration fixes.
