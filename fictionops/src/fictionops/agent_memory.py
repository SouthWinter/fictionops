from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


MEMORY_INDEX_SCHEMA = "fictionops.memory_index.v1"
MEMORY_QUERY_SCHEMA = "fictionops.memory_query.v1"
PREFERENCE_SCHEMA = "fictionops.author_preference.v1"
ACCEPTANCE_MEMORY_SCHEMA = "fictionops.acceptance_memory.v1"

IGNORED_DIRS = {
    ".git",
    ".github",
    ".venv",
    ".fictionops",
    "__pycache__",
    "agent_runs",
    "agent_sessions",
    "fictionops",
    "build",
    "dist",
    "08_publish",
    "archive",
    "archives",
    "归档_旧稿",
    "旧稿归档",
    "历史旧稿",
}

OPERATIONAL_FILE_PATTERN = re.compile(
    r"接手日志|handoff[_-]?log|字数统计|文件统计|发布清单|打包记录|运行日志|agent[_-]?run",
    flags=re.IGNORECASE,
)

AUTHORITY_WEIGHT = {
    "author_explicit": 80,
    "canon": 65,
    "accepted_manuscript": 55,
    "plan": 40,
    "guidance": 35,
    "supporting": 15,
}


@dataclass
class MemoryRecord:
    memory_id: str
    kind: str
    authority: str
    source: str
    source_sha256: str
    heading: str
    start_line: int
    end_line: int
    scope: list[str]
    tags: list[str]
    summary: str
    search_text: str
    inline_content: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_source_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16"
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", data, 0, min(len(data), 1), "unsupported text encoding")


def discover_memory_root(path: Path) -> Path:
    start = path.expanduser().resolve()
    if start.is_file():
        start = start.parent
    markers = ("00_management", "00_总纲与管理", "01_人物弧线", "04_structure", "卷一_冰角", "pyproject.toml")
    for current in [start, *start.parents]:
        if any((current / marker).exists() for marker in markers):
            return current
    return start


def memory_paths(root: Path) -> dict[str, Path]:
    directory = root / ".fictionops" / "memory"
    return {
        "directory": directory,
        "index": directory / "index.json",
        "preferences": directory / "preferences.jsonl",
        "acceptances": directory / "acceptance_events.jsonl",
        "stale": directory / "stale.json",
    }


def ignored(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return any(part in IGNORED_DIRS for part in relative.parts)


def classify_source(path: Path) -> tuple[str, str]:
    value = path.name.lower()
    if re.search(r"人物|弧线|character|arc|voice|智慧", value):
        return "character", "canon"
    if re.search(r"信息|释放|正史|时间|物件|伏笔|回声|canon|information|timeline|object|echo", value):
        return "canon", "canon"
    if re.search(r"写作|风格|口吻|经验|style|guidance|preference", value):
        return "guidance", "guidance"
    if re.search(r"大纲|总纲|书纲|卷纲|发动机|outline|engine|plan", value):
        return "plan", "plan"
    if re.search(r"第\s*\d+\s*章|ch[_-]?\d+", path.stem, flags=re.IGNORECASE):
        return "manuscript", "accepted_manuscript"
    return "supporting", "supporting"


def compact(value: str, limit: int = 240) -> str:
    collapsed = re.sub(r"\s+", " ", value).strip()
    return collapsed[:limit]


def scope_for(path: Path, root: Path, heading: str) -> list[str]:
    relative = path.relative_to(root) if path.is_relative_to(root) else path
    values = [part for part in relative.parts[:-1] if part not in {".", ".."}]
    values.extend(token for token in re.split(r"[_\-\s《》：:]+", path.stem) if len(token) >= 2)
    values.extend(token for token in re.split(r"[_\-\s《》：:]+", heading.lstrip("# ")) if len(token) >= 2)
    return list(dict.fromkeys(values))[:20]


def tags_for(text: str, path: Path, heading: str) -> list[str]:
    seed = " ".join((path.stem, heading, compact(text, 1000)))
    tags: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,32}|[\u4e00-\u9fff]{2,12}", seed):
        if token not in tags:
            tags.append(token)
        if re.fullmatch(r"[\u4e00-\u9fff]{5,12}", token):
            for width in (2, 3, 4):
                for index in range(0, len(token) - width + 1):
                    piece = token[index : index + width]
                    if piece not in tags:
                        tags.append(piece)
        if len(tags) >= 160:
            break
    return tags


def markdown_sections(text: str, *, max_chars: int = 4000) -> list[tuple[str, int, int, str]]:
    lines = text.splitlines()
    if not lines:
        return []
    sections: list[tuple[str, int, int, str]] = []
    heading = "document"
    start = 1
    buffer: list[str] = []

    def flush(end_line: int) -> None:
        nonlocal buffer, start
        if not any(line.strip() for line in buffer):
            buffer = []
            start = end_line + 1
            return
        chunk: list[str] = []
        chunk_start = start
        chunk_chars = 0
        for offset, line in enumerate(buffer):
            line_no = start + offset
            addition = len(line) + 1
            if chunk and chunk_chars + addition > max_chars:
                sections.append((heading, chunk_start, line_no - 1, "\n".join(chunk).strip()))
                chunk = []
                chunk_start = line_no
                chunk_chars = 0
            chunk.append(line)
            chunk_chars += addition
        if chunk:
            sections.append((heading, chunk_start, end_line, "\n".join(chunk).strip()))
        buffer = []
        start = end_line + 1

    for index, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#") and buffer:
            flush(index - 1)
            heading = line.strip()
            start = index
        elif line.lstrip().startswith("#"):
            heading = line.strip()
            start = index
        buffer.append(line)
    flush(len(lines))
    return sections


def preference_records(root: Path) -> list[MemoryRecord]:
    path = memory_paths(root)["preferences"]
    if not path.exists():
        return []
    records: list[MemoryRecord] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict) or payload.get("schema") != PREFERENCE_SCHEMA:
            raise ValueError(f"invalid author preference at {path}:{line_no}")
        content = "\n".join(
            [
                f"Rule: {payload.get('rule') or ''}",
                f"Prefer: {payload.get('prefer') or ''}",
                f"Avoid: {payload.get('avoid') or ''}",
                f"Exceptions: {payload.get('exceptions') or ''}",
                f"Evidence: {payload.get('evidence') or ''}",
            ]
        ).strip()
        records.append(
            MemoryRecord(
                memory_id=str(payload.get("preference_id")),
                kind="preference",
                authority="author_explicit",
                source=str(path),
                source_sha256=sha256_text(line),
                heading=str(payload.get("rule") or "author preference"),
                start_line=line_no,
                end_line=line_no,
                scope=[str(item) for item in payload.get("scope") or []],
                tags=tags_for(content, path, str(payload.get("rule") or "")),
                summary=compact(content),
                search_text=content,
                inline_content=content,
            )
        )
    return records


def build_memory_index(path: Path, *, write: bool = True) -> dict[str, object]:
    root = discover_memory_root(path)
    records: list[MemoryRecord] = []
    source_manifest: list[dict[str, object]] = []
    scan_errors: list[dict[str, str]] = []
    sources = sorted(
        [
            item
            for item in root.rglob("*.md")
            if item.is_file() and not ignored(item, root) and not OPERATIONAL_FILE_PATTERN.search(item.name)
        ],
        key=lambda item: str(item).casefold(),
    )
    for source in sources:
        try:
            text, encoding = read_source_text(source)
        except (OSError, UnicodeDecodeError) as exc:
            scan_errors.append({"path": str(source.resolve()), "error": str(exc)})
            continue
        digest = sha256_text(text)
        kind, authority = classify_source(source)
        source_manifest.append({"path": str(source.resolve()), "sha256": digest, "chars": len(text), "encoding": encoding})
        for heading, start_line, end_line, content in markdown_sections(text):
            if not content:
                continue
            token = sha256_text(f"{source.resolve()}|{start_line}|{end_line}|{digest}")[:16]
            records.append(
                MemoryRecord(
                    memory_id=f"mem_{token}",
                    kind=kind,
                    authority=authority,
                    source=str(source.resolve()),
                    source_sha256=digest,
                    heading=heading,
                    start_line=start_line,
                    end_line=end_line,
                    scope=scope_for(source, root, heading),
                    tags=tags_for(content, source, heading),
                    summary=compact(content),
                    search_text=compact(content, 4000),
                )
            )
    records.extend(preference_records(root))
    payload: dict[str, object] = {
        "schema": MEMORY_INDEX_SCHEMA,
        "project_root": str(root),
        "generated_at": utc_now(),
        "record_count": len(records),
        "source_count": len(source_manifest),
        "source_manifest": source_manifest,
        "scan_errors": scan_errors,
        "records": [asdict(record) for record in records],
    }
    if write:
        paths = memory_paths(root)
        paths["directory"].mkdir(parents=True, exist_ok=True)
        paths["index"].write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        if paths["stale"].exists():
            paths["stale"].unlink()
    return payload


def load_memory_index(path: Path, *, rebuild_if_missing: bool = True, write: bool = True) -> dict[str, object]:
    root = discover_memory_root(path)
    paths = memory_paths(root)
    if paths["index"].exists() and not paths["stale"].exists():
        payload = json.loads(paths["index"].read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("schema") == MEMORY_INDEX_SCHEMA:
            return payload
    if not rebuild_if_missing:
        raise FileNotFoundError(paths["index"])
    return build_memory_index(root, write=write)


def query_terms(query: str) -> set[str]:
    terms: set[str] = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,32}|[\u4e00-\u9fff]{2,20}", query):
        terms.add(token.casefold())
        if re.fullmatch(r"[\u4e00-\u9fff]{3,20}", token):
            for width in (2, 3, 4):
                for index in range(0, len(token) - width + 1):
                    terms.add(token[index : index + width])
    return {term for term in terms if len(term) >= 2}


def source_segment(record: dict[str, object]) -> str:
    inline = record.get("inline_content")
    if isinstance(inline, str) and inline.strip():
        return inline.strip()
    source = Path(str(record.get("source") or ""))
    if not source.is_file():
        return ""
    try:
        text, _encoding = read_source_text(source)
    except (OSError, UnicodeDecodeError):
        return ""
    if sha256_text(text) != str(record.get("source_sha256") or ""):
        return ""
    lines = text.splitlines()
    start = max(0, int(record.get("start_line") or 1) - 1)
    end = min(len(lines), int(record.get("end_line") or len(lines)))
    return "\n".join(lines[start:end]).strip()


def query_memory(
    path: Path,
    *,
    query: str,
    kinds: list[str] | None = None,
    max_items: int = 16,
    max_chars: int = 30000,
    write_index: bool = True,
    index_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if max_items < 1 or max_chars < 1:
        raise ValueError("memory query budgets must be positive")
    index = index_payload or load_memory_index(path, rebuild_if_missing=True, write=write_index)
    terms = query_terms(query)
    allowed = set(kinds or [])
    scored: list[tuple[int, dict[str, object]]] = []
    for raw in index.get("records") or []:
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("kind") or "supporting")
        if allowed and kind not in allowed:
            continue
        tags = {str(item).casefold() for item in raw.get("tags") or []}
        scope = {str(item).casefold() for item in raw.get("scope") or []}
        heading = str(raw.get("heading") or "").casefold()
        search = str(raw.get("search_text") or "").casefold()
        source = str(raw.get("source") or "").casefold()
        overlap = terms & (tags | scope)
        score = AUTHORITY_WEIGHT.get(str(raw.get("authority") or "supporting"), 0)
        score += 18 * len(overlap)
        score += sum(8 for term in terms if term in heading)
        score += sum(5 for term in terms if term in source)
        score += min(30, sum(2 for term in terms if term in search))
        if kind == "preference":
            score += 220
        if overlap or kind == "preference" or score >= 70:
            scored.append((score, raw))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("source")), int(item[1].get("start_line") or 0)))
    selected: list[dict[str, object]] = []
    remaining = max_chars
    seen_sources: dict[str, int] = {}
    for score, record in scored:
        if len(selected) >= max_items or remaining <= 0:
            break
        source = str(record.get("source") or "")
        if seen_sources.get(source, 0) >= 3 and str(record.get("kind")) != "preference":
            continue
        content = source_segment(record)
        if not content:
            continue
        per_record_limit = remaining if str(record.get("kind")) == "preference" else min(4000, remaining)
        included = content[:per_record_limit]
        selected.append(
            {
                **{key: value for key, value in record.items() if key not in {"search_text", "inline_content"}},
                "score": score,
                "content": included,
                "truncated": len(included) < len(content),
            }
        )
        remaining -= len(included)
        seen_sources[source] = seen_sources.get(source, 0) + 1
    return {
        "schema": MEMORY_QUERY_SCHEMA,
        "project_root": index.get("project_root"),
        "query": query,
        "terms": sorted(terms),
        "record_count": len(selected),
        "included_chars": sum(len(str(item.get("content") or "")) for item in selected),
        "max_items": max_items,
        "max_chars": max_chars,
        "results": selected,
    }


def render_memory_query(payload: dict[str, object]) -> str:
    lines = [
        "# FictionOps Retrieved Memory",
        "",
        f"- Query: {payload.get('query')}",
        f"- Records: {payload.get('record_count')}",
        f"- Included chars: {payload.get('included_chars')}/{payload.get('max_chars')}",
    ]
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                "",
                f"## {item.get('kind')}: `{item.get('source')}:{item.get('start_line')}`",
                "",
                f"Authority: `{item.get('authority')}`. Score: {item.get('score')}.",
                "",
                str(item.get("content") or ""),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def append_author_preference(
    path: Path,
    *,
    rule: str,
    evidence: str,
    prefer: str = "",
    avoid: str = "",
    exceptions: str = "",
    scope: list[str] | None = None,
) -> dict[str, object]:
    if not rule.strip() or not evidence.strip():
        raise ValueError("author preferences require both rule and evidence")
    root = discover_memory_root(path)
    paths = memory_paths(root)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    token = sha256_text("|".join((rule.strip(), evidence.strip(), ",".join(scope or []))))[:16]
    preference = {
        "schema": PREFERENCE_SCHEMA,
        "preference_id": f"pref_{token}",
        "rule": rule.strip(),
        "prefer": prefer.strip(),
        "avoid": avoid.strip(),
        "exceptions": exceptions.strip(),
        "scope": [item.strip() for item in scope or [] if item.strip()],
        "evidence": evidence.strip(),
        "authority": "author_explicit",
        "created_at": utc_now(),
    }
    existing = paths["preferences"].read_text(encoding="utf-8") if paths["preferences"].exists() else ""
    if any(
        isinstance(item, dict) and item.get("preference_id") == preference["preference_id"]
        for item in (json.loads(line) for line in existing.splitlines() if line.strip())
    ):
        raise FileExistsError(f"author preference already exists: {preference['preference_id']}")
    with paths["preferences"].open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(preference, ensure_ascii=False, sort_keys=True) + "\n")
    paths["stale"].write_text(
        json.dumps({"schema": "fictionops.memory_stale.v1", "reason": "author_preference_added", "at": utc_now()}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return preference


def record_acceptance_memory(
    path: Path,
    *,
    session_id: str,
    source_file: Path,
    source_sha256_before: str,
    source_sha256_after: str,
    run_dir: Path,
    canon_sync_suggestions: list[object] | None = None,
) -> dict[str, object]:
    root = discover_memory_root(path)
    paths = memory_paths(root)
    paths["directory"].mkdir(parents=True, exist_ok=True)
    event = {
        "schema": ACCEPTANCE_MEMORY_SCHEMA,
        "session_id": session_id,
        "source_file": str(source_file.resolve()),
        "source_sha256_before": source_sha256_before,
        "source_sha256_after": source_sha256_after,
        "run_dir": str(run_dir.resolve()),
        "canon_sync_suggestions": canon_sync_suggestions or [],
        "authority": "accepted_manuscript",
        "accepted_at": utc_now(),
    }
    with paths["acceptances"].open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    paths["stale"].write_text(
        json.dumps({"schema": "fictionops.memory_stale.v1", "reason": "manuscript_accepted", "at": utc_now()}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return event


def memory_status(path: Path) -> dict[str, object]:
    root = discover_memory_root(path)
    paths = memory_paths(root)
    index: dict[str, object] = {}
    if paths["index"].exists():
        raw = json.loads(paths["index"].read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            index = raw
    return {
        "schema": "fictionops.memory_status.v1",
        "project_root": str(root),
        "index_file": str(paths["index"]),
        "index_exists": paths["index"].exists(),
        "stale": paths["stale"].exists(),
        "record_count": int(index.get("record_count") or 0),
        "source_count": int(index.get("source_count") or 0),
        "preferences_file": str(paths["preferences"]),
        "preference_count": len(preference_records(root)),
        "acceptance_file": str(paths["acceptances"]),
        "acceptance_count": len(paths["acceptances"].read_text(encoding="utf-8").splitlines()) if paths["acceptances"].exists() else 0,
    }
