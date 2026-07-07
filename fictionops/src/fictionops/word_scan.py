from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .markdown import collect_markdown_files, count_latin_words, display_path, strip_markdown_noise
from .models import CountItem, WordScanFile, WordScanReport


DEFAULT_WORD_STOPWORDS = {
    "一个",
    "一种",
    "一些",
    "这个",
    "那个",
    "这些",
    "那些",
    "他们",
    "她们",
    "我们",
    "自己",
    "没有",
    "不是",
    "可以",
    "不能",
    "不会",
    "已经",
    "因为",
    "所以",
    "如果",
    "时候",
    "里面",
    "什么",
    "正文",
    "章节",
    "故事",
    "读者",
    "信息",
    "需要",
    "状态",
}


def parse_watch_terms(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[、，,;；\n]+", value) if part.strip()]


def phrase_counter(text: str, *, min_size: int = 2, max_size: int = 4) -> Counter[str]:
    counter: Counter[str] = Counter()
    plain = strip_markdown_noise(text)
    for run in re.findall(r"[\u4e00-\u9fff]{2,24}", plain):
        upper = min(max_size, len(run))
        for size in range(upper, min_size - 1, -1):
            for index in range(0, len(run) - size + 1):
                phrase = run[index : index + size]
                if phrase in DEFAULT_WORD_STOPWORDS:
                    continue
                if any(stop in phrase for stop in DEFAULT_WORD_STOPWORDS if len(stop) >= 3):
                    continue
                counter[phrase] += 1
    for match in re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", plain):
        counter[match.lower()] += 1
    return counter


def top_count_items(counter: Counter[str], *, min_count: int, top: int) -> list[CountItem]:
    ranked = sorted(counter.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [CountItem(item=term, count=count) for term, count in ranked if count >= min_count][:top]


def watch_count_items(text: str, watch_terms: list[str]) -> list[CountItem]:
    if not watch_terms:
        return []
    plain = strip_markdown_noise(text)
    hits = [CountItem(item=term, count=plain.count(term)) for term in watch_terms if plain.count(term) > 0]
    return sorted(hits, key=lambda item: (-item.count, item.item))


def build_word_scan_report(
    target: Path,
    *,
    all_markdown: bool,
    pattern: str,
    watch: str | None,
    min_count: int,
    top: int,
) -> WordScanReport:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if min_count < 1:
        raise ValueError("min_count must be >= 1")
    if top < 1:
        raise ValueError("top must be >= 1")

    files = collect_markdown_files(resolved, all_markdown=all_markdown, pattern=pattern)
    mode = "all-markdown" if all_markdown else "chapters"
    watch_terms = parse_watch_terms(watch)
    base = resolved if resolved.is_dir() else resolved.parent
    aggregate: Counter[str] = Counter()
    aggregate_watch: Counter[str] = Counter()
    file_reports: list[WordScanFile] = []
    total_latin = 0
    total_phrases = 0

    for path in files:
        text = path.read_text(encoding="utf-8")
        counter = phrase_counter(text)
        aggregate.update(counter)
        latin_words = count_latin_words(strip_markdown_noise(text))
        total_latin += latin_words
        total_phrases += sum(counter.values())
        watch_hits = watch_count_items(text, watch_terms)
        for item in watch_hits:
            aggregate_watch[item.item] += item.count
        file_reports.append(
            WordScanFile(
                path=display_path(path, base),
                chars=len(text),
                nonspace_chars=sum(1 for char in text if not char.isspace()),
                latin_words=latin_words,
                phrase_total=sum(counter.values()),
                top_terms=top_count_items(counter, min_count=min_count, top=top),
                watch_hits=watch_hits,
            )
        )

    return WordScanReport(
        target=str(resolved),
        mode=mode,
        file_count=len(file_reports),
        min_count=min_count,
        top=top,
        watch_terms=watch_terms,
        total_latin_words=total_latin,
        total_phrases=total_phrases,
        aggregate_terms=top_count_items(aggregate, min_count=min_count, top=top),
        watch_hits=top_count_items(aggregate_watch, min_count=1, top=max(top, len(watch_terms) or 1)),
        files=file_reports,
    )


def render_word_scan_report(report: WordScanReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported scan-words format: {format_}")
    lines = [
        "# FictionOps Word Scan",
        "",
        f"- Target: `{report.target}`",
        f"- Mode: {report.mode}",
        f"- Files: {report.file_count}",
        f"- Min count: {report.min_count}",
        f"- Top: {report.top}",
        f"- Watch terms: {', '.join(report.watch_terms) if report.watch_terms else '-'}",
        f"- Total Latin words: {report.total_latin_words}",
        f"- Total phrases: {report.total_phrases}",
        "",
        "## Aggregate Terms",
        "",
        "| Term | Count |",
        "| --- | ---: |",
    ]
    if report.aggregate_terms:
        for item in report.aggregate_terms:
            lines.append(f"| {item.item} | {item.count} |")
    else:
        lines.append("| - | 0 |")
    lines.extend(["", "## Watch Hits", "", "| Term | Count |", "| --- | ---: |"])
    if report.watch_hits:
        for item in report.watch_hits:
            lines.append(f"| {item.item} | {item.count} |")
    else:
        lines.append("| - | 0 |")
    lines.extend(["", "## Files", "", "| File | Nonspace | Latin Words | Phrases | Top Terms | Watch Hits |", "| --- | ---: | ---: | ---: | --- | --- |"])
    for file in report.files:
        top_terms = ", ".join(f"{item.item}:{item.count}" for item in file.top_terms[:5]) or "-"
        watch_hits = ", ".join(f"{item.item}:{item.count}" for item in file.watch_hits) or "-"
        lines.append(f"| `{file.path}` | {file.nonspace_chars} | {file.latin_words} | {file.phrase_total} | {top_terms} | {watch_hits} |")
    if not report.files:
        lines.append("| - | 0 | 0 | 0 | - | - |")
    return "\n".join(lines)
