from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .agent_inbox import build_agent_inbox, default_agent_runs_dir
from .audit_plan import build_plan_audit_report
from .chapter_wave import build_chapter_wave_report
from .character_audit import build_character_audit_report
from .continuity_audit import build_continuity_report, format_bool
from .echo_audit import build_echo_report
from .information_audit import build_info_report
from .markdown import safe_cell
from .models import (
    ContinuityReport,
    CharacterAuditReport,
    ChapterWaveReport,
    DoctorReport,
    EchoReport,
    EpubAuditReport,
    InfoBoundaryReport,
    AgentInboxReport,
    ModelConfigReport,
    PlanAuditReport,
    PublishAuditReport,
    PublishManifestIssue,
    PublishManifestReport,
    PublishMetadataReport,
    RetrospectiveReport,
    StatsReport,
    StyleAuditReport,
    TableCheckReport,
    WordScanReport,
)
from .model_config import build_model_config_report, default_model_config_path
from .plan_chapter import normalize_book_for_plan, resolve_outline_path
from .publish_audit import build_publish_audit_report
from .epub_audit import build_epub_audit_report
from .publish_metadata import (
    blank_value,
    default_metadata_output_path,
    default_publish_checklist_path,
    export_publish_metadata,
)
from .publish_epub import default_epub_output_path
from .publish_manifest import default_manifest_output_path, export_publish_manifest
from .retrospective import book_retrospective_path, build_retrospective_report
from .stats import build_stats_report
from .style_audit import build_style_audit_report, format_counter_dict
from .table_check import build_table_check_report
from .word_scan import build_word_scan_report
from .export_clean import default_clean_output_path

def looks_like_standard_project(path: Path) -> bool:
    if not path.is_dir():
        return False
    markers = ["project.yml", "00_management", "05_canon", "06_drafts"]
    return any((path / marker).exists() for marker in markers)


def has_character_assets(path: Path) -> bool:
    if not path.is_dir():
        return False
    markers = [
        "03_characters",
        "character_index.md",
        "intelligence_profiles.md",
        "voice_profiles.md",
        "relationship_map.md",
    ]
    return any((path / marker).exists() for marker in markers)


def count_severities(*issue_lists: list[object]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for issues in issue_lists:
        for issue in issues:
            severity = getattr(issue, "severity", None)
            if severity:
                counts[severity] += 1
    return {key: counts.get(key, 0) for key in ["P1", "P2", "P3", "P4", "P5"]}


def doctor_status(issue_counts: dict[str, int]) -> str:
    if issue_counts.get("P1", 0):
        return "critical"
    if issue_counts.get("P2", 0):
        return "needs_attention"
    if issue_counts.get("P3", 0):
        return "maintenance_needed"
    if issue_counts.get("P4", 0):
        return "review"
    return "pass"


def actionable_table_issues(table_report: TableCheckReport) -> list[object]:
    return [issue for issue in table_report.issues if issue.code != "no_tables"]


def build_doctor_recommendations(
    *,
    stats: StatsReport,
    wave: ChapterWaveReport,
    style: StyleAuditReport,
    word_scan: WordScanReport,
    tables: TableCheckReport,
    table_issues: list[object],
    continuity: ContinuityReport,
    characters: CharacterAuditReport,
    echoes: EchoReport,
    info: InfoBoundaryReport,
    plan: PlanAuditReport | None,
    retrospective: RetrospectiveReport | None,
    book_gate: object | None,
    agent_inbox: AgentInboxReport | None,
    model_config: ModelConfigReport | None,
    publish: PublishAuditReport | None,
    metadata: PublishMetadataReport | None,
    manifest: PublishManifestReport | None,
    epub: EpubAuditReport | None,
    release_gate: object | None,
) -> list[str]:
    recommendations: list[str] = []
    if stats.file_count == 0:
        recommendations.append("No chapter files were detected. Check the path or use a FictionOps chapter layout.")
    if wave.issues:
        recommendations.append(f"Review {len(wave.issues)} chapter length wave issue(s) for pacing variation.")
    if table_issues:
        recommendations.append(f"Fix {len(table_issues)} Markdown table structure issue(s) before relying on project memory.")
    if continuity.missing_engine_count:
        recommendations.append(f"Add or link chapter engines for {continuity.missing_engine_count} detected chapters.")
    if continuity.missing_retrospective_count:
        recommendations.append(
            f"Add chapter retrospectives or revision notes for {continuity.missing_retrospective_count} chapters."
        )
    if continuity.missing_standard_files:
        recommendations.append(f"Create {continuity.missing_standard_files} missing standard project-memory files.")
    if continuity.placeholder_standard_files:
        recommendations.append(f"Fill {continuity.placeholder_standard_files} standard files that still look like templates.")
    if characters.issues:
        recommendations.append("Review character arc, intelligence, and voice-profile maintenance gaps.")
    if echoes.thread_count == 0:
        recommendations.append("Create a filled foreshadowing echo table with at least one thread.")
    elif echoes.issues:
        recommendations.append("Complete missing fields in the echo table: first plant, last echo, next echo, and payoff.")
    if info.item_count == 0:
        recommendations.append("Create a filled information release table with at least one tracked secret or rule.")
    elif info.issues:
        recommendations.append("Review information boundary issues: missing knowledge states or possible early text hits.")
    if plan is not None and plan.issues:
        recommendations.append("Align the book outline plan with chapter drafts and chapter engines.")
    if retrospective is not None and retrospective.sync_item_count:
        recommendations.append(f"Resolve {retrospective.sync_item_count} open retrospective sync item(s).")
    elif retrospective is not None and retrospective.book_retrospective_placeholder:
        recommendations.append("Fill the book retrospective so post-draft memory is not left as a template.")
    if book_gate is not None and not bool(getattr(book_gate, "ready", False)):
        recommendations.append(f"Review book-gate status `{getattr(book_gate, 'status', 'unknown')}` before clean export.")
    if agent_inbox is not None and agent_inbox.needs_attention_count:
        recommendations.append("Review agent inbox issues before applying staged model output.")
    elif agent_inbox is not None and agent_inbox.ready_count:
        recommendations.append("Review ready agent output in the inbox before applying it to project files.")
    if publish is not None and publish.issues:
        recommendations.append(f"Fix {len(publish.issues)} publish clean Markdown issue(s) before release.")
    if metadata is not None and metadata.issues:
        recommendations.append(f"Fix {len(metadata.issues)} publish metadata issue(s) before release.")
    if manifest is not None and manifest.issues:
        recommendations.append(f"Fix {len(manifest.issues)} publish manifest issue(s) before release.")
    if epub is not None and epub.issues:
        recommendations.append(f"Fix {len(epub.issues)} EPUB export issue(s) before release.")
    if release_gate is not None and not bool(getattr(release_gate, "ready", False)):
        recommendations.append(f"Review release-gate status `{getattr(release_gate, 'status', 'unknown')}` before upload.")
    if style.aggregate_terms:
        top_term = style.aggregate_terms[0]
        recommendations.append(f"Review high-density style marker `{top_term.item}` ({top_term.count} hits).")
    if word_scan.watch_hits and not style.aggregate_terms:
        top_term = word_scan.watch_hits[0]
        recommendations.append(f"Review watched word `{top_term.item}` ({top_term.count} hits).")
    if model_config is not None and model_config.issues:
        recommendations.append("Review model provider configuration before handing tasks to model-backed agents.")
    return recommendations[:8]


def build_plan_doctor_section(
    target: Path,
    *,
    book: str,
    outline: str | None,
) -> tuple[PlanAuditReport | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "outline": None,
            "planned_chapters": 0,
            "chapter_files": 0,
            "engine_files": 0,
            "synced_engines": 0,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }

    outline_path = resolve_outline_path(target, book=book_id, outline=outline)
    if not outline_path.exists() and outline is None:
        return None, {
            "enabled": False,
            "book": book_id,
            "outline": str(outline_path),
            "planned_chapters": 0,
            "chapter_files": 0,
            "engine_files": 0,
            "synced_engines": 0,
            "issues": 0,
            "skipped_reason": "outline_not_found",
        }

    plan = build_plan_audit_report(target, book=book_id, outline=outline)
    return plan, {
        "enabled": True,
        "book": plan.book,
        "outline": plan.outline_file,
        "planned_chapters": plan.planned_chapters,
        "chapter_files": plan.chapter_files,
        "engine_files": plan.engine_files,
        "synced_engines": plan.synced_engines,
        "issues": len(plan.issues),
        "skipped_reason": None,
    }


def build_retrospective_doctor_section(
    target: Path,
    *,
    book: str,
) -> tuple[RetrospectiveReport | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "book_retrospective": None,
            "chapters": 0,
            "retrospectives": 0,
            "missing_retrospectives": 0,
            "placeholder_retrospectives": 0,
            "sync_items": 0,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }

    book_root = target / "06_drafts" / book_id
    book_retro = book_retrospective_path(target, book=book_id)
    if not book_root.exists() and not book_retro.exists():
        return None, {
            "enabled": False,
            "book": book_id,
            "book_retrospective": str(book_retro),
            "chapters": 0,
            "retrospectives": 0,
            "missing_retrospectives": 0,
            "placeholder_retrospectives": 0,
            "sync_items": 0,
            "issues": 0,
            "skipped_reason": "book_not_found",
        }

    retrospective = build_retrospective_report(target, book=book_id)
    return retrospective, {
        "enabled": True,
        "book": retrospective.book,
        "book_retrospective": retrospective.book_retrospective_file,
        "chapters": retrospective.chapter_count,
        "retrospectives": retrospective.retrospective_count,
        "missing_retrospectives": retrospective.missing_retrospectives,
        "placeholder_retrospectives": retrospective.placeholder_retrospectives,
        "sync_items": retrospective.sync_item_count,
        "issues": len(retrospective.issues),
        "skipped_reason": None,
    }


def build_book_gate_doctor_section(
    target: Path,
    *,
    book: str,
    outline: str | None,
    min_chapter_chars: int,
    pattern: str,
) -> tuple[object | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "status": None,
            "ready": False,
            "issues": 0,
            "blocking_issues": 0,
            "checks": 0,
            "skipped_reason": "target_is_not_directory",
        }

    outline_path = resolve_outline_path(target, book=book_id, outline=outline)
    book_root = target / "06_drafts" / book_id
    book_retro = book_retrospective_path(target, book=book_id)
    if not outline_path.exists() and not book_root.exists() and not book_retro.exists():
        return None, {
            "enabled": False,
            "book": book_id,
            "status": None,
            "ready": False,
            "issues": 0,
            "blocking_issues": 0,
            "checks": 0,
            "skipped_reason": "book_not_found",
        }

    from .book_gate import build_book_gate

    gate = build_book_gate(
        target,
        book=book_id,
        outline=outline,
        min_chapter_chars=min_chapter_chars,
        pattern=pattern,
        out=None,
        force=False,
        dry_run=True,
    )
    return gate, {
        "enabled": True,
        "book": gate.book,
        "status": gate.status,
        "ready": gate.ready,
        "issues": gate.issue_count,
        "blocking_issues": gate.blocking_issue_count,
        "checks": len(gate.checks),
        "skipped_reason": None,
    }


def build_publish_doctor_section(
    target: Path,
    *,
    book: str,
    min_chapter_chars: int,
) -> tuple[PublishAuditReport | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    if target.is_file():
        publish = build_publish_audit_report(target, book=book_id, file_path=None, min_chapter_chars=min_chapter_chars)
        return publish, {
            "enabled": True,
            "book": publish.book,
            "clean_file": publish.clean_file,
            "clean_file_exists": publish.clean_file_exists,
            "draft_chapters": publish.draft_chapters,
            "clean_chapters": publish.clean_chapters,
            "total_nonspace_chars": publish.total_nonspace_chars,
            "total_cjk_chars": publish.total_cjk_chars,
            "issues": len(publish.issues),
            "skipped_reason": None,
        }

    clean_file = default_clean_output_path(target, book=book_id)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "clean_file": str(clean_file),
            "clean_file_exists": False,
            "draft_chapters": 0,
            "clean_chapters": 0,
            "total_nonspace_chars": 0,
            "total_cjk_chars": 0,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }

    if not clean_file.exists():
        return None, {
            "enabled": False,
            "book": book_id,
            "clean_file": str(clean_file),
            "clean_file_exists": False,
            "draft_chapters": 0,
            "clean_chapters": 0,
            "total_nonspace_chars": 0,
            "total_cjk_chars": 0,
            "issues": 0,
            "skipped_reason": "clean_markdown_not_found",
        }

    publish = build_publish_audit_report(target, book=book_id, file_path=None, min_chapter_chars=min_chapter_chars)
    return publish, {
        "enabled": True,
        "book": publish.book,
        "clean_file": publish.clean_file,
        "clean_file_exists": publish.clean_file_exists,
        "draft_chapters": publish.draft_chapters,
        "clean_chapters": publish.clean_chapters,
        "total_nonspace_chars": publish.total_nonspace_chars,
        "total_cjk_chars": publish.total_cjk_chars,
        "issues": len(publish.issues),
        "skipped_reason": None,
    }


def has_started_publish_metadata(metadata: dict[str, object]) -> bool:
    return any(not blank_value(value) for value in metadata.values())


def build_metadata_doctor_section(
    target: Path,
    *,
    book: str,
) -> tuple[PublishMetadataReport | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    if target.is_file():
        if "publish_checklist" not in target.name.lower():
            return None, {
                "enabled": False,
                "book": book_id,
                "checklist_file": None,
                "checklist_file_exists": False,
                "output_file": None,
                "metadata_file_exists": False,
                "fields_filled": 0,
                "issues": 0,
                "skipped_reason": "target_is_not_publish_checklist",
            }
        metadata = export_publish_metadata(
            target,
            book=book_id,
            file_path=None,
            out=None,
            force=False,
            dry_run=True,
        )
        return metadata, {
            "enabled": True,
            "book": metadata.book,
            "checklist_file": metadata.checklist_file,
            "checklist_file_exists": metadata.checklist_file_exists,
            "output_file": metadata.output_file,
            "metadata_file_exists": Path(metadata.output_file or "").exists(),
            "fields_filled": sum(1 for value in metadata.metadata.values() if not blank_value(value)),
            "issues": len(metadata.issues),
            "skipped_reason": None,
        }

    checklist_file = default_publish_checklist_path(target)
    metadata_file = default_metadata_output_path(target, book=book_id)
    clean_file = default_clean_output_path(target, book=book_id)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "checklist_file": str(checklist_file),
            "checklist_file_exists": False,
            "output_file": str(metadata_file),
            "metadata_file_exists": False,
            "fields_filled": 0,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }

    metadata = export_publish_metadata(
        target,
        book=book_id,
        file_path=None,
        out=None,
        force=False,
        dry_run=True,
    )
    fields_filled = sum(1 for value in metadata.metadata.values() if not blank_value(value))
    publish_stage_started = clean_file.exists() or metadata_file.exists() or has_started_publish_metadata(metadata.metadata)
    if not publish_stage_started:
        return None, {
            "enabled": False,
            "book": book_id,
            "checklist_file": metadata.checklist_file,
            "checklist_file_exists": metadata.checklist_file_exists,
            "output_file": metadata.output_file,
            "metadata_file_exists": metadata_file.exists(),
            "fields_filled": fields_filled,
            "issues": 0,
            "skipped_reason": "publish_stage_not_started",
        }

    return metadata, {
        "enabled": True,
        "book": metadata.book,
        "checklist_file": metadata.checklist_file,
        "checklist_file_exists": metadata.checklist_file_exists,
        "output_file": metadata.output_file,
        "metadata_file_exists": metadata_file.exists(),
        "fields_filled": fields_filled,
        "issues": len(metadata.issues),
        "skipped_reason": None,
    }


def manifest_hashes_match(path: Path, current_manifest: dict[str, object]) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(existing, dict):
        return False
    existing_files = existing.get("files", {})
    current_files = current_manifest.get("files", {})
    if not isinstance(existing_files, dict) or not isinstance(current_files, dict):
        return False
    for key in ("clean_markdown", "metadata_json"):
        existing_file = existing_files.get(key, {})
        current_file = current_files.get(key, {})
        if not isinstance(existing_file, dict) or not isinstance(current_file, dict):
            return False
        if existing_file.get("sha256") != current_file.get("sha256"):
            return False
    return True


def build_manifest_doctor_section(
    target: Path,
    *,
    book: str,
) -> tuple[PublishManifestReport | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    clean_file = default_clean_output_path(target, book=book_id)
    metadata_file = default_metadata_output_path(target, book=book_id)
    manifest_file = default_manifest_output_path(target, book=book_id)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "output_file": str(manifest_file),
            "manifest_file_exists": False,
            "clean_file_exists": False,
            "metadata_file_exists": False,
            "hashes_match": False,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }

    publish_stage_started = clean_file.exists() or metadata_file.exists() or manifest_file.exists()
    if not publish_stage_started:
        return None, {
            "enabled": False,
            "book": book_id,
            "output_file": str(manifest_file),
            "manifest_file_exists": False,
            "clean_file_exists": False,
            "metadata_file_exists": False,
            "hashes_match": False,
            "issues": 0,
            "skipped_reason": "publish_stage_not_started",
        }

    manifest = export_publish_manifest(
        target,
        book=book_id,
        clean_file=None,
        metadata_file=None,
        out=None,
        force=False,
        dry_run=True,
    )
    issues = list(manifest.issues)
    clean_exists = clean_file.exists()
    metadata_exists = metadata_file.exists()
    manifest_exists = manifest_file.exists()
    hashes_match = manifest_hashes_match(manifest_file, manifest.manifest) if manifest_exists else False
    if clean_exists and metadata_exists and not manifest_exists:
        issues.append(
            PublishManifestIssue(
                severity="P3",
                code="manifest_not_exported",
                path=str(manifest_file),
                message="Publish manifest has not been exported yet.",
            )
        )
    elif manifest_exists and clean_exists and metadata_exists and not hashes_match:
        issues.append(
            PublishManifestIssue(
                severity="P3",
                code="stale_manifest",
                path=str(manifest_file),
                message="Publish manifest hashes do not match the current clean Markdown or metadata JSON.",
            )
        )
    manifest.issues = issues
    return manifest, {
        "enabled": True,
        "book": manifest.book,
        "output_file": manifest.output_file,
        "manifest_file_exists": manifest_exists,
        "clean_file_exists": clean_exists,
        "metadata_file_exists": metadata_exists,
        "hashes_match": hashes_match,
        "issues": len(issues),
        "skipped_reason": None,
    }


def build_epub_doctor_section(
    target: Path,
    *,
    book: str,
) -> tuple[EpubAuditReport | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    clean_file = default_clean_output_path(target, book=book_id)
    metadata_file = default_metadata_output_path(target, book=book_id)
    manifest_file = default_manifest_output_path(target, book=book_id)
    epub_file = default_epub_output_path(target, book=book_id)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "output_file": str(epub_file),
            "epub_file_exists": False,
            "epub_valid": False,
            "manifest_file_exists": False,
            "chapter_count": 0,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }

    publish_stage_started = clean_file.exists() or metadata_file.exists() or manifest_file.exists() or epub_file.exists()
    if not publish_stage_started:
        return None, {
            "enabled": False,
            "book": book_id,
            "output_file": str(epub_file),
            "epub_file_exists": False,
            "epub_valid": False,
            "manifest_file_exists": False,
            "chapter_count": 0,
            "issues": 0,
            "skipped_reason": "publish_stage_not_started",
        }

    epub = build_epub_audit_report(
        target,
        book=book_id,
        file_path=None,
        clean_file=None,
        metadata_file=None,
        manifest_file=None,
    )
    return epub, {
        "enabled": True,
        "book": epub.book,
        "output_file": epub.epub_file,
        "epub_file_exists": epub.epub_file_exists,
        "epub_valid": epub.epub_valid,
        "manifest_file_exists": manifest_file.exists(),
        "chapter_count": epub.chapter_count,
        "issues": len(epub.issues),
        "skipped_reason": None,
    }


def build_model_config_doctor_section(target: Path) -> tuple[ModelConfigReport | None, dict[str, object]]:
    config_file = default_model_config_path(target)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "config_file": str(config_file),
            "config_file_exists": False,
            "provider": "",
            "planning_model": "",
            "drafting_model": "",
            "audit_model": "",
            "api_key_env": "",
            "env_present": False,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }

    if not looks_like_standard_project(target) and not config_file.exists():
        return None, {
            "enabled": False,
            "config_file": str(config_file),
            "config_file_exists": False,
            "provider": "",
            "planning_model": "",
            "drafting_model": "",
            "audit_model": "",
            "api_key_env": "",
            "env_present": False,
            "issues": 0,
            "skipped_reason": "target_is_not_standard_project",
        }

    model_config = build_model_config_report(target, write=False, dry_run=True)
    return model_config, {
        "enabled": True,
        "config_file": model_config.config_file,
        "config_file_exists": model_config.config_file_exists,
        "provider": model_config.provider,
        "planning_model": model_config.planning_model,
        "drafting_model": model_config.drafting_model,
        "audit_model": model_config.audit_model,
        "api_key_env": model_config.api_key_env,
        "env_present": model_config.env_present,
        "issues": len(model_config.issues),
        "skipped_reason": None,
    }


def build_agent_inbox_doctor_section(target: Path) -> tuple[AgentInboxReport | None, dict[str, object]]:
    runs_dir = default_agent_runs_dir(target)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "runs_dir": str(runs_dir),
            "status": None,
            "runs": 0,
            "ready": 0,
            "awaiting": 0,
            "needs_attention": 0,
            "issues": 0,
            "skipped_reason": "target_is_not_directory",
        }
    if not runs_dir.exists():
        return None, {
            "enabled": False,
            "runs_dir": str(runs_dir),
            "status": None,
            "runs": 0,
            "ready": 0,
            "awaiting": 0,
            "needs_attention": 0,
            "issues": 0,
            "skipped_reason": "agent_runs_not_found",
        }

    inbox = build_agent_inbox(target)
    return inbox, {
        "enabled": True,
        "runs_dir": inbox.runs_dir,
        "status": inbox.status,
        "runs": inbox.run_count,
        "ready": inbox.ready_count,
        "awaiting": inbox.awaiting_count,
        "needs_attention": inbox.needs_attention_count,
        "issues": len(inbox.issues),
        "skipped_reason": None,
    }


def empty_character_audit_report(target: Path) -> CharacterAuditReport:
    return CharacterAuditReport(
        target=str(target),
        index_file=None,
        intelligence_file=None,
        voice_file=None,
        relationship_file=None,
        arc_files=[],
        character_count=0,
        arc_count=0,
        index_count=0,
        intelligence_count=0,
        voice_count=0,
        relationship_count=0,
        issues=[],
        characters=[],
        arcs=[],
    )


def build_character_doctor_section(
    target: Path,
    *,
    pattern: str,
    enabled: bool,
) -> tuple[CharacterAuditReport, dict[str, object]]:
    if not enabled:
        return empty_character_audit_report(target), {
            "enabled": False,
            "characters": 0,
            "arc_files": 0,
            "index_rows": 0,
            "intelligence_rows": 0,
            "voice_rows": 0,
            "issues": 0,
            "skipped_reason": "target_is_not_standard_project",
        }

    characters = build_character_audit_report(target, pattern=pattern)
    return characters, {
        "enabled": True,
        "characters": characters.character_count,
        "arc_files": characters.arc_count,
        "index_rows": characters.index_count,
        "intelligence_rows": characters.intelligence_count,
        "voice_rows": characters.voice_count,
        "issues": len(characters.issues),
        "skipped_reason": None,
    }


def build_release_gate_doctor_section(
    target: Path,
    *,
    book: str,
    min_chapter_chars: int,
    publish: PublishAuditReport | None,
    metadata: PublishMetadataReport | None,
    manifest: PublishManifestReport | None,
    epub: EpubAuditReport | None,
) -> tuple[object | None, dict[str, object]]:
    book_id = normalize_book_for_plan(book)
    if not target.is_dir():
        return None, {
            "enabled": False,
            "book": book_id,
            "status": None,
            "ready": False,
            "issues": 0,
            "blocking_issues": 0,
            "checks": 0,
            "skipped_reason": "target_is_not_directory",
        }

    publish_started = any(item is not None for item in [publish, metadata, manifest, epub])
    if not publish_started:
        return None, {
            "enabled": False,
            "book": book_id,
            "status": None,
            "ready": False,
            "issues": 0,
            "blocking_issues": 0,
            "checks": 0,
            "skipped_reason": "publish_stage_not_started",
        }

    from .release_gate import build_release_gate

    gate = build_release_gate(
        target,
        book=book_id,
        min_chapter_chars=min_chapter_chars,
        out=None,
        force=False,
        dry_run=True,
    )
    return gate, {
        "enabled": True,
        "book": gate.book,
        "status": gate.status,
        "ready": gate.ready,
        "issues": gate.issue_count,
        "blocking_issues": gate.blocking_issue_count,
        "checks": len(gate.checks),
        "skipped_reason": None,
    }


def build_doctor_report(
    target: Path,
    *,
    all_markdown: bool,
    pattern: str,
    metric: str,
    skip_standard: bool,
    strict_standard: bool,
    min_chapter_chars: int,
    watch_terms: list[str],
    top: int,
    min_repeat: int,
    scan_text: bool,
    stale_after: int,
    book: str = "book_01",
    outline: str | None = None,
    flat_tolerance: int = 200,
    min_spread_ratio: int = 15,
    max_flat_run: int = 4,
    max_same_band_run: int = 5,
) -> DoctorReport:
    resolved = target.expanduser().resolve()
    standard_enabled = strict_standard or (not skip_standard and looks_like_standard_project(resolved))
    continuity = build_continuity_report(
        resolved,
        pattern=pattern,
        skip_standard=not standard_enabled,
        min_chapter_chars=min_chapter_chars,
    )
    character_enabled = looks_like_standard_project(resolved) or has_character_assets(resolved)
    character_report, character_section = build_character_doctor_section(
        resolved,
        pattern=pattern,
        enabled=character_enabled,
    )
    stats = build_stats_report(resolved, all_markdown=all_markdown, pattern=pattern, metric=metric)
    wave = build_chapter_wave_report(
        resolved,
        all_markdown=all_markdown,
        pattern=pattern,
        metric=metric,
        flat_tolerance=flat_tolerance,
        min_spread_ratio=min_spread_ratio,
        max_flat_run=max_flat_run,
        max_same_band_run=max_same_band_run,
    )
    style = build_style_audit_report(
        resolved,
        all_markdown=all_markdown,
        pattern=pattern,
        watch_terms=watch_terms,
        top=top,
        min_repeat=min_repeat,
    )
    word_scan = build_word_scan_report(
        resolved,
        all_markdown=all_markdown,
        pattern=pattern,
        watch=",".join(watch_terms),
        min_count=max(2, min_repeat),
        top=top,
    )
    tables = build_table_check_report(
        resolved,
        all_markdown=True,
        pattern=pattern,
        min_filled_cells=1,
    )
    table_issues = actionable_table_issues(tables)
    echoes = build_echo_report(
        resolved,
        pattern=pattern,
        table_path=None,
        scan_text=scan_text,
        stale_after=stale_after,
    )
    info = build_info_report(
        resolved,
        pattern=pattern,
        table_path=None,
        scan_text=scan_text,
    )
    plan_report, plan_section = build_plan_doctor_section(resolved, book=book, outline=outline)
    plan_issues = plan_report.issues if plan_report is not None else []
    retrospective_report, retrospective_section = build_retrospective_doctor_section(resolved, book=book)
    retrospective_issues = retrospective_report.issues if retrospective_report is not None else []
    book_gate_report, book_gate_section = build_book_gate_doctor_section(
        resolved,
        book=book,
        outline=outline,
        min_chapter_chars=min_chapter_chars,
        pattern=pattern,
    )
    agent_inbox_report, agent_inbox_section = build_agent_inbox_doctor_section(resolved)
    agent_inbox_issues = agent_inbox_report.issues if agent_inbox_report is not None else []
    model_config_report, model_config_section = build_model_config_doctor_section(resolved)
    model_config_issues = model_config_report.issues if model_config_report is not None else []
    publish_report, publish_section = build_publish_doctor_section(
        resolved,
        book=book,
        min_chapter_chars=min_chapter_chars,
    )
    publish_issues = publish_report.issues if publish_report is not None else []
    metadata_report, metadata_section = build_metadata_doctor_section(resolved, book=book)
    metadata_issues = metadata_report.issues if metadata_report is not None else []
    manifest_report, manifest_section = build_manifest_doctor_section(resolved, book=book)
    manifest_issues = manifest_report.issues if manifest_report is not None else []
    epub_report, epub_section = build_epub_doctor_section(resolved, book=book)
    epub_issues = epub_report.issues if epub_report is not None else []
    release_gate_report, release_gate_section = build_release_gate_doctor_section(
        resolved,
        book=book,
        min_chapter_chars=min_chapter_chars,
        publish=publish_report,
        metadata=metadata_report,
        manifest=manifest_report,
        epub=epub_report,
    )
    issue_counts = count_severities(
        wave.issues,
        table_issues,
        continuity.issues,
        character_report.issues,
        echoes.issues,
        info.issues,
        plan_issues,
        retrospective_issues,
        agent_inbox_issues,
        model_config_issues,
        publish_issues,
        metadata_issues,
        manifest_issues,
        epub_issues,
    )
    status = doctor_status(issue_counts)
    standard_check = "enabled" if standard_enabled else "skipped"
    return DoctorReport(
        target=str(resolved),
        status=status,
        standard_check=standard_check,
        issue_counts=issue_counts,
        stats={
            "mode": stats.mode,
            "metric": stats.metric,
            "files": stats.file_count,
            "total": stats.total,
            "average": stats.average,
            "minimum": stats.minimum,
            "maximum": stats.maximum,
        },
        wave={
            "mode": wave.mode,
            "metric": wave.metric,
            "files": wave.file_count,
            "average": wave.average,
            "minimum": wave.minimum,
            "maximum": wave.maximum,
            "spread": wave.spread,
            "spread_ratio_percent": wave.spread_ratio_percent,
            "average_delta": wave.average_delta,
            "longest_flat_run": wave.longest_flat_run,
            "longest_same_band_run": wave.longest_same_band_run,
            "band_counts": wave.band_counts,
            "issues": len(wave.issues),
        },
        style={
            "mode": style.mode,
            "files": style.file_count,
            "watch_hits": style.watch_total,
            "top_terms": [asdict(item) for item in style.aggregate_terms[:5]],
            "top_repeated_openings": [asdict(item) for item in style.repeated_openings[:5]],
            "opening_types": style.opening_types,
            "ending_types": style.ending_types,
        },
        word_scan={
            "mode": word_scan.mode,
            "files": word_scan.file_count,
            "total_latin_words": word_scan.total_latin_words,
            "total_phrases": word_scan.total_phrases,
            "watch_hits": [asdict(item) for item in word_scan.watch_hits[:5]],
            "top_terms": [asdict(item) for item in word_scan.aggregate_terms[:5]],
        },
        tables={
            "mode": tables.mode,
            "files": tables.file_count,
            "tables": tables.table_count,
            "issues": len(table_issues),
            "all_issues": tables.issue_count,
            "no_table_files": sum(1 for issue in tables.issues if issue.code == "no_tables"),
            "min_filled_cells": tables.min_filled_cells,
        },
        continuity={
            "chapters": continuity.chapter_count,
            "placeholder_chapters": continuity.placeholder_chapters,
            "missing_engines": continuity.missing_engine_count,
            "missing_retrospectives": continuity.missing_retrospective_count,
            "missing_standard_files": continuity.missing_standard_files,
            "placeholder_standard_files": continuity.placeholder_standard_files,
            "issues": len(continuity.issues),
        },
        characters=character_section,
        echoes={
            "table_files": len(echoes.table_files),
            "chapters": echoes.chapter_count,
            "threads": echoes.thread_count,
            "text_scan": echoes.text_scan,
            "issues": len(echoes.issues),
        },
        info={
            "table_files": len(info.table_files),
            "chapters": info.chapter_count,
            "items": info.item_count,
            "text_scan": info.text_scan,
            "issues": len(info.issues),
        },
        plan=plan_section,
        retrospective=retrospective_section,
        book_gate=book_gate_section,
        agent_inbox=agent_inbox_section,
        model_config=model_config_section,
        publish=publish_section,
        metadata=metadata_section,
        manifest=manifest_section,
        epub=epub_section,
        release_gate=release_gate_section,
        recommendations=build_doctor_recommendations(
            stats=stats,
            wave=wave,
            style=style,
            word_scan=word_scan,
            tables=tables,
            table_issues=table_issues,
            continuity=continuity,
            characters=character_report,
            echoes=echoes,
            info=info,
            plan=plan_report,
            retrospective=retrospective_report,
            book_gate=book_gate_report,
            agent_inbox=agent_inbox_report,
            model_config=model_config_report,
            publish=publish_report,
            metadata=metadata_report,
            manifest=manifest_report,
            epub=epub_report,
            release_gate=release_gate_report,
        ),
    )


def format_doctor_report(report: DoctorReport) -> str:
    lines = [
        "# FictionOps Doctor",
        "",
        f"- Target: `{report.target}`",
        f"- Status: `{report.status}`",
        f"- Standard project check: `{report.standard_check}`",
        f"- Issue counts: P1={report.issue_counts.get('P1', 0)}, P2={report.issue_counts.get('P2', 0)}, P3={report.issue_counts.get('P3', 0)}, P4={report.issue_counts.get('P4', 0)}",
        "",
        "## Summary",
        "",
        "| Area | Key Metrics |",
        "| --- | --- |",
        f"| Stats | files={report.stats['files']}, metric={report.stats['metric']}, total={report.stats['total']}, avg={report.stats['average']}, min/max={report.stats['minimum']}/{report.stats['maximum']} |",
        f"| Wave | files={report.wave['files']}, spread={report.wave['spread']} ({report.wave['spread_ratio_percent']}%), avg_delta={report.wave['average_delta']}, flat_run={report.wave['longest_flat_run']}, same_band_run={report.wave['longest_same_band_run']}, issues={report.wave['issues']} |",
        f"| Style | files={report.style['files']}, watch_hits={report.style['watch_hits']}, openings={format_counter_dict(report.style['opening_types'])} |",
        f"| Word Scan | files={report.word_scan['files']}, phrases={report.word_scan['total_phrases']}, latin_words={report.word_scan['total_latin_words']}, watch_hits={len(report.word_scan['watch_hits'])} |",
        f"| Tables | files={report.tables['files']}, tables={report.tables['tables']}, issues={report.tables['issues']}, no_table_files={report.tables['no_table_files']} |",
        f"| Continuity | chapters={report.continuity['chapters']}, missing_engines={report.continuity['missing_engines']}, missing_retrospectives={report.continuity['missing_retrospectives']}, issues={report.continuity['issues']} |",
        f"| Characters | characters={report.characters['characters']}, arcs={report.characters['arc_files']}, intelligence={report.characters['intelligence_rows']}, voice={report.characters['voice_rows']}, issues={report.characters['issues']} |",
        f"| Echoes | tables={report.echoes['table_files']}, threads={report.echoes['threads']}, issues={report.echoes['issues']}, text_scan={format_bool(bool(report.echoes['text_scan']))} |",
        f"| Information | tables={report.info['table_files']}, items={report.info['items']}, issues={report.info['issues']}, text_scan={format_bool(bool(report.info['text_scan']))} |",
        f"| Plan | book={report.plan['book']}, enabled={format_bool(bool(report.plan['enabled']))}, planned={report.plan['planned_chapters']}, synced_engines={report.plan['synced_engines']}, issues={report.plan['issues']} |",
        f"| Retrospective | book={report.retrospective['book']}, enabled={format_bool(bool(report.retrospective['enabled']))}, missing={report.retrospective['missing_retrospectives']}, sync_items={report.retrospective['sync_items']}, issues={report.retrospective['issues']} |",
        f"| Book Gate | book={report.book_gate['book']}, enabled={format_bool(bool(report.book_gate['enabled']))}, status={report.book_gate['status'] or '-'}, ready={format_bool(bool(report.book_gate['ready']))}, blocking={report.book_gate['blocking_issues']}, issues={report.book_gate['issues']} |",
        f"| Agent Inbox | enabled={format_bool(bool(report.agent_inbox['enabled']))}, status={report.agent_inbox['status'] or '-'}, runs={report.agent_inbox['runs']}, ready={report.agent_inbox['ready']}, awaiting={report.agent_inbox['awaiting']}, needs_attention={report.agent_inbox['needs_attention']}, issues={report.agent_inbox['issues']} |",
        f"| Model Config | enabled={format_bool(bool(report.model_config['enabled']))}, provider={report.model_config['provider'] or '-'}, config_file_exists={format_bool(bool(report.model_config['config_file_exists']))}, api_key_env={report.model_config['api_key_env'] or '-'}, env_present={format_bool(bool(report.model_config['env_present']))}, issues={report.model_config['issues']} |",
        f"| Publish | book={report.publish['book']}, enabled={format_bool(bool(report.publish['enabled']))}, clean_chapters={report.publish['clean_chapters']}, issues={report.publish['issues']} |",
        f"| Metadata | book={report.metadata['book']}, enabled={format_bool(bool(report.metadata['enabled']))}, fields_filled={report.metadata['fields_filled']}, issues={report.metadata['issues']} |",
        f"| Manifest | book={report.manifest['book']}, enabled={format_bool(bool(report.manifest['enabled']))}, exported={format_bool(bool(report.manifest['manifest_file_exists']))}, hashes_match={format_bool(bool(report.manifest['hashes_match']))}, issues={report.manifest['issues']} |",
        f"| EPUB | book={report.epub['book']}, enabled={format_bool(bool(report.epub['enabled']))}, exported={format_bool(bool(report.epub['epub_file_exists']))}, valid={format_bool(bool(report.epub['epub_valid']))}, chapters={report.epub['chapter_count']}, issues={report.epub['issues']} |",
        f"| Release Gate | book={report.release_gate['book']}, enabled={format_bool(bool(report.release_gate['enabled']))}, status={report.release_gate['status'] or '-'}, ready={format_bool(bool(report.release_gate['ready']))}, blocking={report.release_gate['blocking_issues']}, issues={report.release_gate['issues']} |",
        "",
        "## Top Style Markers",
        "",
    ]
    top_terms = report.style.get("top_terms", [])
    if top_terms:
        lines.extend(["| Term | Count |", "| --- | ---: |"])
        for item in top_terms:
            lines.append(f"| {safe_cell(str(item.get('item')))} | {item.get('count')} |")
    else:
        lines.append("No watched style markers found.")

    lines.extend(["", "## Top Word Scan Terms", ""])
    word_terms = report.word_scan.get("top_terms", [])
    if word_terms:
        lines.extend(["| Term | Count |", "| --- | ---: |"])
        for item in word_terms:
            lines.append(f"| {safe_cell(str(item.get('item')))} | {item.get('count')} |")
    else:
        lines.append("No repeated word-scan terms above threshold.")

    lines.extend(["", "## Recommendations", ""])
    if report.recommendations:
        for item in report.recommendations:
            lines.append(f"- {item}")
    else:
        lines.append("No maintenance recommendations.")
    return "\n".join(lines)
