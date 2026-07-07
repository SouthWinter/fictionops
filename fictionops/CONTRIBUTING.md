# Contributing To FictionOps

Thanks for considering a contribution. FictionOps is not a one-click novel generator. It is a local workflow toolkit for keeping long-form fiction projects maintainable while allowing bounded AI-agent collaboration.

## Good Contributions

High-value changes include:

- fixing CLI contract bugs;
- improving package installation and template loading;
- adding regression tests for long workflow edges;
- improving local-first audits;
- making migration safer;
- clarifying agent inputs, outputs, and no-overwrite boundaries;
- improving documentation and examples.

Changes that should be treated cautiously:

- one-click full-novel generation;
- mandatory network services for core workflows;
- large GUI or database layers before the file workflow is stable;
- hard-coded literary taste as if it were an objective test.

## Development Setup

Use Python 3.10 or newer:

```bash
python -m pip install -e ./fictionops
fictionops --version
python -m fictionops --version
```

Run tests:

```bash
python -m unittest discover -s fictionops/tests -v
```

Run a targeted smoke:

```bash
python -m unittest discover -s fictionops/tests -p test_cli.py -k release_smoke -v
```

## Before Submitting

Check that:

- new commands have direct function tests and CLI subprocess tests;
- JSON output is parsed in tests when a command supports JSON;
- write commands refuse accidental overwrite unless `--force` is explicit;
- package-affecting changes update sdist/wheel content checks;
- root `templates/` and `src/fictionops/templates/` remain synchronized;
- docs commands can actually run;
- private manuscript or outline material is not added as test data.

## Design Principles

FictionOps should stay:

- file-first, so writers can inspect and version project state;
- local-first, so core work does not require cloud services;
- author-first, so tools surface structure gaps without replacing aesthetic judgment;
- agent-aware, so model outputs are staged and auditable;
- long-form-first, so decisions remain useful after hundreds of chapters.

## Release Notes And Docs

User-visible changes should update `CHANGELOG.md`. Release-shaping changes should also update the release notes, completion audit, and relevant docs.

Chinese docs currently contain the deepest methodology. English docs should still keep install, migration, agent, testing, release, and contribution paths usable for external contributors.

