from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import AgentInboxIssue, AgentInboxReport, AgentInboxRun


DEFAULT_AGENT_OUTPUT_NAMES = [
    "output.md",
    "response.md",
    "result.md",
    "staging.md",
    "model_output.md",
    "agent_output.md",
]


def default_agent_runs_dir(project: Path) -> Path:
    return project / "00_management" / "agent_runs"


def resolve_agent_inbox_runs_dir(project: Path, runs_dir: str | None) -> Path:
    if not runs_dir:
        return default_agent_runs_dir(project).resolve()
    candidate = Path(runs_dir).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def issue(severity: str, code: str, run_dir: Path, path: Path | None, message: str) -> AgentInboxIssue:
    return AgentInboxIssue(
        severity=severity,
        code=code,
        run_dir=str(run_dir),
        path=str(path or run_dir),
        message=message,
    )


def load_request(request_file: Path, run_dir: Path) -> tuple[dict[str, object], list[AgentInboxIssue]]:
    try:
        data = json.loads(request_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [issue("P1", "invalid_request_json", run_dir, request_file, f"request.json could not be parsed: {exc}")]
    if not isinstance(data, dict):
        return {}, [issue("P1", "invalid_request_shape", run_dir, request_file, "request.json must contain a JSON object.")]
    issues: list[AgentInboxIssue] = []
    if data.get("schema") != "fictionops.agent_run_request.v1":
        issues.append(
            issue(
                "P2",
                "unknown_request_schema",
                run_dir,
                request_file,
                "request.json does not declare schema fictionops.agent_run_request.v1.",
            )
        )
    if data.get("execution_mode") != "prepare_only":
        issues.append(
            issue(
                "P2",
                "unexpected_execution_mode",
                run_dir,
                request_file,
                "Agent run requests should be prepare_only before external runner output is accepted.",
            )
        )
    safety = data.get("safety")
    if not isinstance(safety, dict):
        issues.append(issue("P2", "missing_safety_policy", run_dir, request_file, "request.json is missing its safety policy."))
    else:
        unsafe = []
        if safety.get("calls_model") is not False:
            unsafe.append("calls_model must be false")
        if safety.get("stores_api_keys") is not False:
            unsafe.append("stores_api_keys must be false")
        if safety.get("overwrites_manuscript") is not False:
            unsafe.append("overwrites_manuscript must be false")
        if safety.get("requires_human_apply") is not True:
            unsafe.append("requires_human_apply must be true")
        if unsafe:
            issues.append(issue("P1", "unsafe_safety_policy", run_dir, request_file, "; ".join(unsafe) + "."))
    return data, issues


def request_string(data: dict[str, object], key: str, default: str = "-") -> str:
    value = data.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def request_optional_string(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def validate_bundle_files(data: dict[str, object], run_dir: Path) -> list[AgentInboxIssue]:
    issues: list[AgentInboxIssue] = []
    files = data.get("files")
    if not isinstance(files, list):
        return [issue("P2", "missing_bundle_file_list", run_dir, run_dir / "request.json", "request.json has no files list.")]
    required = {"prompt", "context_pack"}
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        path_text = str(item.get("path") or "").strip()
        if not kind:
            continue
        seen.add(kind)
        if kind in required and path_text:
            path = Path(path_text)
            if not path.exists():
                issues.append(issue("P2", "missing_bundle_file", run_dir, path, f"Bundle file `{kind}` is missing."))
    for kind in sorted(required - seen):
        issues.append(issue("P2", "missing_required_bundle_kind", run_dir, run_dir / "request.json", f"Bundle file `{kind}` is not listed in request.json."))
    return issues


def output_candidates(run_dir: Path, output_name: str | None) -> list[Path]:
    if output_name:
        candidate = Path(output_name).expanduser()
        if not candidate.is_absolute():
            candidate = run_dir / candidate
        return [candidate.resolve()] if candidate.exists() else []
    found: list[Path] = []
    for name in DEFAULT_AGENT_OUTPUT_NAMES:
        candidate = run_dir / name
        if candidate.exists():
            found.append(candidate.resolve())
    found.extend(sorted(path.resolve() for path in run_dir.glob("*.staging.md") if path.is_file()))
    return sorted(set(found), key=lambda path: path.name.lower())


def next_actions_for_inbox_run(run: AgentInboxRun) -> list[str]:
    if run.state == "awaiting_output":
        return ["Save the external runner result as `output.md` in this run directory, then rerun `fictionops agent-inbox`."]
    if run.state == "needs_attention":
        return ["Fix the inbox issue before using this output as project memory."]
    if run.task == "draft" and run.chapter:
        return [
            f"Review the staged draft, then manually apply accepted text to `06_drafts/{run.book}/chapters/ch_{run.chapter}.md`.",
            f"Run `fictionops post-draft . --book {run.book} --chapter {run.chapter}` after applying accepted text.",
            f"Run `fictionops review-gate . --book {run.book} --chapter {run.chapter}` before broader revision.",
        ]
    if run.task == "review":
        return [f"Convert accepted findings into revision notes or run `fictionops revision-plan . --book {run.book}` before rewriting."]
    if run.task == "canon-sync":
        return ["Apply accepted canon changes manually, then rerun `fictionops doctor .`."]
    return [f"Use the staged output to update handoff/planning files, then run `fictionops workflow-plan . --stage {run.task} --book {run.book}` if unsure."]


def inspect_agent_run_dir(run_dir: Path, *, output_name: str | None) -> AgentInboxRun:
    request_file = run_dir / "request.json"
    issues: list[AgentInboxIssue] = []
    data: dict[str, object] = {}
    if not request_file.exists():
        issues.append(issue("P1", "missing_request", run_dir, request_file, "Agent run directory has no request.json."))
    else:
        data, request_issues = load_request(request_file, run_dir)
        issues.extend(request_issues)
        if data:
            issues.extend(validate_bundle_files(data, run_dir))

    candidates = output_candidates(run_dir, output_name)
    output_file: Path | None = None
    output_chars = 0
    if len(candidates) > 1:
        issues.append(
            issue(
                "P2",
                "ambiguous_output",
                run_dir,
                run_dir,
                "Multiple output candidates found: " + ", ".join(path.name for path in candidates) + ".",
            )
        )
    elif len(candidates) == 1:
        output_file = candidates[0]
        text = output_file.read_text(encoding="utf-8", errors="replace")
        output_chars = len(text.strip())
        if output_chars == 0:
            issues.append(issue("P2", "empty_output", run_dir, output_file, "Agent output file is empty."))
    else:
        issues.append(issue("P4", "missing_output", run_dir, run_dir, "No agent output file found in this run directory."))

    blocking = [item for item in issues if item.severity in {"P0", "P1", "P2"}]
    if blocking:
        state = "needs_attention"
    elif output_file is None:
        state = "awaiting_output"
    else:
        state = "ready_for_review"

    run = AgentInboxRun(
        run_dir=str(run_dir),
        request_file=str(request_file) if request_file.exists() else None,
        output_file=str(output_file) if output_file else None,
        state=state,
        role=request_string(data, "role"),
        task=request_string(data, "task"),
        book=request_string(data, "book", "book_01"),
        chapter=request_optional_string(data, "chapter"),
        output_chars=output_chars,
        issue_count=len(issues),
        issues=issues,
        next_actions=[],
    )
    run.next_actions = next_actions_for_inbox_run(run)
    return run


def find_agent_run_dirs(target: Path, *, runs_dir: str | None) -> tuple[str, Path, list[Path]]:
    if (target / "request.json").exists():
        return "run_dir", target.resolve(), [target.resolve()]
    resolved_runs_dir = resolve_agent_inbox_runs_dir(target, runs_dir)
    if not resolved_runs_dir.exists():
        return "project", resolved_runs_dir, []
    run_dirs = sorted({path.parent.resolve() for path in resolved_runs_dir.rglob("request.json")})
    return "project", resolved_runs_dir, run_dirs


def status_for_agent_inbox(runs: list[AgentInboxRun], issues: list[AgentInboxIssue]) -> str:
    if not runs:
        return "no_runs"
    if any(issue.severity in {"P0", "P1", "P2"} for issue in issues):
        return "needs_attention"
    if all(run.state == "awaiting_output" for run in runs):
        return "awaiting_output"
    if all(run.state == "ready_for_review" for run in runs):
        return "ready_for_review"
    return "mixed"


def build_agent_inbox(
    target: Path,
    *,
    runs_dir: str | None = None,
    output_name: str | None = None,
) -> AgentInboxReport:
    if not target.exists():
        raise FileNotFoundError(f"path does not exist: {target}")
    if not target.is_dir():
        raise ValueError(f"agent-inbox requires a FictionOps project or agent run directory: {target}")

    resolved = target.expanduser().resolve()
    mode, resolved_runs_dir, run_dirs = find_agent_run_dirs(resolved, runs_dir=runs_dir)
    runs = [inspect_agent_run_dir(run_dir, output_name=output_name) for run_dir in run_dirs]
    issues = [issue for run in runs for issue in run.issues]
    if not runs and not resolved_runs_dir.exists():
        issues.append(issue("P3", "missing_runs_dir", resolved_runs_dir, resolved_runs_dir, "Agent runs directory does not exist."))

    ready_count = sum(1 for run in runs if run.state == "ready_for_review")
    awaiting_count = sum(1 for run in runs if run.state == "awaiting_output")
    needs_attention_count = sum(1 for run in runs if run.state == "needs_attention")
    return AgentInboxReport(
        target=str(resolved),
        mode=mode,
        runs_dir=str(resolved_runs_dir),
        status=status_for_agent_inbox(runs, issues),
        run_count=len(runs),
        ready_count=ready_count,
        awaiting_count=awaiting_count,
        needs_attention_count=needs_attention_count,
        output_name=output_name,
        runs=runs,
        issues=issues,
    )


def render_agent_inbox(report: AgentInboxReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_inbox(report)


def format_agent_inbox(report: AgentInboxReport) -> str:
    lines = [
        "# FictionOps Agent Inbox",
        "",
        f"- Target: `{report.target}`",
        f"- Mode: `{report.mode}`",
        f"- Runs dir: `{report.runs_dir}`",
        f"- Status: `{report.status}`",
        f"- Runs: {report.run_count}",
        f"- Ready: {report.ready_count}",
        f"- Awaiting output: {report.awaiting_count}",
        f"- Needs attention: {report.needs_attention_count}",
        "",
        "## Runs",
        "",
    ]
    if report.runs:
        lines.extend(["| State | Role | Task | Book | Chapter | Output chars | Run dir |", "| --- | --- | --- | --- | --- | ---: | --- |"])
        for run in report.runs:
            lines.append(
                f"| `{run.state}` | `{run.role}` | `{run.task}` | `{run.book}` | `{run.chapter or '-'}` | {run.output_chars} | `{run.run_dir}` |"
            )
    else:
        lines.append("No agent run bundles found.")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(f"| {item.severity} | `{item.code}` | `{item.path}` | {item.message} |")
    else:
        lines.append("No inbox issues found.")

    lines.extend(["", "## Next Actions", ""])
    if report.runs:
        for index, run in enumerate(report.runs, 1):
            lines.append(f"### Run {index}: `{Path(run.run_dir).name}`")
            for action in run.next_actions:
                lines.append(f"- {action}")
            lines.append("")
    else:
        lines.append("- Run `fictionops agent-run ... --out-dir 00_management/agent_runs/<name>` to create a task bundle.")
    return "\n".join(lines).rstrip() + "\n"
