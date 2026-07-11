from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .agent_budget import ModelExecutionBudget, execute_model_bundle, start_model_budget
from .agent_exec import DEFAULT_AGENT_EXEC_OUTPUT
from .agent_inbox import build_agent_inbox
from .agent_comprehensive_review import (
    augment_revision_bundle,
    merge_comprehensive_review,
    parse_comprehensive_review,
    prepare_comprehensive_review_bundle,
    prepare_comprehensive_review_repair_bundle,
)
from .agent_project_context import compile_project_context, render_project_context
from .agent_preservation_verifier import (
    apply_preservation_verification,
    parse_preservation_verification,
    prepare_preservation_verifier_bundle,
    prepare_preservation_verifier_repair_bundle,
)
from .agent_session_control import validate_checkpoint_for_resume, write_agent_checkpoint
from .agent_trajectory import append_trajectory, context_attribution
from .agent_revision_runtime import (
    finalize_revision_candidate,
    initialize_revision_runtime,
    merge_semantic_verification,
    parse_semantic_verifier_output,
    prepare_targeted_retry,
    prepare_semantic_verifier_bundle,
    REQUIRED_SEMANTIC_INVARIANTS,
    SEMANTIC_VERIFICATION_SCHEMA,
    revision_runtime_files,
    session_id_for,
    sha256_text,
)
from .model_config import build_model_config_report
from .models import AgentExecReport, AgentInboxReport
from .review_workflow import build_review_workflow_report, render_review_workflow_report


REVISION_CONTRACT = """# FictionOps Revision Contract

You are revising a long-form fiction chapter from a staged review workflow.

## Goal

Produce a revised version of the source chapter that addresses the review workflow's highest-impact prose-pattern issues while preserving story continuity.

## Must Preserve

- Preserve all plot events, character intentions, point of view, chronology, names, places, objects, and information boundaries.
- Preserve ambiguity, silence, and withheld explanation when the source relies on them.
- Preserve functional repetition when it carries theme, pressure, rhythm, or character perception.
- Preserve the chapter's rough length and scene order unless a sentence-level adjustment requires a local move.

## Must Improve

- Reduce low-value repeated negation patterns only where action, object state, gesture, silence, or viewpoint perception can carry the same meaning.
- Reduce default sensory fields, such as cold/heat clusters, only where the image is not doing scene work.
- Reduce explanatory similes and turn signals only where the prose is translating what the scene already shows. Vary metaphor form by function and viewpoint voice: direct scene, action, implicit metaphor, or a register-fit explicit marker. Never solve repeated `像` through mechanical synonym rotation.
- Keep the language alive and varied. Do not flatten the author's style into generic smoothness.

## Must Not Do

- Do not add new lore, new motives, new facts, new foreshadowing, or new exposition.
- Do not solve mysteries that the chapter intentionally leaves open.
- Do not optimize word counts mechanically.
- Do not output commentary, diagnosis, bullet points, or a summary.

## Output

Write only the revised chapter text to stdout. FictionOps will save it as staged output and will not apply it automatically.
"""


@dataclass
class AgentReviseWorkflowFile:
    kind: str
    path: str
    written: bool


@dataclass
class AgentReviseWorkflowReport:
    command: str
    target: str
    chapter_file: str
    review_file: str | None
    run_dir: str
    role: str
    task: str
    provider: str
    model: str
    review_model: str
    prepared: bool
    executed: bool
    inbox_status: str | None
    ready_count: int
    source_sha256: str
    session_id: str
    verification_status: str | None
    ready_for_approval: bool
    max_retries: int
    retry_count: int
    review_scope: str
    context_file_count: int
    memory_record_count: int
    comprehensive_review: dict[str, object] | None
    preservation_verification_enabled: bool
    preservation_call_count: int
    preservation_verification: dict[str, object] | None
    semantic_verification_enabled: bool
    semantic_call_count: int
    max_model_calls: int
    model_calls_used: int
    max_runtime_seconds: int
    output_name: str
    stop_reason: str
    files: list[AgentReviseWorkflowFile]
    staged_outputs: list[dict[str, object]]
    safety: dict[str, object]
    next_actions: list[str]
    agent_exec: AgentExecReport | None
    reviewer_exec: AgentExecReport | None
    preservation_exec: AgentExecReport | None
    semantic_exec: AgentExecReport | None
    inbox: AgentInboxReport | None
    verification: dict[str, object] | None


def safe_run_name(chapter_file: Path) -> str:
    stem = chapter_file.stem.strip() or "chapter"
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", stem)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("_")
    return f"revise_workflow_{cleaned or 'chapter'}"


def find_project_anchor(path: Path) -> Path:
    start = path if path.is_dir() else path.parent
    for current in [start, *start.parents]:
        if (current / "00_management").is_dir() or (current / "00_总纲与管理").is_dir():
            return current
    return start


def default_agent_revise_workflow_dir(chapter_file: Path) -> Path:
    anchor = find_project_anchor(chapter_file)
    if (anchor / "00_management").is_dir():
        base = anchor / "00_management" / "agent_runs"
    elif (anchor / "00_总纲与管理").is_dir():
        base = anchor / "00_总纲与管理" / "agent_runs"
    else:
        base = chapter_file.parent / ".fictionops_agent_runs"
    return (base / safe_run_name(chapter_file)).resolve()


def resolve_agent_revise_workflow_dir(chapter_file: Path, out_dir: str | None) -> Path:
    if not out_dir:
        return default_agent_revise_workflow_dir(chapter_file)
    candidate = Path(out_dir).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (find_project_anchor(chapter_file) / candidate).resolve()


def read_or_build_review(chapter_file: Path, review_file: Path | None) -> tuple[str, str | None]:
    if review_file is None:
        report = build_review_workflow_report(chapter_file, top_lines=80)
        return render_review_workflow_report(report, "markdown"), None
    if not review_file.exists():
        raise FileNotFoundError(f"review workflow file does not exist: {review_file}")
    if not review_file.is_file():
        raise ValueError(f"--review must point to a file: {review_file}")
    return review_file.read_text(encoding="utf-8"), str(review_file.resolve())


def build_revision_prompt(*, chapter_file: Path, review_file: str | None) -> str:
    review_source = review_file or "generated from the source chapter during this command"
    return "\n".join(
        [
            "# FictionOps Agent Revision Prompt",
            "",
            "Revise the chapter using the bundled review workflow and revision contract.",
            "",
            "## Inputs",
            "",
            f"- Source chapter: `source_chapter.md` copied from `{chapter_file}`",
            f"- Review workflow: `review_workflow.md` ({review_source})",
            "- Revision contract: `revision_contract.md`",
            "",
            "## Task",
            "",
            "Return a staged revised chapter. Treat the review workflow as a queue of issues to triage, not as a command to erase all repeated words.",
            "",
            "Prioritize P1/P2 pattern families, but keep any repeated phrase that has scene, rhythm, viewpoint, or thematic function.",
            "",
            "## Output Contract",
            "",
            "Write only the revised chapter text. Do not include markdown fences, a change log, comments, or analysis.",
        ]
    ).rstrip() + "\n"


def build_revision_context(
    *,
    chapter_file: Path,
    review_text: str,
    chapter_text: str,
    review_file: str | None,
    max_chapter_chars: int,
    max_review_chars: int,
) -> str:
    clipped_chapter = chapter_text[:max_chapter_chars]
    clipped_review = review_text[:max_review_chars]
    chapter_note = "" if len(chapter_text) <= max_chapter_chars else f"\n\n[Chapter clipped at {max_chapter_chars} characters in context_pack.md; full text is in source_chapter.md.]"
    review_note = "" if len(review_text) <= max_review_chars else f"\n\n[Review clipped at {max_review_chars} characters in context_pack.md; full text is in review_workflow.md.]"
    lines = [
        "# FictionOps Revision Context Pack",
        "",
        "This pack is self-contained for an external revision runner.",
        "",
        "## Files In This Bundle",
        "",
        "- `source_chapter.md`: full source chapter",
        "- `review_workflow.md`: full review workflow report",
        "- `revision_contract.md`: safety and output contract",
        "- `prompt.md`: role/task prompt",
        "",
        "## Source",
        "",
        f"- Chapter file: `{chapter_file}`",
        f"- Review file: `{review_file or 'generated inside this bundle'}`",
        "",
        "## Revision Contract",
        "",
        REVISION_CONTRACT.rstrip(),
        "",
        "## Review Workflow",
        "",
        clipped_review.rstrip(),
        review_note,
        "",
        "## Source Chapter",
        "",
        clipped_chapter.rstrip(),
        chapter_note,
    ]
    return "\n".join(lines).rstrip() + "\n"


def request_payload(
    *,
    chapter_file: Path,
    review_file: str | None,
    run_dir: Path,
    role: str,
    provider: str,
    model: str,
    source_sha256: str,
    files: list[AgentReviseWorkflowFile],
) -> dict[str, object]:
    return {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(chapter_file.resolve()),
        "role": role,
        "role_name": "Style Revision Agent",
        "task": "review",
        "book": "-",
        "chapter": chapter_file.stem,
        "provider": provider,
        "model": model,
        "model_config_file": None,
        "source_chapter_file": str(chapter_file.resolve()),
        "source_chapter_sha256": source_sha256,
        "review_workflow_file": review_file,
        "run_dir": str(run_dir),
        "files": [asdict(item) for item in files],
        "next_actions": [
            "Run `fictionops agent-exec <run_dir> --runner ...` to call a model-backed runner.",
            "Inspect staged output with `fictionops agent-inbox <run_dir>` before applying any text.",
            "After accepting edits manually, rerun `fictionops review-workflow <chapter>` and compare recheck targets.",
        ],
        "safety": agent_revise_workflow_safety(),
    }


def agent_revise_workflow_safety() -> dict[str, object]:
    return {
        "calls_model": False,
        "stores_api_keys": False,
        "overwrites_manuscript": False,
        "writes_staging_output": True,
        "requires_human_apply": True,
        "accepts_direct_chapter_file": True,
    }


def planned_files(run_dir: Path) -> dict[str, Path]:
    return {
        "readme": run_dir / "README.md",
        "request": run_dir / "request.json",
        "prompt": run_dir / "prompt.md",
        "context_pack": run_dir / "context_pack.md",
        "source_chapter": run_dir / "source_chapter.md",
        "review_workflow": run_dir / "review_workflow.md",
        "revision_contract": run_dir / "revision_contract.md",
    }


def write_bundle(
    *,
    run_dir: Path,
    chapter_file: Path,
    review_file: str | None,
    chapter_text: str,
    review_text: str,
    role: str,
    provider: str,
    model: str,
    force: bool,
    max_chapter_chars: int,
    max_review_chars: int,
) -> list[AgentReviseWorkflowFile]:
    files = planned_files(run_dir)
    if not force:
        existing = [path for path in files.values() if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    run_dir.mkdir(parents=True, exist_ok=True)
    file_reports = [AgentReviseWorkflowFile(kind=kind, path=str(path), written=True) for kind, path in files.items()]
    prompt = build_revision_prompt(chapter_file=chapter_file, review_file=review_file)
    context = build_revision_context(
        chapter_file=chapter_file,
        review_text=review_text,
        chapter_text=chapter_text,
        review_file=review_file,
        max_chapter_chars=max_chapter_chars,
        max_review_chars=max_review_chars,
    )
    readme = "\n".join(
        [
            "# FictionOps Agent Revision Workflow Bundle",
            "",
            f"- Source chapter: `{chapter_file}`",
            f"- Review workflow: `{review_file or 'generated from source chapter'}`",
            f"- Role: `{role}`",
            f"- Provider: `{provider}`",
            f"- Model: `{model}`",
            "",
            "## Rule",
            "",
            "This bundle lets an external model revise a chapter from a review workflow. It never applies output to the manuscript automatically.",
            "",
            "## Next Actions",
            "",
            f"- Run `fictionops agent-exec {run_dir} --runner ...`.",
            f"- Inspect staged output with `fictionops agent-inbox {run_dir}`.",
            "- Apply accepted text manually, then rerun `fictionops review-workflow` on the accepted chapter.",
        ]
    ).rstrip() + "\n"
    files["readme"].write_text(readme, encoding="utf-8", newline="\n")
    files["prompt"].write_text(prompt, encoding="utf-8", newline="\n")
    files["context_pack"].write_text(context, encoding="utf-8", newline="\n")
    files["source_chapter"].write_text(chapter_text.rstrip() + "\n", encoding="utf-8", newline="\n")
    files["review_workflow"].write_text(review_text.rstrip() + "\n", encoding="utf-8", newline="\n")
    files["revision_contract"].write_text(REVISION_CONTRACT.rstrip() + "\n", encoding="utf-8", newline="\n")
    payload = request_payload(
        chapter_file=chapter_file,
        review_file=review_file,
        run_dir=run_dir,
        role=role,
        provider=provider,
        model=model,
        source_sha256=sha256_text(chapter_text),
        files=file_reports,
    )
    files["request"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return file_reports


def staged_outputs_from_inbox(inbox: AgentInboxReport) -> list[dict[str, object]]:
    staged: list[dict[str, object]] = []
    for run in inbox.runs:
        if not run.output_file:
            continue
        staged.append(
            {
                "run_dir": run.run_dir,
                "output_file": run.output_file,
                "role": run.role,
                "task": run.task,
                "chapter": run.chapter,
                "state": "revision",
                "review_required": True,
                "output_chars": run.output_chars,
            }
        )
    return staged


def next_actions_for_report(report: AgentReviseWorkflowReport) -> list[str]:
    if report.ready_for_approval:
        return [
            f"Inspect `{Path(report.run_dir) / 'changes.diff'}` and `{Path(report.run_dir) / 'verification.json'}`.",
            f"Run `fictionops agent-accept-revision {report.run_dir} --dry-run` to confirm source and candidate hashes.",
            f"Then run `fictionops agent-accept-revision {report.run_dir}` only when the verified candidate should replace the source chapter.",
        ]
    if report.executed and report.verification_status == "needs_revision_attention":
        return [
            f"Inspect blocking failures in `{Path(report.run_dir) / 'verification.json'}`.",
            "Revise or rerun the candidate; acceptance remains disabled until verification passes.",
        ]
    if report.executed:
        return [f"Inspect `{report.run_dir}` with `fictionops agent-inbox` before retrying."]
    return [
        f"Run a model-backed runner with `fictionops agent-exec {report.run_dir} --runner ...`.",
        f"Then inspect staged output with `fictionops agent-inbox {report.run_dir}`.",
    ]


def build_agent_revise_workflow(
    chapter: Path,
    *,
    review: Path | None = None,
    out_dir: str | None = None,
    role: str = "style-auditor",
    provider: str | None = None,
    model: str | None = None,
    runner: list[str] | None = None,
    output_name: str = DEFAULT_AGENT_EXEC_OUTPUT,
    timeout_seconds: int = 300,
    max_model_calls: int = 12,
    max_runtime_seconds: int = 1800,
    max_total_tokens: int | None = None,
    max_cost: float | None = None,
    cost_currency: str = "USD",
    force: bool = False,
    force_output: bool = False,
    dry_run: bool = False,
    max_chapter_chars: int = 120000,
    max_review_chars: int = 50000,
    max_retries: int = 1,
    semantic_verify: bool = True,
    preservation_verify: bool = True,
    review_scope: str = "comprehensive",
    context_files: list[Path] | None = None,
    max_context_files: int = 24,
    max_project_context_chars: int = 100000,
    use_memory: bool = True,
    resume: bool = False,
) -> AgentReviseWorkflowReport:
    if not chapter.exists():
        raise FileNotFoundError(f"chapter file does not exist: {chapter}")
    if not chapter.is_file():
        raise ValueError(f"agent-revise-workflow requires a chapter file: {chapter}")
    if timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be greater than zero.")
    if max_retries < 0 or max_retries > 2:
        raise ValueError("--max-retries must be between 0 and 2.")
    if max_model_calls < 1:
        raise ValueError("--max-model-calls must be greater than zero.")
    if max_runtime_seconds < 1:
        raise ValueError("--max-runtime-seconds must be greater than zero.")
    if review_scope not in {"style", "comprehensive"}:
        raise ValueError("--review-scope must be style or comprehensive.")
    chapter_file = chapter.expanduser().resolve()
    run_dir = resolve_agent_revise_workflow_dir(chapter_file, out_dir)
    chapter_text = chapter_file.read_text(encoding="utf-8")
    source_sha256 = sha256_text(chapter_text)
    session_id = session_id_for(chapter_file, source_sha256)
    review_text, review_file = read_or_build_review(chapter_file, review.expanduser().resolve() if review else None)

    anchor = find_project_anchor(chapter_file)
    model_config = build_model_config_report(anchor)
    selected_provider = provider or model_config.provider
    selected_model = model or model_config.drafting_model
    selected_review_model = model or model_config.audit_model
    file_reports = [AgentReviseWorkflowFile(kind=kind, path=str(path), written=False) for kind, path in planned_files(run_dir).items()]
    prepared = False
    executed = False
    agent_exec = None
    reviewer_exec = None
    preservation_exec = None
    semantic_exec = None
    inbox = None
    before_report = None
    verification: dict[str, object] | None = None
    staged_outputs: list[dict[str, object]] = []
    retry_count = 0
    semantic_call_count = 0
    preservation_call_count = 0
    context_file_count = 0
    memory_record_count = 0
    comprehensive_review: dict[str, object] | None = None
    preservation_verification: dict[str, object] | None = None
    stop_reason = "agent_run_ready_for_runner"
    budget: ModelExecutionBudget | None = None
    checkpoint: dict[str, object] | None = None

    if resume:
        if dry_run:
            raise ValueError("resume cannot be combined with dry-run")
        resumed_session, checkpoint = validate_checkpoint_for_resume(run_dir)
        if str(resumed_session.get("workflow")) != "chapter_revision":
            raise ValueError("resume target is not a chapter-revision session")
        before_report = build_review_workflow_report(chapter_file, all_markdown=True, top_lines=120)
        prepared = True
        file_reports = [
            AgentReviseWorkflowFile(kind=kind, path=str(path), written=path.exists())
            for kind, path in {**planned_files(run_dir), **revision_runtime_files(run_dir)}.items()
        ]
    elif not dry_run:
        file_reports = write_bundle(
            run_dir=run_dir,
            chapter_file=chapter_file,
            review_file=review_file,
            chapter_text=chapter_text,
            review_text=review_text,
            role=role,
            provider=selected_provider,
            model=selected_model,
            force=force,
            max_chapter_chars=max_chapter_chars,
            max_review_chars=max_review_chars,
        )
        before_report, _session = initialize_revision_runtime(
            run_dir,
            chapter_file=chapter_file,
            chapter_text=chapter_text,
            provider=selected_provider,
            model=selected_model,
            output_name=output_name,
            force=force,
        )
        session_file = revision_runtime_files(run_dir)["session"]
        runtime_session = json.loads(session_file.read_text(encoding="utf-8"))
        runtime_session["workflow_options"] = {
            "review_file": review_file,
            "role": role,
            "output_name": output_name,
            "max_chapter_chars": max_chapter_chars,
            "max_review_chars": max_review_chars,
            "max_retries": max_retries,
            "semantic_verify": semantic_verify,
            "preservation_verify": preservation_verify,
            "review_scope": review_scope,
            "max_context_files": max_context_files,
            "max_project_context_chars": max_project_context_chars,
            "use_memory": use_memory,
        }
        session_file.write_text(json.dumps(runtime_session, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        for kind, path in revision_runtime_files(run_dir).items():
            if kind in {"candidate", "diff", "audits_after", "issues_after", "verification"}:
                continue
            file_reports.append(AgentReviseWorkflowFile(kind=kind, path=str(path), written=path.exists()))
        prepared = True

    if runner:
        if dry_run:
            stop_reason = "dry_run_runner_not_executed"
        else:
            budget = (
                start_model_budget(
                    run_dir,
                    max_calls=max_model_calls,
                    max_runtime_seconds=max_runtime_seconds,
                    max_total_tokens=max_total_tokens,
                    max_cost=max_cost,
                    cost_currency=cost_currency,
                    resume=True,
                )
                if resume
                else ModelExecutionBudget(
                    run_dir=run_dir,
                    max_calls=max_model_calls,
                    max_runtime_seconds=max_runtime_seconds,
                    max_total_tokens=max_total_tokens,
                    max_cost=max_cost,
                    cost_currency=cost_currency,
                )
            )
            resume_phase = str((checkpoint or {}).get("phase") or "context_ready")
            if resume and resume_phase not in {"context_ready", "review_ready", "verification_ready"}:
                raise ValueError(f"chapter-revision resume does not support checkpoint phase yet: {resume_phase}")
            reuse_review = bool(
                resume
                and resume_phase in {"review_ready", "verification_ready"}
                and (run_dir / "comprehensive_review.json").is_file()
            )
            if reuse_review:
                comprehensive_review = json.loads((run_dir / "comprehensive_review.json").read_text(encoding="utf-8"))
                preservation_file = run_dir / "preservation_verification.json"
                if preservation_file.is_file():
                    preservation_verification = json.loads(preservation_file.read_text(encoding="utf-8"))
            elif review_scope == "comprehensive":
                memory_budget = min(30000, max(2000, max_project_context_chars // 3)) if use_memory else 0
                project_context = compile_project_context(
                    chapter_file,
                    task="comprehensive-review",
                    source_text=chapter_text,
                    explicit_files=context_files,
                    max_files=max_context_files,
                    max_total_chars=max(1, max_project_context_chars - memory_budget),
                )
                if use_memory:
                    from .agent_memory import build_memory_index, query_memory, render_memory_query
                    from .agent_write_workflow import augment_context_with_memory

                    memory_index = build_memory_index(anchor, write=True)
                    memory_query = query_memory(
                        anchor,
                        query="\n".join((chapter_file.stem, review_text[:12000], chapter_text[:12000])),
                        max_items=max(8, min(24, max_context_files)),
                        max_chars=memory_budget,
                        index_payload=memory_index,
                    )
                    memory_record_count = int(memory_query.get("record_count") or 0)
                    project_context = augment_context_with_memory(
                        project_context,
                        memory_query,
                        max_total_chars=max_project_context_chars,
                    )
                    memory_query_file = run_dir / "memory_query.json"
                    memory_context_file = run_dir / "memory_context.md"
                    memory_query_file.write_text(json.dumps(memory_query, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
                    memory_context_file.write_text(render_memory_query(memory_query), encoding="utf-8", newline="\n")
                    append_trajectory(
                        run_dir,
                        kind="context_selected",
                        phase="reviewing",
                        actor="context_compiler",
                        observation={
                            "query": memory_query.get("query"),
                            "memory_records": memory_query.get("record_count"),
                            "included_chars": project_context.included_chars,
                        },
                        context=[
                            *context_attribution(memory_query),
                            *[
                                {
                                    "source": item.path,
                                    "kind": item.role,
                                    "authority": item.authority,
                                    "reason": item.reason,
                                    "chars": item.included_chars,
                                    "sha256": item.sha256,
                                }
                                for item in project_context.items
                            ],
                        ],
                        authority="controller",
                    )
                    file_reports.extend(
                        [
                            AgentReviseWorkflowFile(kind="memory_query", path=str(memory_query_file), written=True),
                            AgentReviseWorkflowFile(kind="memory_context", path=str(memory_context_file), written=True),
                        ]
                    )
                context_file_count = len(project_context.items)
                project_context_file = run_dir / "project_context.md"
                project_context_file.write_text(render_project_context(project_context), encoding="utf-8", newline="\n")
                file_reports.append(AgentReviseWorkflowFile(kind="project_context", path=str(project_context_file), written=True))
                reviewer_dir = prepare_comprehensive_review_bundle(
                    run_dir,
                    chapter_file=chapter_file,
                    chapter_text=chapter_text,
                    context=project_context,
                    provider=selected_provider,
                    model=selected_review_model,
                    force=force or resume,
                )
                reviewer_exec = execute_model_bundle(
                    budget,
                    reviewer_dir,
                    role="comprehensive-reviewer",
                    command=runner,
                    output_name="output.md",
                    timeout_seconds=timeout_seconds,
                    force=force_output or force or resume,
                    dry_run=False,
                )
                initial_reviewer_output_file = reviewer_exec.output_file
                reviewer_output = Path(initial_reviewer_output_file).read_text(encoding="utf-8")
                try:
                    comprehensive_review = parse_comprehensive_review(reviewer_output)
                except ValueError as exc:
                    repair_dir = prepare_comprehensive_review_repair_bundle(
                        run_dir,
                        invalid_output=reviewer_output,
                        parse_error=str(exc),
                        provider=selected_provider,
                        model=selected_review_model,
                        force=force or resume,
                    )
                    reviewer_exec = execute_model_bundle(
                        budget,
                        repair_dir,
                        role="comprehensive-review-repair",
                        command=runner,
                        output_name="output.md",
                        timeout_seconds=timeout_seconds,
                        force=force_output or force or resume,
                        dry_run=False,
                    )
                    comprehensive_review = parse_comprehensive_review(
                        Path(reviewer_exec.output_file).read_text(encoding="utf-8")
                    )
                    file_reports.append(
                        AgentReviseWorkflowFile(
                            kind="comprehensive_reviewer_retry_output",
                            path=reviewer_exec.output_file,
                            written=True,
                        )
                    )
                model_preservation: dict[str, object] | None = None
                if preservation_verify and comprehensive_review.get("issues"):
                    verifier_dir = prepare_preservation_verifier_bundle(
                        run_dir,
                        chapter_file=chapter_file,
                        chapter_text=chapter_text,
                        project_context=project_context_file.read_text(encoding="utf-8"),
                        review=comprehensive_review,
                        provider=selected_provider,
                        model=selected_review_model,
                        force=force or resume,
                    )
                    preservation_exec = execute_model_bundle(
                        budget,
                        verifier_dir,
                        role="preservation-verifier",
                        command=runner,
                        output_name="output.md",
                        timeout_seconds=timeout_seconds,
                        force=force_output or force or resume,
                        dry_run=False,
                    )
                    preservation_call_count += 1
                    try:
                        model_preservation = parse_preservation_verification(
                            Path(preservation_exec.output_file).read_text(encoding="utf-8"),
                            issue_count=len(comprehensive_review.get("issues") or []),
                        )
                    except (json.JSONDecodeError, ValueError) as exc:
                        repair_dir = prepare_preservation_verifier_repair_bundle(
                            run_dir,
                            invalid_output=Path(preservation_exec.output_file).read_text(encoding="utf-8"),
                            parse_error=str(exc),
                            issue_count=len(comprehensive_review.get("issues") or []),
                            provider=selected_provider,
                            model=selected_review_model,
                            force=force or resume,
                        )
                        preservation_exec = execute_model_bundle(
                            budget,
                            repair_dir,
                            role="preservation-verifier-repair",
                            command=runner,
                            output_name="output.md",
                            timeout_seconds=timeout_seconds,
                            force=force_output or force or resume,
                            dry_run=False,
                        )
                        preservation_call_count += 1
                        try:
                            model_preservation = parse_preservation_verification(
                                Path(preservation_exec.output_file).read_text(encoding="utf-8"),
                                issue_count=len(comprehensive_review.get("issues") or []),
                            )
                        except (json.JSONDecodeError, ValueError):
                            model_preservation = None
                comprehensive_review, preservation_verification = apply_preservation_verification(
                    comprehensive_review,
                    model_preservation,
                )
                preservation_file = run_dir / "preservation_verification.json"
                preservation_file.write_text(
                    json.dumps(preservation_verification, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                merge_comprehensive_review(
                    run_dir,
                    chapter_file=chapter_file,
                    payload=comprehensive_review,
                )
                augment_revision_bundle(run_dir, comprehensive_review, project_context)
                file_reports.extend(
                    [
                        AgentReviseWorkflowFile(kind="comprehensive_review", path=str(run_dir / "comprehensive_review.json"), written=True),
                        AgentReviseWorkflowFile(kind="comprehensive_reviewer_output", path=initial_reviewer_output_file, written=True),
                        AgentReviseWorkflowFile(kind="preservation_verification", path=str(preservation_file), written=True),
                    ]
                )
                write_agent_checkpoint(
                    run_dir,
                    phase="review_ready",
                    next_action="run_chapter_reviser",
                    artifacts=[run_dir / "comprehensive_review.json", run_dir / "issues.before.json", preservation_file, project_context_file],
                )
            reuse_candidate = bool(
                resume
                and resume_phase == "verification_ready"
                and (run_dir / "candidate.md").is_file()
                and (run_dir / "verification.json").is_file()
            )
            if reuse_candidate:
                verification = json.loads((run_dir / "verification.json").read_text(encoding="utf-8"))
                candidate_file = run_dir / "candidate.md"
                staged_outputs = [
                    {
                        "run_dir": str(run_dir),
                        "output_file": str(candidate_file),
                        "role": role,
                        "task": "review",
                        "chapter": chapter_file.stem,
                        "state": "revision",
                        "review_required": True,
                        "output_chars": len(candidate_file.read_text(encoding="utf-8").strip()),
                    }
                ]
            else:
                agent_exec = execute_model_bundle(
                    budget,
                    run_dir,
                    role="chapter-reviser",
                    command=runner,
                    output_name=output_name,
                    timeout_seconds=timeout_seconds,
                    force=force_output or force or resume,
                    dry_run=False,
                )
                executed = True
                inbox = build_agent_inbox(run_dir, output_name=output_name)
                staged_outputs = staged_outputs_from_inbox(inbox)
            if reuse_candidate or (inbox is not None and inbox.ready_count > 0):
                if before_report is None:
                    raise RuntimeError("revision runtime was not initialized before candidate verification.")
                if not reuse_candidate:
                    verification = finalize_revision_candidate(
                        run_dir,
                        chapter_file=chapter_file,
                        output_file=run_dir / output_name,
                        before_report=before_report,
                        force=force_output or force,
                    )
                while True:
                    if verification.get("ready_for_approval") and semantic_verify:
                        verifier_dir = prepare_semantic_verifier_bundle(
                            run_dir,
                            chapter_file=chapter_file,
                            provider=selected_provider,
                            model=selected_review_model,
                            force=semantic_call_count > 0 or force or resume,
                        )
                        semantic_exec = execute_model_bundle(
                            budget,
                            verifier_dir,
                            role="semantic-verifier",
                            command=runner,
                            output_name="output.md",
                            timeout_seconds=timeout_seconds,
                            force=semantic_call_count > 0 or force_output or force or resume,
                            dry_run=False,
                        )
                        executed = True
                        semantic_call_count += 1
                        semantic_text = Path(semantic_exec.output_file).read_text(encoding="utf-8")
                        try:
                            semantic_payload = parse_semantic_verifier_output(semantic_text)
                        except (json.JSONDecodeError, ValueError) as exc:
                            semantic_payload = {
                                "schema": SEMANTIC_VERIFICATION_SCHEMA,
                                "verdict": "uncertain",
                                "invariants": [
                                    {"name": name, "status": "uncertain", "evidence": str(exc)}
                                    for name in REQUIRED_SEMANTIC_INVARIANTS
                                ],
                                "new_issues": ["semantic_verifier_output_invalid"],
                                "summary": str(exc),
                            }
                        verification = merge_semantic_verification(run_dir, semantic_payload)
                    if verification.get("ready_for_approval") or retry_count >= max_retries:
                        break
                    retry_count += 1
                    retry_output_name = prepare_targeted_retry(run_dir, verification, retry_number=retry_count)
                    agent_exec = execute_model_bundle(
                        budget,
                        run_dir,
                        role="chapter-reviser-retry",
                        command=runner,
                        output_name=retry_output_name,
                        timeout_seconds=timeout_seconds,
                        force=False,
                        dry_run=False,
                    )
                    verification = finalize_revision_candidate(
                        run_dir,
                        chapter_file=chapter_file,
                        output_file=run_dir / retry_output_name,
                        before_report=before_report,
                        force=True,
                    )
                    staged_outputs.append(
                        {
                            "run_dir": str(run_dir),
                            "output_file": str(run_dir / retry_output_name),
                            "role": role,
                            "task": "review",
                            "chapter": chapter_file.stem,
                            "state": f"revision_retry_{retry_count}",
                            "review_required": True,
                            "output_chars": len((run_dir / retry_output_name).read_text(encoding="utf-8").strip()),
                        }
                    )
                for kind, path in revision_runtime_files(run_dir).items():
                    if kind not in {"candidate", "diff", "audits_after", "issues_after", "verification"}:
                        continue
                    file_reports.append(AgentReviseWorkflowFile(kind=kind, path=str(path), written=path.exists()))
                stop_reason = str(verification["status"])
                write_agent_checkpoint(
                    run_dir,
                    phase="ready_for_approval" if verification.get("ready_for_approval") else "needs_revision_attention",
                    next_action="await_author_approval" if verification.get("ready_for_approval") else "prepare_targeted_retry_or_request_decision",
                    artifacts=[
                        run_dir / "candidate.md",
                        run_dir / "changes.diff",
                        run_dir / "audits.after.json",
                        run_dir / "issues.after.json",
                        run_dir / "verification.json",
                    ],
                )
            else:
                stop_reason = "agent_output_needs_attention"
            budget.complete()
            file_reports.append(AgentReviseWorkflowFile(kind="model_budget", path=str(budget.path), written=True))

    report = AgentReviseWorkflowReport(
        command="agent-revise-workflow",
        target=str(chapter_file),
        chapter_file=str(chapter_file),
        review_file=review_file,
        run_dir=str(run_dir),
        role=role,
        task="review",
        provider=selected_provider,
        model=selected_model,
        review_model=selected_review_model,
        prepared=prepared,
        executed=executed,
        inbox_status=inbox.status if inbox else None,
        ready_count=inbox.ready_count if inbox else 0,
        source_sha256=source_sha256,
        session_id=session_id,
        verification_status=str(verification["status"]) if verification else None,
        ready_for_approval=bool(verification and verification.get("ready_for_approval")),
        max_retries=max_retries,
        retry_count=retry_count,
        review_scope=review_scope,
        context_file_count=context_file_count,
        memory_record_count=memory_record_count,
        comprehensive_review=comprehensive_review,
        preservation_verification_enabled=preservation_verify,
        preservation_call_count=preservation_call_count,
        preservation_verification=preservation_verification,
        semantic_verification_enabled=semantic_verify,
        semantic_call_count=semantic_call_count,
        max_model_calls=max_model_calls,
        model_calls_used=budget.used_calls if budget else 0,
        max_runtime_seconds=max_runtime_seconds,
        output_name=output_name,
        stop_reason=stop_reason,
        files=file_reports,
        staged_outputs=staged_outputs,
        safety=agent_revise_workflow_safety(),
        next_actions=[],
        agent_exec=agent_exec,
        reviewer_exec=reviewer_exec,
        preservation_exec=preservation_exec,
        semantic_exec=semantic_exec,
        inbox=inbox,
        verification=verification,
    )
    report.next_actions = next_actions_for_report(report)
    return report


def render_agent_revise_workflow(report: AgentReviseWorkflowReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"Unsupported agent-revise-workflow format: {output_format}")
    return format_agent_revise_workflow(report)


def format_agent_revise_workflow(report: AgentReviseWorkflowReport) -> str:
    lines = [
        "# FictionOps Agent Revise Workflow",
        "",
        f"- Chapter: `{report.chapter_file}`",
        f"- Review workflow: `{report.review_file or 'generated'}`",
        f"- Run dir: `{report.run_dir}`",
        f"- Role: `{report.role}`",
        f"- Provider: `{report.provider}`",
        f"- Model: `{report.model}`",
        f"- Review model: `{report.review_model}`",
        f"- Prepared: {'yes' if report.prepared else 'no'}",
        f"- Executed runner: {'yes' if report.executed else 'no'}",
        f"- Inbox status: `{report.inbox_status or '-'}`",
        f"- Ready staged outputs: {report.ready_count}",
        f"- Session: `{report.session_id}`",
        f"- Verification: `{report.verification_status or '-'}`",
        f"- Ready for approval: {'yes' if report.ready_for_approval else 'no'}",
        f"- Targeted retries: {report.retry_count}/{report.max_retries}",
        f"- Review scope: `{report.review_scope}`",
        f"- Project context files: {report.context_file_count}",
        f"- Retrieved memory records: {report.memory_record_count}",
        f"- Preservation verifier calls: {report.preservation_call_count if report.preservation_verification_enabled else 'disabled'}",
        f"- Semantic verifier calls: {report.semantic_call_count if report.semantic_verification_enabled else 'disabled'}",
        f"- Model-call budget: {report.model_calls_used}/{report.max_model_calls} calls; runtime limit {report.max_runtime_seconds}s",
        f"- Stop reason: `{report.stop_reason}`",
        "",
        "## Safety",
        "",
        "- The source chapter is copied into the bundle.",
        "- Runner output is staged only and never applied to the manuscript automatically.",
        "- Candidate output is diffed and re-audited before acceptance is enabled.",
        "- Explicit acceptance is required, with source and candidate hash checks.",
        "",
        "## Bundle Files",
        "",
    ]
    if report.files:
        lines.extend(["| Kind | Written | Path |", "| --- | --- | --- |"])
        for item in report.files:
            lines.append(f"| `{item.kind}` | {'yes' if item.written else 'no'} | `{item.path}` |")
    else:
        lines.append("No bundle files planned.")

    lines.extend(["", "## Staged Outputs", ""])
    if report.staged_outputs:
        lines.extend(["| State | Output | Chars |", "| --- | --- | --- |"])
        for item in report.staged_outputs:
            lines.append(f"| `{item['state']}` | `{item['output_file']}` | {item['output_chars']} |")
    else:
        lines.append("No staged output is ready yet.")

    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
