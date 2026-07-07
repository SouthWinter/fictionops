from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .export_clean import default_clean_output_path
from .markdown import clean_preview, safe_cell, split_sentences, strip_markdown_noise, substantive_blocks
from .models import PublishCopyIssue, PublishCopyReport, PublishCopySource
from .plan_chapter import normalize_book_for_plan
from .publish_audit import split_clean_chapters
from .publish_metadata import blank_value, default_publish_checklist_path, empty_metadata, parse_publish_metadata


TAG_RULES: list[tuple[str, list[str]]] = [
    ("权谋", ["权力", "朝堂", "皇帝", "王朝", "帝国", "国家机器", "政局", "谋局", "夺位"]),
    ("成长", ["成长", "少年", "少女", "选择", "代价", "学会", "离开旧身份", "不可逆"]),
    ("神话", ["神话", "古神", "神剑", "天命", "旧藏", "神侍", "神明", "祭"]),
    ("复仇", ["复仇", "仇", "杀父", "旧案", "追凶", "清算"]),
    ("战争", ["战争", "军", "战场", "联军", "攻城", "边境", "乱局"]),
    ("群像", ["群像", "多视角", "众人", "人物", "势力", "同盟"]),
    ("悬疑", ["秘密", "真相", "谜", "线索", "查证", "误读", "隐瞒"]),
    ("家国", ["家国", "天下", "百姓", "土地", "国家", "王朝", "帝国"]),
    ("商战", ["商会", "账", "票据", "交易", "粮商", "市", "信用"]),
    ("冒险", ["旅途", "远行", "异域", "荒原", "逃亡", "探索"]),
]

PHRASE_STOPWORDS = {
    "一个",
    "一种",
    "一些",
    "不是",
    "没有",
    "可以",
    "不能",
    "不会",
    "什么",
    "自己",
    "他们",
    "她们",
    "我们",
    "这个",
    "那个",
    "这些",
    "那些",
    "因为",
    "所以",
    "如果",
    "已经",
    "时候",
    "里面",
    "第一",
    "第二",
    "第三",
    "本书",
    "故事",
    "读者",
    "正文",
    "章节",
    "主要",
    "需要",
    "禁止",
    "状态",
    "信息",
    "释放",
    "计划",
}


def default_publish_copy_output_path(project: Path, *, book: str) -> Path:
    return project / "08_publish" / "synopsis" / f"{book}_publish_copy.md"


def resolve_project_file(project: Path, value: str | None, default_path: Path) -> Path:
    if not value:
        return default_path.resolve()
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (project / path).resolve()


def resolve_publish_copy_output_path(project: Path, out_path: str | None, *, book: str) -> Path:
    return resolve_project_file(project, out_path, default_publish_copy_output_path(project, book=book))


def read_text_if_file(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, ""
    if not path.is_file():
        raise IsADirectoryError(f"path is not a file: {path}")
    return True, path.read_text(encoding="utf-8")


def dedupe(items: list[str], *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", str(item).strip())
        if not cleaned or cleaned in {"-", "—", "……", "..."} or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
        if limit is not None and len(result) >= limit:
            break
    return result


def first_heading(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def section_blockquote(text: str, header_token: str) -> str:
    lines = text.splitlines()
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if in_section:
                break
            in_section = header_token in stripped
            continue
        if in_section and stripped.startswith(">"):
            candidate = stripped.lstrip(">").strip()
            if candidate:
                return candidate
    return ""


def label_value(text: str, labels: list[str]) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*").strip()
        match = re.match(r"^([^：:]+)[：:]\s*(.+?)\s*$", stripped)
        if not match:
            continue
        label = match.group(1).strip()
        if label in labels:
            value = match.group(2).strip()
            if value and value not in {"-", "—", "……", "..."}:
                return value
    return ""


def metadata_text(metadata: dict[str, object], key: str) -> str:
    value = metadata.get(key, "")
    if blank_value(value):
        return ""
    if isinstance(value, list):
        return "，".join(str(item) for item in value if str(item).strip())
    return str(value).strip()


def collect_title_candidates(metadata: dict[str, object], *, clean_text: str, outline_text: str, seed_text: str, book: str) -> list[str]:
    return dedupe(
        [
            metadata_text(metadata, "title"),
            metadata_text(metadata, "book_title"),
            first_heading(clean_text),
            first_heading(outline_text),
            first_heading(seed_text),
            book,
        ],
        limit=8,
    )


def collect_chapter_titles(clean_text: str, *, limit: int = 12) -> list[str]:
    titles = [heading for _line, heading, chapter_number, _body in split_clean_chapters(clean_text) if chapter_number is not None]
    if not titles:
        for line in clean_text.splitlines():
            match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
            if match:
                titles.append(match.group(1).strip())
    return dedupe(titles, limit=limit)


def signal_tag_scores(text: str) -> list[tuple[str, int]]:
    scored: list[tuple[str, int]] = []
    for tag, needles in TAG_RULES:
        score = sum(text.count(needle) for needle in needles)
        if score:
            scored.append((tag, score))
    return sorted(scored, key=lambda item: (-item[1], item[0]))


def collect_tag_candidates(metadata: dict[str, object], corpus: str, *, limit: int = 8) -> list[str]:
    existing = metadata.get("tags", [])
    candidates: list[str] = []
    if isinstance(existing, list):
        candidates.extend(str(item) for item in existing)
    category = metadata_text(metadata, "category")
    if category:
        candidates.append(category)
    candidates.extend(tag for tag, _score in signal_tag_scores(corpus))
    return dedupe(candidates, limit=limit)


def is_bad_phrase(phrase: str) -> bool:
    if phrase in PHRASE_STOPWORDS:
        return True
    return any(stop in phrase for stop in PHRASE_STOPWORDS if len(stop) >= 3)


def collect_phrase_keywords(corpus: str, *, limit: int = 10) -> list[str]:
    counter: Counter[str] = Counter()
    for run in re.findall(r"[\u4e00-\u9fff]{2,20}", strip_markdown_noise(corpus)):
        max_size = min(6, len(run))
        for size in range(max_size, 1, -1):
            for index in range(0, len(run) - size + 1):
                phrase = run[index : index + size]
                if is_bad_phrase(phrase):
                    continue
                counter[phrase] += 1
    ranked = sorted(counter.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [phrase for phrase, count in ranked if count >= 2][:limit]


def collect_signal_keywords(corpus: str, *, limit: int = 10) -> list[str]:
    candidates: list[str] = []
    for _tag, needles in TAG_RULES:
        for needle in needles:
            if len(needle) >= 2 and needle in corpus:
                candidates.append(needle)
    return dedupe(candidates, limit=limit)


def collect_keyword_candidates(metadata: dict[str, object], corpus: str, *, limit: int = 10) -> list[str]:
    existing = metadata.get("keywords", [])
    candidates: list[str] = []
    if isinstance(existing, list):
        candidates.extend(str(item) for item in existing)
    candidates.extend(collect_signal_keywords(corpus, limit=limit))
    candidates.extend(collect_phrase_keywords(corpus, limit=limit))
    return dedupe(candidates, limit=limit)


def first_story_sentence(*texts: str) -> str:
    for text in texts:
        for sentence in split_sentences(text):
            stripped = sentence.strip().lstrip("-*>").strip()
            if len(stripped) >= 12 and not stripped.startswith(("项目", "状态", "备注")):
                return stripped
    return ""


def build_short_synopsis(metadata: dict[str, object], *, title: str, category: str, tags: list[str], seed_text: str, outline_text: str) -> str:
    existing = metadata_text(metadata, "short_synopsis")
    if existing:
        return existing
    premise = section_blockquote(outline_text, "本书一句话") or section_blockquote(seed_text, "一句话前提")
    if premise:
        return clean_preview(premise, limit=88)
    sentence = first_story_sentence(outline_text, seed_text)
    if sentence:
        return clean_preview(sentence, limit=88)
    topic = "、".join(tags[:3]) if tags else "核心人物选择"
    type_text = category or "长篇小说"
    return f"《{title}》是一部围绕{topic}展开的{type_text}。"


def build_long_synopsis(
    metadata: dict[str, object],
    *,
    short_synopsis: str,
    tags: list[str],
    keywords: list[str],
    chapter_titles: list[str],
    seed_text: str,
    outline_text: str,
) -> str:
    existing = metadata_text(metadata, "long_synopsis")
    if existing:
        return existing
    parts = [short_synopsis]
    theme = label_value(seed_text, ["本故事反复追问的问题", "主题问题"]) or label_value(outline_text, ["主要情绪", "主要空间", "主要视角"])
    if theme:
        parts.append(f"它更关心的是：{theme}")
    if chapter_titles:
        if len(chapter_titles) == 1:
            parts.append(f"当前清稿以“{chapter_titles[0]}”为主要章节入口。")
        else:
            parts.append(f"当前清稿从“{chapter_titles[0]}”推进到“{chapter_titles[-1]}”，中途保留章节标题所提示的阶段变化。")
    if tags:
        parts.append("可主打标签包括：" + "、".join(tags[:5]) + "。")
    if keywords:
        parts.append("可用于站内关键词的词包括：" + "、".join(keywords[:5]) + "。")
    return "".join(part for part in parts if part).strip()


def source_preview(text: str) -> str:
    for block in substantive_blocks(text):
        cleaned = re.sub(r"\s+", " ", block.strip().lstrip("-*>").strip())
        if len(cleaned) >= 8:
            return clean_preview(cleaned, limit=72)
    return ""


def source_report(name: str, path: Path, exists: bool, text: str, *, project: Path) -> PublishCopySource:
    return PublishCopySource(
        name=name,
        path=str(path),
        exists=exists,
        nonspace_chars=sum(1 for char in text if not char.isspace()),
        preview=source_preview(text),
    )


def publish_copy_issues(sources: list[PublishCopySource], *, checklist_exists: bool) -> list[PublishCopyIssue]:
    issues: list[PublishCopyIssue] = []
    if not checklist_exists:
        issues.append(
            PublishCopyIssue(
                severity="P3",
                code="missing_publish_checklist",
                source="publish_checklist",
                path="-",
                message="Publish checklist is missing; generated copy can still be used as a draft.",
            )
        )
    usable_sources = [source for source in sources if source.exists and source.nonspace_chars > 0]
    if not usable_sources:
        issues.append(
            PublishCopyIssue(
                severity="P2",
                code="missing_copy_sources",
                source="project",
                path="-",
                message="No seed, outline, clean Markdown, or checklist text was available for publish-copy.",
            )
        )
    for source in sources:
        if not source.exists:
            issues.append(
                PublishCopyIssue(
                    severity="P4",
                    code="missing_source_file",
                    source=source.name,
                    path=source.path,
                    message=f"Optional source file is missing: {source.name}.",
                )
            )
    return issues


def build_publish_copy(
    project: Path,
    *,
    book: str,
    clean_file: str | None,
    checklist_file: str | None,
    outline_file: str | None,
    seed_file: str | None,
    out: str | None,
    force: bool,
    dry_run: bool,
) -> PublishCopyReport:
    resolved = project.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"path is not a directory: {resolved}")

    book_id = normalize_book_for_plan(book)
    clean_path = resolve_project_file(resolved, clean_file, default_clean_output_path(resolved, book=book_id))
    checklist_path = resolve_project_file(resolved, checklist_file, default_publish_checklist_path(resolved))
    outline_path = resolve_project_file(resolved, outline_file, resolved / "04_structure" / "book_outlines" / f"{book_id}_outline.md")
    seed_path = resolve_project_file(resolved, seed_file, resolved / "01_story_seed" / "story_seed.md")
    output_path = resolve_publish_copy_output_path(resolved, out, book=book_id)

    clean_exists, clean_text = read_text_if_file(clean_path)
    checklist_exists, checklist_text = read_text_if_file(checklist_path)
    outline_exists, outline_text = read_text_if_file(outline_path)
    seed_exists, seed_text = read_text_if_file(seed_path)

    metadata = parse_publish_metadata(checklist_text) if checklist_exists else empty_metadata()
    corpus = "\n\n".join([checklist_text, seed_text, outline_text, clean_text])
    titles = collect_title_candidates(metadata, clean_text=clean_text, outline_text=outline_text, seed_text=seed_text, book=book_id)
    title = titles[0] if titles else book_id
    category = metadata_text(metadata, "category")
    tags = collect_tag_candidates(metadata, corpus)
    keywords = collect_keyword_candidates(metadata, corpus)
    chapter_titles = collect_chapter_titles(clean_text)
    short_synopsis = build_short_synopsis(
        metadata,
        title=title,
        category=category,
        tags=tags,
        seed_text=seed_text,
        outline_text=outline_text,
    )
    long_synopsis = build_long_synopsis(
        metadata,
        short_synopsis=short_synopsis,
        tags=tags,
        keywords=keywords,
        chapter_titles=chapter_titles,
        seed_text=seed_text,
        outline_text=outline_text,
    )
    suggested_metadata = {
        "title": title,
        "category": category,
        "tags": tags,
        "short_synopsis": short_synopsis,
        "long_synopsis": long_synopsis,
        "keywords": keywords,
    }
    sources = [
        source_report("publish_checklist", checklist_path, checklist_exists, checklist_text, project=resolved),
        source_report("story_seed", seed_path, seed_exists, seed_text, project=resolved),
        source_report("book_outline", outline_path, outline_exists, outline_text, project=resolved),
        source_report("clean_markdown", clean_path, clean_exists, clean_text, project=resolved),
    ]
    issues = publish_copy_issues(sources, checklist_exists=checklist_exists)

    if output_path.exists() and not force and not dry_run:
        raise FileExistsError(f"output file exists: {output_path}")

    report = PublishCopyReport(
        target=str(resolved),
        book=book_id,
        output_file=str(output_path),
        dry_run=dry_run,
        written=False,
        checklist_file=str(checklist_path),
        clean_file=str(clean_path),
        outline_file=str(outline_path),
        seed_file=str(seed_path),
        metadata=metadata,
        suggested_metadata=suggested_metadata,
        title_candidates=titles,
        tag_candidates=tags,
        keyword_candidates=keywords,
        chapter_titles=chapter_titles,
        sources=sources,
        issues=issues,
    )
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report.written = True
        output_path.write_text(format_publish_copy_report(report), encoding="utf-8", newline="\n")
    return report


def render_publish_copy_report(report: PublishCopyReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "markdown":
        raise ValueError(f"Unsupported publish-copy format: {format_}")
    return format_publish_copy_report(report)


def format_publish_copy_report(report: PublishCopyReport) -> str:
    suggested = report.suggested_metadata
    tags = suggested.get("tags", [])
    keywords = suggested.get("keywords", [])
    tag_text = "，".join(str(item) for item in tags) if isinstance(tags, list) else str(tags)
    keyword_text = "，".join(str(item) for item in keywords) if isinstance(keywords, list) else str(keywords)
    lines = [
        "# FictionOps Publish Copy Draft",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- Output: `{report.output_file or '-'}`",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        f"- Written: {'yes' if report.written else 'no'}",
        "",
        "## Suggested Metadata",
        "",
        f"- 书名：{safe_cell(str(suggested.get('title', '')))}",
        f"- 分类：{safe_cell(str(suggested.get('category', '')))}",
        f"- 标签：{safe_cell(tag_text)}",
        f"- 简介短版：{safe_cell(str(suggested.get('short_synopsis', '')))}",
        f"- 简介长版：{safe_cell(str(suggested.get('long_synopsis', '')))}",
        f"- 关键词：{safe_cell(keyword_text)}",
        "",
        "## Candidates",
        "",
        f"- Title candidates: {safe_cell('，'.join(report.title_candidates))}",
        f"- Tag candidates: {safe_cell('，'.join(report.tag_candidates))}",
        f"- Keyword candidates: {safe_cell('，'.join(report.keyword_candidates))}",
        "",
        "## Chapter Titles",
        "",
    ]
    if report.chapter_titles:
        lines.extend(f"- {title}" for title in report.chapter_titles)
    else:
        lines.append("- -")
    lines.extend(
        [
            "",
            "## Source Evidence",
            "",
            "| Source | Exists | Nonspace | Path | Preview |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for source in report.sources:
        lines.append(
            f"| {safe_cell(source.name)} | {'yes' if source.exists else 'no'} | {source.nonspace_chars} | "
            f"`{source.path}` | {safe_cell(source.preview)} |"
        )
    lines.extend(["", "## Issues", "", "| Severity | Code | Source | Path | Message |", "| --- | --- | --- | --- | --- |"])
    if report.issues:
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | `{issue.code}` | {safe_cell(issue.source)} | "
                f"`{issue.path}` | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("| - | - | - | - | No publish-copy issues found. |")
    lines.extend(
        [
            "",
            "## Usage Note",
            "",
            "This is a drafting aid. Copy only the lines you accept into `08_publish/publish_checklist.md`, then run `fictionops export-metadata`.",
        ]
    )
    return "\n".join(lines)
