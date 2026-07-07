from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .doctor import build_doctor_report, looks_like_standard_project
from .markdown import safe_cell
from .models import AgentNextCandidate, AgentNextReport, DoctorReport
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan
from .stable_core import build_stable_core_audit
from .workflow_plan import quote_command_arg


def agent_next_candidate(
    priority: str,
    stage: str,
    command: str,
    reason: str,
    *,
    safe_to_auto_run: bool = True,
    requires_human_review: bool = False,
) -> AgentNextCandidate:
    return AgentNextCandidate(
        priority=priority,
        stage=stage,
        command=command,
        reason=reason,
        safe_to_auto_run=safe_to_auto_run,
        requires_human_review=requires_human_review,
    )


def count_import_queue_files(project: Path) -> int:
    queue = project / "06_drafts" / "import_queue"
    if not queue.exists() or not queue.is_dir():
        return 0
    return sum(1 for path in queue.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".txt"})


def chapter_paths(project: Path, *, book: str, chapter: str) -> dict[str, Path]:
    token = normalize_chapter_number(chapter)
    return {
        "chapter": project / "06_drafts" / book / "chapters" / f"ch_{token}.md",
        "engine": project / "06_drafts" / book / "chapter_engines" / f"ch_{token}_engine.md",
        "retrospective": project / "06_drafts" / book / "revision_notes" / f"ch_{token}_retrospective.md",
    }


def command_arg_for_agent_next(target: Path) -> str:
    raw = str(target)
    if raw in {"", "."}:
        return "."
    return quote_command_arg(raw)


def looks_like_fictionops_package(target: Path) -> bool:
    return (
        (target / "pyproject.toml").exists()
        and (target / "src" / "fictionops" / "cli.py").exists()
        and (target / "docs" / "stable-core-audit.md").exists()
    )


def stable_core_action_command(item_id: str, project_arg: str, evidence_file: str) -> str:
    if item_id == "release-trial-evidence":
        return f"fictionops audit-release-evidence {project_arg} --file {quote_command_arg(evidence_file)} --format json"
    if item_id == "sustained-dogfood-cycle":
        return f"fictionops audit-dogfood-cycle {project_arg} --file {quote_command_arg(evidence_file)} --format json"
    if item_id == "stability-window":
        return f"fictionops audit-stability-window {project_arg} --file {quote_command_arg(evidence_file)} --format json"
    return f"fictionops audit-stable-core {project_arg} --format json"


def evidence_from_doctor(report: DoctorReport | None, *, import_queue_files: int) -> dict[str, object]:
    if report is None:
        return {"doctor_enabled": False, "import_queue_files": import_queue_files}
    return {
        "doctor_enabled": True,
        "doctor_status": report.status,
        "issue_counts": report.issue_counts,
        "standard_check": report.standard_check,
        "chapter_files": report.stats.get("files"),
        "book_gate_status": report.book_gate.get("status"),
        "book_gate_ready": report.book_gate.get("ready"),
        "agent_inbox_status": report.agent_inbox.get("status"),
        "agent_inbox_ready": report.agent_inbox.get("ready"),
        "agent_inbox_needs_attention": report.agent_inbox.get("needs_attention"),
        "release_gate_status": report.release_gate.get("status"),
        "release_gate_ready": report.release_gate.get("ready"),
        "import_queue_files": import_queue_files,
    }


def select_agent_next_status(candidates: list[AgentNextCandidate]) -> str:
    if not candidates:
        return "no_action"
    if candidates[0].requires_human_review:
        return "needs_human_review"
    if candidates[0].safe_to_auto_run:
        return "ready_for_agent_step"
    return "needs_manual_step"


def build_agent_next(
    target: Path,
    *,
    book: str = "book_01",
    chapter: str | None = None,
    all_markdown: bool = False,
    pattern: str = "**/*.md",
    metric: str = "nonspace",
    skip_standard: bool = False,
    strict_standard: bool = False,
    min_chapter_chars: int = 200,
    watch_terms: list[str] | None = None,
    top: int = 12,
    min_repeat: int = 3,
    scan_text: bool = True,
    stale_after: int = 8,
    flat_tolerance: int = 200,
    min_spread_ratio: int = 15,
    max_flat_run: int = 4,
    max_same_band_run: int = 5,
) -> AgentNextReport:
    normalized_book = normalize_book_for_plan(book)
    normalized_chapter = normalize_chapter_number(chapter) if chapter else None
    project_arg = command_arg_for_agent_next(target)
    candidates: list[AgentNextCandidate] = []
    notes: list[str] = [
        "agent-next is read-only; it selects a safe next command but does not execute it.",
        "Staged agent output must still pass human review and FictionOps gates before becoming manuscript or canon.",
    ]

    if not target.exists():
        command = f"fictionops init {project_arg} --title \"<title>\""
        candidates.append(
            agent_next_candidate(
                "P1",
                "init",
                command,
                "Target path does not exist; create a FictionOps project skeleton before planning or drafting.",
            )
        )
        status = select_agent_next_status(candidates)
        return AgentNextReport(
            target=str(target),
            book=normalized_book,
            chapter=normalized_chapter,
            status=status,
            selected_command=candidates[0].command,
            selected_reason=candidates[0].reason,
            candidate_count=len(candidates),
            candidates=candidates,
            evidence={"target_exists": False},
            notes=notes,
        )

    resolved = target.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"agent-next requires a project directory or future project path: {target}")

    import_queue_files = count_import_queue_files(resolved)

    if looks_like_fictionops_package(resolved):
        package_arg = quote_command_arg(str(resolved))
        stable_core = build_stable_core_audit(resolved)
        stable_candidates: list[AgentNextCandidate] = []
        for item in stable_core.action_items:
            if item.status == "complete":
                continue
            stable_candidates.append(
                agent_next_candidate(
                    item.priority,
                    "stable-core",
                    stable_core_action_command(item.item_id, package_arg, item.evidence_file),
                    f"{item.title}: {item.status}. {item.acceptance}",
                    safe_to_auto_run=False,
                    requires_human_review=True,
                )
            )
        if not stable_candidates:
            stable_candidates.append(
                agent_next_candidate(
                    "P3",
                    "stable-core",
                    f"fictionops audit-stable-core {package_arg} --format json",
                    "Stable-core evidence appears ready; rerun the aggregate gate before changing milestone claims.",
                    safe_to_auto_run=True,
                    requires_human_review=False,
                )
            )
        selected = stable_candidates[0]
        status = select_agent_next_status(stable_candidates)
        return AgentNextReport(
            target=str(resolved),
            book=normalized_book,
            chapter=normalized_chapter,
            status=status,
            selected_command=selected.command,
            selected_reason=selected.reason,
            candidate_count=len(stable_candidates),
            candidates=stable_candidates,
            evidence={
                "target_exists": True,
                "standard_project": False,
                "fictionops_package": True,
                "stable_core_status": stable_core.status,
                "stable_core_ready": stable_core.ready,
                "stable_core_blocking_issues": stable_core.blocking_issue_count,
                "stable_core_action_items": [item.item_id for item in stable_core.action_items if item.status != "complete"],
            },
            notes=notes
            + [
                "Target is a FictionOps package checkout, so agent-next selected from stable-core governance action items.",
                "External evidence items require a human maintainer or external release/dogfood event; controllers must not fabricate them.",
            ],
        )

    if not looks_like_standard_project(resolved):
        candidates.append(
            agent_next_candidate(
                "P1",
                "migration",
                f"fictionops adopt {project_arg} --format json",
                "Target does not look like a standard FictionOps project; inspect and map the legacy material first.",
            )
        )
        status = select_agent_next_status(candidates)
        return AgentNextReport(
            target=str(resolved),
            book=normalized_book,
            chapter=normalized_chapter,
            status=status,
            selected_command=candidates[0].command,
            selected_reason=candidates[0].reason,
            candidate_count=len(candidates),
            candidates=candidates,
            evidence={"target_exists": True, "standard_project": False, "import_queue_files": import_queue_files},
            notes=notes,
        )

    doctor = build_doctor_report(
        resolved,
        all_markdown=all_markdown,
        pattern=pattern,
        metric=metric,
        skip_standard=skip_standard,
        strict_standard=strict_standard,
        min_chapter_chars=min_chapter_chars,
        watch_terms=watch_terms or ["不是", "没有", "有人"],
        top=top,
        min_repeat=min_repeat,
        scan_text=scan_text,
        stale_after=stale_after,
        book=normalized_book,
        outline=None,
        flat_tolerance=flat_tolerance,
        min_spread_ratio=min_spread_ratio,
        max_flat_run=max_flat_run,
        max_same_band_run=max_same_band_run,
    )

    inbox_status = doctor.agent_inbox.get("status")
    inbox_ready = int(doctor.agent_inbox.get("ready") or 0)
    inbox_attention = int(doctor.agent_inbox.get("needs_attention") or 0)

    if import_queue_files:
        candidates.append(
            agent_next_candidate(
                "P1",
                "migration",
                f"fictionops import-plan {project_arg} --book {normalized_book} --format json",
                f"{import_queue_files} imported file(s) are still waiting in 06_drafts/import_queue.",
            )
        )

    if inbox_attention:
        candidates.append(
            agent_next_candidate(
                "P1",
                "agent-inbox",
                f"fictionops agent-inbox {project_arg} --format json",
                f"{inbox_attention} agent run(s) need attention before new agent work is started.",
                safe_to_auto_run=True,
                requires_human_review=True,
            )
        )
    elif inbox_ready:
        candidates.append(
            agent_next_candidate(
                "P1",
                "agent-inbox",
                f"fictionops agent-inbox {project_arg} --format json",
                f"{inbox_ready} staged agent output(s) are ready for review.",
                safe_to_auto_run=True,
                requires_human_review=True,
            )
        )

    if normalized_chapter:
        paths = chapter_paths(resolved, book=normalized_book, chapter=normalized_chapter)
        if not paths["chapter"].exists() and not paths["engine"].exists():
            candidates.append(
                agent_next_candidate(
                    "P2",
                    "chapter-prep",
                    f"fictionops new-chapter {project_arg} --book {normalized_book} --chapter {normalized_chapter}",
                    "Requested chapter has no draft or chapter engine yet; create the chapter scaffold.",
                )
            )
        elif not paths["engine"].exists():
            candidates.append(
                agent_next_candidate(
                    "P2",
                    "chapter-prep",
                    f"fictionops plan-chapter {project_arg} --book {normalized_book} --chapter {normalized_chapter}",
                    "Requested chapter has no engine; sync outline intent into a chapter engine before drafting.",
                )
            )
        elif not paths["chapter"].exists():
            candidates.append(
                agent_next_candidate(
                    "P3",
                    "draft",
                    f"fictionops agent-run {project_arg} --role draft-writer --book {normalized_book} --chapter {normalized_chapter} --out-dir 00_management/agent_runs/ch_{normalized_chapter}",
                    "Chapter engine exists but no draft was found; prepare a bounded draft-writer task bundle.",
                    safe_to_auto_run=True,
                    requires_human_review=True,
                )
            )
        else:
            candidates.append(
                agent_next_candidate(
                    "P3",
                    "review",
                    f"fictionops review-gate {project_arg} --book {normalized_book} --chapter {normalized_chapter} --format json",
                    "Chapter draft exists; run the chapter review gate before broader revision.",
                )
            )

    if doctor.issue_counts.get("P1", 0) or doctor.issue_counts.get("P2", 0):
        candidates.append(
            agent_next_candidate(
                "P2",
                "revision",
                f"fictionops revision-plan {project_arg} --book {normalized_book} --format json",
                f"Doctor status is {doctor.status}; convert high-priority findings into ordered revision tasks.",
            )
        )

    book_gate_status = str(doctor.book_gate.get("status") or "")
    book_gate_ready = bool(doctor.book_gate.get("ready"))
    if book_gate_ready or book_gate_status == "ready_for_clean_export":
        candidates.append(
            agent_next_candidate(
                "P3",
                "publish",
                f"fictionops export-clean {project_arg} --book {normalized_book}",
                "Book gate is ready; export a clean Markdown manuscript before publish audits.",
            )
        )

    release_gate_status = str(doctor.release_gate.get("status") or "")
    if release_gate_status and release_gate_status != "ready_for_release":
        candidates.append(
            agent_next_candidate(
                "P4",
                "publish",
                f"fictionops release-gate {project_arg} --book {normalized_book} --format json",
                f"Release gate status is {release_gate_status}; inspect remaining publish blockers.",
            )
        )

    candidates.append(
        agent_next_candidate(
            "P5",
            "handoff",
            f"fictionops workflow-plan {project_arg} --stage all --book {normalized_book} --format json",
            "No narrower blocker was selected; refresh the staged workflow checklist.",
        )
    )

    status = select_agent_next_status(candidates)
    selected = candidates[0]
    return AgentNextReport(
        target=str(resolved),
        book=normalized_book,
        chapter=normalized_chapter,
        status=status,
        selected_command=selected.command,
        selected_reason=selected.reason,
        candidate_count=len(candidates),
        candidates=candidates,
        evidence=evidence_from_doctor(doctor, import_queue_files=import_queue_files),
        notes=notes,
    )


def format_agent_next(report: AgentNextReport) -> str:
    lines = [
        "# FictionOps Agent Next",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Status: `{report.status}`",
        f"- Selected command: `{report.selected_command}`",
        f"- Selected reason: {report.selected_reason}",
        "",
        "## Candidates",
        "",
        "| Priority | Stage | Auto | Human Review | Command | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in report.candidates:
        lines.append(
            "| "
            f"{safe_cell(candidate.priority)} | "
            f"{safe_cell(candidate.stage)} | "
            f"{'yes' if candidate.safe_to_auto_run else 'no'} | "
            f"{'yes' if candidate.requires_human_review else 'no'} | "
            f"`{safe_cell(candidate.command)}` | "
            f"{safe_cell(candidate.reason)} |"
        )
    lines.extend(["", "## Evidence", ""])
    for key, value in report.evidence.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Notes", ""])
    for note in report.notes:
        lines.append(f"- {note}")
    return "\n".join(lines).rstrip() + "\n"


def render_agent_next(report: AgentNextReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_next(report)
