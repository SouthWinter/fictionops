from __future__ import annotations

import html
import json
import re
import uuid
import zipfile
from dataclasses import asdict
from pathlib import Path

from .export_clean import default_clean_output_path
from .markdown import is_cjk, safe_cell
from .models import PublishEpubChapter, PublishEpubIssue, PublishEpubReport
from .plan_chapter import normalize_book_for_plan
from .publish_audit import split_clean_chapters
from .publish_manifest import default_manifest_output_path, resolve_manifest_file
from .publish_metadata import default_metadata_output_path


def default_epub_output_path(project: Path, *, book: str) -> Path:
    return project / "08_publish" / "epub" / f"{book}.epub"


DEFAULT_EPUB_CSS = """\
html {
  margin: 0;
  padding: 0;
}

body {
  color: #1f1f1f;
  font-family: serif;
  line-height: 1.75;
  margin: 7%;
}

h1,
h2,
h3 {
  font-family: sans-serif;
  font-weight: 600;
  line-height: 1.35;
  margin: 2.4em 0 1.2em;
  text-align: center;
}

p {
  margin: 0.35em 0;
  text-indent: 2em;
}

blockquote {
  border-left: 0.25em solid #999;
  color: #444;
  margin: 1.4em 0;
  padding-left: 1em;
}

blockquote p {
  text-indent: 0;
}

nav ol {
  line-height: 1.8;
}

.cover {
  margin: 0;
  text-align: center;
}

.cover img {
  max-height: 96vh;
  max-width: 100%;
}
"""


def epub_issue(severity: str, code: str, path: Path | str, message: str) -> PublishEpubIssue:
    return PublishEpubIssue(severity=severity, code=code, path=str(path), message=message)


def load_json_object(path: Path, *, code: str, issues: list[PublishEpubIssue]) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(epub_issue("P2", code, path, f"JSON could not be parsed: {exc}"))
        return {}
    if not isinstance(payload, dict):
        issues.append(epub_issue("P2", code, path, "JSON root must be an object."))
        return {}
    return payload


def value_as_text(value: object, default: str = "") -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value if str(item).strip())
    text = str(value).strip()
    return text or default


def metadata_from_payload(payload: dict[str, object]) -> dict[str, object]:
    metadata = payload.get("metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def metadata_as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r"[、,;；\n]+", text) if item.strip()]


def metadata_cover_text(metadata: dict[str, object]) -> str:
    return value_as_text(metadata.get("cover_image", ""))


def cover_media_type(path: Path) -> str | None:
    suffix = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix)


def paths_from_manifest(
    project: Path,
    *,
    book: str,
    manifest_path: Path,
    clean_file: str | None,
    metadata_file: str | None,
    issues: list[PublishEpubIssue],
) -> tuple[Path, Path, dict[str, object]]:
    manifest_payload: dict[str, object] = {}
    if manifest_path.exists():
        manifest_payload = load_json_object(manifest_path, code="invalid_manifest_json", issues=issues)
    else:
        issues.append(epub_issue("P3", "missing_manifest", manifest_path, "Publish manifest was not found; default paths will be used."))

    files = manifest_payload.get("files", {})
    if not isinstance(files, dict):
        files = {}
    clean_default = default_clean_output_path(project, book=book)
    metadata_default = default_metadata_output_path(project, book=book)
    manifest_clean = files.get("clean_markdown", {})
    manifest_metadata = files.get("metadata_json", {})
    clean_default_text = manifest_clean.get("path") if isinstance(manifest_clean, dict) else None
    metadata_default_text = manifest_metadata.get("path") if isinstance(manifest_metadata, dict) else None

    clean_path = resolve_manifest_file(project, clean_file, default_path=Path(str(clean_default_text or clean_default)))
    metadata_path = resolve_manifest_file(project, metadata_file, default_path=Path(str(metadata_default_text or metadata_default)))
    return clean_path, metadata_path, manifest_payload


def cover_path_from_manifest(manifest_payload: dict[str, object]) -> str | None:
    files = manifest_payload.get("files", {})
    if not isinstance(files, dict):
        return None
    cover_file = files.get("cover_image", {})
    if not isinstance(cover_file, dict):
        return None
    path = cover_file.get("path")
    return str(path).strip() if path else None


def resolve_cover_path(
    project: Path,
    *,
    cover_file: str | None,
    manifest_payload: dict[str, object],
    metadata: dict[str, object],
) -> Path | None:
    cover_text = cover_file or cover_path_from_manifest(manifest_payload) or metadata_cover_text(metadata)
    if not cover_text:
        return None
    return resolve_manifest_file(project, cover_text, default_path=Path(cover_text))


def clean_title_from_metadata(metadata: dict[str, object], *, book: str) -> str:
    for key in ("title", "book_title"):
        value = value_as_text(metadata.get(key, ""))
        if value:
            return value
    return book


def chapter_number_label(number: int | None, index: int) -> str:
    return f"{number:03d}" if number is not None else f"{index:03d}"


def markdown_body_to_xhtml(body: str, *, fallback_title: str) -> str:
    lines = body.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    parts: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        text = " ".join(item.strip() for item in paragraph if item.strip())
        if text:
            parts.append(f"<p>{html.escape(text)}</p>")
        paragraph.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)), 3)
            parts.append(f"<h{level}>{html.escape(heading.group(2))}</h{level}>")
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            quote = stripped.lstrip(">").strip()
            if quote:
                parts.append(f"<blockquote><p>{html.escape(quote)}</p></blockquote>")
            continue
        paragraph.append(stripped)
    flush_paragraph()
    if not parts:
        parts.append(f"<h1>{html.escape(fallback_title)}</h1>")
    return "\n".join(parts)


def split_epub_chapters(text: str) -> list[tuple[str, str, str, int]]:
    parsed = split_clean_chapters(text)
    chapters: list[tuple[str, str, str, int]] = []
    for index, _line_no_heading_number_body in enumerate(parsed, start=1):
        _line_no, heading, number, body = _line_no_heading_number_body
        label = chapter_number_label(number, index)
        title = heading or f"Chapter {label}"
        chapters.append((label, title, body, sum(1 for char in body if not char.isspace())))
    if chapters:
        return chapters
    stripped = text.strip()
    if stripped:
        return [("001", "正文", stripped, sum(1 for char in stripped if not char.isspace()))]
    return []


def xhtml_document(*, title: str, body: str, style_href: str | None = None) -> str:
    style = f'<link rel="stylesheet" type="text/css" href="{html.escape(style_href)}" />\n' if style_href else ""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" lang="zh-CN">\n'
        "<head>\n"
        f"<title>{html.escape(title)}</title>\n"
        '<meta charset="utf-8" />\n'
        f"{style}"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


def render_container_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        "  <rootfiles>\n"
        '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
        "  </rootfiles>\n"
        "</container>\n"
    )


def render_nav_xhtml(*, title: str, chapters: list[PublishEpubChapter]) -> str:
    items = "\n".join(
        f'<li><a href="{html.escape(chapter.file)}">{html.escape(chapter.title)}</a></li>' for chapter in chapters
    )
    body = f"<h1>{html.escape(title)}</h1>\n<nav epub:type=\"toc\" id=\"toc\"><ol>{items}</ol></nav>"
    return xhtml_document(title=title, body=body, style_href="styles/fictionops.css").replace(
        "<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"zh-CN\">",
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-CN">',
    )


def render_cover_xhtml(*, title: str, image_file: str) -> str:
    body = (
        '<section class="cover">\n'
        f'<img src="{html.escape(image_file)}" alt="{html.escape(title)}" />\n'
        "</section>"
    )
    return xhtml_document(title=title, body=body, style_href="styles/fictionops.css")


def render_content_opf(
    *,
    identifier: str,
    title: str,
    author: str,
    language: str,
    description: str,
    subjects: list[str],
    release_date: str,
    chapters: list[PublishEpubChapter],
    cover_file: str | None,
    cover_media_type_: str | None,
) -> str:
    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="style" href="styles/fictionops.css" media-type="text/css"/>',
    ]
    spine_items: list[str] = []
    if cover_file and cover_media_type_:
        manifest_items.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
        manifest_items.append(
            f'<item id="cover-image" href="{html.escape(cover_file)}" media-type="{html.escape(cover_media_type_)}" properties="cover-image"/>'
        )
        spine_items.append('<itemref idref="cover"/>')
    for index, chapter in enumerate(chapters, start=1):
        item_id = f"chapter-{index:03d}"
        manifest_items.append(f'<item id="{item_id}" href="{html.escape(chapter.file)}" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="{item_id}"/>')
    metadata_items = [
        f'    <dc:identifier id="book-id">{html.escape(identifier)}</dc:identifier>',
        f"    <dc:title>{html.escape(title)}</dc:title>",
        f"    <dc:creator>{html.escape(author or 'Unknown')}</dc:creator>",
        f"    <dc:language>{html.escape(language or 'zh-CN')}</dc:language>",
    ]
    if description:
        metadata_items.append(f"    <dc:description>{html.escape(description)}</dc:description>")
    if release_date:
        metadata_items.append(f"    <dc:date>{html.escape(release_date)}</dc:date>")
    for subject in subjects:
        metadata_items.append(f"    <dc:subject>{html.escape(subject)}</dc:subject>")
    if cover_file and cover_media_type_:
        metadata_items.append('    <meta name="cover" content="cover-image"/>')
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package version="3.0" unique-identifier="book-id" xmlns="http://www.idpf.org/2007/opf">\n'
        "  <metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\">\n"
        + "\n".join(metadata_items)
        + "\n"
        "  </metadata>\n"
        "  <manifest>\n    "
        + "\n    ".join(manifest_items)
        + "\n  </manifest>\n"
        "  <spine>\n    "
        + "\n    ".join(spine_items)
        + "\n  </spine>\n"
        "</package>\n"
    )


def write_epub(
    output_path: Path,
    *,
    title: str,
    author: str,
    language: str,
    description: str,
    subjects: list[str],
    release_date: str,
    chapters: list[tuple[PublishEpubChapter, str]],
    identifier: str,
    cover_path: Path | None,
    cover_file: str | None,
    cover_media_type_: str | None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", render_container_xml(), compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/styles/fictionops.css", DEFAULT_EPUB_CSS, compress_type=zipfile.ZIP_DEFLATED)
        if cover_path and cover_file and cover_media_type_:
            zf.writestr(
                f"OEBPS/{cover_file}",
                cover_path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
            )
            zf.writestr(
                "OEBPS/cover.xhtml",
                render_cover_xhtml(title=title, image_file=cover_file),
                compress_type=zipfile.ZIP_DEFLATED,
            )
        zf.writestr(
            "OEBPS/content.opf",
            render_content_opf(
                identifier=identifier,
                title=title,
                author=author,
                language=language,
                description=description,
                subjects=subjects,
                release_date=release_date,
                chapters=[chapter for chapter, _ in chapters],
                cover_file=cover_file,
                cover_media_type_=cover_media_type_,
            ),
            compress_type=zipfile.ZIP_DEFLATED,
        )
        zf.writestr(
            "OEBPS/nav.xhtml",
            render_nav_xhtml(title=title, chapters=[chapter for chapter, _ in chapters]),
            compress_type=zipfile.ZIP_DEFLATED,
        )
        for chapter, xhtml in chapters:
            zf.writestr(f"OEBPS/{chapter.file}", xhtml, compress_type=zipfile.ZIP_DEFLATED)


def export_epub(
    project: Path,
    *,
    book: str,
    manifest_file: str | None,
    clean_file: str | None,
    metadata_file: str | None,
    cover_file: str | None,
    out: str | None,
    force: bool,
    dry_run: bool,
) -> PublishEpubReport:
    resolved = project.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"path is not a directory: {resolved}")

    book_id = normalize_book_for_plan(book)
    issues: list[PublishEpubIssue] = []
    manifest_path = resolve_manifest_file(
        resolved,
        manifest_file,
        default_path=default_manifest_output_path(resolved, book=book_id),
    )
    clean_path, metadata_path, manifest_payload = paths_from_manifest(
        resolved,
        book=book_id,
        manifest_path=manifest_path,
        clean_file=clean_file,
        metadata_file=metadata_file,
        issues=issues,
    )
    output_path = resolve_manifest_file(
        resolved,
        out,
        default_path=default_epub_output_path(resolved, book=book_id),
    )

    metadata_payload = load_json_object(metadata_path, code="invalid_metadata_json", issues=issues)
    metadata = metadata_from_payload(metadata_payload) or metadata_from_payload(manifest_payload)
    cover_path = resolve_cover_path(
        resolved,
        cover_file=cover_file,
        manifest_payload=manifest_payload,
        metadata=metadata,
    )
    cover_type = cover_media_type(cover_path) if cover_path else None
    usable_cover_path: Path | None = None
    epub_cover_file: str | None = None
    if cover_path:
        if not cover_path.exists() or not cover_path.is_file():
            issues.append(epub_issue("P3", "missing_cover_image", cover_path, "Cover image was requested but not found."))
        elif not cover_type:
            issues.append(
                epub_issue(
                    "P3",
                    "unsupported_cover_image",
                    cover_path,
                    "Cover image type is not supported; use jpg, png, gif, or webp.",
                )
            )
        else:
            usable_cover_path = cover_path
            epub_cover_file = f"images/cover{cover_path.suffix.lower()}"

    if not clean_path.exists():
        issues.append(epub_issue("P2", "missing_clean_markdown", clean_path, "Clean Markdown file was not found."))
        return PublishEpubReport(
            target=str(resolved),
            book=book_id,
            output_file=str(output_path),
            manifest_file=str(manifest_path),
            manifest_file_exists=manifest_path.exists(),
            clean_file=str(clean_path),
            metadata_file=str(metadata_path),
            cover_file=str(cover_path) if cover_path else "",
            cover_file_exists=bool(cover_path and cover_path.exists() and cover_path.is_file()),
            dry_run=dry_run,
            written=False,
            chapter_count=0,
            total_nonspace_chars=0,
            metadata=metadata,
            chapters=[],
            issues=issues,
        )
    if not metadata_path.exists():
        issues.append(epub_issue("P2", "missing_metadata_json", metadata_path, "Metadata JSON file was not found."))

    clean_text = clean_path.read_text(encoding="utf-8")
    title = clean_title_from_metadata(metadata, book=book_id)
    author = value_as_text(metadata.get("author", ""), default="Unknown")
    language = value_as_text(metadata.get("language", ""), default="zh-CN")
    description = value_as_text(metadata.get("long_synopsis", "")) or value_as_text(metadata.get("short_synopsis", ""))
    subjects = metadata_as_list(metadata.get("tags", [])) + metadata_as_list(metadata.get("keywords", []))
    release_date = value_as_text(metadata.get("release_date", ""))
    chapter_sources = split_epub_chapters(clean_text)
    chapters: list[tuple[PublishEpubChapter, str]] = []
    for label, chapter_title, body, nonspace in chapter_sources:
        file_name = f"chapters/chapter_{label}.xhtml"
        chapter = PublishEpubChapter(chapter=label, title=chapter_title, file=file_name, nonspace_chars=nonspace)
        xhtml = xhtml_document(
            title=chapter_title,
            body=markdown_body_to_xhtml(body, fallback_title=chapter_title),
            style_href="../styles/fictionops.css",
        )
        chapters.append((chapter, xhtml))

    if not chapters:
        issues.append(epub_issue("P2", "no_epub_chapters", clean_path, "No readable chapters were found in clean Markdown."))

    written = False
    if chapters and not dry_run:
        if output_path.exists() and not force:
            raise FileExistsError(f"output file exists: {output_path}")
        identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, str(clean_path) + str(output_path))}"
        write_epub(
            output_path,
            title=title,
            author=author,
            language=language,
            description=description,
            subjects=subjects,
            release_date=release_date,
            chapters=chapters,
            identifier=identifier,
            cover_path=usable_cover_path,
            cover_file=epub_cover_file,
            cover_media_type_=cover_type if usable_cover_path else None,
        )
        written = True

    return PublishEpubReport(
        target=str(resolved),
        book=book_id,
        output_file=str(output_path),
        manifest_file=str(manifest_path),
        manifest_file_exists=manifest_path.exists(),
        clean_file=str(clean_path),
        metadata_file=str(metadata_path),
        cover_file=str(cover_path) if cover_path else "",
        cover_file_exists=bool(cover_path and cover_path.exists() and cover_path.is_file()),
        dry_run=dry_run,
        written=written,
        chapter_count=len(chapters),
        total_nonspace_chars=sum(chapter.nonspace_chars for chapter, _ in chapters),
        metadata=metadata,
        chapters=[chapter for chapter, _ in chapters],
        issues=issues,
    )


def render_epub_report(report: PublishEpubReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "table":
        raise ValueError(f"Unsupported export-epub format: {format_}")

    lines = [
        "# FictionOps EPUB Export",
        "",
        f"- Target: `{report.target}`",
        f"- Book: `{report.book}`",
        f"- EPUB: `{report.output_file}`",
        f"- Manifest: `{report.manifest_file}`",
        f"- Manifest exists: {'yes' if report.manifest_file_exists else 'no'}",
        f"- Clean Markdown: `{report.clean_file}`",
        f"- Metadata JSON: `{report.metadata_file}`",
        f"- Cover image: `{report.cover_file or '-'}`",
        f"- Cover exists: {'yes' if report.cover_file_exists else 'no'}",
        f"- Chapters: {report.chapter_count}",
        f"- Nonspace: {report.total_nonspace_chars}",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        "",
        "## Chapters",
        "",
    ]
    if report.chapters:
        lines.extend(["| # | Title | File | Nonspace |", "| --- | --- | --- | ---: |"])
        for chapter in report.chapters:
            lines.append(
                f"| {chapter.chapter} | {safe_cell(chapter.title)} | `{safe_cell(chapter.file)}` | {chapter.nonspace_chars} |"
            )
    else:
        lines.append("No EPUB chapters.")

    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(["| Severity | Code | Path | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(
                f"| {issue.severity} | {safe_cell(issue.code)} | `{safe_cell(issue.path)}` | {safe_cell(issue.message)} |"
            )
    else:
        lines.append("No EPUB export issues found.")
    return "\n".join(lines)
