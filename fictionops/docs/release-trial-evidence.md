# Release Trial Evidence

This file is the evidence template for the 0.4 release-trial milestone. It records real external release proof; it does not replace that proof.

Local tests, local wheels, local source distributions, and local clean-venv smoke tests are necessary preflight evidence. They do not prove the external release trial. To close the 0.4 milestone, record actual GitHub Actions run URLs and, when TestPyPI is used, the TestPyPI project or version URLs plus install smoke results.

When `.github/workflows/fictionops-publish.yml` runs, it uploads a workflow-generated release trial evidence draft as `fictionops-release-trial-evidence-<version>`. That draft captures the run URL, run ID, distribution artifact name, wheel hash, and sdist hash from the external workflow. Treat it as a starting record, then fill in the publish result, TestPyPI/PyPI URLs, install smoke output, reviewer, and final decision.

## Evidence Rules

- Record only evidence that exists outside the local checkout.
- Keep local command output as preflight context, not as the milestone-closing proof.
- If TestPyPI is skipped, record the reason and who accepted that decision.
- Do not mark the release trial accepted until install smoke commands are run from the published artifact or uploaded workflow artifact.
- Do not mark the release trial accepted unless `Built-wheel smoke result`, `fictionops init smoke result`, and `fictionops doctor smoke result` explicitly show passing results.
- Negative or ambiguous result text such as `not passed`, `failed`, `unsuccessful`, or unrelated words containing `pass` must not be treated as passing smoke evidence.
- `Date` must use `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`; when a local `pyproject.toml` exists, `Version` must match its project version, and both version smoke results must include that version.
- `GitHub Actions run URL` must use `https://github.com/<owner>/<repo>/actions/runs/<run-id>`, and `GitHub Actions run ID` must be the same positive integer run id.
- When TestPyPI is used, `TestPyPI project URL` and `TestPyPI version URL` must use `https://test.pypi.org/project/...`.
- The wheel filename must end in `.whl`, and the sdist filename must end in `.tar.gz`.
- Do not mark the release trial accepted without a named human reviewer.
- Keep the evidence draft artifact separate from `fictionops-dist-<version>` so publishing jobs upload only wheel and sdist files.
- Link this file from release notes, milestone status, and any release tag notes when the trial is complete.
- Run `fictionops audit-release-evidence . --file <filled-evidence.md>` before closing the release trial. A template, a deferred record, or an unreviewed workflow draft must not close 0.4.

## External Evidence Template

Copy this section into the release notes or keep a filled copy beside the release record.

```markdown
## Release Trial Evidence

- Date:
- Version:
- Commit / ref / tag:
- Decision: accepted / deferred / failed
- Reviewer:

### GitHub Actions

- Workflow name:
- Workflow file:
- GitHub Actions run URL:
- GitHub Actions run ID:
- Runner OS / Python matrix:
- Build job status:
- Test job status:
- Publish job status:
- Artifact name:
- Artifact download URL:
- Artifact retention note:

### Distribution Artifacts

- Wheel filename:
- Wheel SHA256:
- sdist filename:
- sdist SHA256:
- Built-wheel smoke result:
- sdist content check result:

### TestPyPI

- TestPyPI used: yes / no
- TestPyPI project URL:
- TestPyPI version URL:
- TestPyPI skip reason:
- TestPyPI skip accepted by:
- Trusted Publishing environment:
- Publish result:
- Clean venv install command:
- `fictionops --version` result:
- `python -m fictionops --version` result:
- `fictionops init` smoke result:
- `fictionops doctor` smoke result:
- Rollback / cleanup note:

### Notes

- Known issue:
- Follow-up:
- Waiver, if any:
```

## Collection Commands

Use a clean shell and a temporary directory.

```bash
python -m venv .venv-release-trial
. .venv-release-trial/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps fictionops==0.1.0
fictionops --version
python -m fictionops --version
smoke_dir="$(mktemp -d)"
fictionops init "$smoke_dir/release-trial-smoke" --title "Release Trial Smoke"
fictionops doctor "$smoke_dir/release-trial-smoke" --format json
```

For a GitHub Actions artifact instead of TestPyPI, download the workflow artifact into a clean directory and install the wheel directly:

```bash
python -m venv .venv-release-trial
. .venv-release-trial/bin/activate
python -m pip install --upgrade pip
python -m pip install --no-deps dist/fictionops-*.whl
fictionops --version
python -m fictionops --version
smoke_dir="$(mktemp -d)"
fictionops init "$smoke_dir/release-trial-smoke" --title "Release Trial Smoke"
fictionops doctor "$smoke_dir/release-trial-smoke" --format json
```

On Windows PowerShell, replace the activation and temporary-directory lines with:

```powershell
python -m venv .venv-release-trial
.\.venv-release-trial\Scripts\Activate.ps1
python -m pip install --upgrade pip
$smokeDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ("fictionops-release-trial-" + [guid]::NewGuid()))
fictionops init (Join-Path $smokeDir "release-trial-smoke") --title "Release Trial Smoke"
fictionops doctor (Join-Path $smokeDir "release-trial-smoke") --format json
```

## Acceptance Decision

Use one of these decisions. The compact decision set is `accepted/deferred/failed`.

- `accepted`: the workflow ran externally, artifacts were produced, install smoke passed, and release notes link the run.
- `deferred`: the repository is ready, but GitHub Actions, TestPyPI, or release timing prevents completion.
- `failed`: external evidence exists and shows a real problem that needs a fix, test, and rerun.

## Accepted Evidence Record

- Date: 2026-07-07T02:48:27Z
- Version: 0.1.0
- Commit / ref / tag: fcb97170bb263bc4e4f0992f0bcdb795f1152bf0 / main
- Decision: accepted
- Reviewer: SouthWinter

### GitHub Actions

- Workflow name: FictionOps Publish
- Workflow file: .github/workflows/fictionops-publish.yml
- GitHub Actions run URL: https://github.com/SouthWinter/fictionops/actions/runs/28837872185
- GitHub Actions run ID: 28837872185
- Runner OS / Python matrix: ubuntu-latest / Python 3.12
- Build job status: passed
- Test job status: passed
- Publish job status: passed to TestPyPI
- Distribution artifact name: fictionops-dist-0.1.0
- Artifact download URL: https://github.com/SouthWinter/fictionops/actions/runs/28837872185
- Artifact retention note: GitHub Actions artifacts retained until 2026-10-05

### Distribution Artifacts

- Wheel filename: fictionops-0.1.0-py3-none-any.whl
- Wheel SHA256: b4481ce53387f75cd5cfe0cbdb36041befbc1a57cc03a8f26acf6a5af3d05ab3
- sdist filename: fictionops-0.1.0.tar.gz
- sdist SHA256: 54165d8caa570e3267e30b534fdf90073d5bd5a47774a6481adbd919d9feb6b2
- Built-wheel smoke result: passed in GitHub Actions build job
- sdist content check result: passed in GitHub Actions build job

### TestPyPI

- TestPyPI used: yes
- TestPyPI project URL: https://test.pypi.org/project/fictionops/
- TestPyPI version URL: https://test.pypi.org/project/fictionops/0.1.0/
- TestPyPI skip reason: not skipped
- TestPyPI skip accepted by: not applicable
- Trusted Publishing environment: testpypi
- Publish result: passed
- Clean venv install command: python -m pip install --index-url https://test.pypi.org/simple/ --no-deps fictionops==0.1.0
- `fictionops --version` result: fictionops 0.1.0
- `python -m fictionops --version` result: fictionops 0.1.0
- `fictionops init` smoke result: passed
- `fictionops doctor` smoke result: passed
- Rollback / cleanup note: no rollback needed; TestPyPI trial package remains available for verification

### Notes

- Known issue: none for release trial
- Follow-up: continue sustained dogfood-cycle and stability-window evidence before 1.0 closure
- Waiver, if any: none
