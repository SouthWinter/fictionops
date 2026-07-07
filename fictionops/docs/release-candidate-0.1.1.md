# FictionOps 0.1.1 Release Candidate Plan

Status: TestPyPI run completed and accepted on 2026-07-07. GitHub Actions run `28849146871` published `fictionops==0.1.1` to TestPyPI, clean install smoke passed, and the accepted evidence record is now in `docs/release-trial-evidence.md`.

This plan exists because the accepted TestPyPI evidence for `0.1.0` was produced before later packaging and onboarding changes landed on `main`.

The `0.1.0` evidence is still useful historical proof that the publish workflow, Trusted Publishing, TestPyPI install, and smoke tests worked. It should not be treated as exact artifact evidence for the current repository head.

## Current Decision

Do not publish the current `main` artifact to formal PyPI as `0.1.0`.

Recommended next public package version:

```text
0.1.1
```

Reason:

- TestPyPI and PyPI artifacts are immutable for a version.
- `fictionops==0.1.0` already exists on TestPyPI from an earlier commit.
- Current `main` includes later changes to the GitHub landing page, package README, provider runner docs, model-provider onboarding, promotion kit, citation metadata, packaging metadata, and sdist contents.
- A fresh TestPyPI run should publish the exact version and commit intended for formal PyPI.

## What Stays 0.1.0

These files remain historical milestone evidence:

- `docs/release-notes-0.1.0.zh-CN.md`
- `docs/completion-audit-0.1.0.zh-CN.md`
- the accepted `docs/release-trial-evidence.md` record for GitHub Actions run `28837872185`
- roadmap and milestone entries describing the 0.1.0 pre-alpha MVP

Do not rename those files just because the next package upload is `0.1.1`.

## 0.1.1 Scope

`0.1.1` should be a packaging and onboarding patch release. It should not claim a new feature milestone.

Expected scope:

- GitHub root README and quickstart terminal preview;
- root `LICENSE` and `CITATION.cff`;
- repository topics and description;
- OpenAI-compatible Chat Completions runner example and model-provider docs;
- promotion kit and quickstart feedback template;
- updated package metadata URLs and keywords;
- workflow sdist checks for newly added docs/assets/examples.

## Required Version Bump

When ready to cut the candidate, update:

- `fictionops/pyproject.toml`
- `fictionops/src/fictionops/__init__.py`
- fallback `__version__` in `fictionops/src/fictionops/cli.py`
- `CITATION.cff`
- hardcoded package-version checks in CI and tests
- release-candidate or release-note text that describes the package artifact version

Keep `0.1.0` milestone evidence as historical evidence.

## TestPyPI Sequence

1. Bump the package version to `0.1.1`.
2. Run local preflight:

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

3. Push to `main` and wait for CI.
4. Trigger GitHub Actions `FictionOps Publish`:

```text
target = testpypi
version = 0.1.1
```

5. Download the `fictionops-release-trial-evidence-0.1.1` artifact.
6. Install from TestPyPI in a clean environment:

```bash
python -m venv .venv-release-trial
. .venv-release-trial/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps fictionops==0.1.1
fictionops --version
python -m fictionops --version
smoke_dir="$(mktemp -d)"
fictionops init "$smoke_dir/release-trial-smoke" --title "Release Trial Smoke"
fictionops doctor "$smoke_dir/release-trial-smoke" --format json
```

7. Fill a reviewed release evidence record and run:

```bash
fictionops audit-release-evidence . --file <filled-0.1.1-evidence.md> --format json
```

8. Only after the 0.1.1 TestPyPI evidence is accepted, trigger:

```text
target = pypi
version = 0.1.1
```

## GitHub Release

Recommended release tag:

```text
v0.1.1
```

Recommended title:

```text
FictionOps 0.1.1: pre-alpha packaging and onboarding release
```

Release notes should say:

- `0.1.0` proved the MVP and TestPyPI pipeline.
- `0.1.1` is the first recommended public package candidate after GitHub onboarding, provider docs, citation metadata, and README improvements.
- The project is still pre-alpha.
