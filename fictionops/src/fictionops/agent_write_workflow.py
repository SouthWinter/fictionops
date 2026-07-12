from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from .agent_budget import ModelExecutionBudget, execute_model_bundle, start_model_budget
from .agent_exec import AgentExecReport
from .agent_memory import build_memory_index, query_memory, render_memory_query
from .agent_project_context import ProjectContextBundle, ProjectContextItem, compile_project_context, discover_project_root, render_project_context
from .agent_revision_runtime import (
    SESSION_SCHEMA,
    append_event,
    first_heading,
    sha256_text,
    starts_with_wrapper,
    unified_diff,
    utc_now,
    write_json,
)
from .agent_session_control import load_agent_checkpoint, validate_checkpoint_for_resume, write_agent_checkpoint
from .agent_trajectory import append_trajectory, context_attribution
from .agent_story_reasoning import (
    chapter_contract,
    deterministic_story_audit,
    merge_story_verification,
    normalize_plan_fact_codes,
    parse_adversarial_review,
    parse_causal_simulation,
    prepare_adversarial_review_bundle,
    prepare_causal_simulation_bundle,
    prepare_causal_retry,
    review_evidence_grounding_issues,
    sanitize_theme_answers,
    validate_causal_simulation,
    validate_plan_against_causal,
)
from .model_config import build_model_config_report


DRAFT_EVALUATION_SCHEMA = "fictionops.draft_evaluation.v1"
CHAPTER_PLAN_SCHEMA = "fictionops.chapter_execution_plan.v1"
DRAFT_DIMENSIONS = (
    "chapter_engine",
    "scene_progression",
    "character_voice",
    "information_boundaries",
    "continuity",
    "foreshadowing",
    "prose_freshness",
    "ending_change",
)


@dataclass
class AgentWriteWorkflowFile:
    kind: str
    path: str
    written: bool


@dataclass
class AgentWriteWorkflowReport:
    command: str
    target: str
    chapter_file: str
    engine_file: str
    outline_file: str | None
    run_dir: str
    provider: str
    model: str
    planning_model: str
    evaluation_model: str
    source_existed: bool
    source_sha256: str
    session_id: str
    context_file_count: int
    prepared: bool
    executed: bool
    verification_status: str | None
    ready_for_approval: bool
    min_chars: int
    max_retries: int
    retry_count: int
    evaluator_call_count: int
    planner_call_count: int
    causal_simulator_call_count: int
    adversarial_reviewer_call_count: int
    scene_writer_call_count: int
    max_model_calls: int
    model_calls_used: int
    max_runtime_seconds: int
    scene_by_scene: bool
    memory_record_count: int
    stop_reason: str
    files: list[AgentWriteWorkflowFile]
    next_actions: list[str]
    draft_exec: AgentExecReport | None
    scene_execs: list[AgentExecReport]
    planner_exec: AgentExecReport | None
    evaluator_exec: AgentExecReport | None
    causal_exec: AgentExecReport | None
    adversarial_exec: AgentExecReport | None
    verification: dict[str, object] | None
    evaluation: dict[str, object] | None
    chapter_plan: dict[str, object] | None
    causal_simulation: dict[str, object] | None
    adversarial_review: dict[str, object] | None
    chapter_contract: dict[str, object] | None


def safe_name(path: Path) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\s]+", "_", path.stem).strip("_") or "chapter"
    return f"write_workflow_{cleaned}"


def resolve_run_dir(chapter_file: Path, out_dir: str | None) -> Path:
    root = discover_project_root(chapter_file)
    if out_dir:
        candidate = Path(out_dir).expanduser()
        return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    management = root / ("00_management" if (root / "00_management").is_dir() else "00_总纲与管理")
    return (management / "agent_runs" / safe_name(chapter_file)).resolve()


def engine_line(text: str, labels: tuple[str, ...]) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        for label in labels:
            if stripped.lower().startswith(label.lower()):
                return stripped[len(label) :].strip()
    return ""


def chapter_title_from_path(path: Path) -> str:
    stem = re.sub(r"^第\s*\d+\s*章[_\-\s]*", "", path.stem)
    stem = re.sub(r"^ch[_-]?\d+[_\-\s]*", "", stem, flags=re.IGNORECASE)
    return stem.strip("_- ")


def target_chars_from_engine(text: str) -> int | None:
    value = engine_line(text, ("- 建议体量：", "- 建议体量:", "- target chars:", "- target:"))
    match = re.search(r"(\d[\d,]*)", value)
    return int(match.group(1).replace(",", "")) if match else None


def target_chars_from_outline(text: str, chapter_file: Path) -> int | None:
    title = chapter_title_from_path(chapter_file)
    if not text.strip() or not title:
        return None
    lines = text.splitlines()
    heading_indexes = [index for index, line in enumerate(lines) if title in line and line.lstrip().startswith("#")]
    indexes = heading_indexes or [index for index, line in enumerate(lines) if title in line]
    for index in indexes:
        end = min(len(lines), index + 90)
        for next_index in range(index + 1, end):
            if lines[next_index].startswith("### "):
                end = next_index
                break
        segment = "\n".join(lines[index:end])
        range_match = re.search(r"目标\s*([0-9][0-9,]{2,})\s*[-—~至到]\s*([0-9][0-9,]{2,})\s*字?", segment)
        if range_match:
            return int(range_match.group(1).replace(",", ""))
        single_match = re.search(r"目标\s*([0-9][0-9,]{2,})\s*字", segment)
        if single_match:
            return int(single_match.group(1).replace(",", ""))
    return None


def expected_title_from_engine(text: str, chapter_file: Path | None = None) -> str:
    title = engine_line(text, ("- 标题：", "- 标题:", "- title:", "- Title:"))
    if title:
        return title
    for line in text.splitlines():
        if not line.lstrip().startswith("#"):
            continue
        quoted = re.search(r"[《\"]([^》\"]+)[》\"]", line)
        if quoted:
            return quoted.group(1).strip()
        heading = re.search(r"第\s*\d+\s*章[：:_\-\s]+(.+?)(?:章节发动机)?\s*$", line)
        if heading:
            return heading.group(1).strip()
        plain = re.sub(r"^\s*#{1,6}\s*", "", line).strip()
        if plain and not re.search(r"(?:章节发动机|chapter\s+engine)$", plain, flags=re.IGNORECASE):
            return plain
    return chapter_title_from_path(chapter_file) if chapter_file else ""


def draft_constraint_specs(plan: dict[str, object]) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    for prefix, key, kind in (("P", "preserve_constraints", "preserve"), ("F", "forbidden_reveals", "forbidden")):
        values = plan.get(key) or []
        if not isinstance(values, list):
            continue
        for index, value in enumerate(values, start=1):
            text = str(value).strip()
            if text:
                specs.append({"id": f"{prefix}{index}", "kind": kind, "text": text})
    return specs


def augment_context_with_memory(context: ProjectContextBundle, memory: dict[str, object], *, max_total_chars: int) -> ProjectContextBundle:
    existing = {str(Path(item.path).resolve()) for item in context.items if "#L" not in item.path}
    items = list(context.items)
    included = context.included_chars
    for result in memory.get("results") or []:
        if not isinstance(result, dict):
            continue
        content = str(result.get("content") or "").strip()
        source = str(result.get("source") or "")
        if not content or not source:
            continue
        try:
            resolved_source = str(Path(source).resolve())
        except OSError:
            resolved_source = source
        # Keep high-authority preference snippets even when their source file is
        # already present; other file segments would only duplicate context.
        if resolved_source in existing and str(result.get("kind")) != "preference":
            continue
        if included + len(content) > max_total_chars:
            break
        items.append(
            ProjectContextItem(
                role=f"typed memory:{result.get('kind')}",
                path=f"{source}#L{result.get('start_line')}-L{result.get('end_line')}",
                authority=str(result.get("authority") or "supporting"),
                reason=f"memory retrieval score {result.get('score')}",
                sha256=str(result.get("source_sha256") or ""),
                chars=len(content),
                included_chars=len(content),
                truncated=bool(result.get("truncated")),
                content=content,
            )
        )
        included += len(content)
    return ProjectContextBundle(
        schema="fictionops.project_context.v2",
        project_root=context.project_root,
        task=context.task,
        target_file=context.target_file,
        source_chars=context.source_chars,
        max_files=context.max_files + max(0, len(items) - len(context.items)),
        max_total_chars=max_total_chars,
        included_chars=included,
        truncated=context.truncated,
        items=items,
    )


def sanitized_context_bundle(context: ProjectContextBundle, causal: dict[str, object]) -> ProjectContextBundle:
    return ProjectContextBundle(
        schema=context.schema,
        project_root=context.project_root,
        task=context.task,
        target_file=context.target_file,
        source_chars=context.source_chars,
        max_files=context.max_files,
        max_total_chars=context.max_total_chars,
        included_chars=context.included_chars,
        truncated=context.truncated,
        items=[
            ProjectContextItem(
                role=item.role,
                path=item.path,
                authority=item.authority,
                reason=item.reason,
                sha256=item.sha256,
                chars=item.chars,
                included_chars=item.included_chars,
                truncated=item.truncated,
                content=sanitize_theme_answers(item.content, causal),
            )
            for item in context.items
        ],
    )


def placeholder_source(text: str) -> bool:
    plain = text.strip()
    if not plain:
        return True
    if "> Draft starts here." in text:
        return True
    body = "\n".join(line for line in text.splitlines() if not line.strip().startswith("#")).strip()
    return len(body) < 40 and ("待写" in body or "TODO" in body or not body)


def session_id_for_write(chapter_file: Path, source_sha: str, engine_sha: str) -> str:
    token = hashlib.sha1(f"{chapter_file.resolve()}|{source_sha}|{engine_sha}".encode("utf-8")).hexdigest()[:12]
    return f"write-{re.sub(r'[^A-Za-z0-9]+', '-', chapter_file.stem).strip('-').lower() or 'chapter'}-{token}"


def bundle_files(run_dir: Path) -> dict[str, Path]:
    return {
        "readme": run_dir / "README.md",
        "request": run_dir / "request.json",
        "prompt": run_dir / "prompt.md",
        "context": run_dir / "context_pack.md",
        "project_context": run_dir / "project_context.md",
        "memory_query": run_dir / "memory_query.json",
        "memory_context": run_dir / "memory_context.md",
        "source": run_dir / "source_chapter.md",
        "engine": run_dir / "chapter_engine.md",
        "causal_simulation": run_dir / "causal_simulation.json",
        "plan": run_dir / "chapter_plan.json",
        "chapter_contract": run_dir / "chapter_contract.json",
        "story_fact_ledger": run_dir / "story_fact_ledger.json",
        "scene_states": run_dir / "scene_state_contract.json",
        "scene_execution": run_dir / "scene_execution.json",
        "source_manifest": run_dir / "source_manifest.json",
        "session": run_dir / "session.json",
        "events": run_dir / "events.jsonl",
        "trajectory": run_dir / "trajectory.jsonl",
        "candidate": run_dir / "candidate.md",
        "diff": run_dir / "changes.diff",
        "verification": run_dir / "verification.json",
        "evaluation": run_dir / "draft_evaluation.json",
        "adversarial_review": run_dir / "adversarial_review.json",
        "deterministic_story_audit": run_dir / "deterministic_story_audit.json",
        "retrospective": run_dir / "retrospective.draft.md",
        "canon_sync": run_dir / "canon_sync_suggestions.json",
    }


def write_initial_bundle(
    run_dir: Path,
    *,
    chapter_file: Path,
    source_text: str,
    source_existed: bool,
    engine_file: Path,
    engine_text: str,
    outline_file: Path | None,
    context: ProjectContextBundle,
    provider: str,
    model: str,
    min_chars: int,
    workflow_options: dict[str, object],
    force: bool,
) -> tuple[str, str, list[AgentWriteWorkflowFile]]:
    files = bundle_files(run_dir)
    initial_names = ("readme", "request", "prompt", "context", "project_context", "source", "engine", "source_manifest", "session", "events", "trajectory")
    if not force:
        existing = [files[name] for name in initial_names if files[name].exists()]
        if existing:
            raise FileExistsError(existing[0])
    run_dir.mkdir(parents=True, exist_ok=True)
    if files["events"].exists() and force:
        files["events"].unlink()
    source_sha = sha256_text(source_text)
    engine_sha = sha256_text(engine_text)
    session_id = session_id_for_write(chapter_file, source_sha, engine_sha)
    title = expected_title_from_engine(engine_text, chapter_file)
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(chapter_file.resolve()),
        "role": "draft-writer",
        "role_name": "Closed-loop Chapter Draft Writer",
        "task": "draft",
        "book": chapter_file.parent.name,
        "chapter": chapter_file.stem,
        "provider": provider,
        "model": model,
        "run_dir": str(run_dir.resolve()),
        "source_existed": source_existed,
        "source_sha256": source_sha,
        "engine_file": str(engine_file.resolve()),
        "outline_file": str(outline_file.resolve()) if outline_file else None,
        "safety": {
            "overwrites_manuscript": False,
            "writes_staging_output": True,
            "requires_human_apply": True,
        },
    }
    prompt = "\n".join(
        [
            "# FictionOps Closed-loop Chapter Draft",
            "",
            f"Write the complete target chapter `{title or chapter_file.stem}` from the chapter engine and project context.",
            "",
            "## Requirements",
            "",
            "- Execute every engine pressure/desire/obstacle/change/remainder function through scenes, not outline explanation.",
            "- Stay inside the viewpoint character's knowledge and preserve all information-release prohibitions.",
            "- Keep character intelligence, voice, region, age, and relationship behavior distinct.",
            "- Use foreshadowing as light contact, not explanation.",
            "- Avoid formulaic openings, explanatory narrator verdicts, and mechanical target-word padding.",
            "- Vary metaphor form by scene function and viewpoint voice. Use direct description, action, implicit metaphor, or explicit comparison as needed; do not mechanically rotate 像/好似/仿佛/仿若/犹如/宛如 as synonyms.",
            f"- Produce at least {min_chars} non-whitespace characters unless the engine itself clearly calls for a deliberately short chapter.",
            "",
            "## Output",
            "",
            "Write only the complete chapter Markdown. Do not output notes, a plan, analysis, or fences.",
        ]
    ).rstrip() + "\n"
    context_text = "\n".join(
        [
            "# FictionOps Draft Context",
            "",
            "## Chapter Engine",
            "",
            engine_text.rstrip(),
            "",
            "## Project Context",
            "",
            render_project_context(context).rstrip(),
        ]
    ).rstrip() + "\n"
    manifest = {
        "schema": "fictionops.revision_source_manifest.v1",
        "source_file": str(chapter_file.resolve()),
        "source_existed": source_existed,
        "source_sha256": source_sha,
        "source_chars": len(source_text),
        "engine_file": str(engine_file.resolve()),
        "engine_sha256": engine_sha,
        "created_at": utc_now(),
    }
    session = {
        "schema": SESSION_SCHEMA,
        "session_id": session_id,
        "workflow": "chapter_write",
        "state": "context_ready",
        "source_file": str(chapter_file.resolve()),
        "source_existed": source_existed,
        "source_sha256": source_sha,
        "engine_file": str(engine_file.resolve()),
        "engine_sha256": engine_sha,
        "provider": provider,
        "model": model,
        "candidate_file": None,
        "candidate_sha256": None,
        "ready_for_approval": False,
        "workflow_options": workflow_options,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    files["readme"].write_text(
        f"# FictionOps Agent Write Workflow\n\n- Target: `{chapter_file}`\n- Engine: `{engine_file}`\n- Source existed: `{source_existed}`\n",
        encoding="utf-8",
        newline="\n",
    )
    write_json(files["request"], request, force=force)
    files["prompt"].write_text(prompt, encoding="utf-8", newline="\n")
    files["context"].write_text(context_text, encoding="utf-8", newline="\n")
    files["project_context"].write_text(render_project_context(context), encoding="utf-8", newline="\n")
    files["source"].write_text(source_text, encoding="utf-8", newline="\n")
    files["engine"].write_text(engine_text, encoding="utf-8", newline="\n")
    write_json(files["source_manifest"], manifest, force=force)
    write_json(files["session"], session, force=force)
    append_event(run_dir, "write_runtime_initialized", "context_ready", source_existed=source_existed, min_chars=min_chars)
    write_agent_checkpoint(
        run_dir,
        phase="context_ready",
        next_action="run_causal_simulator_or_planner",
        artifacts=[files["source_manifest"], files["engine"], files["project_context"]],
    )
    reports = [AgentWriteWorkflowFile(kind=name, path=str(files[name]), written=True) for name in initial_names]
    return source_sha, session_id, reports


def static_draft_verification(
    *,
    chapter_file: Path,
    candidate_file: Path,
    candidate_text: str,
    engine_text: str,
    min_chars: int,
) -> dict[str, object]:
    nonspace = sum(1 for char in candidate_text if not char.isspace())
    heading = first_heading(candidate_text)
    title = expected_title_from_engine(engine_text, chapter_file)
    checks = [
        {"name": "candidate_nonempty", "passed": bool(candidate_text.strip()), "blocking": True, "evidence": {"nonspace_chars": nonspace}},
        {"name": "chapter_output_only", "passed": not starts_with_wrapper(candidate_text), "blocking": True, "evidence": {"first_heading": heading}},
        {"name": "chapter_heading_present", "passed": heading is not None, "blocking": True, "evidence": {"heading": heading}},
        {
            "name": "engine_title_present",
            "passed": not title or bool(heading and title.casefold() in heading.casefold()),
            "blocking": True,
            "evidence": {"engine_title": title, "heading": heading},
        },
        {"name": "minimum_draft_size", "passed": nonspace >= min_chars, "blocking": True, "evidence": {"minimum": min_chars, "actual": nonspace}},
        {"name": "placeholder_removed", "passed": "> Draft starts here." not in candidate_text, "blocking": True, "evidence": {}},
    ]
    failures = [item["name"] for item in checks if item["blocking"] and not item["passed"]]
    return {
        "schema": "fictionops.write_verification.v1",
        "status": "static_passed" if not failures else "needs_revision_attention",
        "ready_for_approval": False,
        "source_file": str(chapter_file.resolve()),
        "candidate_file": str(candidate_file.resolve()),
        "candidate_sha256": sha256_text(candidate_text),
        "checks": checks,
        "blocking_failures": failures,
        "warnings": [],
        "verified_at": utc_now(),
    }


def prepare_evaluator_bundle(
    run_dir: Path,
    *,
    chapter_file: Path,
    engine_text: str,
    candidate_text: str,
    chapter_plan: dict[str, object],
    contract: dict[str, object],
    adversarial_review: dict[str, object],
    context: ProjectContextBundle,
    provider: str,
    model: str,
    force: bool,
) -> Path:
    evaluator_dir = run_dir / "draft_evaluator"
    request_file = evaluator_dir / "request.json"
    prompt_file = evaluator_dir / "prompt.md"
    context_file = evaluator_dir / "context_pack.md"
    if not force:
        existing = [path for path in (request_file, prompt_file, context_file) if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    evaluator_dir.mkdir(parents=True, exist_ok=True)
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(chapter_file.resolve()),
        "role": "draft-evaluator",
        "role_name": "Closed-loop Draft Evaluator",
        "task": "review",
        "book": chapter_file.parent.name,
        "chapter": chapter_file.stem,
        "provider": provider,
        "model": model,
        "run_dir": str(evaluator_dir.resolve()),
        "safety": {"overwrites_manuscript": False, "writes_staging_output": True, "requires_human_apply": True},
    }
    dimension_rows = ",\n".join(
        f'    {{"name": "{name}", "status": "pass|fail|uncertain", "evidence": "brief evidence"}}'
        for name in DRAFT_DIMENSIONS
    )
    constraints = draft_constraint_specs(chapter_plan)
    prompt = "\n".join(
        [
            "# FictionOps Draft Evaluator",
            "",
            "Judge whether the candidate is a usable execution of the engine and project constraints. Do not rewrite it.",
            "A polished chapter fails if it invents canon, leaks information, flattens character voice, misses the engine change, or merely paraphrases the plan.",
            "Under prose_freshness, inspect explicit comparison-marker distribution and implicit metaphors. Fail mechanical synonym rotation, repeated over-precise images, and markers whose literary register does not fit the viewpoint; do not demand low counts when comparisons are functional.",
            "Before assigning dimension verdicts, try to disprove every constraint below. Copy each constraint id exactly and quote the strongest candidate passage for or against it. A forbidden constraint passes only when the prohibited completion or reveal is absent. A broad dimension cannot override a failed constraint.",
            "Resolve apparent constraint conflicts by specificity: a concrete event explicitly required by the engine or plan is not itself a violation of a broader prohibition. Distinguish accidental weak response from deliberate or skilled control.",
            "Visible actions such as looking, walking, touching, or pausing do not enter another character's viewpoint. Require inaccessible thought, intention, memory, or judgment before reporting viewpoint leakage.",
            "The assembled prose has no visible scene markers. Judge state transitions by event order and achieved state; do not fail only because you guessed a different invisible scene boundary.",
            "The independent adversarial review is binding evidence. If it reports an unresolved P1/P2 issue, failed constraint, or failed scene state, your verdict cannot be pass.",
            "Constraint specs:",
            json.dumps(constraints, ensure_ascii=False, indent=2),
            "",
            "Return one JSON object with no Markdown fences:",
            "{",
            f'  "schema": "{DRAFT_EVALUATION_SCHEMA}",',
            '  "verdict": "pass|fail|uncertain",',
            '  "dimensions": [',
            dimension_rows,
            "  ],",
            '  "constraint_checks": [{"id": "P1", "status": "pass|fail|uncertain", "evidence": "exact candidate quotation plus reasoning"}],',
            '  "issues": [{"category": "chapter_engine", "severity": "P1|P2|P3|P4|P5", "problem": "...", "evidence": ["..."], "suggested_action": "...", "preserve_constraints": ["..."]}],',
            '  "retrospective": {"chapter_change": "...", "residue": "...", "character_updates": [], "information_updates": [], "foreshadowing_updates": []},',
            '  "canon_sync_suggestions": [{"area": "character|information|foreshadowing|timeline|object|none", "suggestion": "...", "evidence": "..."}],',
            '  "summary": "short conclusion"',
            "}",
        ]
    ).rstrip() + "\n"
    context_text = "\n".join(
        [
            "# Draft Evaluation Context",
            "",
            "## Chapter Engine",
            "",
            engine_text.rstrip(),
            "",
            "## Candidate Chapter",
            "",
            candidate_text.rstrip(),
            "",
            "## Chapter Execution Plan",
            "",
            "```json",
            json.dumps(chapter_plan, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Chapter Contract",
            "",
            "```json",
            json.dumps(contract, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Independent Adversarial Review",
            "",
            "```json",
            json.dumps(adversarial_review, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Project Context",
            "",
            render_project_context(context).rstrip(),
        ]
    ).rstrip() + "\n"
    write_json(request_file, request, force=force)
    prompt_file.write_text(prompt, encoding="utf-8", newline="\n")
    context_file.write_text(context_text, encoding="utf-8", newline="\n")
    append_event(run_dir, "draft_evaluator_prepared", "verifying", evaluator_dir=str(evaluator_dir.resolve()))
    return evaluator_dir


def prepare_planner_bundle(
    run_dir: Path,
    *,
    chapter_file: Path,
    engine_text: str,
    outline_text: str,
    causal_simulation: dict[str, object],
    context: ProjectContextBundle,
    provider: str,
    model: str,
    force: bool,
) -> Path:
    planner_dir = run_dir / "chapter_planner"
    request_file = planner_dir / "request.json"
    prompt_file = planner_dir / "prompt.md"
    context_file = planner_dir / "context_pack.md"
    if not force:
        existing = [path for path in (request_file, prompt_file, context_file) if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    planner_dir.mkdir(parents=True, exist_ok=True)
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(chapter_file.resolve()),
        "role": "chapter-planner",
        "role_name": "Chapter Execution Planner",
        "task": "plan",
        "book": chapter_file.parent.name,
        "chapter": chapter_file.stem,
        "provider": provider,
        "model": model,
        "run_dir": str(planner_dir.resolve()),
        "safety": {"overwrites_manuscript": False, "writes_staging_output": True, "requires_human_apply": True},
    }
    prompt = "\n".join(
        [
            "# FictionOps Chapter Execution Planner",
            "",
            "Turn the outline and chapter engine into an executable scene plan before prose drafting.",
            "Do not invent canon to fill missing context. If a required decision is absent, return status blocked and name it.",
            "Keep scene functions uneven and organic; do not force every chapter into the same number or rhythm of scenes.",
            "Treat the causal simulation as a contract: do not add viewpoints, knowledge, or consequences that it forbids. Preserve transferred costs and unresolved consequences.",
            "Every scene must declare a stable scene_id, the causal event_ids it executes, viewpoint, entry_state, and exit_state so later reviewers can verify state handoff.",
            "Use structured object records only for objects actually tracked by the causal contract; copy their stable state code into each record's code field and keep natural-language detail in state. Otherwise use an empty objects array.",
            "For every declared timeline rule, fact_assertions.timeline must contain exactly one {rule_id, elapsed, unit}. For every coded object transition, fact_assertions.object_transitions must map {rule_id, transition_id, event_id, scene_id, from_code, to_code}. Multiple consecutive transitions may happen inside one scene.",
            "",
            "Return one JSON object with no Markdown fences:",
            "{",
            f'  "schema": "{CHAPTER_PLAN_SCHEMA}",',
            '  "status": "ready|blocked",',
            '  "title": "...", "viewpoint": "...", "kind": "...", "target_chars": 0,',
            '  "engine": {"pressure": "...", "desire": "...", "obstacle": "...", "change": "...", "remainder": "..."},',
            '  "scenes": [{"scene_id": "S1", "event_ids": ["E1"], "order": 1, "viewpoint": "...", "weight": 1.0, "target_chars": 0, "function": "...", "goal": "...", "conflict": "...", "information_boundary": "...", "entry_state": {"facts": [], "knowledge": [], "objects": [{"name": "...", "code": "ON_CART", "state": "..."}], "residue": []}, "exit_state": {"facts": [], "knowledge": [], "objects": [{"name": "...", "code": "LIFTED", "state": "..."}], "residue": []}, "exit": "..."}],',
            '  "fact_assertions": {"timeline": [{"rule_id": "T1", "elapsed": 2, "unit": "hour"}], "object_transitions": [{"rule_id": "O1", "transition_id": "O1T1", "event_id": "E1", "scene_id": "S1", "from_code": "ON_CART", "to_code": "LIFTED"}]},',
            '  "preserve_constraints": ["..."], "forbidden_reveals": ["..."], "foreshadowing": ["..."],',
            '  "missing_context": [], "summary": "short execution logic"',
            "}",
        ]
    ).rstrip() + "\n"
    context_text = "\n".join(
        [
            "# Chapter Planning Context",
            "",
            "## Chapter Engine",
            "",
            engine_text.rstrip(),
            "",
            "## Outline",
            "",
            outline_text.rstrip() or "No explicit outline file was supplied.",
            "",
            "## Causal Simulation",
            "",
            "```json",
            json.dumps(causal_simulation, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Project Context",
            "",
            render_project_context(context).rstrip(),
        ]
    ).rstrip() + "\n"
    write_json(request_file, request, force=force)
    prompt_file.write_text(prompt, encoding="utf-8", newline="\n")
    context_file.write_text(context_text, encoding="utf-8", newline="\n")
    append_event(run_dir, "chapter_planner_prepared", "planning", planner_dir=str(planner_dir.resolve()))
    return planner_dir


def prepare_planner_retry(planner_dir: Path, plan_text: str, issues: list[dict[str, object]]) -> None:
    prompt_file = planner_dir / "prompt.md"
    context_file = planner_dir / "context_pack.md"
    prompt = prompt_file.read_text(encoding="utf-8")
    context = context_file.read_text(encoding="utf-8")
    prompt_file.write_text(
        prompt.rstrip()
        + "\n\n## Plan Contract Repair\n\nThe previous plan violated the causal contract. Return a complete corrected plan. Do not defend or merely annotate the previous plan.\n"
        + "For theme_question_answered_in_plan, remove the abstract answer from every scene field, including function, goal, conflict, knowledge, information_boundary, exit, and state. Replace it with concrete observations and an unresolved residue question; do not move or paraphrase the prohibited conclusion.\n"
        + "For fact-ledger issues, copy stable codes, rule ids, transition ids, and event ids exactly from the causal contract. Timeline assertions require rule_id, one elapsed value, and the same unit. Object transition assertions map each ordered causal transition to a scene; scene entry uses the first transition's from_code and scene exit uses the last transition's to_code. Natural-language state descriptions may be more specific and are not compared as codes.\n"
        + json.dumps(issues, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    context_file.write_text(
        context.rstrip() + "\n\n## Rejected Previous Plan\n\n```json\n" + plan_text.strip() + "\n```\n",
        encoding="utf-8",
        newline="\n",
    )


def execute_chapter_planner(
    run_dir: Path,
    *,
    chapter_file: Path,
    engine_text: str,
    outline_text: str,
    causal_result: dict[str, object],
    context: ProjectContextBundle,
    provider: str,
    model: str,
    runner: list[str],
    budget: ModelExecutionBudget,
    timeout_seconds: int,
    force: bool,
    force_output: bool,
    require_scene_states: bool,
) -> tuple[dict[str, object], AgentExecReport, int]:
    planner_dir = prepare_planner_bundle(
        run_dir,
        chapter_file=chapter_file,
        engine_text=engine_text,
        outline_text=outline_text,
        causal_simulation=causal_result,
        context=context,
        provider=provider,
        model=model,
        force=force,
    )
    planner_exec = execute_model_bundle(
        budget,
        planner_dir,
        role="chapter-planner",
        command=runner,
        output_name="output.md",
        timeout_seconds=timeout_seconds,
        force=force_output or force,
        dry_run=False,
    )
    calls = 1
    output_text = Path(planner_exec.output_file).read_text(encoding="utf-8")
    try:
        chapter_plan = parse_chapter_plan(output_text, require_scene_states=require_scene_states)
        normalize_plan_fact_codes(chapter_plan, causal_result)
        issues = validate_plan_against_causal(chapter_plan, causal_result) if require_scene_states else []
    except (json.JSONDecodeError, ValueError) as exc:
        chapter_plan = None
        issues = [{"kind": "chapter_plan_schema_error", "evidence": str(exc)}]
    for retry in range(1, 4):
        if not issues:
            break
        write_json(
            run_dir / f"chapter_plan.rejected.v{retry}.json",
            {
                "schema": "fictionops.rejected_chapter_plan.v1",
                "plan": chapter_plan,
                "contract_issues": issues,
                "raw_output": output_text,
            },
            force=True,
        )
        prepare_planner_retry(planner_dir, output_text, issues)
        planner_exec = execute_model_bundle(
            budget,
            planner_dir,
            role="chapter-plan-repair",
            command=runner,
            output_name=f"output.retry{retry}.md",
            timeout_seconds=timeout_seconds,
            force=True,
            dry_run=False,
        )
        calls += 1
        output_text = Path(planner_exec.output_file).read_text(encoding="utf-8")
        try:
            chapter_plan = parse_chapter_plan(output_text, require_scene_states=require_scene_states)
            normalize_plan_fact_codes(chapter_plan, causal_result)
            issues = validate_plan_against_causal(chapter_plan, causal_result) if require_scene_states else []
        except (json.JSONDecodeError, ValueError) as exc:
            chapter_plan = None
            issues = [{"kind": "chapter_plan_schema_error", "evidence": str(exc)}]
    if issues or chapter_plan is None:
        raise RuntimeError(
            "chapter plan still violates the causal contract after three repairs: "
            + json.dumps(issues, ensure_ascii=False)
        )
    return chapter_plan, planner_exec, calls


def parse_json_object(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("draft evaluator did not return a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("draft evaluator output must be a JSON object")
    return payload


def parse_draft_evaluation(text: str, expected_constraint_ids: list[str] | None = None) -> dict[str, object]:
    payload = parse_json_object(text)
    if payload.get("schema") != DRAFT_EVALUATION_SCHEMA:
        raise ValueError(f"draft evaluator must declare schema {DRAFT_EVALUATION_SCHEMA}")
    if str(payload.get("verdict")) not in {"pass", "fail", "uncertain"}:
        raise ValueError("draft evaluator verdict must be pass, fail, or uncertain")
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, list):
        raise ValueError("draft evaluator dimensions must be a list")
    by_name = {str(item.get("name")): item for item in dimensions if isinstance(item, dict)}
    missing = [name for name in DRAFT_DIMENSIONS if name not in by_name]
    if missing:
        raise ValueError(f"draft evaluator omitted dimensions: {', '.join(missing)}")
    for name in DRAFT_DIMENSIONS:
        if str(by_name[name].get("status")) not in {"pass", "fail", "uncertain"}:
            raise ValueError(f"draft evaluator dimension {name} has invalid status")
    constraint_checks = payload.get("constraint_checks")
    if not isinstance(constraint_checks, list):
        raise ValueError("draft evaluator constraint_checks must be a list")
    by_id = {str(item.get("id")): item for item in constraint_checks if isinstance(item, dict)}
    missing_constraints = [item for item in expected_constraint_ids or [] if item not in by_id]
    if missing_constraints:
        raise ValueError(f"draft evaluator omitted constraint checks: {', '.join(missing_constraints)}")
    for constraint_id, item in by_id.items():
        if str(item.get("status")) not in {"pass", "fail", "uncertain"}:
            raise ValueError(f"draft evaluator constraint {constraint_id} has invalid status")
        if not str(item.get("evidence") or "").strip():
            raise ValueError(f"draft evaluator constraint {constraint_id} omitted evidence")
    return payload


def parse_chapter_plan(text: str, *, require_scene_states: bool = False) -> dict[str, object]:
    payload = parse_json_object(text)
    if payload.get("schema") != CHAPTER_PLAN_SCHEMA:
        raise ValueError(f"chapter planner must declare schema {CHAPTER_PLAN_SCHEMA}")
    if str(payload.get("status")) not in {"ready", "blocked"}:
        raise ValueError("chapter planner status must be ready or blocked")
    engine = payload.get("engine")
    if not isinstance(engine, dict):
        raise ValueError("chapter planner engine must be an object")
    missing_engine = [name for name in ("pressure", "desire", "obstacle", "change", "remainder") if not str(engine.get(name) or "").strip()]
    if payload.get("status") == "ready" and missing_engine:
        raise ValueError(f"ready chapter plan omitted engine fields: {', '.join(missing_engine)}")
    scenes = payload.get("scenes")
    if payload.get("status") == "ready" and (not isinstance(scenes, list) or not scenes):
        raise ValueError("ready chapter plan requires at least one scene")
    if require_scene_states and isinstance(scenes, list):
        seen: set[str] = set()
        for index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                raise ValueError(f"chapter plan scene {index} must be an object")
            scene_id = str(scene.get("scene_id") or "")
            if not scene_id or scene_id in seen:
                raise ValueError(f"chapter plan scene {index} requires a unique scene_id")
            seen.add(scene_id)
            if not str(scene.get("viewpoint") or "").strip():
                raise ValueError(f"chapter plan scene {scene_id} requires a viewpoint")
            for key in ("entry_state", "exit_state"):
                if not isinstance(scene.get(key), dict):
                    raise ValueError(f"chapter plan scene {scene_id} requires object {key}")
    return payload


def prepare_json_contract_retry(directory: Path, output_text: str, error: str, *, label: str) -> None:
    prompt_file = directory / "prompt.md"
    context_file = directory / "context_pack.md"
    prompt_file.write_text(
        prompt_file.read_text(encoding="utf-8").rstrip()
        + f"\n\n## {label} JSON Contract Repair\n\nThe previous response could not be parsed or violated the required JSON schema: {error}. Return one complete corrected JSON object only. Preserve the substantive review judgment; repair quotation escaping, commas, brackets, required ids, statuses, and evidence fields. Do not wrap the object in Markdown fences.\n",
        encoding="utf-8",
        newline="\n",
    )
    context_file.write_text(
        context_file.read_text(encoding="utf-8").rstrip() + f"\n\n## Rejected {label} Output\n\n```text\n" + output_text.strip() + "\n```\n",
        encoding="utf-8",
        newline="\n",
    )


def augment_draft_with_plan(run_dir: Path, plan: dict[str, object]) -> None:
    files = bundle_files(run_dir)
    plan_file = files["plan"]
    write_json(plan_file, {**plan, "planned_at": utc_now()}, force=True)
    prompt = files["prompt"].read_text(encoding="utf-8")
    context = files["context"].read_text(encoding="utf-8")
    plan_text = json.dumps(plan, ensure_ascii=False, indent=2)
    files["prompt"].write_text(
        prompt.rstrip() + "\n\n## Approved Execution Plan\n\nFollow the plan's functions and constraints, but write living scenes rather than paraphrasing its JSON.\n",
        encoding="utf-8",
        newline="\n",
    )
    files["context"].write_text(
        context.rstrip() + "\n\n## Chapter Execution Plan\n\n```json\n" + plan_text + "\n```\n",
        encoding="utf-8",
        newline="\n",
    )
    append_event(run_dir, "chapter_plan_completed", "planned", scene_count=len(plan.get("scenes") or []))


def augment_draft_with_causal_simulation(run_dir: Path, causal: dict[str, object]) -> None:
    files = bundle_files(run_dir)
    prompt = files["prompt"].read_text(encoding="utf-8")
    context = sanitize_theme_answers(files["context"].read_text(encoding="utf-8"), causal)
    files["prompt"].write_text(
        prompt.rstrip()
        + "\n\n## Causal Contract\n\nWrite consequences and transferred costs as lived action. Do not convert theme questions into narrator answers.\n",
        encoding="utf-8",
        newline="\n",
    )
    files["context"].write_text(
        context.rstrip() + "\n\n## Causal Simulation\n\n```json\n" + json.dumps(causal, ensure_ascii=False, indent=2) + "\n```\n",
        encoding="utf-8",
        newline="\n",
    )
    append_event(run_dir, "causal_simulation_completed", "simulated", event_count=len(causal.get("event_graph") or []))


def scene_target_chars(plan: dict[str, object], total_target: int) -> list[int]:
    scenes = [item for item in plan.get("scenes") or [] if isinstance(item, dict)]
    if not scenes:
        return []
    budget = max(int(total_target), len(scenes))

    def allocate(weights: list[float]) -> list[int]:
        minimum = 50 if budget >= len(weights) * 50 else 1
        remaining = budget - minimum * len(weights)
        total_weight = sum(weights)
        raw_extras = [remaining * weight / total_weight for weight in weights]
        extras = [int(value) for value in raw_extras]
        unassigned = remaining - sum(extras)
        order = sorted(
            range(len(weights)),
            key=lambda index: raw_extras[index] - extras[index],
            reverse=True,
        )
        for index in order[:unassigned]:
            extras[index] += 1
        return [minimum + value for value in extras]

    explicit: list[int] = []
    for item in scenes:
        try:
            explicit.append(int(item.get("target_chars") or 0))
        except (TypeError, ValueError):
            explicit.append(0)
    if all(value > 0 for value in explicit):
        if sum(explicit) == budget:
            return explicit
        return allocate([float(value) for value in explicit])
    weights: list[float] = []
    for item in scenes:
        try:
            weight = float(item.get("weight") or 1.0)
        except (TypeError, ValueError):
            weight = 1.0
        weights.append(max(0.1, weight))
    return allocate(weights)


def prepare_scene_writer_bundle(
    run_dir: Path,
    *,
    chapter_file: Path,
    scene: dict[str, object],
    scene_target: int,
    chapter_plan: dict[str, object],
    contract: dict[str, object],
    causal_simulation: dict[str, object],
    context: ProjectContextBundle,
    previous_scene_tail: str,
    provider: str,
    model: str,
    force: bool,
) -> Path:
    scene_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(scene.get("scene_id") or "scene"))
    directory = run_dir / "scene_writer" / scene_id
    files = (directory / "request.json", directory / "prompt.md", directory / "context_pack.md")
    if not force:
        existing = [path for path in files if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    directory.mkdir(parents=True, exist_ok=True)
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(chapter_file.resolve()),
        "role": "scene-writer",
        "task": "draft-scene",
        "book": chapter_file.parent.name,
        "chapter": chapter_file.stem,
        "scene_id": str(scene.get("scene_id") or scene_id),
        "provider": provider,
        "model": model,
        "safety": {"overwrites_manuscript": False, "writes_staging_output": True, "requires_human_apply": True},
    }
    prompt = "\n".join(
        [
            "# FictionOps State-aware Scene Writer",
            "",
            f"Write only scene {scene.get('scene_id')} as continuous novel prose.",
            f"Aim for about {scene_target} non-whitespace characters; scene rhythm may justify moderate variation.",
            "Enter from the declared entry state and earn the exit state through visible action. Do not merely announce the state change.",
            "Respect the viewpoint, information boundary, causal cost, timeline, quantity, and object-state ledger.",
            "Use the previous scene tail only for continuity of motion, voice, and physical state. Do not repeat or summarize it.",
            "Do not add a chapter or scene heading. Do not output notes, analysis, labels, or Markdown fences.",
        ]
    ).rstrip() + "\n"
    context_text = "\n\n".join(
        [
            "# Scene Execution Context",
            "## Scene Specification\n\n```json\n" + json.dumps(scene, ensure_ascii=False, indent=2) + "\n```",
            "## Chapter Engine And Plan\n\n```json\n" + json.dumps(chapter_plan.get("engine") or {}, ensure_ascii=False, indent=2) + "\n```",
            "## Causal Simulation\n\n```json\n" + json.dumps(causal_simulation, ensure_ascii=False, indent=2) + "\n```",
            "## Chapter Contract And Fact Ledger\n\n```json\n" + json.dumps(contract, ensure_ascii=False, indent=2) + "\n```",
            "## Previous Scene Tail\n\n" + (previous_scene_tail.rstrip() or "This is the first scene."),
            "## Retrieved Project Context\n\n" + render_project_context(context).rstrip(),
        ]
    ).rstrip() + "\n"
    write_json(files[0], request, force=force)
    files[1].write_text(prompt, encoding="utf-8", newline="\n")
    files[2].write_text(context_text, encoding="utf-8", newline="\n")
    return directory


def execute_scene_bundle(
    directory: Path,
    *,
    budget: ModelExecutionBudget,
    runner: list[str],
    timeout_seconds: int,
    target_chars: int,
    force: bool,
) -> tuple[list[AgentExecReport], str]:
    reports: list[AgentExecReport] = []
    report = execute_model_bundle(
        budget,
        directory,
        role="scene-writer",
        command=runner,
        output_name="output.md",
        timeout_seconds=timeout_seconds,
        force=force,
        dry_run=False,
    )
    reports.append(report)
    prose = Path(report.output_file).read_text(encoding="utf-8").strip()
    nonspace = sum(1 for char in prose if not char.isspace())
    for length_retry in range(1, 3):
        minimum = target_chars
        maximum = round(target_chars * 1.35)
        if minimum <= nonspace <= maximum:
            break
        prompt_file = directory / "prompt.md"
        context_file = directory / "context_pack.md"
        if nonspace < minimum:
            instruction = (
                f"The previous scene has {nonspace} non-whitespace characters and materially under-runs its {target_chars}-character allocation. "
                f"Return a complete rewritten scene aiming for {round(target_chars * 1.1)} characters. Expand through concrete action, resistance, sensory consequence, and character-specific behavior."
            )
        else:
            instruction = (
                f"The previous scene has {nonspace} non-whitespace characters and materially exceeds its {target_chars}-character allocation. "
                f"Return a complete rewritten scene aiming for {round(target_chars * 1.05)} characters. Remove repeated gestures, restated sensory details, explanatory conclusions, and duplicated beats while preserving the full causal action."
            )
        prompt_file.write_text(
            prompt_file.read_text(encoding="utf-8").rstrip()
            + f"\n\n## Scene Length Repair {length_retry}\n\n{instruction} Do not add new canon or padding. Preserve every state code and required event.\n",
            encoding="utf-8",
            newline="\n",
        )
        previous_label = "Under-length" if nonspace < minimum else "Over-length"
        context_file.write_text(
            context_file.read_text(encoding="utf-8").rstrip() + f"\n\n## {previous_label} Previous Scene\n\n" + prose + "\n",
            encoding="utf-8",
            newline="\n",
        )
        report = execute_model_bundle(
            budget,
            directory,
            role="scene-writer-length-repair",
            command=runner,
            output_name=f"output.length_retry{length_retry}.md",
            timeout_seconds=timeout_seconds,
            force=True,
            dry_run=False,
        )
        reports.append(report)
        prose = Path(report.output_file).read_text(encoding="utf-8").strip()
        nonspace = sum(1 for char in prose if not char.isspace())
    return reports, prose


def execute_scenes(
    run_dir: Path,
    *,
    chapter_file: Path,
    engine_text: str,
    chapter_plan: dict[str, object],
    contract: dict[str, object],
    causal_simulation: dict[str, object],
    context: ProjectContextBundle,
    total_target: int,
    provider: str,
    model: str,
    runner: list[str],
    budget: ModelExecutionBudget,
    timeout_seconds: int,
    force: bool,
) -> tuple[list[AgentExecReport], str]:
    scenes = [item for item in chapter_plan.get("scenes") or [] if isinstance(item, dict)]
    targets = scene_target_chars(chapter_plan, total_target)
    outputs: list[str] = []
    execs: list[AgentExecReport] = []
    records: list[dict[str, object]] = []
    previous_tail = ""
    for scene, target in zip(scenes, targets):
        directory = prepare_scene_writer_bundle(
            run_dir,
            chapter_file=chapter_file,
            scene=scene,
            scene_target=target,
            chapter_plan=chapter_plan,
            contract=contract,
            causal_simulation=causal_simulation,
            context=context,
            previous_scene_tail=previous_tail,
            provider=provider,
            model=model,
            force=force,
        )
        scene_reports, prose = execute_scene_bundle(
            directory,
            budget=budget,
            runner=runner,
            timeout_seconds=timeout_seconds,
            target_chars=target,
            force=force,
        )
        report = scene_reports[-1]
        if not prose:
            raise ValueError(f"scene writer produced empty prose for {scene.get('scene_id')}")
        if first_heading(prose) is not None or starts_with_wrapper(prose):
            raise ValueError(f"scene writer violated prose-only output contract for {scene.get('scene_id')}")
        outputs.append(prose)
        execs.extend(scene_reports)
        nonspace = sum(1 for char in prose if not char.isspace())
        records.append(
            {
                "scene_id": scene.get("scene_id"),
                "target_chars": target,
                "actual_chars": nonspace,
                "entry_state": scene.get("entry_state") or {},
                "exit_state": scene.get("exit_state") or {},
                "output_file": report.output_file,
                "sha256": sha256_text(prose + "\n"),
            }
        )
        previous_tail = prose[-3000:]
        append_event(run_dir, "scene_drafted", "drafting", scene_id=scene.get("scene_id"), target_chars=target, actual_chars=nonspace)
    title = expected_title_from_engine(engine_text, chapter_file) or chapter_file.stem
    chapter_match = re.match(r"^(第\s*\d+\s*章)", chapter_file.stem)
    heading = f"{chapter_match.group(1)} {title}" if chapter_match and title not in chapter_match.group(1) else title
    candidate = f"# {heading}\n\n" + "\n\n".join(outputs) + "\n"
    write_json(
        bundle_files(run_dir)["scene_execution"],
        {"schema": "fictionops.scene_execution.v1", "mode": "scene_by_scene", "scenes": records, "assembled_sha256": sha256_text(candidate)},
        force=True,
    )
    (run_dir / "output.md").write_text(candidate, encoding="utf-8", newline="\n")
    return execs, "output.md"


def scene_rewrite_evidence(
    verification: dict[str, object],
    evaluation: dict[str, object],
    adversarial: dict[str, object],
    scene_id: str,
    scene_prose: str,
) -> dict[str, object]:
    def grounded(item: dict[str, object]) -> bool:
        evidence = item.get("evidence")
        values = evidence if isinstance(evidence, list) else [evidence]
        compact_scene = re.sub(r"\s+", "", scene_prose)
        for value in values:
            compact = re.sub(r"\s+", "", str(value or "")).strip("'\"‘’“”` ")
            if len(compact) >= 4 and compact in compact_scene:
                return True
            for quote in re.findall(r"[‘'\"“]([^’'\"”]{4,160})[’'\"”]", str(value or "")):
                if re.sub(r"\s+", "", quote) in compact_scene:
                    return True
        return False

    return {
        "blocking_failures": verification.get("blocking_failures") or [],
        "evaluation_issues": [
            item for item in evaluation.get("issues") or [] if isinstance(item, dict) and grounded(item)
        ],
        "failed_evaluation_constraints": [
            item
            for item in evaluation.get("constraint_checks") or []
            if isinstance(item, dict) and str(item.get("status")) != "pass" and grounded(item)
        ],
        "adversarial_issues": [
            item for item in adversarial.get("issues") or [] if isinstance(item, dict) and grounded(item)
        ],
        "scene_check": next(
            (
                item
                for item in adversarial.get("scene_state_checks") or []
                if isinstance(item, dict) and str(item.get("scene_id")) == scene_id
            ),
            None,
        ),
    }


def select_scene_ids_for_rewrite(
    execution: dict[str, object],
    verification: dict[str, object],
    evaluation: dict[str, object],
    adversarial: dict[str, object],
) -> tuple[set[str], dict[str, list[str]]]:
    records = [item for item in execution.get("scenes") or [] if isinstance(item, dict)]
    all_ids = [str(item.get("scene_id") or "") for item in records if str(item.get("scene_id") or "")]
    selected: set[str] = set()
    reasons: dict[str, list[str]] = {scene_id: [] for scene_id in all_ids}

    for item in adversarial.get("scene_state_checks") or []:
        if not isinstance(item, dict) or str(item.get("status")) == "pass":
            continue
        scene_id = str(item.get("scene_id") or "")
        if scene_id in reasons:
            selected.add(scene_id)
            reasons[scene_id].append("failed_scene_state_check")

    evidence_items: list[tuple[str, dict[str, object]]] = []
    for source, values in (
        ("evaluation_issue", evaluation.get("issues") or []),
        ("evaluation_constraint", evaluation.get("constraint_checks") or []),
        ("adversarial_issue", adversarial.get("issues") or []),
        ("adversarial_constraint", adversarial.get("constraint_checks") or []),
    ):
        for item in values:
            if not isinstance(item, dict):
                continue
            if "constraint" in source and str(item.get("status")) == "pass":
                continue
            evidence_items.append((source, item))

    for record in records:
        scene_id = str(record.get("scene_id") or "")
        output_file = Path(str(record.get("output_file") or ""))
        if not scene_id or not output_file.exists():
            continue
        prose = output_file.read_text(encoding="utf-8")
        compact_prose = re.sub(r"\s+", "", prose)
        for source, item in evidence_items:
            evidence = item.get("evidence")
            values = evidence if isinstance(evidence, list) else [evidence]
            matched = False
            for value in values:
                text = str(value or "")
                candidates = [text] + re.findall(r"[‘'\"“]([^’'\"”]{4,160})[’'\"”]", text)
                if any(
                    len(compact) >= 4 and compact in compact_prose
                    for compact in (re.sub(r"\s+", "", candidate).strip("'\"‘’“”` ") for candidate in candidates)
                ):
                    matched = True
                    break
            if matched:
                selected.add(scene_id)
                reasons[scene_id].append(source)

    chapter_wide_failures = {
        "candidate_nonempty",
        "chapter_output_only",
        "chapter_heading_present",
        "engine_title_present",
        "minimum_draft_size",
        "placeholder_removed",
    }
    if chapter_wide_failures.intersection(str(item) for item in verification.get("blocking_failures") or []):
        selected.update(all_ids)
        for scene_id in all_ids:
            reasons[scene_id].append("chapter_wide_static_failure")
    if not selected:
        selected.update(all_ids)
        for scene_id in all_ids:
            reasons[scene_id].append("unlocalized_blocking_failure")
    return selected, {scene_id: values for scene_id, values in reasons.items() if scene_id in selected}


def rewrite_scenes(
    run_dir: Path,
    *,
    attempt: int,
    chapter_file: Path,
    engine_text: str,
    chapter_plan: dict[str, object],
    contract: dict[str, object],
    causal_simulation: dict[str, object],
    verification: dict[str, object],
    evaluation: dict[str, object],
    adversarial: dict[str, object],
    provider: str,
    model: str,
    runner: list[str],
    budget: ModelExecutionBudget,
    timeout_seconds: int,
) -> tuple[list[AgentExecReport], str]:
    execution = json.loads(bundle_files(run_dir)["scene_execution"].read_text(encoding="utf-8"))
    records_by_id = {
        str(item.get("scene_id")): item
        for item in execution.get("scenes") or []
        if isinstance(item, dict)
    }
    scenes = [item for item in chapter_plan.get("scenes") or [] if isinstance(item, dict)]
    outputs: list[str] = []
    execs: list[AgentExecReport] = []
    rewritten_records: list[dict[str, object]] = []
    selected_scene_ids, selection_reasons = select_scene_ids_for_rewrite(
        execution,
        verification,
        evaluation,
        adversarial,
    )
    previous_tail = ""
    for index, scene in enumerate(scenes):
        scene_id = str(scene.get("scene_id") or f"S{index + 1}")
        original_record = records_by_id.get(scene_id)
        if original_record is None:
            raise ValueError(f"scene rewrite is missing execution record for {scene_id}")
        original_file = Path(str(original_record.get("output_file") or ""))
        original_prose = original_file.read_text(encoding="utf-8").strip()
        planned_target = int(original_record.get("target_chars") or 0)
        rewrite_target = max(planned_target, 50)
        if scene_id not in selected_scene_ids:
            outputs.append(original_prose)
            previous_tail = original_prose[-3000:]
            rewritten_records.append(
                {
                    **original_record,
                    "rewritten": False,
                    "selection_reasons": [],
                }
            )
            append_event(run_dir, "scene_preserved", "retrying", retry_number=attempt, scene_id=scene_id)
            continue
        next_scene = scenes[index + 1] if index + 1 < len(scenes) else None
        directory = run_dir / "scene_rewriter" / f"retry_{attempt}" / re.sub(r"[^A-Za-z0-9_.-]+", "_", scene_id)
        directory.mkdir(parents=True, exist_ok=True)
        request = {
            "schema": "fictionops.agent_run_request.v1",
            "execution_mode": "prepare_only",
            "target": str(chapter_file.resolve()),
            "role": "scene-rewriter",
            "task": "rewrite-scene",
            "book": chapter_file.parent.name,
            "chapter": chapter_file.stem,
            "scene_id": scene_id,
            "provider": provider,
            "model": model,
            "safety": {"overwrites_manuscript": False, "writes_staging_output": True, "requires_human_apply": True},
        }
        prompt = "\n".join(
            [
                "# FictionOps Evidence-guided Scene Rewriter",
                "",
                f"Rewrite only scene {scene_id} as continuous novel prose.",
                f"Preserve at least about {rewrite_target} non-whitespace characters unless removing a proven repetition; do not solve quality issues by compressing the scene.",
                "Keep the exact entry/exit state codes and causal events. The next scene must still be able to enter from its declared state.",
                "Treat review findings as hypotheses supported by quotations, not as higher authority than the engine. A specific required event overrides a broad prohibition: an accidental weak response is not a skilled display merely because both involve the same object.",
                "Fix supported knowledge leakage, explanatory narration, mechanical contrast syntax, and seam problems while preserving successful concrete action.",
                "Use the previous rewritten scene tail for continuity, but do not repeat it.",
                "Output only the revised scene prose. No heading, notes, analysis, labels, or Markdown fences.",
            ]
        ).rstrip() + "\n"
        evidence = scene_rewrite_evidence(verification, evaluation, adversarial, scene_id, original_prose)
        context = "\n\n".join(
            [
                "# Scene Rewrite Context",
                "## Scene Specification\n\n```json\n" + json.dumps(scene, ensure_ascii=False, indent=2) + "\n```",
                "## Next Scene Entry Contract\n\n```json\n" + json.dumps((next_scene or {}).get("entry_state") or {}, ensure_ascii=False, indent=2) + "\n```",
                "## Causal Contract\n\n```json\n" + json.dumps(causal_simulation, ensure_ascii=False, indent=2) + "\n```",
                "## Story Contract\n\n```json\n" + json.dumps(contract, ensure_ascii=False, indent=2) + "\n```",
                "## Review Evidence\n\n```json\n" + json.dumps(evidence, ensure_ascii=False, indent=2) + "\n```",
                "## Previous Rewritten Scene Tail\n\n" + (previous_tail or "This is the first scene."),
                "## Original Scene\n\n" + original_prose,
            ]
        ).rstrip() + "\n"
        write_json(directory / "request.json", request, force=True)
        (directory / "prompt.md").write_text(prompt, encoding="utf-8", newline="\n")
        (directory / "context_pack.md").write_text(context, encoding="utf-8", newline="\n")
        scene_reports, prose = execute_scene_bundle(
            directory,
            budget=budget,
            runner=runner,
            timeout_seconds=timeout_seconds,
            target_chars=rewrite_target,
            force=True,
        )
        report = scene_reports[-1]
        if not prose or first_heading(prose) is not None or starts_with_wrapper(prose):
            raise ValueError(f"scene rewriter violated prose-only output contract for {scene_id}")
        nonspace = sum(1 for char in prose if not char.isspace())
        outputs.append(prose)
        execs.extend(scene_reports)
        previous_tail = prose[-3000:]
        rewritten_records.append(
            {
                "scene_id": scene_id,
                "target_chars": rewrite_target,
                "actual_chars": nonspace,
                "entry_state": scene.get("entry_state") or {},
                "exit_state": scene.get("exit_state") or {},
                "output_file": report.output_file,
                "sha256": sha256_text(prose + "\n"),
                "rewritten": True,
                "selection_reasons": selection_reasons.get(scene_id, []),
            }
        )
        append_event(run_dir, "scene_rewritten", "retrying", retry_number=attempt, scene_id=scene_id, target_chars=rewrite_target, actual_chars=nonspace)
    title = expected_title_from_engine(engine_text, chapter_file) or chapter_file.stem
    chapter_match = re.match(r"^(第\s*\d+\s*章)", chapter_file.stem)
    heading = f"{chapter_match.group(1)} {title}" if chapter_match and title not in chapter_match.group(1) else title
    candidate = f"# {heading}\n\n" + "\n\n".join(outputs) + "\n"
    output_name = f"output.scene_retry{attempt}.md"
    (run_dir / output_name).write_text(candidate, encoding="utf-8", newline="\n")
    write_json(
        run_dir / f"scene_execution.retry{attempt}.json",
        {
            "schema": "fictionops.scene_execution.v1",
            "mode": "scene_by_scene_rewrite",
            "retry": attempt,
            "selected_scene_ids": sorted(selected_scene_ids),
            "selection_reasons": selection_reasons,
            "scenes": rewritten_records,
            "assembled_sha256": sha256_text(candidate),
        },
        force=True,
    )
    return execs, output_name


def merge_draft_evaluation(verification: dict[str, object], evaluation: dict[str, object]) -> dict[str, object]:
    dimensions = evaluation.get("dimensions") or []
    failed = [
        str(item.get("name"))
        for item in dimensions
        if isinstance(item, dict) and str(item.get("status")) != "pass"
    ]
    constraint_checks = evaluation.get("constraint_checks") or []
    failed_constraints = [
        str(item.get("id"))
        for item in constraint_checks
        if isinstance(item, dict) and str(item.get("status")) != "pass"
    ]
    passed = str(evaluation.get("verdict")) == "pass" and not failed
    checks = list(verification.get("checks") or [])
    checks = [item for item in checks if item.get("name") != "draft_semantic_dimensions"]
    checks.append(
        {
            "name": "draft_semantic_dimensions",
            "passed": passed,
            "blocking": True,
            "evidence": {"verdict": evaluation.get("verdict"), "failed_or_uncertain": failed, "summary": evaluation.get("summary")},
        }
    )
    checks = [item for item in checks if item.get("name") != "draft_plan_constraints"]
    checks.append(
        {
            "name": "draft_plan_constraints",
            "passed": not failed_constraints,
            "blocking": True,
            "evidence": {"failed_or_uncertain": failed_constraints, "checks": constraint_checks},
        }
    )
    failures = [item["name"] for item in checks if item.get("blocking") and not item.get("passed")]
    return {
        **verification,
        "status": "ready_for_approval" if not failures else "needs_revision_attention",
        "ready_for_approval": not failures,
        "checks": checks,
        "blocking_failures": failures,
        "draft_evaluation": evaluation,
        "verified_at": utc_now(),
    }


def archive_attempt(run_dir: Path, attempt: int) -> None:
    files = bundle_files(run_dir)
    for name in ("prompt", "context", "candidate", "diff", "verification", "evaluation", "adversarial_review", "deterministic_story_audit"):
        path = files[name]
        if path.exists():
            suffix = path.suffix
            destination = path.with_name(f"{path.stem}.v{attempt}{suffix}")
            if destination.exists():
                raise FileExistsError(destination)
            shutil.copy2(path, destination)
    receipt = run_dir / "execution.json"
    if receipt.exists():
        shutil.copy2(receipt, run_dir / f"execution.v{attempt}.json")
        receipt.unlink()


def prepare_write_retry(run_dir: Path, verification: dict[str, object], evaluation: dict[str, object], attempt: int) -> str:
    files = bundle_files(run_dir)
    archive_attempt(run_dir, attempt)
    prompt = files["prompt"].read_text(encoding="utf-8")
    context = files["context"].read_text(encoding="utf-8")
    candidate = files["candidate"].read_text(encoding="utf-8")
    files["prompt"].write_text(
        prompt.rstrip()
        + "\n\n## Targeted Rewrite\n\nThe previous draft failed verification. Return a complete rewritten chapter that fixes only the evidenced failures.\n"
        + json.dumps({"verification": verification, "evaluation": evaluation}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    files["context"].write_text(
        context.rstrip() + "\n\n## Previous Draft\n\n" + candidate.rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    append_event(run_dir, "draft_rewrite_prepared", "retrying", retry_number=attempt, failures=verification.get("blocking_failures"))
    return f"output.retry{attempt}.md"


def write_post_draft_artifacts(run_dir: Path, evaluation: dict[str, object]) -> None:
    files = bundle_files(run_dir)
    retrospective = evaluation.get("retrospective") if isinstance(evaluation.get("retrospective"), dict) else {}
    lines = [
        "# FictionOps Chapter Retrospective Draft",
        "",
        f"- Chapter change: {retrospective.get('chapter_change') or '-'}",
        f"- Residue: {retrospective.get('residue') or '-'}",
        "",
        "## Character Updates",
        "",
    ]
    lines.extend(f"- {item}" for item in retrospective.get("character_updates") or [])
    lines.extend(["", "## Information Updates", ""])
    lines.extend(f"- {item}" for item in retrospective.get("information_updates") or [])
    lines.extend(["", "## Foreshadowing Updates", ""])
    lines.extend(f"- {item}" for item in retrospective.get("foreshadowing_updates") or [])
    files["retrospective"].write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    write_json(
        files["canon_sync"],
        {
            "schema": "fictionops.canon_sync_suggestions.v1",
            "generated_at": utc_now(),
            "suggestions": evaluation.get("canon_sync_suggestions") or [],
            "requires_human_acceptance": True,
        },
        force=True,
    )


def next_actions(report: AgentWriteWorkflowReport) -> list[str]:
    if report.ready_for_approval:
        return [
            f"Inspect `{Path(report.run_dir) / 'candidate.md'}`, `changes.diff`, and `verification.json`.",
            f"Review `{Path(report.run_dir) / 'retrospective.draft.md'}` and `canon_sync_suggestions.json`.",
            f"Run `fictionops agent-accept-revision {report.run_dir} --dry-run`, then accept only if the chapter should enter the manuscript.",
        ]
    if report.executed:
        return [f"Inspect `{Path(report.run_dir) / 'verification.json'}`; the candidate is not eligible for acceptance."]
    return [f"Run the prepared bundle through a model runner to draft `{report.chapter_file}`."]


def build_agent_write_workflow(
    chapter: Path,
    *,
    engine: Path,
    outline: Path | None = None,
    context_files: list[Path] | None = None,
    out_dir: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    runner: list[str] | None = None,
    timeout_seconds: int = 600,
    max_model_calls: int = 32,
    max_runtime_seconds: int = 3600,
    max_total_tokens: int | None = None,
    max_cost: float | None = None,
    cost_currency: str = "USD",
    min_chars: int | None = None,
    max_retries: int = 1,
    max_context_files: int = 24,
    max_context_chars: int = 100000,
    use_memory: bool = True,
    use_causal_simulation: bool = True,
    use_adversarial_review: bool = True,
    scene_by_scene: bool = False,
    force: bool = False,
    force_output: bool = False,
    dry_run: bool = False,
    resume: bool = False,
) -> AgentWriteWorkflowReport:
    if not engine.exists() or not engine.is_file():
        raise FileNotFoundError(f"chapter engine does not exist: {engine}")
    if outline and (not outline.exists() or not outline.is_file()):
        raise FileNotFoundError(f"outline does not exist: {outline}")
    if max_retries < 0 or max_retries > 2:
        raise ValueError("--max-retries must be between 0 and 2")
    if max_model_calls < 1:
        raise ValueError("--max-model-calls must be greater than zero")
    if max_runtime_seconds < 1:
        raise ValueError("--max-runtime-seconds must be greater than zero")
    chapter_file = chapter.expanduser().resolve()
    engine_file = engine.expanduser().resolve()
    outline_file = outline.expanduser().resolve() if outline else None
    source_existed = chapter_file.exists()
    if source_existed and not chapter_file.is_file():
        raise ValueError(f"target chapter is not a file: {chapter_file}")
    source_text = chapter_file.read_text(encoding="utf-8") if source_existed else ""
    if source_existed and not placeholder_source(source_text) and not resume:
        raise ValueError("target chapter already contains substantive prose; use agent-revise-workflow instead")
    engine_text = engine_file.read_text(encoding="utf-8")
    outline_text_for_target = outline_file.read_text(encoding="utf-8") if outline_file else ""
    target_chars = target_chars_from_engine(engine_text) or target_chars_from_outline(outline_text_for_target, chapter_file)
    effective_min = min_chars if min_chars is not None else max(200, target_chars - 200) if target_chars else 200
    if effective_min < 1:
        raise ValueError("--min-chars must be positive")
    run_dir = resolve_run_dir(chapter_file, out_dir)
    root = discover_project_root(chapter_file)
    model_config = build_model_config_report(root)
    selected_provider = provider or model_config.provider
    selected_model = model or model_config.drafting_model
    selected_planning_model = model or model_config.planning_model
    selected_evaluation_model = model or model_config.audit_model
    memory_query: dict[str, object] = {
        "schema": "fictionops.memory_query.v1",
        "project_root": str(root),
        "query": "",
        "record_count": 0,
        "included_chars": 0,
        "max_items": 0,
        "max_chars": 0,
        "results": [],
    }
    memory_budget = min(30000, max(2000, max_context_chars // 3)) if use_memory else 0
    if use_memory:
        index_payload = build_memory_index(root, write=not dry_run)
        memory_query = query_memory(
            root,
            query="\n".join((chapter_file.stem, engine_text, outline_text_for_target)),
            max_items=max(8, min(24, max_context_files)),
            max_chars=memory_budget,
            write_index=not dry_run,
            index_payload=index_payload,
        )
    context = compile_project_context(
        chapter_file,
        task="draft",
        source_text=engine_text,
        engine_file=engine_file,
        outline_file=outline_file,
        explicit_files=context_files,
        max_files=max_context_files,
        max_total_chars=max(1, max_context_chars - memory_budget),
    )
    if use_memory:
        context = augment_context_with_memory(context, memory_query, max_total_chars=max_context_chars)
    source_sha = sha256_text(source_text)
    session_id = session_id_for_write(chapter_file, source_sha, sha256_text(engine_text))
    files = [AgentWriteWorkflowFile(kind=name, path=str(path), written=False) for name, path in bundle_files(run_dir).items()]
    prepared = False
    executed = False
    verification: dict[str, object] | None = None
    evaluation: dict[str, object] | None = None
    draft_exec = None
    scene_execs: list[AgentExecReport] = []
    evaluator_exec = None
    planner_exec = None
    causal_exec = None
    adversarial_exec = None
    chapter_plan: dict[str, object] | None = None
    causal_result: dict[str, object] | None = None
    adversarial_result: dict[str, object] | None = None
    contract: dict[str, object] | None = None
    retry_count = 0
    evaluator_calls = 0
    planner_calls = 0
    causal_calls = 0
    adversarial_calls = 0
    budget: ModelExecutionBudget | None = None
    stop_reason = "write_bundle_ready_for_runner"
    checkpoint: dict[str, object] | None = None
    if resume:
        if dry_run:
            raise ValueError("resume cannot be combined with dry-run")
        resumed_session, checkpoint = validate_checkpoint_for_resume(run_dir)
        if str(resumed_session.get("workflow")) != "chapter_write":
            raise ValueError("resume target is not a chapter-write session")
        source_sha = str(resumed_session.get("source_sha256") or source_sha)
        session_id = str(resumed_session.get("session_id") or session_id)
        prepared = True
        files = [AgentWriteWorkflowFile(kind=name, path=str(path), written=path.exists()) for name, path in bundle_files(run_dir).items()]
    elif not dry_run:
        source_sha, session_id, files = write_initial_bundle(
            run_dir,
            chapter_file=chapter_file,
            source_text=source_text,
            source_existed=source_existed,
            engine_file=engine_file,
            engine_text=engine_text,
            outline_file=outline_file,
            context=context,
            provider=selected_provider,
            model=selected_model,
            min_chars=effective_min,
            workflow_options={
                "outline_file": str(outline_file) if outline_file else None,
                "min_chars": effective_min,
                "max_retries": max_retries,
                "max_context_files": max_context_files,
                "max_context_chars": max_context_chars,
                "use_memory": use_memory,
                "use_causal_simulation": use_causal_simulation,
                "use_adversarial_review": use_adversarial_review,
                "scene_by_scene": scene_by_scene,
            },
            force=force,
        )
        prepared = True
        write_json(bundle_files(run_dir)["memory_query"], memory_query, force=True)
        bundle_files(run_dir)["memory_context"].write_text(render_memory_query(memory_query), encoding="utf-8", newline="\n")
        append_trajectory(
            run_dir,
            kind="context_selected",
            phase="context_ready",
            actor="context_compiler",
            observation={
                "query": memory_query.get("query"),
                "memory_records": memory_query.get("record_count"),
                "included_chars": context.included_chars,
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
                    for item in context.items
                ],
            ],
            authority="controller",
        )
    if runner and not dry_run:
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
        outline_text = outline_file.read_text(encoding="utf-8") if outline_file else ""
        memory_text = render_memory_query(memory_query)
        resume_phase = str((checkpoint or {}).get("phase") or "context_ready")
        supported_resume_phases = {"context_ready", "causal_ready", "plan_ready", "draft_ready"}
        if resume and resume_phase not in supported_resume_phases:
            raise ValueError(f"chapter-write resume does not support checkpoint phase yet: {resume_phase}")
        reuse_causal = bool(
            resume
            and resume_phase in {"causal_ready", "plan_ready", "draft_ready"}
            and bundle_files(run_dir)["causal_simulation"].is_file()
        )
        if reuse_causal:
            causal_result = json.loads(bundle_files(run_dir)["causal_simulation"].read_text(encoding="utf-8"))
            causal_issues = validate_causal_simulation(causal_result)
            if causal_issues or causal_result.get("status") != "ready":
                raise RuntimeError("stored causal checkpoint is invalid: " + json.dumps(causal_issues, ensure_ascii=False))
        elif use_causal_simulation:
            causal_dir = prepare_causal_simulation_bundle(
                run_dir,
                target_file=chapter_file,
                engine_text=engine_text,
                outline_text=outline_text,
                memory_text=memory_text,
                provider=selected_provider,
                model=selected_planning_model,
                force=force or resume,
            )
            causal_exec = execute_model_bundle(
                budget,
                causal_dir,
                role="causal-simulator",
                command=runner,
                output_name="output.md",
                timeout_seconds=timeout_seconds,
                force=force_output or force or resume,
                dry_run=False,
            )
            causal_calls = 1
            causal_output_text = Path(causal_exec.output_file).read_text(encoding="utf-8")
            causal_issues: list[dict[str, object]] = []
            try:
                causal_result = parse_causal_simulation(causal_output_text)
                causal_issues = validate_causal_simulation(causal_result)
            except ValueError as exc:
                causal_result = None
                causal_issues = [{"kind": "causal_schema_error", "evidence": str(exc)}]
            for causal_retry in range(1, 4):
                if not causal_issues:
                    break
                write_json(
                    run_dir / f"causal_simulation.rejected.v{causal_retry}.json",
                    {"schema": "fictionops.rejected_causal_simulation.v1", "issues": causal_issues, "raw_output": causal_output_text},
                    force=True,
                )
                prepare_causal_retry(causal_dir, causal_output_text, causal_issues)
                causal_exec = execute_model_bundle(
                    budget,
                    causal_dir,
                    role="causal-contract-repair",
                    command=runner,
                    output_name=f"output.retry{causal_retry}.md",
                    timeout_seconds=timeout_seconds,
                    force=True,
                    dry_run=False,
                )
                causal_calls += 1
                causal_output_text = Path(causal_exec.output_file).read_text(encoding="utf-8")
                try:
                    causal_result = parse_causal_simulation(causal_output_text)
                    causal_issues = validate_causal_simulation(causal_result)
                except ValueError as exc:
                    causal_result = None
                    causal_issues = [{"kind": "causal_schema_error", "evidence": str(exc)}]
            if causal_issues or causal_result is None:
                raise RuntimeError(
                    "causal simulation still violates the contract after three repairs: "
                    + json.dumps(causal_issues, ensure_ascii=False)
                )
            if causal_result.get("status") != "ready":
                raise RuntimeError(
                    "causal simulation is blocked by missing mechanics: "
                    + json.dumps(causal_result.get("missing_mechanics") or [], ensure_ascii=False)
                )
            write_json(bundle_files(run_dir)["causal_simulation"], causal_result, force=True)
            augment_draft_with_causal_simulation(run_dir, causal_result)
            write_agent_checkpoint(
                run_dir,
                phase="causal_ready",
                next_action="run_chapter_planner",
                artifacts=[bundle_files(run_dir)["causal_simulation"]],
            )
        else:
            causal_result = {
                "schema": "fictionops.causal_simulation.v1",
                "status": "ready",
                "stakeholders": [],
                "event_graph": [{"id": "legacy", "preconditions": [], "action": "follow chapter engine", "immediate_effects": [], "cost_transfer": [], "observable_evidence": [], "unresolved": []}],
                "hard_constraints": {
                    "pov_whitelist": [], "forbidden_pov": [], "knowledge_limits": [], "theme_questions": [],
                    "forbidden_conclusions": [], "special_passage_limits": [], "quantitative_rules": [], "unit_conversions": {},
                    "timeline_rules": [], "object_state_rules": [],
                },
                "missing_mechanics": [],
                "summary": "Causal simulation disabled by caller.",
            }
            write_json(bundle_files(run_dir)["causal_simulation"], causal_result, force=True)
        execution_engine_text = sanitize_theme_answers(engine_text, causal_result)
        model_context = sanitized_context_bundle(context, causal_result)
        memory_text = sanitize_theme_answers(memory_text, causal_result)
        reuse_plan = bool(
            resume
            and resume_phase in {"plan_ready", "draft_ready"}
            and bundle_files(run_dir)["plan"].is_file()
        )
        if reuse_plan:
            chapter_plan = json.loads(bundle_files(run_dir)["plan"].read_text(encoding="utf-8"))
            normalize_plan_fact_codes(chapter_plan, causal_result)
            plan_issues = validate_plan_against_causal(chapter_plan, causal_result) if use_causal_simulation else []
            if plan_issues:
                raise RuntimeError("stored plan checkpoint is invalid: " + json.dumps(plan_issues, ensure_ascii=False))
            planner_calls = 0
        else:
            chapter_plan, planner_exec, planner_calls = execute_chapter_planner(
                run_dir,
                chapter_file=chapter_file,
                engine_text=execution_engine_text,
                outline_text=outline_text,
                causal_result=causal_result,
                context=model_context,
                provider=selected_provider,
                model=selected_planning_model,
                runner=runner,
                budget=budget,
                timeout_seconds=timeout_seconds,
                force=force or resume,
                force_output=force_output or resume,
                require_scene_states=use_causal_simulation,
            )
        if chapter_plan.get("status") != "ready":
            missing = chapter_plan.get("missing_context") or []
            raise RuntimeError(f"chapter planning is blocked by missing context: {json.dumps(missing, ensure_ascii=False)}")
        if reuse_plan:
            contract = json.loads(bundle_files(run_dir)["chapter_contract"].read_text(encoding="utf-8"))
        else:
            augment_draft_with_plan(run_dir, chapter_plan)
            contract = chapter_contract(chapter_plan, causal_result)
            write_json(bundle_files(run_dir)["chapter_contract"], contract, force=True)
            write_json(bundle_files(run_dir)["story_fact_ledger"], contract.get("fact_ledger") or {}, force=True)
            write_json(
                bundle_files(run_dir)["scene_states"],
                {"schema": "fictionops.scene_state_contract.v1", "scenes": contract.get("scene_states") or []},
                force=True,
            )
            write_agent_checkpoint(
                run_dir,
                phase="plan_ready",
                next_action="run_draft_writer",
                artifacts=[
                    bundle_files(run_dir)["plan"],
                    bundle_files(run_dir)["chapter_contract"],
                    bundle_files(run_dir)["story_fact_ledger"],
                    bundle_files(run_dir)["scene_states"],
                ],
            )
        output_name = "output.md"
        reuse_draft = bool(resume and resume_phase == "draft_ready" and (run_dir / output_name).is_file())
        if reuse_draft:
            draft_exec = None
        elif scene_by_scene:
            total_scene_target = int(chapter_plan.get("target_chars") or target_chars or effective_min)
            scene_execs, output_name = execute_scenes(
                run_dir,
                chapter_file=chapter_file,
                engine_text=engine_text,
                chapter_plan=chapter_plan,
                contract=contract,
                causal_simulation=causal_result,
                context=model_context,
                total_target=total_scene_target,
                provider=selected_provider,
                model=selected_model,
                runner=runner,
                budget=budget,
                timeout_seconds=timeout_seconds,
                force=force_output or force or resume,
            )
            draft_exec = scene_execs[-1] if scene_execs else None
        else:
            draft_exec = execute_model_bundle(
                budget,
                run_dir,
                role="draft-writer",
                command=runner,
                output_name=output_name,
                timeout_seconds=timeout_seconds,
                force=force_output or force or resume,
                dry_run=False,
            )
        executed = True
        if not reuse_draft:
            write_agent_checkpoint(
                run_dir,
                phase="draft_ready",
                next_action="verify_candidate",
                artifacts=[run_dir / output_name],
            )
        while True:
            files_map = bundle_files(run_dir)
            raw_output = run_dir / output_name
            candidate_text = raw_output.read_text(encoding="utf-8").rstrip() + "\n"
            files_map["candidate"].write_text(candidate_text, encoding="utf-8", newline="\n")
            files_map["diff"].write_text(unified_diff(source_text, candidate_text, chapter_file, files_map["candidate"]), encoding="utf-8", newline="\n")
            verification = static_draft_verification(
                chapter_file=chapter_file,
                candidate_file=files_map["candidate"],
                candidate_text=candidate_text,
                engine_text=engine_text,
                min_chars=effective_min,
            )
            deterministic = deterministic_story_audit(candidate_text, contract)
            write_json(files_map["deterministic_story_audit"], deterministic, force=True)
            adversarial_result = {
                "schema": "fictionops.adversarial_draft_review.v1",
                "verdict": "pass",
                "profiles": [
                    {"name": name, "status": "pass", "summary": "Adversarial review disabled by caller."}
                    for name in ("continuity", "character_and_knowledge", "prose_and_reader_experience")
                ],
                "constraint_checks": [
                    {"id": str(item.get("id")), "status": "pass", "evidence": "Adversarial review disabled by caller."}
                    for item in contract.get("constraints") or []
                    if isinstance(item, dict)
                ],
                "scene_state_checks": [
                    {"scene_id": str(item.get("scene_id")), "status": "pass", "evidence": "Adversarial review disabled by caller."}
                    for item in contract.get("scene_states") or []
                    if isinstance(item, dict)
                ],
                "issues": [],
                "summary": "Adversarial review disabled by caller.",
            }
            static_failures = list(verification["blocking_failures"])
            if static_failures and use_adversarial_review:
                adversarial_result.update(
                    {
                        "verdict": "uncertain",
                        "profiles": [
                            {"name": name, "status": "uncertain", "summary": "Not run because static verification failed."}
                            for name in ("continuity", "character_and_knowledge", "prose_and_reader_experience")
                        ],
                        "constraint_checks": [
                            {"id": str(item.get("id")), "status": "uncertain", "evidence": "Not run because static verification failed."}
                            for item in contract.get("constraints") or []
                            if isinstance(item, dict)
                        ],
                        "scene_state_checks": [
                            {"scene_id": str(item.get("scene_id")), "status": "uncertain", "evidence": "Not run because static verification failed."}
                            for item in contract.get("scene_states") or []
                            if isinstance(item, dict)
                        ],
                        "summary": "Adversarial review was not run because the candidate failed static verification.",
                    }
                )
            if not static_failures and use_adversarial_review:
                adversarial_dir = prepare_adversarial_review_bundle(
                    run_dir,
                    target_file=chapter_file,
                    candidate_text=candidate_text,
                    contract=contract,
                    memory_text=memory_text,
                    provider=selected_provider,
                    model=selected_evaluation_model,
                    force=adversarial_calls > 0 or force or resume,
                )
                adversarial_exec = execute_model_bundle(
                    budget,
                    adversarial_dir,
                    role="adversarial-reviewer",
                    command=runner,
                    output_name="output.md",
                    timeout_seconds=timeout_seconds,
                    force=adversarial_calls > 0 or force_output or force or resume,
                    dry_run=False,
                )
                adversarial_calls += 1
                adversarial_output = Path(adversarial_exec.output_file).read_text(encoding="utf-8")
                for contract_retry in range(0, 3):
                    try:
                        adversarial_result = parse_adversarial_review(adversarial_output, contract)
                        grounding_issues = review_evidence_grounding_issues(adversarial_result, candidate_text)
                        if grounding_issues:
                            raise ValueError("adversarial evidence is not grounded in candidate text: " + json.dumps(grounding_issues, ensure_ascii=False))
                        break
                    except (json.JSONDecodeError, ValueError) as exc:
                        if contract_retry >= 2:
                            raise
                        prepare_json_contract_retry(adversarial_dir, adversarial_output, str(exc), label="Adversarial Review")
                        adversarial_exec = execute_model_bundle(
                            budget,
                            adversarial_dir,
                            role="adversarial-review-repair",
                            command=runner,
                            output_name=f"output.contract_retry{contract_retry + 1}.md",
                            timeout_seconds=timeout_seconds,
                            force=True,
                            dry_run=False,
                        )
                        adversarial_calls += 1
                        adversarial_output = Path(adversarial_exec.output_file).read_text(encoding="utf-8")
            write_json(files_map["adversarial_review"], adversarial_result, force=True)
            evaluation = {
                "schema": DRAFT_EVALUATION_SCHEMA,
                "verdict": "uncertain",
                "dimensions": [{"name": name, "status": "uncertain", "evidence": "static verification failed"} for name in DRAFT_DIMENSIONS],
                "constraint_checks": [],
                "issues": [],
                "retrospective": {},
                "canon_sync_suggestions": [],
                "summary": "Static verification failed before semantic evaluation.",
            }
            if not static_failures:
                evaluator_dir = prepare_evaluator_bundle(
                    run_dir,
                    chapter_file=chapter_file,
                    engine_text=execution_engine_text,
                    candidate_text=candidate_text,
                    chapter_plan=chapter_plan,
                    contract=contract,
                    adversarial_review=adversarial_result,
                    context=model_context,
                    provider=selected_provider,
                    model=selected_evaluation_model,
                    force=evaluator_calls > 0 or force or resume,
                )
                evaluator_exec = execute_model_bundle(
                    budget,
                    evaluator_dir,
                    role="draft-evaluator",
                    command=runner,
                    output_name="output.md",
                    timeout_seconds=timeout_seconds,
                    force=evaluator_calls > 0 or force_output or force or resume,
                    dry_run=False,
                )
                evaluator_calls += 1
                expected_constraint_ids = [item["id"] for item in draft_constraint_specs(chapter_plan)]
                evaluator_output = Path(evaluator_exec.output_file).read_text(encoding="utf-8")
                for contract_retry in range(0, 3):
                    try:
                        evaluation = parse_draft_evaluation(
                            evaluator_output,
                            expected_constraint_ids=expected_constraint_ids,
                        )
                        grounding_issues = review_evidence_grounding_issues(evaluation, candidate_text)
                        if grounding_issues:
                            raise ValueError("evaluation evidence is not grounded in candidate text: " + json.dumps(grounding_issues, ensure_ascii=False))
                        break
                    except (json.JSONDecodeError, ValueError) as exc:
                        if contract_retry >= 2:
                            raise
                        prepare_json_contract_retry(evaluator_dir, evaluator_output, str(exc), label="Draft Evaluation")
                        evaluator_exec = execute_model_bundle(
                            budget,
                            evaluator_dir,
                            role="draft-evaluation-repair",
                            command=runner,
                            output_name=f"output.contract_retry{contract_retry + 1}.md",
                            timeout_seconds=timeout_seconds,
                            force=True,
                            dry_run=False,
                        )
                        evaluator_calls += 1
                        evaluator_output = Path(evaluator_exec.output_file).read_text(encoding="utf-8")
                verification = merge_draft_evaluation(verification, evaluation)
                verification = merge_story_verification(
                    verification,
                    deterministic=deterministic,
                    adversarial=adversarial_result,
                )
            else:
                verification = merge_story_verification(
                    verification,
                    deterministic=deterministic,
                    adversarial=adversarial_result,
                )
            write_json(files_map["evaluation"], evaluation, force=True)
            write_json(files_map["verification"], verification, force=True)
            session = json.loads(files_map["session"].read_text(encoding="utf-8"))
            session.update(
                {
                    "state": verification["status"],
                    "candidate_file": str(files_map["candidate"].resolve()),
                    "candidate_sha256": verification["candidate_sha256"],
                    "ready_for_approval": verification["ready_for_approval"],
                    "updated_at": utc_now(),
                }
            )
            write_json(files_map["session"], session, force=True)
            append_event(run_dir, "draft_verified", str(verification["status"]), failures=verification["blocking_failures"])
            write_agent_checkpoint(
                run_dir,
                phase="ready_for_approval" if verification["ready_for_approval"] else "needs_revision_attention",
                next_action="await_author_approval" if verification["ready_for_approval"] else "rewrite_candidate_or_request_decision",
                artifacts=[files_map["candidate"], files_map["verification"], files_map["evaluation"], files_map["adversarial_review"]],
                details={"retry_count": retry_count, "blocking_failures": verification["blocking_failures"]},
            )
            if verification["ready_for_approval"] or retry_count >= max_retries:
                break
            retry_count += 1
            if scene_by_scene:
                archive_attempt(run_dir, retry_count)
                rewritten_execs, output_name = rewrite_scenes(
                    run_dir,
                    attempt=retry_count,
                    chapter_file=chapter_file,
                    engine_text=engine_text,
                    chapter_plan=chapter_plan,
                    contract=contract,
                    causal_simulation=causal_result,
                    verification=verification,
                    evaluation=evaluation,
                    adversarial=adversarial_result,
                    provider=selected_provider,
                    model=selected_model,
                    runner=runner,
                    budget=budget,
                    timeout_seconds=timeout_seconds,
                )
                scene_execs.extend(rewritten_execs)
                draft_exec = rewritten_execs[-1] if rewritten_execs else draft_exec
            else:
                output_name = prepare_write_retry(run_dir, verification, evaluation, retry_count)
                draft_exec = execute_model_bundle(
                    budget,
                    run_dir,
                    role="draft-writer-retry",
                    command=runner,
                    output_name=output_name,
                    timeout_seconds=timeout_seconds,
                    force=False,
                    dry_run=False,
                )
        if verification and verification["ready_for_approval"] and evaluation:
            write_post_draft_artifacts(run_dir, evaluation)
        files = [AgentWriteWorkflowFile(kind=name, path=str(path), written=path.exists()) for name, path in bundle_files(run_dir).items()]
        stop_reason = str(verification["status"]) if verification else "draft_output_needs_attention"
        budget.complete()
        files.append(AgentWriteWorkflowFile(kind="model_budget", path=str(budget.path), written=True))
    elif runner and dry_run:
        stop_reason = "dry_run_runner_not_executed"
    report = AgentWriteWorkflowReport(
        command="agent-write-workflow",
        target=str(chapter_file),
        chapter_file=str(chapter_file),
        engine_file=str(engine_file),
        outline_file=str(outline_file) if outline_file else None,
        run_dir=str(run_dir),
        provider=selected_provider,
        model=selected_model,
        planning_model=selected_planning_model,
        evaluation_model=selected_evaluation_model,
        source_existed=source_existed,
        source_sha256=source_sha,
        session_id=session_id,
        context_file_count=len(context.items),
        prepared=prepared,
        executed=executed,
        verification_status=str(verification["status"]) if verification else None,
        ready_for_approval=bool(verification and verification["ready_for_approval"]),
        min_chars=effective_min,
        max_retries=max_retries,
        retry_count=retry_count,
        evaluator_call_count=evaluator_calls,
        planner_call_count=planner_calls,
        causal_simulator_call_count=causal_calls,
        adversarial_reviewer_call_count=adversarial_calls,
        scene_writer_call_count=len(scene_execs),
        max_model_calls=max_model_calls,
        model_calls_used=budget.used_calls if budget else 0,
        max_runtime_seconds=max_runtime_seconds,
        scene_by_scene=scene_by_scene,
        memory_record_count=int(memory_query.get("record_count") or 0),
        stop_reason=stop_reason,
        files=files,
        next_actions=[],
        draft_exec=draft_exec,
        scene_execs=scene_execs,
        planner_exec=planner_exec,
        evaluator_exec=evaluator_exec,
        causal_exec=causal_exec,
        adversarial_exec=adversarial_exec,
        verification=verification,
        evaluation=evaluation,
        chapter_plan=chapter_plan,
        causal_simulation=causal_result,
        adversarial_review=adversarial_result,
        chapter_contract=contract,
    )
    report.next_actions = next_actions(report)
    return report


def render_agent_write_workflow(report: AgentWriteWorkflowReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported agent-write-workflow format: {output_format}")
    lines = [
        "# FictionOps Agent Write Workflow",
        "",
        f"- Chapter: `{report.chapter_file}`",
        f"- Engine: `{report.engine_file}`",
        f"- Run dir: `{report.run_dir}`",
        f"- Models: plan=`{report.planning_model}`, draft=`{report.model}`, evaluate=`{report.evaluation_model}`",
        f"- Context files: {report.context_file_count}",
        f"- Executed: {'yes' if report.executed else 'no'}",
        f"- Verification: `{report.verification_status or '-'}`",
        f"- Ready for approval: {'yes' if report.ready_for_approval else 'no'}",
        f"- Retries: {report.retry_count}/{report.max_retries}",
        f"- Planner calls: {report.planner_call_count}",
        f"- Causal simulator calls: {report.causal_simulator_call_count}",
        f"- Adversarial reviewer calls: {report.adversarial_reviewer_call_count}",
        f"- Model-call budget: {report.model_calls_used}/{report.max_model_calls} calls; runtime limit {report.max_runtime_seconds}s",
        f"- Scene-by-scene drafting: {'yes' if report.scene_by_scene else 'no'} ({report.scene_writer_call_count} scene calls)",
        f"- Retrieved memory records: {report.memory_record_count}",
        f"- Stop reason: `{report.stop_reason}`",
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in report.next_actions)
    return "\n".join(lines).rstrip() + "\n"
