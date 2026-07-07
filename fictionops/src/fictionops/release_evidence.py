from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from .markdown import safe_cell
from .models import ReleaseEvidenceIssue, ReleaseEvidenceReport


DECISIONS = {"accepted", "deferred", "failed"}
REQUIRED_FIELDS = [
    "Date",
    "Version",
    "Commit / ref / tag",
    "Decision",
    "Reviewer",
    "GitHub Actions run URL",
    "GitHub Actions run ID",
    "Wheel filename",
    "Wheel SHA256",
    "sdist filename",
    "sdist SHA256",
    "Built-wheel smoke result",
    "TestPyPI used",
    "fictionops --version result",
    "python -m fictionops --version result",
    "fictionops init smoke result",
    "fictionops doctor smoke result",
]
PASS_RESULT_FIELDS = [
    "Built-wheel smoke result",
    "fictionops init smoke result",
    "fictionops doctor smoke result",
]
PLACEHOLDER_VALUES = {
    "",
    "accepted / deferred / failed",
    "yes / no",
    "accepted/deferred/failed",
    "passed when this artifact is present",
}


def default_release_evidence_path(target: Path) -> Path:
    if target.is_file():
        return target.resolve()
    return (target / "docs" / "release-trial-evidence.md").resolve()


def normalize_field_name(raw: str) -> str:
    key = raw.strip().replace("`", "").strip()
    key = re.sub(r"\s+", " ", key)
    aliases = {
        "Artifact name": "Distribution artifact name",
        "artifact name": "Distribution artifact name",
        "wheel filename": "Wheel filename",
        "wheel SHA256": "Wheel SHA256",
        "sdist filename": "sdist filename",
        "sdist SHA256": "sdist SHA256",
        "fictionops --version result": "fictionops --version result",
        "python -m fictionops --version result": "python -m fictionops --version result",
        "fictionops init smoke result": "fictionops init smoke result",
        "fictionops doctor smoke result": "fictionops doctor smoke result",
        "TestPyPI skipped reason": "TestPyPI skip reason",
        "TestPyPI skip accepted by": "TestPyPI skip accepted by",
    }
    return aliases.get(key, key)


def is_placeholder(value: str) -> bool:
    cleaned = value.strip()
    if cleaned in PLACEHOLDER_VALUES:
        return True
    if cleaned.endswith(":") and len(cleaned) <= 40:
        return True
    return False


def parse_release_evidence_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]\s+(.+?):\s*(.*)\s*$", line)
        if not match:
            continue
        key = normalize_field_name(match.group(1))
        value = match.group(2).strip()
        fields[key] = value
    return fields


def issue(severity: str, code: str, field: str, message: str) -> ReleaseEvidenceIssue:
    return ReleaseEvidenceIssue(severity=severity, code=code, field=field, message=message)


def sha256_like(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value.strip()))


def github_actions_run_id_from_url(value: str) -> str | None:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        return None
    match = re.fullmatch(r"/[^/]+/[^/]+/actions/runs/(\d+)(?:/.*)?", parsed.path)
    return match.group(1) if match else None


def testpypi_url_like(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and parsed.netloc.lower() == "test.pypi.org" and parsed.path.startswith("/project/")


def positive_int_like(value: str) -> bool:
    cleaned = value.strip()
    return cleaned.isdigit() and int(cleaned) > 0


def valid_release_date(value: str) -> bool:
    cleaned = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", cleaned):
        try:
            date.fromisoformat(cleaned)
            return True
        except ValueError:
            return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", cleaned):
        try:
            datetime.strptime(cleaned, "%Y-%m-%dT%H:%M:%SZ")
            return True
        except ValueError:
            return False
    return False


def pyproject_version(target: Path) -> str | None:
    pyproject = target / "pyproject.toml"
    if not pyproject.exists() or not pyproject.is_file():
        return None
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"\s*$', text)
    return match.group(1).strip() if match else None


NEGATIVE_RESULT_PATTERNS = (
    r"(?<![a-z])did[\s_-]+not[\s_-]+pass(?:ed)?(?![a-z])",
    r"(?<![a-z])not[\s_-]+pass(?:ed)?(?![a-z])",
    r"(?<![a-z])not[\s_-]+ok(?![a-z])",
    r"(?<![a-z])fail(?:ed|ing)?(?![a-z])",
    r"(?<![a-z])unsuccessful(?![a-z])",
)
PASS_RESULT_PATTERNS = (
    r"(?<![a-z])pass(?:ed)?(?![a-z])",
    r"(?<![a-z])ok(?![a-z])",
    r"(?<![a-z])success(?:ful)?(?![a-z])",
    r"(?<![a-z])succeeded(?![a-z])",
)


def pass_like(value: str) -> bool:
    lowered = value.strip().lower()
    if any(re.search(pattern, lowered) for pattern in NEGATIVE_RESULT_PATTERNS):
        return False
    return any(re.search(pattern, lowered) for pattern in PASS_RESULT_PATTERNS)


def build_release_evidence_audit(
    target: Path,
    *,
    file_path: str | None = None,
) -> ReleaseEvidenceReport:
    resolved = target.expanduser().resolve()
    evidence_file = Path(file_path).expanduser() if file_path else default_release_evidence_path(resolved)
    if file_path and not evidence_file.is_absolute():
        evidence_file = (resolved / evidence_file).resolve()
    issues: list[ReleaseEvidenceIssue] = []

    if not evidence_file.exists():
        issues.append(
            issue(
                "P1",
                "missing_release_evidence",
                "evidence_file",
                f"Release trial evidence file was not found: {evidence_file}",
            )
        )
        return ReleaseEvidenceReport(
            target=str(resolved),
            evidence_file=str(evidence_file),
            evidence_file_exists=False,
            status="missing",
            ready=False,
            decision="",
            field_count=0,
            missing_required_fields=REQUIRED_FIELDS.copy(),
            issue_count=len(issues),
            blocking_issue_count=len(issues),
            issues=issues,
            next_actions=["Create or download a filled release trial evidence record, then rerun audit-release-evidence."],
        )
    if not evidence_file.is_file():
        raise IsADirectoryError(f"release evidence path is not a file: {evidence_file}")

    text = evidence_file.read_text(encoding="utf-8")
    fields = parse_release_evidence_fields(text)
    missing_required: list[str] = []
    for field in REQUIRED_FIELDS:
        value = fields.get(field, "")
        if is_placeholder(value):
            missing_required.append(field)
            issues.append(
                issue(
                    "P2",
                    "missing_required_evidence",
                    field,
                    f"Required release evidence field is empty or still a placeholder: {field}",
                )
            )

    decision = fields.get("Decision", "").strip().lower()
    if decision not in DECISIONS:
        issues.append(
            issue(
                "P1",
                "invalid_decision",
                "Decision",
                "Decision must be one of accepted, deferred, or failed.",
            )
        )
    elif decision != "accepted":
        issues.append(
            issue(
                "P2",
                f"decision_{decision}",
                "Decision",
                f"Release trial decision is {decision}, so the evidence does not close the milestone.",
            )
        )

    release_date = fields.get("Date", "")
    if release_date and not is_placeholder(release_date) and not valid_release_date(release_date):
        issues.append(
            issue(
                "P1",
                "invalid_release_date",
                "Date",
                "Date should use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ.",
            )
        )

    version = fields.get("Version", "").strip()
    package_version = pyproject_version(resolved)
    if version and not is_placeholder(version):
        if package_version and version != package_version:
            issues.append(
                issue(
                    "P1",
                    "release_version_mismatch",
                    "Version",
                    f"Version should match pyproject.toml version {package_version}.",
                )
            )
        for field in ("fictionops --version result", "python -m fictionops --version result"):
            value = fields.get(field, "")
            if value and not is_placeholder(value) and version not in value:
                issues.append(
                    issue(
                        "P2",
                        "version_result_mismatch",
                        field,
                        f"{field} should include the release evidence Version value {version}.",
                    )
                )

    run_url = fields.get("GitHub Actions run URL", "")
    run_url_id: str | None = None
    if run_url and not is_placeholder(run_url):
        run_url_id = github_actions_run_id_from_url(run_url)
        if run_url_id is None:
            issues.append(
                issue(
                    "P1",
                    "invalid_github_run_url",
                    "GitHub Actions run URL",
                    "GitHub Actions run URL should be an https://github.com/<owner>/<repo>/actions/runs/<run-id> URL.",
                )
            )

    run_id = fields.get("GitHub Actions run ID", "")
    if run_id and not is_placeholder(run_id) and not positive_int_like(run_id):
        issues.append(
            issue(
                "P1",
                "invalid_github_run_id",
                "GitHub Actions run ID",
                "GitHub Actions run ID should be a positive integer copied from the external workflow run.",
            )
        )
    elif run_id and run_url_id and run_id.strip() != run_url_id:
        issues.append(
            issue(
                "P1",
                "github_run_id_mismatch",
                "GitHub Actions run ID",
                "GitHub Actions run ID should match the run id embedded in GitHub Actions run URL.",
            )
        )

    filename_rules = {
        "Wheel filename": ".whl",
        "sdist filename": ".tar.gz",
    }
    for field, suffix in filename_rules.items():
        value = fields.get(field, "")
        if value and not is_placeholder(value) and not value.endswith(suffix):
            issues.append(issue("P1", "invalid_distribution_filename", field, f"{field} should end with `{suffix}`."))

    for field in ("Wheel SHA256", "sdist SHA256"):
        value = fields.get(field, "")
        if value and not is_placeholder(value) and not sha256_like(value):
            issues.append(
                issue("P1", "invalid_sha256", field, f"{field} should be a 64-character hexadecimal SHA256.")
            )

    testpypi_used = fields.get("TestPyPI used", "").strip().lower()
    if testpypi_used and testpypi_used not in {"yes", "no"} and not is_placeholder(testpypi_used):
        issues.append(issue("P1", "invalid_testpypi_used", "TestPyPI used", "TestPyPI used must be yes or no."))
    elif testpypi_used == "yes":
        for field in ("TestPyPI project URL", "TestPyPI version URL"):
            value = fields.get(field, "")
            if is_placeholder(value) or not testpypi_url_like(value):
                issues.append(
                    issue(
                        "P2",
                        "missing_testpypi_url",
                        field,
                        f"{field} must be an https://test.pypi.org/project/... URL when TestPyPI used is yes.",
                    )
                )
        publish_result = fields.get("Publish result", "")
        if is_placeholder(publish_result) or not pass_like(publish_result):
            issues.append(
                issue(
                    "P2",
                    "testpypi_publish_not_passed",
                    "Publish result",
                    "Publish result should show a successful TestPyPI publish when TestPyPI used is yes.",
                )
            )
        install_command = fields.get("Clean venv install command", "")
        if is_placeholder(install_command) or "pip install" not in install_command:
            issues.append(
                issue(
                    "P2",
                    "missing_clean_install_command",
                    "Clean venv install command",
                    "Clean venv install command should record the exact pip install command used for the smoke test.",
                )
            )
    elif testpypi_used == "no":
        for field in ("TestPyPI skip reason", "TestPyPI skip accepted by"):
            value = fields.get(field, "")
            if is_placeholder(value):
                issues.append(
                    issue("P2", "missing_testpypi_skip_record", field, f"{field} is required when TestPyPI used is no.")
                )

    for field in PASS_RESULT_FIELDS:
        value = fields.get(field, "")
        if value and not is_placeholder(value) and not pass_like(value):
            issues.append(
                issue(
                    "P2",
                    "release_smoke_not_passed",
                    field,
                    f"{field} should show a passing smoke result before release evidence can be accepted.",
                )
            )

    blocking_count = sum(1 for item in issues if item.severity in {"P0", "P1", "P2"})
    if decision == "accepted" and blocking_count == 0:
        status = "accepted"
        ready = True
        next_actions = ["Link this evidence from release notes, milestone status, and the release/tag record."]
    elif decision == "failed":
        status = "failed"
        ready = False
        next_actions = ["Fix the release problem, add regression coverage, and rerun the external release trial."]
    elif decision == "deferred":
        status = "deferred"
        ready = False
        next_actions = ["Finish external publishing or artifact install smoke, then update the evidence decision."]
    else:
        status = "incomplete"
        ready = False
        next_actions = ["Fill missing evidence fields from the GitHub Actions artifact or TestPyPI/PyPI run."]

    return ReleaseEvidenceReport(
        target=str(resolved),
        evidence_file=str(evidence_file),
        evidence_file_exists=True,
        status=status,
        ready=ready,
        decision=decision,
        field_count=len(fields),
        missing_required_fields=missing_required,
        issue_count=len(issues),
        blocking_issue_count=blocking_count,
        issues=issues,
        next_actions=next_actions,
    )


def format_release_evidence_audit(report: ReleaseEvidenceReport) -> str:
    lines = [
        "# FictionOps Release Evidence Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Evidence file: `{report.evidence_file}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Decision: `{report.decision or '-'}`",
        f"- Parsed fields: {report.field_count}",
        f"- Missing required fields: {len(report.missing_required_fields)}",
        f"- Issues: {report.issue_count}",
        f"- Blocking issues: {report.blocking_issue_count}",
        "",
        "## Issues",
        "",
    ]
    if report.issues:
        lines.extend(["| Severity | Code | Field | Message |", "| --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(item.severity),
                        f"`{safe_cell(item.code)}`",
                        safe_cell(item.field),
                        safe_cell(item.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No release evidence issues found.")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_release_evidence_audit(report: ReleaseEvidenceReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_release_evidence_audit(report)
