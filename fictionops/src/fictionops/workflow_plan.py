from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .markdown import safe_cell
from .models import WorkflowPlanReport, WorkflowPlanStep
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


WORKFLOW_STAGES = [
    "init",
    "foundation",
    "book-plan",
    "chapter-prep",
    "draft",
    "review",
    "book-retrospective",
    "publish",
    "handoff",
]

WORKFLOW_STAGE_CHOICES = ["all", *WORKFLOW_STAGES]

STAGE_ALIASES = {
    "0": "init",
    "seed": "init",
    "start": "init",
    "1": "foundation",
    "beam": "foundation",
    "beams": "foundation",
    "canon": "foundation",
    "2": "book-plan",
    "book": "book-plan",
    "book-planning": "book-plan",
    "outline": "book-plan",
    "3": "chapter-prep",
    "prep": "chapter-prep",
    "chapter": "chapter-prep",
    "chapter-plan": "chapter-prep",
    "4": "draft",
    "write": "draft",
    "writing": "draft",
    "5": "review",
    "audit": "review",
    "revise": "review",
    "6": "book-retrospective",
    "retrospective": "book-retrospective",
    "book-retro": "book-retrospective",
    "7": "publish",
    "release": "publish",
    "publication": "publish",
    "8": "handoff",
    "continue": "handoff",
    "next": "handoff",
    "all": "all",
}

CHAPTER_STAGES = {"chapter-prep", "draft", "review"}


def normalize_workflow_stage(stage: str) -> str:
    key = re.sub(r"[\s_]+", "-", stage.strip().lower())
    key = STAGE_ALIASES.get(key, key)
    if key not in WORKFLOW_STAGE_CHOICES:
        choices = ", ".join(WORKFLOW_STAGE_CHOICES)
        raise ValueError(f"unsupported workflow stage: {stage}. Available stages: {choices}")
    return key


def workflow_chapter_token(stage: str, chapter: str | None) -> tuple[str | None, str]:
    if chapter:
        normalized = normalize_chapter_number(chapter)
        return normalized, normalized
    if stage in CHAPTER_STAGES:
        raise ValueError(f"workflow-plan --stage {stage} requires --chapter")
    return None, "<chapter>"


def quote_command_arg(value: str) -> str:
    if not value:
        return '""'
    if any(char.isspace() for char in value) or any(char in value for char in ['"', "'", "\\", ":"]):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def command_for_project(target: Path) -> str:
    if target.exists() and target.is_dir():
        return "."
    return quote_command_arg(str(target))


def step(
    stage: str,
    order: int,
    title: str,
    purpose: str,
    command: str,
    *,
    produces: list[str],
    exit_checks: list[str],
    required: bool = True,
) -> WorkflowPlanStep:
    return WorkflowPlanStep(
        stage=stage,
        order=order,
        title=title,
        purpose=purpose,
        command=command,
        required=required,
        produces=produces,
        exit_checks=exit_checks,
    )


def stage_steps(stage: str, *, project_arg: str, book: str, chapter_token: str) -> list[WorkflowPlanStep]:
    if stage == "init":
        return [
            step(
                stage,
                1,
                "Create project skeleton",
                "Create the file layout before adding story-specific material.",
                f"fictionops init {project_arg} --title \"<title>\"",
                produces=["project.yml", "00_management/", "01_story_seed/", "03_characters/", "05_canon/"],
                exit_checks=["Project language, genre, and status are visible.", "Story promise can be summarized in a few sentences."],
            ),
            step(
                stage,
                2,
                "Record model boundary",
                "Optional model settings should be explicit and should not store raw API keys.",
                f"fictionops model-config {project_arg} --provider local --planning-model planner --drafting-model writer --audit-model auditor --write",
                produces=["00_management/model_config.json"],
                exit_checks=["Provider and model names are documented.", "Real API keys remain outside the project files."],
                required=False,
            ),
        ]

    if stage == "foundation":
        return [
            step(
                stage,
                1,
                "Fill core memory files",
                "Build the load-bearing story memory before chapter drafting.",
                "manual: fill story seed, world rules, character arcs, information table, and echo table",
                produces=["01_story_seed/story_seed.md", "03_characters/", "05_canon/"],
                exit_checks=["Major characters have desire, fear, intelligence mode, voice, and failure path."],
            ),
            step(
                stage,
                2,
                "Audit character memory",
                "Check whether cast files can support long-form handoff.",
                f"fictionops audit-characters {project_arg}",
                produces=["character arc maintenance report"],
                exit_checks=["No major indexed character lacks an arc, intelligence mode, or voice profile."],
            ),
            step(
                stage,
                3,
                "Audit information boundary",
                "Check that secrets, public versions, and next releases are trackable.",
                f"fictionops audit-info {project_arg}",
                produces=["information boundary report"],
                exit_checks=["Author truth, reader knowledge, public version, and next release are separated."],
            ),
            step(
                stage,
                4,
                "Audit foreshadowing echoes",
                "Check that long-range threads have initial plants, reminders, and payoff directions.",
                f"fictionops audit-echoes {project_arg}",
                produces=["foreshadowing echo report"],
                exit_checks=["Active threads either have a recent echo or an intentional dormant state."],
            ),
        ]

    if stage == "book-plan":
        return [
            step(
                stage,
                1,
                "Create or refresh book scaffold",
                "Make sure the book has an outline, chapter directory, engines, and retrospective file.",
                f"fictionops new-book {project_arg} --book {book} --title \"<book title>\"",
                produces=[f"04_structure/book_outlines/{book}_outline.md", f"06_drafts/{book}/"],
                exit_checks=["Book entering state and leaving state are clear."],
            ),
            step(
                stage,
                2,
                "Audit plan coverage",
                "Check whether outline rows, chapters, and chapter engines match.",
                f"fictionops audit-plan {project_arg} --book {book}",
                produces=["plan coverage report"],
                exit_checks=["Every planned chapter has pressure, desire, obstacle, change, and remainder."],
            ),
            step(
                stage,
                3,
                "Check chapter wave",
                "Keep chapter length serving pressure rather than mechanical uniformity.",
                f"fictionops audit-wave {project_arg}",
                produces=["chapter length wave report"],
                exit_checks=["Length variation is intentional and explained by chapter function."],
            ),
        ]

    if stage == "chapter-prep":
        return [
            step(
                stage,
                1,
                "Create chapter files",
                "Create the draft, chapter engine, and retrospective shell.",
                f"fictionops new-chapter {project_arg} --book {book} --chapter {chapter_token}",
                produces=[f"06_drafts/{book}/chapters/ch_{chapter_token}.md", f"06_drafts/{book}/chapter_engines/ch_{chapter_token}_engine.md"],
                exit_checks=["The chapter has a place to draft and a place to record pressure."],
            ),
            step(
                stage,
                2,
                "Sync chapter engine",
                "Pull chapter-level plan fields from the book outline without overwriting filled fields by default.",
                f"fictionops plan-chapter {project_arg} --book {book} --chapter {chapter_token}",
                produces=[f"06_drafts/{book}/chapter_engines/ch_{chapter_token}_engine.md"],
                exit_checks=["Pressure, desire, obstacle, change, and remainder are not empty."],
            ),
            step(
                stage,
                3,
                "Build scene skeleton",
                "Turn the filled chapter engine into a scene-level writing plan without drafting prose.",
                f"fictionops scene-plan {project_arg} --book {book} --chapter {chapter_token}",
                produces=["scene skeleton"],
                exit_checks=["Scenes carry pressure, desire, obstacle, change, residue, information boundary, and echo reminders."],
            ),
            step(
                stage,
                4,
                "Build draft brief",
                "Combine scene tasks and scoped context into a task-ready writing brief without drafting prose.",
                f"fictionops draft-brief {project_arg} --book {book} --chapter {chapter_token}",
                produces=["task-ready draft brief"],
                exit_checks=["The brief names scene tasks, guardrails, missing context, and must-not rules before drafting."],
            ),
        ]

    if stage == "draft":
        return [
            step(
                stage,
                1,
                "Render draft prompt",
                "Give the writer role strict boundaries before prose generation or human drafting.",
                f"fictionops agent-prompt {project_arg} --role draft-writer --book {book} --chapter {chapter_token} --include-context",
                produces=["draft-writer prompt with scoped context"],
                exit_checks=["The prompt states viewpoint, information boundary, and must-not rules."],
            ),
            step(
                stage,
                2,
                "Draft chapter",
                "Write the chapter under the chapter engine and context constraints.",
                f"manual: draft 06_drafts/{book}/chapters/ch_{chapter_token}.md",
                produces=[f"06_drafts/{book}/chapters/ch_{chapter_token}.md"],
                exit_checks=["The chapter ends with change and residue, not only explanation."],
            ),
            step(
                stage,
                3,
                "Record immediate residue",
                "Keep post-draft discoveries from living only in chat history.",
                f"manual: fill 06_drafts/{book}/revision_notes/ch_{chapter_token}_retrospective.md",
                produces=[f"06_drafts/{book}/revision_notes/ch_{chapter_token}_retrospective.md"],
                exit_checks=["Open sync items are listed instead of left in memory."],
            ),
            step(
                stage,
                4,
                "Close post-draft gate",
                "Check that the draft, engine, retrospective, and sync notes are ready before review.",
                f"fictionops post-draft {project_arg} --book {book} --chapter {chapter_token}",
                produces=["post-draft gate report"],
                exit_checks=["The chapter is not placeholder text, the retrospective is filled, and sync items are explicit."],
            ),
        ]

    if stage == "review":
        return [
            step(
                stage,
                1,
                "Run review gate",
                "Aggregate the chapter's post-draft, memory, information, character, echo, style, and wave risks before detailed review.",
                f"fictionops review-gate {project_arg} --book {book} --chapter {chapter_token}",
                produces=["single-chapter review gate report"],
                exit_checks=["Post-draft readiness and blocking review issues are visible before detailed audit work."],
            ),
            step(
                stage,
                2,
                "Audit continuity",
                "Check standard project memory, chapter engines, retrospectives, and placeholder files.",
                f"fictionops audit-continuity {project_arg}",
                produces=["continuity audit report"],
                exit_checks=["Missing engines, retrospectives, and project memory files are visible."],
            ),
            step(
                stage,
                3,
                "Audit information boundary",
                "Check whether secrets or forbidden terms appear before planned release.",
                f"fictionops audit-info {project_arg}",
                produces=["information boundary report"],
                exit_checks=["Possible early leaks are reviewed before style polish."],
            ),
            step(
                stage,
                4,
                "Check project tables",
                "Check Markdown table structure and placeholder rows before relying on canon and audit tables.",
                f"fictionops check-tables {project_arg} --all",
                produces=["table check report"],
                exit_checks=["Broken table rows, duplicate headers, and placeholder rows are visible before memory sync."],
            ),
            step(
                stage,
                5,
                "Audit character memory",
                "Check character arcs, intelligence modes, voice profiles, and cast index coverage.",
                f"fictionops audit-characters {project_arg}",
                produces=["character audit report"],
                exit_checks=["Characters have limits, voice, and failure paths recorded."],
            ),
            step(
                stage,
                6,
                "Audit foreshadowing echoes",
                "Check whether active threads have enough light reminders and no early explanations.",
                f"fictionops audit-echoes {project_arg}",
                produces=["foreshadowing echo report"],
                exit_checks=["Active threads have a planned next echo or payoff direction."],
            ),
            step(
                stage,
                7,
                "Scan repeated words",
                "Scan general high-frequency terms and watch words as a freshness signal.",
                f"fictionops scan-words {project_arg}",
                produces=["word scan report"],
                exit_checks=["Repeated terms are visible as judgment prompts rather than automatic deletion orders."],
            ),
            step(
                stage,
                8,
                "Audit prose patterns",
                "Check high-frequency markers and repeated sentence openings after structural risks are visible.",
                f"fictionops audit-style {project_arg}",
                produces=["style report"],
                exit_checks=["Repeated forms are either justified or marked for revision."],
            ),
            step(
                stage,
                9,
                "Audit chapter wave",
                "Check whether chapter length serves pressure rather than mechanical targets.",
                f"fictionops audit-wave {project_arg}",
                produces=["chapter wave report"],
                exit_checks=["Flat runs, same-band runs, and abrupt jumps are intentional or queued for revision."],
            ),
            step(
                stage,
                10,
                "Create revision plan",
                "Turn audit noise into ordered work.",
                f"fictionops revision-plan {project_arg} --book {book} --out 07_audits/revision_plan.md --force",
                produces=["07_audits/revision_plan.md"],
                exit_checks=["P1/P2 tasks come before pacing and style tasks."],
            ),
        ]

    if stage == "book-retrospective":
        return [
            step(
                stage,
                1,
                "Summarize post-draft memory",
                "Make sure chapter-level discoveries are rolled into book-level memory.",
                f"fictionops retrospective {project_arg} --book {book} --out 07_audits/book_retrospectives/{book}_report.md --force",
                produces=[f"07_audits/book_retrospectives/{book}_report.md"],
                exit_checks=["Open sync items are visible and assigned."],
            ),
            step(
                stage,
                2,
                "Run book gate",
                "Decide whether the book can move from retrospection into clean export.",
                f"fictionops book-gate {project_arg} --book {book}",
                produces=["book-level closing gate report"],
                exit_checks=["Plan coverage, retrospectives, blocking revision tasks, table structure, word-scan signals, and chapter wave are visible."],
            ),
            step(
                stage,
                3,
                "Audit book plan",
                "Check that the closed book's outline, chapters, and engines still align.",
                f"fictionops audit-plan {project_arg} --book {book}",
                produces=["book plan audit report"],
                exit_checks=["Planned chapters and actual chapters are reconciled."],
            ),
            step(
                stage,
                4,
                "Re-run long-range audits",
                "Check that the closed book still preserves secrets, echoes, and characters.",
                f"fictionops audit-info {project_arg}",
                produces=["information boundary report"],
                exit_checks=["Next book inherits information states instead of rediscovering them."],
            ),
            step(
                stage,
                5,
                "Re-run echo audit",
                "Check long-range callback memory before opening the next book.",
                f"fictionops audit-echoes {project_arg}",
                produces=["foreshadowing echo report"],
                exit_checks=["Threads know whether the next book should lightly touch, reveal, or close them."],
            ),
            step(
                stage,
                6,
                "Re-run character audit",
                "Check that character leaving states are recorded.",
                f"fictionops audit-characters {project_arg}",
                produces=["character audit report"],
                exit_checks=["Next book can inherit character states without resetting them."],
            ),
        ]

    if stage == "publish":
        return [
            step(
                stage,
                1,
                "Export clean manuscript",
                "Create a publish copy without overwriting draft sources.",
                f"fictionops export-clean {project_arg} --book {book}",
                produces=[f"08_publish/clean_markdown/{book}.md"],
                exit_checks=["Clean Markdown has no draft markers and chapter order is stable."],
            ),
            step(
                stage,
                2,
                "Audit clean manuscript",
                "Check chapter order, draft markers, missing chapters, and short chapters.",
                f"fictionops audit-publish {project_arg} --book {book}",
                produces=["publish audit report"],
                exit_checks=["Publish blockers are visible before packaging."],
            ),
            step(
                stage,
                3,
                "Draft publish copy",
                "Create editable synopsis, tag, and keyword candidates from project evidence.",
                f"fictionops publish-copy {project_arg} --book {book}",
                produces=[f"08_publish/synopsis/{book}_publish_copy.md"],
                exit_checks=["Accepted synopsis, tags, and keywords are copied back into the publish checklist."],
            ),
            step(
                stage,
                4,
                "Export metadata",
                "Make synopsis, tags, category, author, and content notes machine-readable.",
                f"fictionops export-metadata {project_arg} --book {book}",
                produces=[f"08_publish/metadata/{book}_metadata.json"],
                exit_checks=["Required publish metadata fields are filled."],
            ),
            step(
                stage,
                5,
                "Export manifest",
                "Create a reproducible package manifest with hashes.",
                f"fictionops export-manifest {project_arg} --book {book}",
                produces=[f"08_publish/manifest/{book}_manifest.json"],
                exit_checks=["Manifest hashes record the current clean Markdown and metadata."],
            ),
            step(
                stage,
                6,
                "Export EPUB",
                "Create the styled EPUB package.",
                f"fictionops export-epub {project_arg} --book {book}",
                produces=[f"08_publish/epub/{book}.epub"],
                exit_checks=["EPUB output exists and is newer than its inputs."],
            ),
            step(
                stage,
                7,
                "Audit EPUB",
                "Verify EPUB structure and freshness.",
                f"fictionops audit-epub {project_arg} --book {book}",
                produces=["EPUB audit report"],
                exit_checks=["Manifest hashes match current inputs and EPUB is structurally valid."],
            ),
            step(
                stage,
                8,
                "Run release gate",
                "Aggregate book closure, publish, metadata, manifest, and EPUB evidence before upload or archive.",
                f"fictionops release-gate {project_arg} --book {book}",
                produces=["release gate report"],
                exit_checks=["Book closure has not been bypassed, no release artifacts are missing or stale, and EPUB is structurally valid."],
            ),
        ]

    if stage == "handoff":
        return [
            step(
                stage,
                1,
                "Run project health summary",
                "Give the next human or agent a compact project state.",
                f"fictionops doctor {project_arg} --book {book}",
                produces=["project health summary"],
                exit_checks=["Health status and highest priority gaps are visible."],
            ),
            step(
                stage,
                2,
                "Write handoff report",
                "Persist the project state instead of relying on chat context.",
                f"fictionops report {project_arg} --book {book} --out 07_audits/doctor_report.md --force",
                produces=["07_audits/doctor_report.md"],
                exit_checks=["Report includes wave, continuity, characters, information, publish, and EPUB sections."],
            ),
            step(
                stage,
                3,
                "Build handoff context pack",
                "Collect a bounded set of files for the next session.",
                f"fictionops context-pack {project_arg} --task handoff --book {book} --out 00_management/context_pack.md --force",
                produces=["00_management/context_pack.md"],
                exit_checks=["Next worker can continue without reading the whole chat history."],
            ),
        ]

    raise ValueError(f"unsupported workflow stage: {stage}")


def build_steps_for_stage(stage: str, *, project_arg: str, book: str, chapter_token: str) -> list[WorkflowPlanStep]:
    stages = WORKFLOW_STAGES if stage == "all" else [stage]
    steps: list[WorkflowPlanStep] = []
    for current in stages:
        steps.extend(stage_steps(current, project_arg=project_arg, book=book, chapter_token=chapter_token))
    return steps


def resolve_workflow_plan_output_path(target: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    base = target if target.exists() and target.is_dir() else target.parent
    return (base / candidate).resolve()


def write_workflow_plan(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_workflow_plan(
    target: Path,
    *,
    stage: str = "all",
    book: str = "book_01",
    chapter: str | None = None,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> WorkflowPlanReport:
    stage_id = normalize_workflow_stage(stage)
    if stage_id != "init" and not target.exists():
        raise FileNotFoundError(f"path does not exist: {target}")
    if target.exists() and not target.is_dir():
        raise ValueError(f"workflow-plan requires a project directory or a future project path: {target}")

    book_id = normalize_book_for_plan(book)
    chapter_number, chapter_token = workflow_chapter_token(stage_id, chapter)
    resolved = target.expanduser().resolve()
    project_arg = command_for_project(target)
    steps = build_steps_for_stage(stage_id, project_arg=project_arg, book=book_id, chapter_token=chapter_token)
    commands = [item.command for item in steps if item.command and not item.command.startswith("manual:")]
    notes = [
        "This plan does not execute commands or call model providers.",
        "Manual steps are explicit because FictionOps should not replace author judgment.",
        "Run doctor or revision-plan after major changes to refresh project health.",
    ]

    output_path = resolve_workflow_plan_output_path(target, out) if out else None
    report = WorkflowPlanReport(
        target=str(resolved),
        stage=stage_id,
        book=book_id,
        chapter=chapter_number,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        step_count=len(steps),
        commands=commands,
        steps=steps,
        notes=notes,
    )
    if output_path and not dry_run:
        write_workflow_plan(output_path, render_workflow_plan(report, "markdown"), force=force)
        report.written = True
    return report


def render_workflow_plan(report: WorkflowPlanReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_workflow_plan(report)


def format_list(values: list[str]) -> str:
    return "<br>".join(safe_cell(value) for value in values) if values else "-"


def format_workflow_plan(report: WorkflowPlanReport) -> str:
    lines = [
        "# FictionOps Workflow Plan",
        "",
        f"- Target: `{report.target}`",
        f"- Stage: `{report.stage}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Steps: {report.step_count}",
        "",
        "## Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in report.notes)
    lines.extend(
        [
            "",
            "## Steps",
            "",
            "| # | Stage | Required | Step | Purpose | Command | Produces | Exit Checks |",
            "| ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for index, item in enumerate(report.steps, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    safe_cell(item.stage),
                    "yes" if item.required else "optional",
                    safe_cell(item.title),
                    safe_cell(item.purpose),
                    f"`{safe_cell(item.command)}`",
                    format_list(item.produces),
                    format_list(item.exit_checks),
                ]
            )
            + " |"
        )
    if report.commands:
        lines.extend(["", "## Runnable Commands", ""])
        lines.append("```bash")
        lines.extend(report.commands)
        lines.append("```")
    return "\n".join(lines) + "\n"
