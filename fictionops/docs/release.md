# FictionOps Release Guide

This guide covers the package release path for FictionOps itself. It does not publish or package any private novel, outline, draft, or author project.

The Chinese PyPI guide remains the detailed operational reference: [pypi-release.zh-CN.md](pypi-release.zh-CN.md). Use [release-trial-evidence.md](release-trial-evidence.md) to record the external GitHub Actions run URL, artifact details, TestPyPI record, smoke commands, and final `accepted/deferred/failed` decision. The publish workflow also uploads a workflow-generated release trial evidence draft artifact so the run URL, package hashes, and artifact names are captured in the same external run.

## Release Boundary

FictionOps releases ship:

- Python source files under `src/fictionops/`;
- packaged templates;
- docs and examples;
- tests and workflow documentation;
- CLI entry points.

FictionOps releases must not include:

- private manuscript files;
- private outlines or notes;
- API keys or publishing tokens;
- local build caches;
- temporary migration sandboxes.

## Local Preflight

From the repository root:

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

Expected artifacts:

```text
fictionops/dist/fictionops-<version>-py3-none-any.whl
fictionops/dist/fictionops-<version>.tar.gz
```

Inspect package contents before publishing. The wheel must include CLI modules and packaged templates. The sdist must include source, docs, examples, root templates, tests, and workflow documentation.

The CI and publish workflows also install the freshly built wheel into a clean virtual environment and run the smoke commands before upload or publishing. This protects against source-checkout success hiding a broken wheel entry point or missing packaged template.

The publish workflow uploads two separate artifacts:

- `fictionops-dist-<version>` contains only the wheel and sdist that may be passed to TestPyPI or PyPI.
- `fictionops-release-trial-evidence-<version>` contains the workflow-generated release trial evidence draft. Keep it separate from `dist/` so evidence notes are never treated as package files.

Use `fictionops audit-release-evidence . --file <downloaded-evidence.md> --format json` before closing the release-trial milestone. The command reports `ready=true` only when the evidence decision is `accepted`, the external run URL, run ID, artifact hashes, named reviewer, TestPyPI decision record, and install smoke fields are filled, and the built-wheel/init/doctor smoke fields explicitly show passing results.

## Install Smoke

Install the wheel in a clean virtual environment and verify:

```bash
fictionops --version
python -m fictionops --version
fictionops agent-exec --help
fictionops init smoke-novel --title "Smoke Novel"
fictionops doctor smoke-novel
```

The initialized project may report `needs_attention`; that is normal because starter files are intentionally incomplete.

## GitHub Actions Publishing

The publish workflow is:

```text
.github/workflows/fictionops-publish.yml
```

It is manually triggered with `workflow_dispatch` and requires:

- `target`: `testpypi` or `pypi`;
- `version`: expected package version.

The build job checks the input version against `fictionops/pyproject.toml`. A mismatch fails before upload.

## Credential Isolation

Publishing uses PyPI Trusted Publishing / OIDC. Do not store API tokens in the repository.

Configure PyPI or TestPyPI Trusted Publisher with:

- GitHub owner and repository;
- workflow file: `.github/workflows/fictionops-publish.yml`;
- environment: `testpypi` or `pypi`;
- package name: `fictionops`.

Only the publish job receives `id-token: write`. Build and test jobs have no publishing identity.

## Recommended Order

1. Run local preflight.
2. Confirm release notes and completion audit are current.
3. Trigger GitHub Actions publish with `target=testpypi`.
4. Install from TestPyPI and run the smoke commands.
5. Download the `fictionops-release-trial-evidence-<version>` artifact, then fill `docs/release-trial-evidence.md` or copy its evidence block into the release notes with the GitHub Actions run URL, artifact hashes, TestPyPI URLs, smoke results, and final decision.
6. Run `fictionops audit-release-evidence . --file <filled-evidence.md>` and do not close 0.4 unless it reports `ready=yes`.
7. Trigger GitHub Actions publish with `target=pypi`.

Skipping TestPyPI is discouraged. It can catch package-name, metadata, README rendering, and Trusted Publishing binding problems that local wheel smoke cannot.

## Rollback And Incidents

PyPI files are immutable for a version. Do not try to overwrite a broken release.

If a release is wrong:

1. Decide whether the issue affects installation, CLI entry points, templates, package contents, or user-data safety.
2. Yank the release on PyPI if the issue is severe.
3. Add a regression test.
4. Publish a patch version.
5. Record the incident in `CHANGELOG.md`, release notes, and the completion audit.

If the issue is documentation-only and does not affect installation or CLI contracts, it may be fixed in the next release, but it should still be recorded.
