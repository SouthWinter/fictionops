# End-To-End Migration And Publishing Case

This case shows how an outside contributor can move from a messy legacy folder to a FictionOps migration sandbox, then exercise the local publishing pipeline without relying on the Chinese deep-design notes.

It uses the tiny included legacy folder at `examples/legacy_novel_source/`. The folder is intentionally not a FictionOps project.

This is not a claim that the example is a finished novel. It proves the workflow shape:

```text
legacy folder
  -> read-only diagnosis
  -> copied sandbox
  -> import queue sorting
  -> ordinary migration fixes
  -> clean Markdown / metadata / manifest / EPUB
  -> release-gate evidence
```

## 1. Create A Temporary Sandbox

From the repository root:

```bash
tmpdir="$(mktemp -d)"
cp -R fictionops/examples/legacy_novel_source "$tmpdir/legacy_novel_source"

python fictionops/src/fictionops/cli.py init "$tmpdir/migrated-legacy" --title "Migrated Legacy"
```

On PowerShell, use a normal temporary directory and `Copy-Item -Recurse` instead of `cp -R`.

## 2. Diagnose And Copy The Legacy Folder

Run a read-only diagnosis:

```bash
python fictionops/src/fictionops/cli.py adopt "$tmpdir/legacy_novel_source" --format json
```

Then copy candidates into the initialized FictionOps sandbox:

```bash
python fictionops/src/fictionops/cli.py adopt "$tmpdir/legacy_novel_source" \
  --copy-to "$tmpdir/migrated-legacy" \
  --format json
```

The source folder remains unchanged. The sandbox receives copied candidates and an adoption manifest at:

```text
00_management/adopted_handoff/adopt_manifest.json
```

## 3. Review And Sort Imports

First review:

```bash
python fictionops/src/fictionops/cli.py adopt-review "$tmpdir/migrated-legacy" --format json
```

Expected status:

```text
needs_import_sorting
```

Inspect the import plan:

```bash
python fictionops/src/fictionops/cli.py import-plan "$tmpdir/migrated-legacy" --format json
```

Apply only safe moves and create missing chapter scaffolds:

```bash
python fictionops/src/fictionops/cli.py import-plan "$tmpdir/migrated-legacy" \
  --apply \
  --create-scaffolds \
  --replace-placeholder-targets \
  --format json
```

Review again:

```bash
python fictionops/src/fictionops/cli.py adopt-review "$tmpdir/migrated-legacy" --format json
```

Expected shape:

- status moves from `needs_import_sorting` to `needs_migration_fixes`;
- `import_queue_files` is `0`;
- remaining issues are ordinary project-memory work: information boundaries, character memory, chapter engines, retrospectives, and book closure.

That distinction matters. A migration can be file-sorted without being ready for normal creative work.

## 4. Generate Local Publishing Artifacts

Export clean Markdown:

```bash
python fictionops/src/fictionops/cli.py export-clean "$tmpdir/migrated-legacy" --book book_01 --format json
python fictionops/src/fictionops/cli.py audit-publish "$tmpdir/migrated-legacy" --book book_01 --format json
```

For this example, `audit-publish` should see two clean chapters after import sorting.

Add minimal editable metadata to `08_publish/publish_checklist.md`:

```markdown
# Publish Checklist

- Title: Migrated Legacy
- Author: FictionOps Example
- Language: en
- Category: Fantasy
- Tags: migration, workflow, example
- Keywords: legacy, fictionops, publish
- Synopsis: A tiny migrated legacy example used to exercise the FictionOps publishing pipeline.
```

Then build the remaining local package artifacts:

```bash
python fictionops/src/fictionops/cli.py export-metadata "$tmpdir/migrated-legacy" --book book_01 --format json
python fictionops/src/fictionops/cli.py export-manifest "$tmpdir/migrated-legacy" --book book_01 --format json
python fictionops/src/fictionops/cli.py export-epub "$tmpdir/migrated-legacy" --book book_01 --format json
python fictionops/src/fictionops/cli.py audit-epub "$tmpdir/migrated-legacy" --book book_01 --format json
```

Expected artifact shape:

- metadata title is `Migrated Legacy`;
- manifest schema is `fictionops.publish_manifest.v1`;
- EPUB audit reports a valid EPUB;
- all outputs remain inside `08_publish/`.

## 5. Run The Release Gate

Finally:

```bash
python fictionops/src/fictionops/cli.py release-gate "$tmpdir/migrated-legacy" --book book_01 --format json
```

Expected status:

```text
needs_release_fixes
```

That is the correct result for this tiny migration case. The package artifacts exist, but the migrated project still has book-level and migration-memory gaps. A contributor should not force the gate green by hiding those gaps. They should either:

- fill the missing durable memory files;
- record deliberate migration waivers where a human has accepted a gap;
- rerun `adopt-review`, `book-gate`, and `release-gate`.

## 6. Cleanup

When finished:

```bash
rm -rf "$tmpdir"
```

On PowerShell:

```powershell
Remove-Item -LiteralPath $tmpdir -Recurse -Force
```

## What This Case Proves

This case proves an English-speaking contributor can follow the whole local chain:

- diagnose a legacy folder without modifying it;
- copy into a sandbox;
- clear the import queue;
- understand why migration fixes remain;
- generate clean Markdown, metadata, manifest, and EPUB artifacts;
- use `release-gate` as a conservative local readiness check.

It does not prove a real long project is fully migrated, and it does not publish anything to PyPI, TestPyPI, or a fiction platform.
