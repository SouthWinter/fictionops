from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .continuity_audit import format_bool
from .echo_audit import blankish, cell_at, header_index, is_markdown_separator, split_markdown_row
from .markdown import clean_preview, collect_markdown_files, display_path, natural_key, safe_cell
from .models import CharacterArcFile, CharacterAuditIssue, CharacterAuditReport, CharacterProfile


ARC_DIR = "03_characters/character_arcs"
INDEX_FILE = "03_characters/character_index.md"
INTELLIGENCE_FILE = "03_characters/intelligence_profiles.md"
VOICE_FILE = "03_characters/voice_profiles.md"
RELATIONSHIP_FILE = "03_characters/relationship_map.md"


def normalize_character_name(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip()


def display_character(value: str) -> str:
    return value.strip() or "-"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_tables(path: Path) -> list[tuple[int, list[str], list[list[str]]]]:
    lines = read_text(path).splitlines()
    tables: list[tuple[int, list[str], list[list[str]]]] = []
    index = 0
    while index < len(lines) - 1:
        if "|" not in lines[index] or "|" not in lines[index + 1]:
            index += 1
            continue
        headers = split_markdown_row(lines[index])
        separator = split_markdown_row(lines[index + 1])
        if not is_markdown_separator(separator):
            index += 1
            continue
        rows: list[list[str]] = []
        row_index = index + 2
        while row_index < len(lines) and "|" in lines[row_index]:
            row = split_markdown_row(lines[row_index])
            if not is_markdown_separator(row):
                rows.append(row)
            row_index += 1
        tables.append((index + 1, headers, rows))
        index = row_index
    return tables


def first_table_with_character(path: Path) -> tuple[int, list[str], list[list[str]]] | None:
    for table in markdown_tables(path):
        _line, headers, _rows = table
        if header_index(headers, ["character", "name", "人物", "姓名", "角色"]) is not None:
            return table
    return None


def parse_character_table_names(path: Path) -> dict[str, int]:
    table = first_table_with_character(path)
    if table is None:
        return {}
    line, headers, rows = table
    character_i = header_index(headers, ["character", "name", "人物", "姓名", "角色"])
    names: dict[str, int] = {}
    for offset, row in enumerate(rows, start=2):
        name = cell_at(row, character_i)
        if blankish(name):
            continue
        names[normalize_character_name(name)] = line + offset
    return names


def parse_character_index(path: Path) -> tuple[dict[str, tuple[int, str]], list[CharacterAuditIssue]]:
    table = first_table_with_character(path)
    if table is None:
        return {}, [
            CharacterAuditIssue(
                "P3",
                "no_character_index_rows",
                "-",
                str(path),
                "Character index exists but no recognizable character rows were parsed.",
            )
        ]
    line, headers, rows = table
    character_i = header_index(headers, ["character", "name", "人物", "姓名", "角色"])
    arc_i = header_index(headers, ["arc", "arc file", "弧线文件", "人物弧线"])
    result: dict[str, tuple[int, str]] = {}
    for offset, row in enumerate(rows, start=2):
        name = cell_at(row, character_i)
        if blankish(name):
            continue
        result[normalize_character_name(name)] = (line + offset, cell_at(row, arc_i))
    issues: list[CharacterAuditIssue] = []
    if not result:
        issues.append(
            CharacterAuditIssue(
                "P3",
                "no_character_index_rows",
                "-",
                str(path),
                "Character index exists but no filled character rows were parsed.",
            )
        )
    return result, issues


def find_character_files(target: Path, *, pattern: str) -> tuple[Path | None, Path | None, Path | None, Path | None, list[Path]]:
    resolved = target.expanduser().resolve()
    if resolved.is_file():
        return None, None, None, None, [resolved] if resolved.suffix.lower() == ".md" else []

    index_file = resolved / INDEX_FILE
    intelligence_file = resolved / INTELLIGENCE_FILE
    voice_file = resolved / VOICE_FILE
    relationship_file = resolved / RELATIONSHIP_FILE
    arc_root = resolved / ARC_DIR
    if arc_root.exists():
        arc_files = sorted(
            [
                path
                for path in arc_root.glob("*.md")
                if path.is_file() and "template" not in path.stem.lower() and "模板" not in path.stem
            ],
            key=natural_key,
        )
    else:
        candidates = collect_markdown_files(resolved, all_markdown=True, pattern=pattern)
        arc_files = [
            path
            for path in candidates
            if ("character_arcs" in str(path).lower() or "人物弧线" in path.name)
            and "template" not in path.stem.lower()
            and "模板" not in path.stem
        ]
    return (
        index_file if index_file.exists() else None,
        intelligence_file if intelligence_file.exists() else None,
        voice_file if voice_file.exists() else None,
        relationship_file if relationship_file.exists() else None,
        arc_files,
    )


def parse_bullet_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"\s*[-*]\s*([^：:]+)[：:]\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        fields[key] = value
    return fields


def value_for(fields: dict[str, str], *labels: str) -> str:
    normalized = {re.sub(r"\s+", "", key): value for key, value in fields.items()}
    for label in labels:
        key = re.sub(r"\s+", "", label)
        if key in normalized:
            return normalized[key]
    return ""


def count_filled(*values: str) -> int:
    return sum(1 for value in values if not blankish(value))


def table_has_meaningful_row(path: Path, candidates: list[str], *, min_nonblank: int = 2) -> bool:
    for _line, headers, rows in markdown_tables(path):
        if not any(header_index(headers, [candidate]) is not None for candidate in candidates):
            continue
        for row in rows:
            nonblank = [cell for cell in row if not blankish(cell)]
            if len(nonblank) >= min_nonblank:
                return True
    return False


def growth_table_filled(path: Path) -> bool:
    for _line, headers, rows in markdown_tables(path):
        if header_index(headers, ["阶段", "phase", "stage"]) is None:
            continue
        filled_rows = 0
        for row in rows:
            nonblank = [cell for cell in row if not blankish(cell)]
            if len(nonblank) >= 3:
                filled_rows += 1
        return filled_rows >= 2
    return False


def paragraph_after_label(text: str, label: str) -> str:
    escaped = re.escape(label)
    pattern = rf"{escaped}[：:]?\s*(.*?)(?:\n\s*\n|^##|\Z)"
    match = re.search(pattern, text, flags=re.S | re.M)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def infer_character_name(path: Path, text: str, fields: dict[str, str]) -> str:
    name = value_for(fields, "姓名", "人物", "角色", "Name", "Character")
    if not blankish(name):
        return name.strip()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading = stripped.lstrip("#").strip()
        if heading and "模板" not in heading and "template" not in heading.lower():
            return heading.replace("人物弧线", "").replace("Character Arc", "").strip() or heading
    return path.stem


def analyze_arc_file(path: Path, *, base: Path) -> CharacterArcFile:
    text = read_text(path)
    fields = parse_bullet_fields(text)
    character = infer_character_name(path, text, fields)
    has_identity = not blankish(value_for(fields, "姓名", "Name", "Character"))
    has_start = count_filled(
        value_for(fields, "起点创伤"),
        value_for(fields, "起点欲望"),
        value_for(fields, "起点恐惧"),
        value_for(fields, "起点误解"),
        value_for(fields, "起点自我保护方式"),
    ) >= 2
    has_intelligence = table_has_meaningful_row(path, ["看得快的东西", "容易错过", "解决问题", "典型失败"], min_nonblank=2)
    has_voice = count_filled(
        value_for(fields, "说话节奏"),
        value_for(fields, "常用判断方式"),
        value_for(fields, "不会说的话"),
        value_for(fields, "紧张时的动作"),
        value_for(fields, "撒谎方式"),
        value_for(fields, "表达关心的方式"),
    ) >= 2
    has_relationships = table_has_meaningful_row(path, ["对象", "关系", "未说出口"], min_nonblank=2)
    has_growth = growth_table_filled(path)
    has_failure_path = not blankish(paragraph_after_label(text, "如果这个人物走偏，会变成")) or not blankish(
        paragraph_after_label(text, "这条失败路径在正文中如何诱惑他/她")
    )
    placeholder = not any(
        [
            has_identity,
            has_start,
            has_intelligence,
            has_voice,
            has_relationships,
            has_growth,
            has_failure_path,
        ]
    )
    return CharacterArcFile(
        path=display_path(path, base),
        character=character,
        placeholder=placeholder,
        has_identity=has_identity,
        has_start=has_start,
        has_intelligence=has_intelligence,
        has_voice=has_voice,
        has_relationships=has_relationships,
        has_growth=has_growth,
        has_failure_path=has_failure_path,
    )


def issue_for_arc_gap(arc: CharacterArcFile, code: str, severity: str, message: str) -> CharacterAuditIssue:
    return CharacterAuditIssue(severity, code, arc.character or "-", arc.path, message)


def build_character_audit_report(
    target: Path,
    *,
    pattern: str = "**/*.md",
) -> CharacterAuditReport:
    resolved = target.expanduser().resolve()
    base = resolved if resolved.is_dir() else resolved.parent
    index_file, intelligence_file, voice_file, relationship_file, arc_paths = find_character_files(resolved, pattern=pattern)
    issues: list[CharacterAuditIssue] = []

    index_entries: dict[str, tuple[int, str]] = {}
    if index_file is None:
        if resolved.is_dir():
            issues.append(
                CharacterAuditIssue(
                    "P3",
                    "missing_character_index",
                    "-",
                    INDEX_FILE,
                    "Character index is missing; handoff cannot see the cast at a glance.",
                )
            )
    else:
        index_entries, index_issues = parse_character_index(index_file)
        for issue in index_issues:
            issue.path = display_path(index_file, base)
        issues.extend(index_issues)

    intelligence_entries = parse_character_table_names(intelligence_file) if intelligence_file else {}
    voice_entries = parse_character_table_names(voice_file) if voice_file else {}
    relationship_entries = parse_character_table_names(relationship_file) if relationship_file else {}
    if intelligence_file is None and resolved.is_dir():
        issues.append(CharacterAuditIssue("P3", "missing_intelligence_profiles", "-", INTELLIGENCE_FILE, "Character intelligence profile table is missing."))
    elif intelligence_file is not None and not intelligence_entries:
        issues.append(CharacterAuditIssue("P3", "no_intelligence_profiles", "-", display_path(intelligence_file, base), "Intelligence profile table exists but has no filled character rows."))
    if voice_file is None and resolved.is_dir():
        issues.append(CharacterAuditIssue("P3", "missing_voice_profiles", "-", VOICE_FILE, "Character voice profile table is missing."))
    elif voice_file is not None and not voice_entries:
        issues.append(CharacterAuditIssue("P3", "no_voice_profiles", "-", display_path(voice_file, base), "Voice profile table exists but has no filled character rows."))

    arcs = [analyze_arc_file(path, base=base) for path in arc_paths]
    arc_by_name = {normalize_character_name(arc.character): arc for arc in arcs if not blankish(arc.character)}
    if resolved.is_dir() and not arcs:
        issues.append(
            CharacterAuditIssue(
                "P3",
                "missing_character_arcs",
                "-",
                ARC_DIR,
                "No filled character arc files were found; only templates or no arc files are present.",
            )
        )

    for arc in arcs:
        if arc.placeholder:
            issues.append(issue_for_arc_gap(arc, "placeholder_character_arc", "P3", "Character arc file still looks unfilled."))
            continue
        if not arc.has_identity:
            issues.append(issue_for_arc_gap(arc, "missing_character_identity", "P2", "Character arc has no filled identity/name field."))
        if not arc.has_start:
            issues.append(issue_for_arc_gap(arc, "missing_character_start", "P2", "Character arc lacks enough starting wound, desire, fear, or misunderstanding."))
        if not arc.has_intelligence:
            issues.append(issue_for_arc_gap(arc, "missing_character_intelligence", "P2", "Character arc lacks a filled intelligence/failure mode."))
        if not arc.has_voice:
            issues.append(issue_for_arc_gap(arc, "missing_character_voice", "P2", "Character arc lacks voice or behavior markers."))
        if not arc.has_growth:
            issues.append(issue_for_arc_gap(arc, "missing_character_growth", "P2", "Character arc lacks a filled growth path."))
        if not arc.has_failure_path:
            issues.append(issue_for_arc_gap(arc, "missing_failure_path", "P3", "Character arc lacks the tempting failure path."))
        if not arc.has_relationships:
            issues.append(issue_for_arc_gap(arc, "missing_relationship_anchors", "P4", "Character arc lacks relationship anchors."))

    all_names = set(index_entries) | set(arc_by_name) | set(intelligence_entries) | set(voice_entries)
    characters: list[CharacterProfile] = []
    for name in sorted(all_names):
        arc = arc_by_name.get(name)
        index_row = index_entries.get(name, (None, ""))[0]
        has_intelligence = name in intelligence_entries or (arc.has_intelligence if arc else False)
        has_voice = name in voice_entries or (arc.has_voice if arc else False)
        has_relationships = name in relationship_entries or (arc.has_relationships if arc else False)
        has_growth = arc.has_growth if arc else False
        has_failure_path = arc.has_failure_path if arc else False
        characters.append(
            CharacterProfile(
                character=display_character(name),
                arc_file=arc.path if arc else None,
                index_row=index_row,
                has_intelligence=has_intelligence,
                has_voice=has_voice,
                has_relationships=has_relationships,
                has_growth=has_growth,
                has_failure_path=has_failure_path,
            )
        )
        if name in index_entries and arc is None:
            row, arc_hint = index_entries[name]
            issues.append(
                CharacterAuditIssue(
                    "P2",
                    "indexed_character_missing_arc",
                    display_character(name),
                    f"{display_path(index_file, base) if index_file else INDEX_FILE}:{row}",
                    f"Indexed character has no matching filled arc file. Index arc hint: {arc_hint or '-'}",
                )
            )
        if arc is not None and name not in index_entries and index_file is not None:
            issues.append(
                CharacterAuditIssue(
                    "P4",
                    "arc_not_listed_in_index",
                    display_character(name),
                    arc.path,
                    "Character arc exists but the character is not listed in the character index.",
                )
            )
        if name in index_entries and not has_intelligence:
            issues.append(
                CharacterAuditIssue(
                    "P3",
                    "character_missing_intelligence_profile",
                    display_character(name),
                    display_path(intelligence_file, base) if intelligence_file else INTELLIGENCE_FILE,
                    "Indexed character has no filled intelligence profile.",
                )
            )
        if name in index_entries and not has_voice:
            issues.append(
                CharacterAuditIssue(
                    "P3",
                    "character_missing_voice_profile",
                    display_character(name),
                    display_path(voice_file, base) if voice_file else VOICE_FILE,
                    "Indexed character has no filled voice profile.",
                )
            )

    return CharacterAuditReport(
        target=str(resolved),
        index_file=display_path(index_file, base) if index_file else None,
        intelligence_file=display_path(intelligence_file, base) if intelligence_file else None,
        voice_file=display_path(voice_file, base) if voice_file else None,
        relationship_file=display_path(relationship_file, base) if relationship_file else None,
        arc_files=[arc.path for arc in arcs],
        character_count=len(characters),
        arc_count=len(arcs),
        index_count=len(index_entries),
        intelligence_count=len(intelligence_entries),
        voice_count=len(voice_entries),
        relationship_count=len(relationship_entries),
        issues=issues,
        characters=characters,
        arcs=arcs,
    )


def format_character_audit_report(report: CharacterAuditReport) -> str:
    lines = [
        "# FictionOps Character Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Characters: {report.character_count}",
        f"- Arc files: {report.arc_count}",
        f"- Index rows: {report.index_count}",
        f"- Intelligence rows: {report.intelligence_count}",
        f"- Voice rows: {report.voice_count}",
        f"- Issues: {len(report.issues)}",
        "",
        "## Files",
        "",
        f"- Index: `{report.index_file or '-'}`",
        f"- Intelligence: `{report.intelligence_file or '-'}`",
        f"- Voice: `{report.voice_file or '-'}`",
        f"- Relationship: `{report.relationship_file or '-'}`",
        "",
        "## Characters",
        "",
        "| Character | Arc | Intelligence | Voice | Relationships | Growth | Failure Path |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if report.characters:
        for character in report.characters:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(character.character),
                        f"`{safe_cell(character.arc_file)}`" if character.arc_file else "-",
                        format_bool(character.has_intelligence),
                        format_bool(character.has_voice),
                        format_bool(character.has_relationships),
                        format_bool(character.has_growth),
                        format_bool(character.has_failure_path),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| - | - | - | - | - | - | - |")

    lines.extend(["", "## Arc Files", ""])
    if report.arcs:
        lines.extend(
            [
                "| Character | Path | Placeholder | Start | Intelligence | Voice | Growth | Failure Path |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for arc in report.arcs:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(clean_preview(arc.character, 24)),
                        f"`{safe_cell(arc.path)}`",
                        format_bool(arc.placeholder),
                        format_bool(arc.has_start),
                        format_bool(arc.has_intelligence),
                        format_bool(arc.has_voice),
                        format_bool(arc.has_growth),
                        format_bool(arc.has_failure_path),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No filled character arc files found.")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Character | Path | Message |", "| --- | --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        issue.severity,
                        f"`{safe_cell(issue.code)}`",
                        safe_cell(issue.character),
                        f"`{safe_cell(issue.path)}`",
                        safe_cell(issue.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No character maintenance issues found.")
    return "\n".join(lines)


def render_character_audit_report(report: CharacterAuditReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ == "table":
        return format_character_audit_report(report)
    raise ValueError(f"Unsupported character audit format: {format_}")
