from __future__ import annotations

import re
from pathlib import Path

from .constants import PLACEHOLDER_MARKERS

def is_cjk(char: str) -> bool:
    codepoint = ord(char)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
        or 0x20000 <= codepoint <= 0x2A6DF
        or 0x2A700 <= codepoint <= 0x2B73F
        or 0x2B740 <= codepoint <= 0x2B81F
        or 0x2B820 <= codepoint <= 0x2CEAF
    )


def count_latin_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))


def natural_key(path: Path) -> list[object]:
    parts: list[object] = []
    for chunk in re.split(r"(\d+)", str(path)):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            parts.append(chunk.lower())
    return parts


def is_chapter_file(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    if "chapters" in lowered_parts:
        return True
    name = path.name
    if re.search(r"^ch[_-]?\d+\.md$", name, flags=re.IGNORECASE):
        return True
    if re.search(r"第[0-9零〇一二三四五六七八九十百两]+章", name):
        return True
    return False


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def collect_markdown_files(target: Path, *, all_markdown: bool, pattern: str) -> list[Path]:
    if target.is_file():
        files = [target] if target.suffix.lower() == ".md" else []
    else:
        files = [path for path in target.glob(pattern) if path.is_file() and path.suffix.lower() == ".md"]
    files = sorted(files, key=natural_key)
    if all_markdown:
        return files
    return [path for path in files if is_chapter_file(path)]


def strip_markdown_noise(text: str) -> str:
    cleaned: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            cleaned.append("")
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            stripped = stripped.lstrip(">").strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if re.fullmatch(r"-{3,}", stripped):
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned).strip()


def substantive_blocks(text: str) -> list[str]:
    plain = strip_markdown_noise(text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n+", plain) if block.strip()]
    return blocks


def split_sentences(text: str) -> list[str]:
    plain = strip_markdown_noise(text)
    pieces = re.split(r"(?<=[。！？!?；;])\s*|\n+", plain)
    return [piece.strip() for piece in pieces if piece.strip()]


def clean_preview(text: str, limit: int = 36) -> str:
    preview = re.sub(r"\s+", " ", text.strip())
    if len(preview) > limit:
        preview = preview[: limit - 1] + "…"
    return preview.replace("|", "\\|")


def safe_cell(text: str | None) -> str:
    if not text:
        return "-"
    return text.replace("|", "\\|")


def chinese_numeral_to_int(value: str) -> int | None:
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    units = {"十": 10, "百": 100}
    if not value:
        return None
    total = 0
    current = 0
    seen = False
    for char in value:
        if char in digits:
            current = digits[char]
            seen = True
        elif char in units:
            unit = units[char]
            if current == 0:
                current = 1
            total += current * unit
            current = 0
            seen = True
        else:
            return None
    total += current
    return total if seen else None


def extract_chapter_key(path: Path) -> str:
    stem = path.stem
    match = re.search(r"ch[_-]?(\d+)", stem, flags=re.IGNORECASE)
    if match:
        return match.group(1).zfill(3)
    match = re.search(r"第(\d+)章", stem)
    if match:
        return match.group(1).zfill(3)
    match = re.search(r"第([零〇一二三四五六七八九十百两]+)章", stem)
    if match:
        number = chinese_numeral_to_int(match.group(1))
        if number is not None:
            return str(number).zfill(3)
    match = re.search(r"(\d+)", stem)
    if match:
        return match.group(1).zfill(3)
    return stem.lower()


def looks_placeholder(text: str, *, min_chars: int = 120) -> bool:
    nonspace = sum(1 for char in text if not char.isspace())
    if nonspace < min_chars:
        return True
    marker_hits = sum(1 for marker in PLACEHOLDER_MARKERS if marker in text)
    return marker_hits >= 2
