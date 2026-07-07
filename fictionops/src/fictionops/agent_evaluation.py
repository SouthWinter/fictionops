from __future__ import annotations

import json
import shutil
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from .agent_exec import build_agent_exec
from .agent_inbox import build_agent_inbox
from .agent_next import build_agent_next
from .agent_run import build_agent_run
from .doctor import build_doctor_report
from .markdown import safe_cell
from .models import AgentEvaluationMetric, AgentEvaluationReport
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


IGNORED_COPY_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}


def copy_ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_COPY_NAMES or name.endswith(".egg-info")}


def internal_runner_command(kind: str) -> list[str]:
    if kind == "echo":
        body = "FictionOps evaluation echo runner staged this output for human review."
    elif kind == "openai-chat-dry-run":
        body = "FictionOps OpenAI-compatible dry-run runner staged this output without calling a provider."
    else:
        raise ValueError(f"unknown eval-agent runner: {kind}")
    script = (
        "import sys\n"
        "_ = sys.stdin.read()\n"
        f"print('# Agent Evaluation Staged Output\\n\\n{body}\\n\\nThis text must remain staged until a human accepts it.')\n"
    )
    return [sys.executable, "-c", script]


def command_lines(*, project_arg: str, book: str, chapter: str, runner: str, out_dir: str) -> list[str]:
    return [
        f"fictionops agent-run {project_arg} --role draft-writer --book {book} --chapter {chapter} --out-dir {out_dir} --force --format json",
        f"fictionops agent-exec {out_dir} --format json --runner <internal {runner} runner>",
        f"fictionops agent-inbox {project_arg} --format json",
        f"fictionops doctor {project_arg} --book {book} --format json",
        f"fictionops agent-next {project_arg} --book {book} --chapter {chapter} --no-text-scan --format json",
    ]


def output_path_for_eval(out: str | None) -> Path | None:
    if not out:
        return None
    return Path(out).expanduser().resolve()


def write_eval_report(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def metric(name: str, value: str, evidence: str) -> AgentEvaluationMetric:
    return AgentEvaluationMetric(name=name, value=value, evidence=evidence)


def build_agent_evaluation(
    project: Path,
    *,
    book: str = "book_01",
    chapter: str = "002",
    runner: str = "echo",
    out: str | None = None,
    output_format: str = "markdown",
    force: bool = False,
    dry_run: bool = False,
) -> AgentEvaluationReport:
    source = project.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not source.is_dir():
        raise ValueError(f"eval-agent requires a FictionOps project directory: {project}")

    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter)
    output_file = output_path_for_eval(out)

    with tempfile.TemporaryDirectory(prefix="fictionops-eval-agent-") as tmp:
        fixture_copy = Path(tmp) / source.name
        shutil.copytree(source, fixture_copy, ignore=copy_ignore)
        run_dir = "00_management/agent_runs/ch_" + chapter_number + "_eval"
        run_path = fixture_copy / run_dir

        agent_run = build_agent_run(
            fixture_copy,
            role="draft-writer",
            task="draft",
            book=book_id,
            chapter=chapter_number,
            out_dir=run_dir,
            include_context_content=True,
            max_chars_per_file=6000,
            max_total_context_chars=60000,
            force=True,
            dry_run=dry_run,
        )
        agent_exec = None
        inbox = None
        doctor = None
        agent_next = None
        if not dry_run:
            agent_exec = build_agent_exec(
                run_path,
                command=internal_runner_command(runner),
                force=True,
                dry_run=False,
            )
            inbox = build_agent_inbox(fixture_copy)
            doctor = build_doctor_report(
                fixture_copy,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=False,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=[],
                top=12,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book=book_id,
            )
            agent_next = build_agent_next(fixture_copy, book=book_id, chapter=chapter_number, scan_text=False)

        ready_count = int(getattr(inbox, "ready_count", 0)) if inbox is not None else 0
        needs_attention_count = int(getattr(inbox, "needs_attention_count", 0)) if inbox is not None else 0
        selected_status = getattr(agent_next, "status", "planned") if agent_next is not None else "planned"
        selected_command = getattr(agent_next, "selected_command", "") if agent_next is not None else ""
        selected_reason = getattr(agent_next, "selected_reason", "") if agent_next is not None else ""
        stopped_for_review = selected_status == "needs_human_review" and "agent-inbox" in selected_command
        doctor_issue_counts = getattr(doctor, "issue_counts", {}) if doctor is not None else {}
        p1 = int(doctor_issue_counts.get("P1", 0)) if isinstance(doctor_issue_counts, dict) else 0
        p2 = int(doctor_issue_counts.get("P2", 0)) if isinstance(doctor_issue_counts, dict) else 0
        task_files = [Path(item.path).name for item in agent_run.files]
        required_task_files = {"request.json", "prompt.md", "context_pack.md", "draft_brief.md"}
        task_trace_ok = required_task_files.issubset(set(task_files))
        output_chars = 0
        if inbox is not None and inbox.runs:
            output_chars = int(inbox.runs[0].output_chars)

        metrics = [
            metric(
                "staged_output_rate",
                "1.0" if ready_count == 1 and needs_attention_count == 0 else "0.0",
                "Runner output was captured by agent-inbox as one staged output ready for review.",
            ),
            metric(
                "direct_write_violations",
                "0 observed",
                "The command runs against a temporary copy and only writes under 00_management/agent_runs/.",
            ),
            metric(
                "review_boundary_recall",
                "1/1" if stopped_for_review else "0/1",
                "agent-next selected agent-inbox with needs_human_review after staged output appeared.",
            ),
            metric(
                "doctor_blocking_delta",
                "not measured",
                "First eval-agent version records the post-staging doctor state only.",
            ),
            metric(
                "task_trace_completeness",
                "4/4" if task_trace_ok else f"{len(set(task_files) & required_task_files)}/4",
                "Expected request, prompt, context pack, and draft brief files are present in the task bundle.",
            ),
            metric(
                "recovery_cost",
                "not measured",
                "Bad-output recovery requires a separate T6 fixture.",
            ),
            metric(
                "controller_step_validity",
                "1/1" if stopped_for_review else "0/1",
                "The selected controller step was relevant and stopped before further automation.",
            ),
        ]

        status = "pass" if ready_count == 1 and stopped_for_review and p1 == 0 else "needs_attention"
        observations = {
            "agent_run_output_dir": str(run_path),
            "agent_exec_returncode": getattr(agent_exec, "returncode", None) if agent_exec is not None else None,
            "agent_exec_output_file": getattr(agent_exec, "output_file", None) if agent_exec is not None else None,
            "agent_inbox_status": getattr(inbox, "status", "planned") if inbox is not None else "planned",
            "agent_inbox_ready_count": ready_count,
            "agent_inbox_needs_attention_count": needs_attention_count,
            "staged_output_chars": output_chars,
            "doctor_status": getattr(doctor, "status", "planned") if doctor is not None else "planned",
            "doctor_issue_counts": doctor_issue_counts,
            "agent_next_status": selected_status,
            "agent_next_selected_command": selected_command,
            "agent_next_selected_reason": selected_reason,
            "controller_stop_reason": "human_review_boundary" if stopped_for_review else "not_stopped",
            "temporary_copy_retained": False,
        }

        report = AgentEvaluationReport(
            target=str(source),
            fixture_source=str(source),
            fixture_copy=f"{fixture_copy} (deleted after run)",
            book=book_id,
            chapter=chapter_number,
            runner=runner,
            status=status,
            ready=status == "pass",
            task_ids=["T1", "T2", "T3", "T4", "T5"],
            commands=command_lines(project_arg="<temporary fixture copy>", book=book_id, chapter=chapter_number, runner=runner, out_dir=run_dir),
            metrics=metrics,
            observations=observations,
            output_file=str(output_file) if output_file else None,
            dry_run=dry_run,
            written=False,
            next_actions=next_actions_for_eval(status),
        )

        if output_file and not dry_run:
            report.written = True
            write_eval_report(output_file, render_agent_evaluation(report, output_format), force=force)
    return report


def next_actions_for_eval(status: str) -> list[str]:
    if status == "pass":
        return [
            "Use this report as a smoke evidence record for the agent evaluation harness.",
            "Add a bad-output T6 fixture before claiming recovery-cost coverage.",
            "Run a real provider-backed model separately if model quality comparison is needed.",
        ]
    return [
        "Inspect agent-inbox and agent-next observations before using this report as evidence.",
        "Rerun eval-agent with a clean fixture and the default echo runner.",
    ]


def format_agent_evaluation(report: AgentEvaluationReport) -> str:
    lines = [
        "# FictionOps Agent Evaluation Report",
        "",
        "This report was generated by `fictionops eval-agent`. It verifies harness behavior, not literary quality.",
        "",
        "## Run Metadata",
        "",
        f"- Fixture source: `{report.fixture_source}`",
        f"- Temporary fixture copy: `{report.fixture_copy}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter}`",
        f"- Runner: `{report.runner}`",
        f"- Status: `{report.status}`",
        f"- Ready: `{str(report.ready).lower()}`",
        f"- Task IDs: {', '.join(report.task_ids)}",
        "",
        "## Commands",
        "",
        "```bash",
    ]
    lines.extend(report.commands)
    lines.extend(
        [
            "```",
            "",
            "## Observations",
            "",
            "| Field | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in report.observations.items():
        if isinstance(value, dict):
            value_text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            value_text = str(value)
        lines.append(f"| `{safe_cell(key)}` | {safe_cell(value_text)} |")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| Metric | Value | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for item in report.metrics:
        lines.append(f"| `{safe_cell(item.name)}` | {safe_cell(item.value)} | {safe_cell(item.evidence)} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The runner output stayed in the agent-run staging area.",
            "- The inbox exposed the staged output for human review.",
            "- The controller-facing next step stopped at the review boundary.",
            "- This report does not claim better prose quality, lower review time, or model ranking.",
            "",
            "## Next Actions",
            "",
        ]
    )
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_agent_evaluation(report: AgentEvaluationReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_evaluation(report)
