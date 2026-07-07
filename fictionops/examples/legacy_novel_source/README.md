# Legacy Novel Source

This directory is intentionally not a FictionOps project. It is a tiny legacy source folder used to demonstrate safe migration:

1. diagnose with `adopt`;
2. copy into a clean `fictionops init` sandbox;
3. review with `adopt-review`;
4. plan cleanup with `adopt-plan`;
5. sort imported drafts with `import-plan`.

From the repository root:

```bash
python fictionops/src/fictionops/cli.py adopt fictionops/examples/legacy_novel_source --format json
python fictionops/src/fictionops/cli.py init migrated-legacy --title "Migrated Legacy"
python fictionops/src/fictionops/cli.py adopt fictionops/examples/legacy_novel_source --copy-to migrated-legacy --format json
python fictionops/src/fictionops/cli.py adopt-review migrated-legacy --format json
python fictionops/src/fictionops/cli.py import-plan migrated-legacy --apply --create-scaffolds --replace-placeholder-targets --format json
```
