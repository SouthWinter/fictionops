from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .markdown import natural_key


IGNORED_DIRS = {
    ".git",
    ".github",
    ".venv",
    "__pycache__",
    "agent_runs",
    "agent_sessions",
    "fictionops",
    "build",
    "dist",
    "08_publish",
}

CANON_NAME_PATTERN = re.compile(
    r"大纲|总纲|书纲|卷纲|人物|弧线|信息|释放|伏笔|回声|正史|连续|时间|物件|口吻|智慧|写作|风格|"
    r"outline|character|arc|information|echo|canon|continuity|timeline|object|voice|style",
    flags=re.IGNORECASE,
)

CHAPTER_NAME_PATTERN = re.compile(r"(?:第\s*\d+\s*章|ch[_-]?\d+)", flags=re.IGNORECASE)


@dataclass
class ProjectContextItem:
    role: str
    path: str
    authority: str
    reason: str
    sha256: str
    chars: int
    included_chars: int
    truncated: bool
    content: str


@dataclass
class ProjectContextBundle:
    schema: str
    project_root: str
    task: str
    target_file: str
    source_chars: int
    max_files: int
    max_total_chars: int
    included_chars: int
    truncated: bool
    items: list[ProjectContextItem]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def discover_project_root(path: Path) -> Path:
    start = path if path.is_dir() else path.parent
    markers = ("00_management", "00_总纲与管理", "01_人物弧线", "04_structure", "卷一_冰角")
    for current in [start, *start.parents]:
        if any((current / marker).exists() for marker in markers):
            return current.resolve()
    return start.resolve()


def ignored(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return any(part in IGNORED_DIRS for part in relative.parts)


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        [path for path in root.rglob("*.md") if path.is_file() and not ignored(path, root)],
        key=natural_key,
    )


def adjacent_chapters(target: Path) -> list[Path]:
    if not target.parent.exists():
        return []
    chapters = sorted(
        [path for path in target.parent.glob("*.md") if path.is_file() and CHAPTER_NAME_PATTERN.search(path.stem)],
        key=natural_key,
    )
    if not chapters:
        return []
    resolved = target.resolve()
    if resolved in [path.resolve() for path in chapters]:
        index = next(index for index, path in enumerate(chapters) if path.resolve() == resolved)
    else:
        target_key = natural_key(target)
        index = next((index for index, path in enumerate(chapters) if natural_key(path) > target_key), len(chapters))
    result: list[Path] = []
    if index > 0:
        result.append(chapters[index - 1])
    if index < len(chapters) and chapters[index].resolve() != resolved:
        result.append(chapters[index])
    elif index + 1 < len(chapters):
        result.append(chapters[index + 1])
    return result


def candidate_score(path: Path, *, root: Path, target: Path, evidence_text: str) -> tuple[int, str, str, str]:
    relative = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    stem = path.stem
    score = 0
    role = "project memory"
    authority = "supporting"
    reasons: list[str] = []
    is_chapter = bool(CHAPTER_NAME_PATTERN.search(stem))
    if path.parent == target.parent and not is_chapter:
        score += 80
        role = "same-book material"
        authority = "plan"
        reasons.append("same directory as target chapter")
    if CANON_NAME_PATTERN.search(path.name):
        score += 45
        reasons.append("filename indicates outline/canon/character memory")
    if is_chapter:
        score -= 100
        reasons.append("non-adjacent chapter excluded from bounded context")
    if re.search(r"发布|简介|标签|清稿|打包|publish|metadata", relative, flags=re.IGNORECASE):
        score -= 120
        reasons.append("publishing material is irrelevant to chapter semantics")
    if re.search(r"字数统计|文件统计|接手日志|当前接手摘要", path.name, flags=re.IGNORECASE):
        score -= 100
        reasons.append("operational summary is not task evidence")
    if re.search(r"人物|character|arc|弧线", relative, flags=re.IGNORECASE):
        role = "character memory"
        authority = "canon"
    elif re.search(r"信息|释放|伏笔|回声|正史|时间|物件|canon|information|echo|timeline|object", relative, flags=re.IGNORECASE):
        role = "canon boundary"
        authority = "canon"
    elif re.search(r"大纲|总纲|书纲|卷纲|outline", relative, flags=re.IGNORECASE):
        role = "outline"
        authority = "plan"
    elif re.search(r"写作|风格|口吻|智慧|voice|style", relative, flags=re.IGNORECASE):
        role = "writing guidance"
        authority = "guidance"
    compact_stem = re.sub(r"(人物弧线|人物|弧线|设定|总设|arc|profile).*$", "", stem, flags=re.IGNORECASE)
    generic_entities = {"江山", "人物", "角色", "主要", "完整", "全书", "当前", "写作", "章节", "第一", "第二", "第三", "第四"}
    entity = ""
    for token in re.split(r"[_\-\s]", compact_stem):
        if not token or token in generic_entities:
            continue
        for width in range(min(4, len(token)), 1, -1):
            prefix = token[:width]
            if prefix not in generic_entities and prefix in evidence_text:
                entity = prefix
                break
        if entity:
            break
    if entity:
        score += 100
        reasons.append(f"filename entity `{entity}` appears in task evidence")
    if role == "character memory" and not entity and not re.search(r"主要角色|智慧|口吻|少女角色|voice_profiles|intelligence_profiles", path.name, flags=re.IGNORECASE):
        score -= 60
        reasons.append("unmatched character-specific memory excluded")
    depth = len(path.relative_to(root).parts) if path.is_relative_to(root) else 9
    score -= min(depth, 8)
    return score, role, authority, "; ".join(reasons) or "project-memory candidate"


def add_unique(
    selected: list[tuple[Path, str, str, str]],
    seen: set[Path],
    path: Path | None,
    *,
    role: str,
    authority: str,
    reason: str,
) -> None:
    if path is None:
        return
    resolved = path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_file() or resolved.suffix.lower() != ".md" or resolved in seen:
        return
    selected.append((resolved, role, authority, reason))
    seen.add(resolved)


def compile_project_context(
    target_file: Path,
    *,
    task: str,
    source_text: str,
    engine_file: Path | None = None,
    outline_file: Path | None = None,
    explicit_files: list[Path] | None = None,
    max_files: int = 24,
    max_chars_per_file: int = 10000,
    max_total_chars: int = 100000,
) -> ProjectContextBundle:
    if max_files < 1:
        raise ValueError("max_files must be at least 1")
    if max_chars_per_file < 1 or max_total_chars < 1:
        raise ValueError("context character budgets must be positive")
    target = target_file.expanduser().resolve()
    root = discover_project_root(target)
    selected: list[tuple[Path, str, str, str]] = []
    seen: set[Path] = set()
    add_unique(selected, seen, engine_file, role="chapter engine", authority="plan", reason="explicit chapter engine")
    add_unique(selected, seen, outline_file, role="outline", authority="plan", reason="explicit outline")
    for path in explicit_files or []:
        add_unique(selected, seen, path, role="explicit context", authority="canon", reason="explicitly requested context")
    for path in adjacent_chapters(target):
        relative_position = "previous or next chapter"
        add_unique(selected, seen, path, role="adjacent chapter", authority="manuscript", reason=relative_position)

    evidence_text = "\n".join(
        [
            source_text,
            engine_file.read_text(encoding="utf-8") if engine_file and engine_file.exists() else "",
            outline_file.read_text(encoding="utf-8") if outline_file and outline_file.exists() else "",
        ]
    )
    scored: list[tuple[int, Path, str, str, str]] = []
    for path in markdown_files(root):
        resolved = path.resolve()
        if resolved in seen or resolved == target:
            continue
        score, role, authority, reason = candidate_score(path, root=root, target=target, evidence_text=evidence_text)
        if score >= 35:
            scored.append((score, resolved, role, authority, reason))
    scored.sort(key=lambda item: (-item[0], natural_key(item[1])))
    # Preserve evidence diversity before filling the remaining slots by score.
    # Without this reservation, two long adjacent chapters and one large outline
    # can consume the entire character budget before writing guidance is reached.
    for required_role in ("outline", "canon boundary", "character memory", "writing guidance"):
        if any(role == required_role for _path, role, _authority, _reason in selected):
            continue
        match = next((item for item in scored if item[2] == required_role), None)
        if match is None:
            continue
        _score, path, role, authority, reason = match
        add_unique(selected, seen, path, role=role, authority=authority, reason=reason)
    core_count = min(len(selected), max_files)
    for _score, path, role, authority, reason in scored:
        if len(selected) >= max_files:
            break
        add_unique(selected, seen, path, role=role, authority=authority, reason=reason)

    items: list[ProjectContextItem] = []
    remaining = max_total_chars
    for index, (path, role, authority, reason) in enumerate(selected[:max_files]):
        if remaining <= 0:
            break
        text = path.read_text(encoding="utf-8")
        core_remaining = max(core_count - index, 1) if index < core_count else 1
        reserved_share = max(1, remaining // core_remaining)
        limit = min(max_chars_per_file, reserved_share if index < core_count else remaining)
        content = text[:limit]
        truncated = len(text) > limit
        items.append(
            ProjectContextItem(
                role=role,
                path=str(path),
                authority=authority,
                reason=reason,
                sha256=sha256_text(text),
                chars=len(text),
                included_chars=len(content),
                truncated=truncated,
                content=content.rstrip() + ("\n\n...[truncated]" if truncated else ""),
            )
        )
        remaining -= len(content)
    included = sum(item.included_chars for item in items)
    return ProjectContextBundle(
        schema="fictionops.project_context.v1",
        project_root=str(root),
        task=task,
        target_file=str(target),
        source_chars=len(source_text),
        max_files=max_files,
        max_total_chars=max_total_chars,
        included_chars=included,
        truncated=len(selected) > len(items) or any(item.truncated for item in items),
        items=items,
    )


def render_project_context(bundle: ProjectContextBundle) -> str:
    lines = [
        "# FictionOps Project-Aware Context",
        "",
        f"- Project root: `{bundle.project_root}`",
        f"- Task: `{bundle.task}`",
        f"- Target: `{bundle.target_file}`",
        f"- Included files: {len(bundle.items)}",
        f"- Included chars: {bundle.included_chars}/{bundle.max_total_chars}",
        "",
        "## Manifest",
        "",
        "```json",
        json.dumps(
            {
                **asdict(bundle),
                "items": [{key: value for key, value in asdict(item).items() if key != "content"} for item in bundle.items],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
    ]
    for item in bundle.items:
        lines.extend(
            [
                "",
                f"## {item.role}: `{item.path}`",
                "",
                f"Authority: `{item.authority}`. Included because: {item.reason}.",
                "",
                item.content,
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
