from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

try:
    from . import __version__
    from .core import *  # noqa: F403 - re-exported for backward-compatible tests and imports.
except ImportError:  # Allows running this file directly from a source checkout.
    __version__ = "0.1.0"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from fictionops.core import *  # noqa: F403

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fictionops",
        description="FictionOps long-form fiction project toolkit.",
    )
    parser.add_argument("--version", action="version", version=f"fictionops {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    adopt_parser = subparsers.add_parser(
        "adopt",
        help="Scan an existing writing directory and map files to FictionOps layers without modifying it.",
    )
    adopt_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Existing writing directory to inspect. Default: current directory.",
    )
    adopt_parser.add_argument(
        "--max-files",
        type=int,
        default=80,
        help="Maximum candidate files to list in detail. Summary counts still include all scanned files. Default: 80.",
    )
    adopt_parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Include normally ignored directories such as .git, .github, fictionops, build, and dist.",
    )
    adopt_parser.add_argument(
        "--out",
        help="Write a Markdown adopt report to a file. Relative paths are resolved inside PATH.",
    )
    adopt_parser.add_argument(
        "--copy-to",
        help="Copy scanned files into an initialized FictionOps project using suggested target paths.",
    )
    adopt_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out or copied target files if they already exist.",
    )
    adopt_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the adopt report without writing --out.",
    )
    adopt_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    adopt_review_parser = subparsers.add_parser(
        "adopt-review",
        help="Review an initialized FictionOps migration sandbox after adopt --copy-to.",
    )
    adopt_review_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="FictionOps migration sandbox to review. Default: current directory.",
    )
    adopt_review_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for book-gate integration. Default: book_01.",
    )
    adopt_review_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used by underlying audits. Default: **/*.md.",
    )
    adopt_review_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Chapters below this nonspace-character count are treated as placeholders. Default: 200.",
    )
    adopt_review_parser.add_argument(
        "--watch",
        help="Comma-separated style watch terms passed to doctor. Defaults to common FictionOps markers.",
    )
    adopt_review_parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="Number of aggregate style/echo items to consider. Default: 12.",
    )
    adopt_review_parser.add_argument(
        "--min-repeat",
        type=int,
        default=3,
        help="Minimum repeated sentence-opening count. Default: 3.",
    )
    adopt_review_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan detected chapter text for rough echo or information-boundary hits.",
    )
    adopt_review_parser.add_argument(
        "--stale-after",
        type=int,
        default=8,
        help="Flag echo threads whose last recorded echo is this many chapters behind. Default: 8.",
    )
    adopt_review_parser.add_argument(
        "--max-issues",
        type=int,
        default=80,
        help="Maximum migration review issues to include in detail. Default: 80.",
    )
    adopt_review_parser.add_argument(
        "--waivers",
        help="Optional JSON waiver file for explicitly deferred migration issues. Relative paths are resolved inside PATH; defaults to 07_audits/adopt_review/waivers.json when present.",
    )
    adopt_review_parser.add_argument(
        "--out",
        help="Write the Markdown adopt-review report to a file. Relative paths are resolved inside PATH.",
    )
    adopt_review_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    adopt_review_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the adopt-review report without writing --out.",
    )
    adopt_review_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    adopt_plan_parser = subparsers.add_parser(
        "adopt-plan",
        help="Turn adopt-review migration findings into a prioritized cleanup task list.",
    )
    adopt_plan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="FictionOps migration sandbox to plan. Default: current directory.",
    )
    adopt_plan_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for book-gate integration. Default: book_01.",
    )
    adopt_plan_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used by underlying audits. Default: **/*.md.",
    )
    adopt_plan_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Chapters below this nonspace-character count are treated as placeholders. Default: 200.",
    )
    adopt_plan_parser.add_argument(
        "--watch",
        help="Comma-separated style watch terms passed to doctor. Defaults to common FictionOps markers.",
    )
    adopt_plan_parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="Number of aggregate style/echo items to consider. Default: 12.",
    )
    adopt_plan_parser.add_argument(
        "--min-repeat",
        type=int,
        default=3,
        help="Minimum repeated sentence-opening count. Default: 3.",
    )
    adopt_plan_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan detected chapter text for rough echo or information-boundary hits.",
    )
    adopt_plan_parser.add_argument(
        "--stale-after",
        type=int,
        default=8,
        help="Flag echo threads whose last recorded echo is this many chapters behind. Default: 8.",
    )
    adopt_plan_parser.add_argument(
        "--max-issues",
        type=int,
        default=200,
        help="Maximum adopt-review issues to convert into tasks. Default: 200.",
    )
    adopt_plan_parser.add_argument(
        "--waivers",
        help="Optional JSON waiver file passed through to adopt-review. Relative paths are resolved inside PATH; defaults to 07_audits/adopt_review/waivers.json when present.",
    )
    adopt_plan_parser.add_argument(
        "--out",
        help="Write the Markdown adopt-plan report to a file. Relative paths are resolved inside PATH.",
    )
    adopt_plan_parser.add_argument(
        "--write-groups",
        help="Write one Markdown workfile per repair group plus index.md. Relative paths are resolved inside PATH.",
    )
    adopt_plan_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out or --write-groups files if they already exist.",
    )
    adopt_plan_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the adopt-plan report without writing --out.",
    )
    adopt_plan_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    import_plan_parser = subparsers.add_parser(
        "import-plan",
        help="Plan or safely apply moves from 06_drafts/import_queue into book chapter folders.",
    )
    import_plan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="FictionOps migration sandbox to inspect. Default: current directory.",
    )
    import_plan_parser.add_argument(
        "--book",
        default="book_01",
        help="Fallback book id when no book marker can be inferred. Default: book_01.",
    )
    import_plan_parser.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="Maximum import queue files to include in detail. Summary counts still include all files. Default: 200.",
    )
    import_plan_parser.add_argument(
        "--apply",
        action="store_true",
        help="Move only unambiguous ready rows into their suggested chapter paths.",
    )
    import_plan_parser.add_argument(
        "--create-scaffolds",
        action="store_true",
        help="With --apply, create missing chapter engines and retrospectives for moved chapter files without overwriting existing files.",
    )
    import_plan_parser.add_argument(
        "--replace-placeholder-targets",
        action="store_true",
        help="With --apply, replace existing chapter targets only when they still look like generated placeholders.",
    )
    import_plan_parser.add_argument(
        "--out",
        help="Write the Markdown import-plan report to a file. Relative paths are resolved inside PATH.",
    )
    import_plan_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    import_plan_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the import-plan report without writing --out or moving files.",
    )
    import_plan_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    init_parser = subparsers.add_parser("init", help="Create a new FictionOps project skeleton.")
    init_parser.add_argument("path", help="Target directory for the new project.")
    init_parser.add_argument("--title", help="Project title. Defaults to the target directory name.")
    init_parser.add_argument("--language", default="zh-CN", help="Project language code. Default: zh-CN.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite generated files if they already exist.")
    init_parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing files.")

    new_book_parser = subparsers.add_parser(
        "new-book",
        help="Create a book outline, draft directories, and book retrospective file.",
    )
    new_book_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    new_book_parser.add_argument(
        "--book",
        required=True,
        help="Book id, such as 2, 02, book_02, or book-02.",
    )
    new_book_parser.add_argument("--title", help="Book title used in generated files.")
    new_book_parser.add_argument("--force", action="store_true", help="Overwrite generated files if they already exist.")
    new_book_parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing files.")

    new_chapter_parser = subparsers.add_parser(
        "new-chapter",
        help="Create a chapter draft, chapter engine, and retrospective file.",
    )
    new_chapter_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    new_chapter_parser.add_argument(
        "--book",
        default="book_01",
        help="Book directory under 06_drafts. Default: book_01.",
    )
    new_chapter_parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter number, such as 1, 001, ch_001, or 第1章.",
    )
    new_chapter_parser.add_argument("--title", help="Chapter title used in generated files.")
    new_chapter_parser.add_argument("--viewpoint", help="Viewpoint character for the chapter engine.")
    new_chapter_parser.add_argument("--kind", help="Chapter type, such as 核心情节, 转场, 战斗, or 情绪承重.")
    new_chapter_parser.add_argument("--target-chars", type=int, help="Suggested chapter length for the engine.")
    new_chapter_parser.add_argument("--force", action="store_true", help="Overwrite generated files if they already exist.")
    new_chapter_parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing files.")

    plan_chapter_parser = subparsers.add_parser(
        "plan-chapter",
        help="Fill a chapter engine from the book outline chapter-planning table.",
    )
    plan_chapter_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    plan_chapter_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    plan_chapter_parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter number, such as 1, 001, ch_001, or 第1章.",
    )
    plan_chapter_parser.add_argument(
        "--outline",
        help="Specific book outline path. Relative paths are resolved inside PATH.",
    )
    plan_chapter_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite non-empty fields in the chapter engine.",
    )
    plan_chapter_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned field updates without writing the engine file.",
    )

    scene_parser = subparsers.add_parser(
        "scene-plan",
        help="Build a scene skeleton from a filled chapter engine.",
    )
    scene_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    scene_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    scene_parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter number, such as 1, 001, ch_001, or 第1章.",
    )
    scene_parser.add_argument(
        "--engine",
        help="Specific chapter engine path. Relative paths are resolved inside PATH.",
    )
    scene_parser.add_argument(
        "--out",
        help="Write a Markdown scene plan to a file. Relative paths are resolved inside PATH.",
    )
    scene_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    scene_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the scene plan without writing --out.",
    )
    scene_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    draft_brief_parser = subparsers.add_parser(
        "draft-brief",
        help="Build a task-ready drafting brief from scene plan and scoped context.",
    )
    draft_brief_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    draft_brief_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    draft_brief_parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter number, such as 1, 001, ch_001, or 第1章.",
    )
    draft_brief_parser.add_argument(
        "--engine",
        help="Specific chapter engine path. Relative paths are resolved inside PATH.",
    )
    draft_brief_parser.add_argument(
        "--include-context-content",
        action="store_true",
        help="Embed scoped context file contents in the brief.",
    )
    draft_brief_parser.add_argument(
        "--max-chars-per-file",
        type=int,
        default=6000,
        help="Maximum characters to embed from each context file. Default: 6000.",
    )
    draft_brief_parser.add_argument(
        "--max-total-chars",
        type=int,
        default=60000,
        help="Maximum total characters to embed across context files. Default: 60000.",
    )
    draft_brief_parser.add_argument(
        "--out",
        help="Write the Markdown draft brief to a file. Relative paths are resolved inside PATH.",
    )
    draft_brief_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    draft_brief_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the draft brief without writing --out.",
    )
    draft_brief_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    post_draft_parser = subparsers.add_parser(
        "post-draft",
        help="Check whether a drafted chapter has closed its immediate post-draft memory.",
    )
    post_draft_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    post_draft_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    post_draft_parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter number, such as 1, 001, ch_001, or 第1章.",
    )
    post_draft_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Minimum nonspace characters before a chapter stops looking like a placeholder. Default: 200.",
    )
    post_draft_parser.add_argument(
        "--out",
        help="Write the Markdown post-draft gate report to a file. Relative paths are resolved inside PATH.",
    )
    post_draft_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    post_draft_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the post-draft report without writing --out.",
    )
    post_draft_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    review_gate_parser = subparsers.add_parser(
        "review-gate",
        help="Aggregate single-chapter post-draft, continuity, information, character, echo, style, and wave checks.",
    )
    review_gate_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    review_gate_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    review_gate_parser.add_argument(
        "--chapter",
        required=True,
        help="Chapter number, such as 1, 001, ch_001, or 第1章.",
    )
    review_gate_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Minimum nonspace characters before a chapter stops looking like a placeholder. Default: 200.",
    )
    review_gate_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used by the underlying audits. Default: **/*.md.",
    )
    review_gate_parser.add_argument(
        "--out",
        help="Write the Markdown review gate report to a file. Relative paths are resolved inside PATH.",
    )
    review_gate_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    review_gate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the review gate report without writing --out.",
    )
    review_gate_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    book_gate_parser = subparsers.add_parser(
        "book-gate",
        help="Aggregate book-level plan, retrospective, table, word-scan, revision, and wave checks before clean export.",
    )
    book_gate_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    book_gate_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    book_gate_parser.add_argument(
        "--outline",
        help="Specific book outline path. Relative paths are resolved inside PATH.",
    )
    book_gate_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Minimum nonspace characters before a chapter stops looking like a placeholder. Default: 200.",
    )
    book_gate_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used by the underlying audits. Default: **/*.md.",
    )
    book_gate_parser.add_argument(
        "--out",
        help="Write the Markdown book gate report to a file. Relative paths are resolved inside PATH.",
    )
    book_gate_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    book_gate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the book gate report without writing --out.",
    )
    book_gate_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    plan_audit_parser = subparsers.add_parser(
        "audit-plan",
        help="Audit book-outline chapter plans against drafts and chapter engines.",
    )
    plan_audit_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    plan_audit_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    plan_audit_parser.add_argument(
        "--outline",
        help="Specific book outline path. Relative paths are resolved inside PATH.",
    )
    plan_audit_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    retrospective_parser = subparsers.add_parser(
        "retrospective",
        help="Summarize chapter retrospectives and book-level revision follow-up.",
    )
    retrospective_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    retrospective_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    retrospective_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )
    retrospective_parser.add_argument(
        "--out",
        help="Write the retrospective report to a file. Relative paths are resolved inside PATH.",
    )
    retrospective_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )

    stats_parser = subparsers.add_parser("stats", help="Report Markdown chapter length statistics.")
    stats_parser.add_argument("path", nargs="?", default=".", help="Target file or directory. Default: current directory.")
    stats_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files instead of only detected chapter files.",
    )
    stats_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    stats_parser.add_argument(
        "--metric",
        choices=["nonspace", "cjk", "chars"],
        default="nonspace",
        help="Metric for totals, averages, and length bands. Default: nonspace.",
    )
    stats_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    scan_words_parser = subparsers.add_parser("scan-words", help="Scan Markdown files for high-frequency terms and watch words.")
    scan_words_parser.add_argument("path", nargs="?", default=".", help="Target file or directory. Default: current directory.")
    scan_words_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files instead of only detected chapter files.",
    )
    scan_words_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    scan_words_parser.add_argument(
        "--watch",
        help="Comma-separated watch terms to count exactly.",
    )
    scan_words_parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        help="Minimum count for high-frequency terms. Default: 2.",
    )
    scan_words_parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Maximum number of terms to show. Default: 20.",
    )
    scan_words_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    check_tables_parser = subparsers.add_parser("check-tables", help="Check Markdown tables for structural and placeholder gaps.")
    check_tables_parser.add_argument("path", nargs="?", default=".", help="Target file or directory. Default: current directory.")
    check_tables_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files instead of only detected chapter files.",
    )
    check_tables_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    check_tables_parser.add_argument(
        "--min-filled-cells",
        type=int,
        default=1,
        help="Minimum filled cells required per body row. Default: 1.",
    )
    check_tables_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    wave_parser = subparsers.add_parser("audit-wave", help="Audit chapter length wave and pacing variation.")
    wave_parser.add_argument("path", nargs="?", default=".", help="Target file or directory. Default: current directory.")
    wave_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files instead of only detected chapter files.",
    )
    wave_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    wave_parser.add_argument(
        "--metric",
        choices=["nonspace", "cjk", "chars"],
        default="nonspace",
        help="Metric for chapter wave values and bands. Default: nonspace.",
    )
    wave_parser.add_argument(
        "--flat-tolerance",
        type=int,
        default=200,
        help="Adjacent chapters within this metric delta count as a flat run. Default: 200.",
    )
    wave_parser.add_argument(
        "--min-spread-ratio",
        type=int,
        default=15,
        help="Flag book-level wave spread below this percent of average. Default: 15.",
    )
    wave_parser.add_argument(
        "--max-flat-run",
        type=int,
        default=4,
        help="Flag this many adjacent chapters in a flat run. Default: 4.",
    )
    wave_parser.add_argument(
        "--max-same-band-run",
        type=int,
        default=5,
        help="Flag this many adjacent chapters in the same length band. Default: 5.",
    )
    wave_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    style_parser = subparsers.add_parser("audit-style", help="Run a static prose-pattern audit.")
    style_parser.add_argument("path", nargs="?", default=".", help="Target file or directory. Default: current directory.")
    style_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files instead of only detected chapter files.",
    )
    style_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    style_parser.add_argument(
        "--watch",
        help="Comma-separated watch terms. Defaults to common FictionOps style markers.",
    )
    style_parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="Number of aggregate items to show. Default: 12.",
    )
    style_parser.add_argument(
        "--min-repeat",
        type=int,
        default=3,
        help="Minimum repeated sentence-opening count. Default: 3.",
    )
    style_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    continuity_parser = subparsers.add_parser("audit-continuity", help="Run a static continuity maintenance audit.")
    continuity_parser.add_argument("path", nargs="?", default=".", help="Target project, book, chapter file, or directory.")
    continuity_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    continuity_parser.add_argument(
        "--skip-standard",
        action="store_true",
        help="Skip standard FictionOps project-memory file checks.",
    )
    continuity_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Chapters below this nonspace-character count are treated as placeholders. Default: 200.",
    )
    continuity_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    echoes_parser = subparsers.add_parser("audit-echoes", help="Run a static foreshadowing echo-table audit.")
    echoes_parser.add_argument("path", nargs="?", default=".", help="Target project, book, echo table, or directory.")
    echoes_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    echoes_parser.add_argument(
        "--table",
        help="Specific echo table path, relative to PATH when PATH is a directory.",
    )
    echoes_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan detected chapter text for rough thread-label hits.",
    )
    echoes_parser.add_argument(
        "--stale-after",
        type=int,
        default=8,
        help="Flag threads whose last recorded echo is this many chapters behind the latest chapter. Default: 8.",
    )
    echoes_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    info_parser = subparsers.add_parser("audit-info", help="Run a static information-boundary audit.")
    info_parser.add_argument("path", nargs="?", default=".", help="Target project, book, information table, or directory.")
    info_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    info_parser.add_argument(
        "--table",
        help="Specific information release table path, relative to PATH when PATH is a directory.",
    )
    info_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan detected chapter text for rough information-boundary hits.",
    )
    info_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    character_parser = subparsers.add_parser("audit-characters", help="Run a static character arc and voice audit.")
    character_parser.add_argument("path", nargs="?", default=".", help="Target project, character file, or directory.")
    character_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    character_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    agent_prompt_parser = subparsers.add_parser("agent-prompt", help="Render a role-specific FictionOps agent prompt.")
    agent_prompt_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    agent_prompt_parser.add_argument(
        "--role",
        required=True,
        choices=AGENT_ROLE_CHOICES,
        help="Agent role to render.",
    )
    agent_prompt_parser.add_argument(
        "--task",
        choices=CONTEXT_TASKS,
        help="Context task type. Defaults to the role's natural task.",
    )
    agent_prompt_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    agent_prompt_parser.add_argument(
        "--chapter",
        help="Chapter number for draft/review contexts, such as 1, 001, or ch_001.",
    )
    agent_prompt_parser.add_argument(
        "--include-context",
        action="store_true",
        help="Append a scoped context-pack to the prompt.",
    )
    agent_prompt_parser.add_argument(
        "--include-context-content",
        action="store_true",
        help="Embed selected file contents when --include-context is used.",
    )
    agent_prompt_parser.add_argument(
        "--max-chars-per-file",
        type=int,
        default=6000,
        help="Maximum characters embedded from each context file. Default: 6000.",
    )
    agent_prompt_parser.add_argument(
        "--max-total-chars",
        type=int,
        default=60000,
        help="Maximum total characters embedded across context files. Default: 60000.",
    )
    agent_prompt_parser.add_argument(
        "--out",
        help="Write the agent prompt to a file. Relative paths are resolved inside PATH.",
    )
    agent_prompt_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    agent_prompt_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the prompt without writing --out.",
    )
    agent_prompt_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    agent_connect_parser = subparsers.add_parser(
        "agent-connect",
        help="Create a connector handshake kit for an external model runner or controller.",
    )
    agent_connect_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    agent_connect_parser.add_argument(
        "--name",
        default=DEFAULT_CONNECTOR_NAME,
        help="Connector name used for the output directory and manifest. Default: default.",
    )
    agent_connect_parser.add_argument(
        "--mode",
        choices=AGENT_CONNECT_MODES,
        default="runner",
        help="Connector mode to describe. Default: runner.",
    )
    agent_connect_parser.add_argument(
        "--out-dir",
        help="Connector kit output directory. Relative paths are resolved inside PATH.",
    )
    agent_connect_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing connector kit files.",
    )
    agent_connect_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the connector report without writing files.",
    )
    agent_connect_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    agent_smoke_parser = subparsers.add_parser(
        "agent-smoke",
        help="Run a no-network connector smoke test through agent-run, agent-exec, and agent-inbox.",
    )
    agent_smoke_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    agent_smoke_parser.add_argument(
        "--connector",
        required=True,
        help="Connector kit name under 00_management/agent_connectors/<name>.",
    )
    agent_smoke_parser.add_argument(
        "--level",
        choices=["manual", "runner", "controller", "model-runner"],
        help="Expected integration level. Defaults to the connector manifest mode, then runner.",
    )
    agent_smoke_parser.add_argument(
        "--role",
        choices=AGENT_ROLE_CHOICES,
        default="draft-writer",
        help="Agent role used for the smoke task bundle. Default: draft-writer.",
    )
    agent_smoke_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    agent_smoke_parser.add_argument(
        "--chapter",
        default=DEFAULT_AGENT_SMOKE_CHAPTER,
        help="Chapter number used for the smoke task bundle. Default: 001.",
    )
    agent_smoke_parser.add_argument(
        "--out-dir",
        help="Agent smoke run directory. Relative paths are resolved inside PATH.",
    )
    agent_smoke_parser.add_argument(
        "--output-name",
        default=DEFAULT_AGENT_EXEC_OUTPUT,
        help="Staging output filename to write inside the smoke run directory. Default: output.md.",
    )
    agent_smoke_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
        help="Adapter timeout in seconds. Default: 60.",
    )
    agent_smoke_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing smoke bundle output and execution receipt.",
    )
    agent_smoke_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the smoke chain without writing or executing the adapter.",
    )
    agent_smoke_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    agent_run_parser = subparsers.add_parser(
        "agent-run",
        help="Prepare a scoped agent task bundle without calling a model.",
    )
    agent_run_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    agent_run_parser.add_argument(
        "--role",
        required=True,
        choices=AGENT_ROLE_CHOICES,
        help="Agent role to prepare.",
    )
    agent_run_parser.add_argument(
        "--task",
        choices=CONTEXT_TASKS,
        help="Context task type. Defaults to the role's natural task.",
    )
    agent_run_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    agent_run_parser.add_argument(
        "--chapter",
        help="Chapter number for draft/review/canon-sync tasks, such as 1, 001, or ch_001.",
    )
    agent_run_parser.add_argument(
        "--out-dir",
        help="Write the prepared agent bundle to this directory. Relative paths are resolved inside PATH.",
    )
    agent_run_parser.add_argument(
        "--no-context-content",
        action="store_true",
        help="Only list scoped context files; do not embed file contents in prompt/context artifacts.",
    )
    agent_run_parser.add_argument(
        "--max-chars-per-file",
        type=int,
        default=6000,
        help="Maximum characters embedded from each context file. Default: 6000.",
    )
    agent_run_parser.add_argument(
        "--max-total-chars",
        type=int,
        default=60000,
        help="Maximum total characters embedded across context files. Default: 60000.",
    )
    agent_run_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing bundle files if they already exist.",
    )
    agent_run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the agent-run report without writing --out-dir.",
    )
    agent_run_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    agent_exec_parser = subparsers.add_parser(
        "agent-exec",
        help="Run an external command for an agent-run bundle and save stdout as staged output.",
    )
    agent_exec_parser.add_argument(
        "path",
        help="Target agent-run directory containing request.json, prompt.md, and context_pack.md.",
    )
    agent_exec_parser.add_argument(
        "--output-name",
        default=DEFAULT_AGENT_EXEC_OUTPUT,
        help="Staging output filename to write inside PATH. Default: output.md.",
    )
    agent_exec_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="External runner timeout in seconds. Default: 300.",
    )
    agent_exec_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing staged output or execution receipt.",
    )
    agent_exec_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the runner input and report without executing the external command.",
    )
    agent_exec_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )
    agent_exec_parser.add_argument(
        "--runner",
        nargs=argparse.REMAINDER,
        required=True,
        help="External runner command. Put FictionOps options before --runner; everything after it is passed to the runner.",
    )

    agent_inbox_parser = subparsers.add_parser(
        "agent-inbox",
        help="Inspect external agent outputs saved beside agent-run bundles.",
    )
    agent_inbox_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory or a single agent-run directory. Default: current directory.",
    )
    agent_inbox_parser.add_argument(
        "--runs-dir",
        help="Agent runs directory to scan when PATH is a project. Default: 00_management/agent_runs.",
    )
    agent_inbox_parser.add_argument(
        "--output-name",
        help="Specific output filename to look for inside each run directory. Default: output.md/response.md/result.md/staging.md/model_output.md/agent_output.md/*.staging.md.",
    )
    agent_inbox_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    agent_next_parser = subparsers.add_parser(
        "agent-next",
        help="Select the next safe FictionOps command for an external agent controller.",
    )
    agent_next_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory, legacy directory, or future project path. Default: current directory.",
    )
    agent_next_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    agent_next_parser.add_argument(
        "--chapter",
        help="Optional chapter number for chapter-aware next-step selection.",
    )
    agent_next_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan chapter text while building the underlying health evidence.",
    )
    agent_next_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    agent_workflow_parser = subparsers.add_parser(
        "audit-agent-workflow",
        help="Audit whether a project is ready for bounded external agent workflow integration.",
    )
    agent_workflow_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    agent_workflow_parser.add_argument(
        "--level",
        choices=["manual", "runner", "controller", "model-runner"],
        default="runner",
        help="Integration level to audit. Default: runner.",
    )
    agent_workflow_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for controller-level next-step evidence. Default: book_01.",
    )
    agent_workflow_parser.add_argument(
        "--chapter",
        help="Optional chapter number used for controller-level next-step evidence.",
    )
    agent_workflow_parser.add_argument(
        "--connector",
        help="Validate a connector kit under 00_management/agent_connectors/<name>.",
    )
    agent_workflow_parser.add_argument(
        "--scan-text",
        action="store_true",
        help="Allow controller-level audit to run text scans through agent-next.",
    )
    agent_workflow_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    model_config_parser = subparsers.add_parser(
        "model-config",
        help="Create or audit local model provider configuration.",
    )
    model_config_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    model_config_parser.add_argument("--provider", help="Model provider name, such as openai, local, or custom.")
    model_config_parser.add_argument("--planning-model", help="Model id for planning tasks.")
    model_config_parser.add_argument("--drafting-model", help="Model id for drafting tasks.")
    model_config_parser.add_argument("--audit-model", help="Model id for audit/revision tasks.")
    model_config_parser.add_argument(
        "--api-key-env",
        help="Environment variable name containing the API key. Raw keys are never written.",
    )
    model_config_parser.add_argument("--base-url", help="Optional provider base URL.")
    model_config_parser.add_argument("--max-context-chars", type=int, help="Maximum context characters to pass to a model.")
    model_config_parser.add_argument("--max-output-tokens", type=int, help="Maximum model output tokens.")
    model_config_parser.add_argument("--timeout-seconds", type=int, help="Model request timeout in seconds.")
    model_config_parser.add_argument(
        "--out",
        help="Model config output path. Default with --write: 00_management/model_config.json.",
    )
    model_config_parser.add_argument(
        "--write",
        action="store_true",
        help="Write the model config JSON. Without this flag the command only reports the proposed config.",
    )
    model_config_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the config file if it already exists.",
    )
    model_config_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the config report without writing even when --write is set.",
    )
    model_config_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    context_parser = subparsers.add_parser("context-pack", help="Build a scoped context pack for agent handoff.")
    context_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    context_parser.add_argument(
        "--task",
        choices=CONTEXT_TASKS,
        default="draft",
        help="Context task type. Default: draft.",
    )
    context_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    context_parser.add_argument(
        "--chapter",
        help="Chapter number for draft/review/canon-sync tasks, such as 1, 001, or ch_001.",
    )
    context_parser.add_argument(
        "--no-content",
        action="store_true",
        help="Only list scoped files; do not embed file contents.",
    )
    context_parser.add_argument(
        "--max-chars-per-file",
        type=int,
        default=6000,
        help="Maximum characters embedded from each file. Default: 6000.",
    )
    context_parser.add_argument(
        "--max-total-chars",
        type=int,
        default=60000,
        help="Maximum total characters embedded across all files. Default: 60000.",
    )
    context_parser.add_argument(
        "--out",
        help="Write a Markdown context pack to a file. Relative paths are resolved inside PATH.",
    )
    context_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    context_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the context pack summary without writing --out.",
    )
    context_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    workflow_parser = subparsers.add_parser(
        "workflow-plan",
        help="Build a staged FictionOps workflow checklist without executing commands.",
    )
    workflow_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target project directory, or future project path for --stage init. Default: current directory.",
    )
    workflow_parser.add_argument(
        "--stage",
        default="all",
        help="Workflow stage: all, init, foundation, book-plan, chapter-prep, draft, review, book-retrospective, publish, or handoff. Aliases like prep/release are accepted.",
    )
    workflow_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    workflow_parser.add_argument(
        "--chapter",
        help="Chapter number for chapter-prep, draft, or review stages.",
    )
    workflow_parser.add_argument(
        "--out",
        help="Write a Markdown workflow plan to a file. Relative paths are resolved inside PATH.",
    )
    workflow_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    workflow_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the workflow plan without writing --out.",
    )
    workflow_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    revision_parser = subparsers.add_parser(
        "revision-plan",
        help="Turn audit findings into a prioritized revision task list.",
    )
    revision_parser.add_argument("path", nargs="?", default=".", help="Target project, book, or directory.")
    revision_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    revision_parser.add_argument(
        "--outline",
        help="Specific book outline path. Relative paths are resolved inside PATH.",
    )
    revision_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files for stats/style instead of only detected chapter files.",
    )
    revision_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    revision_parser.add_argument(
        "--metric",
        choices=["nonspace", "cjk", "chars"],
        default="nonspace",
        help="Metric for stats totals and chapter-wave thresholds. Default: nonspace.",
    )
    revision_parser.add_argument(
        "--flat-tolerance",
        type=int,
        default=200,
        help="Adjacent chapters within this metric delta count as a flat wave run. Default: 200.",
    )
    revision_parser.add_argument(
        "--min-spread-ratio",
        type=int,
        default=15,
        help="Flag chapter wave spread below this percent of average. Default: 15.",
    )
    revision_parser.add_argument(
        "--max-flat-run",
        type=int,
        default=4,
        help="Flag this many adjacent chapters in a flat wave run. Default: 4.",
    )
    revision_parser.add_argument(
        "--max-same-band-run",
        type=int,
        default=5,
        help="Flag this many adjacent chapters in the same length band. Default: 5.",
    )
    revision_parser.add_argument(
        "--skip-standard",
        action="store_true",
        help="Skip standard FictionOps project-memory file checks.",
    )
    revision_parser.add_argument(
        "--strict-standard",
        action="store_true",
        help="Force standard FictionOps project-memory file checks even if PATH does not look like a standard project.",
    )
    revision_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Chapters below this nonspace-character count are treated as placeholders. Default: 200.",
    )
    revision_parser.add_argument(
        "--watch",
        help="Comma-separated style watch terms. Defaults to common FictionOps style markers.",
    )
    revision_parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="Number of aggregate style items to consider. Default: 12.",
    )
    revision_parser.add_argument(
        "--min-repeat",
        type=int,
        default=3,
        help="Minimum repeated sentence-opening count. Default: 3.",
    )
    revision_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan chapter text for rough echo or information-boundary hits.",
    )
    revision_parser.add_argument(
        "--stale-after",
        type=int,
        default=8,
        help="Flag echo threads whose last recorded echo is this many chapters behind. Default: 8.",
    )
    revision_parser.add_argument(
        "--out",
        help="Write the revision plan to a file. Relative paths are resolved inside PATH.",
    )
    revision_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    revision_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the revision plan without writing --out.",
    )
    revision_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Run a project health summary across available audits.")
    doctor_parser.add_argument("path", nargs="?", default=".", help="Target project, book, or directory.")
    doctor_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files for stats/style instead of only detected chapter files.",
    )
    doctor_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    doctor_parser.add_argument(
        "--metric",
        choices=["nonspace", "cjk", "chars"],
        default="nonspace",
        help="Metric for stats totals and bands. Default: nonspace.",
    )
    doctor_parser.add_argument(
        "--flat-tolerance",
        type=int,
        default=200,
        help="Adjacent chapters within this metric delta count as a flat wave run. Default: 200.",
    )
    doctor_parser.add_argument(
        "--min-spread-ratio",
        type=int,
        default=15,
        help="Flag chapter wave spread below this percent of average. Default: 15.",
    )
    doctor_parser.add_argument(
        "--max-flat-run",
        type=int,
        default=4,
        help="Flag this many adjacent chapters in a flat wave run. Default: 4.",
    )
    doctor_parser.add_argument(
        "--max-same-band-run",
        type=int,
        default=5,
        help="Flag this many adjacent chapters in the same length band. Default: 5.",
    )
    doctor_parser.add_argument(
        "--skip-standard",
        action="store_true",
        help="Skip standard FictionOps project-memory file checks.",
    )
    doctor_parser.add_argument(
        "--strict-standard",
        action="store_true",
        help="Force standard FictionOps project-memory file checks even if PATH does not look like a standard project.",
    )
    doctor_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Chapters below this nonspace-character count are treated as placeholders. Default: 200.",
    )
    doctor_parser.add_argument(
        "--watch",
        help="Comma-separated style watch terms. Defaults to common FictionOps style markers.",
    )
    doctor_parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="Number of aggregate style/echo items to consider. Default: 12.",
    )
    doctor_parser.add_argument(
        "--min-repeat",
        type=int,
        default=3,
        help="Minimum repeated sentence-opening count. Default: 3.",
    )
    doctor_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan detected chapter text for rough echo or information-boundary hits.",
    )
    doctor_parser.add_argument(
        "--stale-after",
        type=int,
        default=8,
        help="Flag echo threads whose last recorded echo is this many chapters behind the latest chapter. Default: 8.",
    )
    doctor_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for plan audit integration. Default: book_01.",
    )
    doctor_parser.add_argument(
        "--outline",
        help="Specific book outline path for plan audit integration. Relative paths are resolved inside PATH.",
    )
    doctor_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    report_parser = subparsers.add_parser("report", help="Write a project health report to Markdown or JSON.")
    report_parser.add_argument("path", nargs="?", default=".", help="Target project, book, or directory.")
    report_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all Markdown files for stats/style instead of only detected chapter files.",
    )
    report_parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="Glob pattern used when PATH is a directory. Default: **/*.md.",
    )
    report_parser.add_argument(
        "--metric",
        choices=["nonspace", "cjk", "chars"],
        default="nonspace",
        help="Metric for stats totals and bands. Default: nonspace.",
    )
    report_parser.add_argument(
        "--flat-tolerance",
        type=int,
        default=200,
        help="Adjacent chapters within this metric delta count as a flat wave run. Default: 200.",
    )
    report_parser.add_argument(
        "--min-spread-ratio",
        type=int,
        default=15,
        help="Flag chapter wave spread below this percent of average. Default: 15.",
    )
    report_parser.add_argument(
        "--max-flat-run",
        type=int,
        default=4,
        help="Flag this many adjacent chapters in a flat wave run. Default: 4.",
    )
    report_parser.add_argument(
        "--max-same-band-run",
        type=int,
        default=5,
        help="Flag this many adjacent chapters in the same length band. Default: 5.",
    )
    report_parser.add_argument(
        "--skip-standard",
        action="store_true",
        help="Skip standard FictionOps project-memory file checks.",
    )
    report_parser.add_argument(
        "--strict-standard",
        action="store_true",
        help="Force standard FictionOps project-memory file checks even if PATH does not look like a standard project.",
    )
    report_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Chapters below this nonspace-character count are treated as placeholders. Default: 200.",
    )
    report_parser.add_argument(
        "--watch",
        help="Comma-separated style watch terms. Defaults to common FictionOps style markers.",
    )
    report_parser.add_argument(
        "--top",
        type=int,
        default=12,
        help="Number of aggregate style/echo items to consider. Default: 12.",
    )
    report_parser.add_argument(
        "--min-repeat",
        type=int,
        default=3,
        help="Minimum repeated sentence-opening count. Default: 3.",
    )
    report_parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Do not scan detected chapter text for rough echo or information-boundary hits.",
    )
    report_parser.add_argument(
        "--stale-after",
        type=int,
        default=8,
        help="Flag echo threads whose last recorded echo is this many chapters behind the latest chapter. Default: 8.",
    )
    report_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for plan audit integration. Default: book_01.",
    )
    report_parser.add_argument(
        "--outline",
        help="Specific book outline path for plan audit integration. Relative paths are resolved inside PATH.",
    )
    report_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Report format. Default: markdown.",
    )
    report_parser.add_argument(
        "--out",
        help="Write the report to a file. Relative paths are resolved inside PATH when PATH is a directory.",
    )
    report_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )

    export_clean_parser = subparsers.add_parser(
        "export-clean",
        help="Merge book draft chapters into clean publish-ready Markdown.",
    )
    export_clean_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    export_clean_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id or directory under 06_drafts. Default: book_01.",
    )
    export_clean_parser.add_argument(
        "--out",
        help="Write clean Markdown to a file. Default: 08_publish/clean_markdown/<book>.md.",
    )
    export_clean_parser.add_argument(
        "--title",
        help="Optional top-level title inserted before chapter content.",
    )
    export_clean_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Summary output format. Default: table.",
    )
    export_clean_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the clean Markdown output if it already exists.",
    )
    export_clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing the clean Markdown file.",
    )

    publish_audit_parser = subparsers.add_parser(
        "audit-publish",
        help="Audit clean Markdown before publishing.",
    )
    publish_audit_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory or clean Markdown file. Default: current directory.",
    )
    publish_audit_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for the default clean Markdown path. Default: book_01.",
    )
    publish_audit_parser.add_argument(
        "--file",
        help="Specific clean Markdown file. Relative paths are resolved inside PATH when PATH is a directory.",
    )
    publish_audit_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Chapters below this nonspace-character count are flagged. Default: 200.",
    )
    publish_audit_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format. Default: table.",
    )

    publish_copy_parser = subparsers.add_parser(
        "publish-copy",
        help="Draft synopsis, tag, and keyword candidates from project evidence.",
    )
    publish_copy_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    publish_copy_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for default publish paths. Default: book_01.",
    )
    publish_copy_parser.add_argument(
        "--clean-file",
        help="Specific clean Markdown file. Relative paths are resolved inside PATH.",
    )
    publish_copy_parser.add_argument(
        "--checklist-file",
        help="Specific publish checklist file. Relative paths are resolved inside PATH.",
    )
    publish_copy_parser.add_argument(
        "--outline-file",
        help="Specific book outline file. Relative paths are resolved inside PATH.",
    )
    publish_copy_parser.add_argument(
        "--seed-file",
        help="Specific story seed file. Relative paths are resolved inside PATH.",
    )
    publish_copy_parser.add_argument(
        "--out",
        help="Write publish-copy Markdown draft. Default: 08_publish/synopsis/<book>_publish_copy.md.",
    )
    publish_copy_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )
    publish_copy_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the publish-copy draft if it already exists.",
    )
    publish_copy_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the publish-copy draft without writing --out.",
    )

    metadata_parser = subparsers.add_parser(
        "export-metadata",
        help="Export publish checklist metadata to JSON.",
    )
    metadata_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory or publish checklist file. Default: current directory.",
    )
    metadata_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for the default metadata output path. Default: book_01.",
    )
    metadata_parser.add_argument(
        "--file",
        help="Specific publish checklist file. Relative paths are resolved inside PATH when PATH is a directory.",
    )
    metadata_parser.add_argument(
        "--out",
        help="Write metadata JSON to a file. Default: 08_publish/metadata/<book>_metadata.json.",
    )
    metadata_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Summary output format. Default: table.",
    )
    metadata_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the metadata JSON output if it already exists.",
    )
    metadata_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing metadata JSON.",
    )

    manifest_parser = subparsers.add_parser(
        "export-manifest",
        help="Export a publish package manifest from clean Markdown and metadata JSON.",
    )
    manifest_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    manifest_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for default publish package paths. Default: book_01.",
    )
    manifest_parser.add_argument(
        "--clean-file",
        help="Specific clean Markdown file. Relative paths are resolved inside PATH.",
    )
    manifest_parser.add_argument(
        "--metadata-file",
        help="Specific metadata JSON file. Relative paths are resolved inside PATH.",
    )
    manifest_parser.add_argument(
        "--out",
        help="Write manifest JSON to a file. Default: 08_publish/manifest/<book>_manifest.json.",
    )
    manifest_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Summary output format. Default: table.",
    )
    manifest_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the manifest JSON output if it already exists.",
    )
    manifest_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing manifest JSON.",
    )

    epub_parser = subparsers.add_parser(
        "export-epub",
        help="Export a styled EPUB from publish manifest, clean Markdown, and metadata JSON.",
    )
    epub_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    epub_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for default publish paths. Default: book_01.",
    )
    epub_parser.add_argument(
        "--manifest-file",
        help="Specific publish manifest JSON file. Relative paths are resolved inside PATH.",
    )
    epub_parser.add_argument(
        "--clean-file",
        help="Specific clean Markdown file. Relative paths are resolved inside PATH.",
    )
    epub_parser.add_argument(
        "--metadata-file",
        help="Specific metadata JSON file. Relative paths are resolved inside PATH.",
    )
    epub_parser.add_argument(
        "--cover-file",
        help="Optional cover image file. Relative paths are resolved inside PATH and override manifest/metadata cover_image.",
    )
    epub_parser.add_argument(
        "--out",
        help="Write EPUB to a file. Default: 08_publish/epub/<book>.epub.",
    )
    epub_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Summary output format. Default: table.",
    )
    epub_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the EPUB output if it already exists.",
    )
    epub_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without writing EPUB.",
    )

    audit_epub_parser = subparsers.add_parser(
        "audit-epub",
        help="Audit an exported FictionOps EPUB package.",
    )
    audit_epub_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory or EPUB file. Default: current directory.",
    )
    audit_epub_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for default publish paths. Default: book_01.",
    )
    audit_epub_parser.add_argument(
        "--file",
        help="Specific EPUB file. Relative paths are resolved inside PATH when PATH is a directory.",
    )
    audit_epub_parser.add_argument(
        "--manifest-file",
        help="Specific publish manifest JSON file. Relative paths are resolved inside PATH.",
    )
    audit_epub_parser.add_argument(
        "--clean-file",
        help="Specific clean Markdown file. Relative paths are resolved inside PATH.",
    )
    audit_epub_parser.add_argument(
        "--metadata-file",
        help="Specific metadata JSON file. Relative paths are resolved inside PATH.",
    )
    audit_epub_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Summary output format. Default: table.",
    )

    release_gate_parser = subparsers.add_parser(
        "release-gate",
        help="Aggregate book closure, publish, metadata, manifest, and EPUB checks before release.",
    )
    release_gate_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target FictionOps project directory. Default: current directory.",
    )
    release_gate_parser.add_argument(
        "--book",
        default="book_01",
        help="Book id used for default publish paths. Default: book_01.",
    )
    release_gate_parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=200,
        help="Minimum nonspace characters for clean Markdown chapter checks. Default: 200.",
    )
    release_gate_parser.add_argument(
        "--out",
        help="Write the Markdown release gate report to a file. Relative paths are resolved inside PATH.",
    )
    release_gate_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite --out if it already exists.",
    )
    release_gate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the release gate report without writing --out.",
    )
    release_gate_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    release_evidence_parser = subparsers.add_parser(
        "audit-release-evidence",
        help="Audit FictionOps package release-trial evidence before closing the release milestone.",
    )
    release_evidence_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root or evidence file to inspect. Default: current directory.",
    )
    release_evidence_parser.add_argument(
        "--file",
        help="Specific release evidence Markdown file. Relative paths are resolved inside PATH.",
    )
    release_evidence_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    dogfood_cycle_parser = subparsers.add_parser(
        "audit-dogfood-cycle",
        help="Audit sustained real-project dogfood-cycle evidence before 1.0 stable-core closure.",
    )
    dogfood_cycle_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root or dogfood cycle evidence file to inspect. Default: current directory.",
    )
    dogfood_cycle_parser.add_argument(
        "--file",
        help="Specific dogfood cycle evidence Markdown file. Relative paths are resolved inside PATH.",
    )
    dogfood_cycle_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    stability_window_parser = subparsers.add_parser(
        "audit-stability-window",
        help="Audit compatibility/stability-window evidence before 1.0 stable-core closure.",
    )
    stability_window_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root or stability window evidence file to inspect. Default: current directory.",
    )
    stability_window_parser.add_argument(
        "--file",
        help="Specific stability window evidence Markdown file. Relative paths are resolved inside PATH.",
    )
    stability_window_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    stable_core_parser = subparsers.add_parser(
        "audit-stable-core",
        help="Aggregate 1.0 stable-core evidence before closing the stable milestone.",
    )
    stable_core_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root to inspect. Default: current directory.",
    )
    stable_core_parser.add_argument(
        "--release-file",
        help="Specific release evidence Markdown file. Relative paths are resolved inside PATH.",
    )
    stable_core_parser.add_argument(
        "--dogfood-file",
        help="Specific dogfood cycle evidence Markdown file. Relative paths are resolved inside PATH.",
    )
    stable_core_parser.add_argument(
        "--stability-file",
        help="Specific stability window evidence Markdown file. Relative paths are resolved inside PATH.",
    )
    stable_core_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )

    return parser


def handle_init(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    title = args.title or target.name
    try:
        result = create_project(
            target,
            title=title,
            language=args.language,
            force=args.force,
            dry_run=args.dry_run,
        )
    except OSError as exc:
        print(f"fictionops: init failed: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Would initialize FictionOps project at: {target}")
        print(f"Planned actions: {result.planned_actions}")
        return 0

    print(f"Initialized FictionOps project at: {target}")
    print(f"Created directories: {result.created_dirs}")
    print(f"Created files: {result.created_files}")
    if result.skipped_files:
        print(f"Skipped existing files: {result.skipped_files}")
        print("Use --force to overwrite generated files.")
    print("Next: fill 01_story_seed/story_seed.md")
    return 0


def handle_adopt(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_adopt_report(
            target,
            max_files=args.max_files,
            include_ignored=args.include_ignored,
            out=args.out,
            copy_to=args.copy_to,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: adopt failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: adopt failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run and args.format != "json":
        print(f"Wrote FictionOps adopt report to: {report.output_file}")
    if args.copy_to and not args.dry_run and args.format != "json":
        print(f"Copied FictionOps adopt files to: {report.copy_to}")
    print(render_adopt_report(report, args.format))
    return 0


def handle_adopt_review(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_adopt_review(
            target,
            book=args.book,
            pattern=args.pattern,
            min_chapter_chars=args.min_chapter_chars,
            watch_terms=parse_watch_terms(args.watch),
            top=args.top,
            min_repeat=args.min_repeat,
            scan_text=not args.no_text_scan,
            stale_after=args.stale_after,
            max_issues=args.max_issues,
            waivers=args.waivers,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: adopt-review failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: adopt-review failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run and args.format != "json":
        print(f"Wrote FictionOps adopt-review report to: {report.output_file}")
    print(render_adopt_review(report, args.format))
    return 0


def handle_adopt_plan(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_adopt_plan(
            target,
            book=args.book,
            pattern=args.pattern,
            min_chapter_chars=args.min_chapter_chars,
            watch_terms=parse_watch_terms(args.watch),
            top=args.top,
            min_repeat=args.min_repeat,
            scan_text=not args.no_text_scan,
            stale_after=args.stale_after,
            max_issues=args.max_issues,
            waivers=args.waivers,
            out=args.out,
            group_out=args.write_groups,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: adopt-plan failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: adopt-plan failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run and args.format != "json":
        print(f"Wrote FictionOps adopt-plan report to: {report.output_file}")
    if args.write_groups and not args.dry_run and args.format != "json":
        print(f"Wrote FictionOps adopt repair groups to: {report.group_output_dir}")
    print(render_adopt_plan(report, args.format))
    return 0


def handle_import_plan(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_import_plan(
            target,
            book=args.book,
            max_files=args.max_files,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
            apply=args.apply,
            create_scaffolds=args.create_scaffolds,
            replace_placeholder_targets=args.replace_placeholder_targets,
        )
    except FileExistsError as exc:
        print(f"fictionops: import-plan failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: import-plan failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run and args.format != "json":
        print(f"Wrote FictionOps import-plan report to: {report.output_file}")
    print(render_import_plan(report, args.format))
    return 0


def handle_new_chapter(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: new-chapter failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: new-chapter failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        result = create_chapter(
            target,
            book=args.book,
            chapter=args.chapter,
            title=args.title,
            viewpoint=args.viewpoint,
            kind=args.kind,
            target_chars=args.target_chars,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: new-chapter failed: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Would create FictionOps chapter files in: {target}")
        print(f"Planned actions: {result.planned_actions}")
    else:
        print(f"Created chapter files in: {target}")
        print(f"Created directories: {result.created_dirs}")
        print(f"Created files: {result.created_files}")
        if result.skipped_files:
            print(f"Skipped existing files: {result.skipped_files}")
            print("Use --force to overwrite generated files.")
    if result.paths:
        print("Paths:")
        for path in result.paths:
            print(f"- {path}")
    return 0


def handle_new_book(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: new-book failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: new-book failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        result = create_book(
            target,
            book=args.book,
            title=args.title,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: new-book failed: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Would create FictionOps book files in: {target}")
        print(f"Planned actions: {result.planned_actions}")
    else:
        print(f"Created book files in: {target}")
        print(f"Created directories: {result.created_dirs}")
        print(f"Created files: {result.created_files}")
        if result.skipped_files:
            print(f"Skipped existing files: {result.skipped_files}")
            print("Use --force to overwrite generated files.")
    if result.paths:
        print("Paths:")
        for path in result.paths:
            print(f"- {path}")
    return 0


def handle_plan_chapter(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: plan-chapter failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: plan-chapter failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        result = plan_chapter(
            target,
            book=args.book,
            chapter=args.chapter,
            outline=args.outline,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: plan-chapter failed: {exc}", file=sys.stderr)
        return 1

    verb = "Would update" if args.dry_run else "Updated"
    print(f"{verb} chapter engine: {result.engine_file}")
    print(f"Outline: {result.outline_file}:{result.plan_row}")
    print(f"Updated fields: {', '.join(result.updated_fields) if result.updated_fields else '-'}")
    print(f"Skipped non-empty fields: {', '.join(result.skipped_fields) if result.skipped_fields else '-'}")
    if result.skipped_fields and not args.force:
        print("Use --force to overwrite skipped fields.")
    return 0


def handle_scene_plan(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: scene-plan failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: scene-plan failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_scene_plan(
            target,
            book=args.book,
            chapter=args.chapter,
            engine=args.engine,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: scene-plan failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: scene-plan failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps scene plan to: {report.output_file}")
    print(render_scene_plan(report, args.format))
    return 0


def handle_draft_brief(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: draft-brief failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: draft-brief failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_draft_brief(
            target,
            book=args.book,
            chapter=args.chapter,
            engine=args.engine,
            include_context_content=args.include_context_content,
            max_chars_per_file=args.max_chars_per_file,
            max_total_context_chars=args.max_total_chars,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: draft-brief failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: draft-brief failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps draft brief to: {report.output_file}")
    print(render_draft_brief(report, args.format))
    return 0


def handle_post_draft(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: post-draft failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: post-draft failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_post_draft_report(
            target,
            book=args.book,
            chapter=args.chapter,
            min_chapter_chars=args.min_chapter_chars,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: post-draft failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: post-draft failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps post-draft gate to: {report.output_file}")
    print(render_post_draft_report(report, args.format))
    return 0


def handle_review_gate(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: review-gate failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: review-gate failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_review_gate(
            target,
            book=args.book,
            chapter=args.chapter,
            min_chapter_chars=args.min_chapter_chars,
            pattern=args.pattern,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: review-gate failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: review-gate failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps review gate to: {report.output_file}")
    print(render_review_gate(report, args.format))
    return 0


def handle_book_gate(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: book-gate failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: book-gate failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_book_gate(
            target,
            book=args.book,
            outline=args.outline,
            min_chapter_chars=args.min_chapter_chars,
            pattern=args.pattern,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: book-gate failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: book-gate failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps book gate to: {report.output_file}")
    print(render_book_gate(report, args.format))
    return 0


def handle_audit_plan(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: audit-plan failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: audit-plan failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_plan_audit_report(
            target,
            book=args.book,
            outline=args.outline,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-plan failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(format_plan_audit_report(report))
    return 0


def handle_retrospective(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: retrospective failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: retrospective failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_retrospective_report(target, book=args.book)
        output = render_retrospective_report(report, args.format)
        if args.out:
            output_path = resolve_report_output_path(target, args.out)
            write_report_file(output_path, output, force=args.force)
            print(f"Wrote FictionOps retrospective to: {output_path}")
        else:
            print(output)
    except FileExistsError as exc:
        print(f"fictionops: retrospective failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: retrospective failed: {exc}", file=sys.stderr)
        return 1
    return 0


def handle_stats(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: stats failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_stats_report(
            target,
            all_markdown=args.all,
            pattern=args.pattern,
            metric=args.metric,
        )
    except OSError as exc:
        print(f"fictionops: stats failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(format_table(report))
    return 0


def handle_scan_words(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: scan-words failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_word_scan_report(
            target,
            all_markdown=args.all,
            pattern=args.pattern,
            watch=args.watch,
            min_count=args.min_count,
            top=args.top,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: scan-words failed: {exc}", file=sys.stderr)
        return 1

    print(render_word_scan_report(report, args.format))
    return 0


def handle_check_tables(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: check-tables failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_table_check_report(
            target,
            all_markdown=args.all,
            pattern=args.pattern,
            min_filled_cells=args.min_filled_cells,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: check-tables failed: {exc}", file=sys.stderr)
        return 1

    print(render_table_check_report(report, args.format))
    return 0


def handle_audit_wave(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: audit-wave failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_chapter_wave_report(
            target,
            all_markdown=args.all,
            pattern=args.pattern,
            metric=args.metric,
            flat_tolerance=args.flat_tolerance,
            min_spread_ratio=args.min_spread_ratio,
            max_flat_run=args.max_flat_run,
            max_same_band_run=args.max_same_band_run,
        )
    except OSError as exc:
        print(f"fictionops: audit-wave failed: {exc}", file=sys.stderr)
        return 1

    print(render_chapter_wave_report(report, args.format))
    return 0


def handle_audit_style(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: audit-style failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_style_audit_report(
            target,
            all_markdown=args.all,
            pattern=args.pattern,
            watch_terms=parse_watch_terms(args.watch),
            top=args.top,
            min_repeat=args.min_repeat,
        )
    except OSError as exc:
        print(f"fictionops: audit-style failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(format_style_audit_table(report))
    return 0


def handle_audit_continuity(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: audit-continuity failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_continuity_report(
            target,
            pattern=args.pattern,
            skip_standard=args.skip_standard,
            min_chapter_chars=args.min_chapter_chars,
        )
    except OSError as exc:
        print(f"fictionops: audit-continuity failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(format_continuity_report(report))
    return 0


def handle_audit_echoes(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: audit-echoes failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_echo_report(
            target,
            pattern=args.pattern,
            table_path=args.table,
            scan_text=not args.no_text_scan,
            stale_after=args.stale_after,
        )
    except OSError as exc:
        print(f"fictionops: audit-echoes failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(format_echo_report(report))
    return 0


def handle_audit_info(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: audit-info failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_info_report(
            target,
            pattern=args.pattern,
            table_path=args.table,
            scan_text=not args.no_text_scan,
        )
    except OSError as exc:
        print(f"fictionops: audit-info failed: {exc}", file=sys.stderr)
        return 1

    print(render_info_report(report, args.format))
    return 0


def handle_audit_characters(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: audit-characters failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_character_audit_report(target, pattern=args.pattern)
    except OSError as exc:
        print(f"fictionops: audit-characters failed: {exc}", file=sys.stderr)
        return 1

    print(render_character_audit_report(report, args.format))
    return 0


def handle_agent_prompt(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_agent_prompt(
            target,
            role=args.role,
            task=args.task,
            book=args.book,
            chapter=args.chapter,
            include_context=args.include_context,
            include_context_content=args.include_context_content,
            max_chars_per_file=args.max_chars_per_file,
            max_total_context_chars=args.max_total_chars,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: agent-prompt failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: agent-prompt failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps agent prompt to: {report.output_file}")
    print(render_agent_prompt(report, args.format))
    return 0


def handle_agent_connect(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_agent_connect(
            target,
            name=args.name,
            mode=args.mode,
            out_dir=args.out_dir,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: agent-connect failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: agent-connect failed: {exc}", file=sys.stderr)
        return 1

    if report.written and args.format != "json":
        print(f"Wrote FictionOps agent connector kit to: {report.output_dir}")
    print(render_agent_connect(report, args.format))
    return 0


def handle_agent_smoke(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_agent_smoke(
            target,
            connector=args.connector,
            level=args.level,
            role=args.role,
            book=args.book,
            chapter=args.chapter,
            out_dir=args.out_dir,
            output_name=args.output_name,
            timeout_seconds=args.timeout_seconds,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: agent-smoke failed: {exc}. Use --force to overwrite or choose a fresh --out-dir.", file=sys.stderr)
        return 1
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"fictionops: agent-smoke failed: {exc}", file=sys.stderr)
        return 1

    if report.written and args.format != "json":
        print(f"Wrote FictionOps agent smoke run to: {report.run_dir}")
    print(render_agent_smoke(report, args.format))
    return 0


def handle_agent_run(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_agent_run(
            target,
            role=args.role,
            task=args.task,
            book=args.book,
            chapter=args.chapter,
            out_dir=args.out_dir,
            include_context_content=not args.no_context_content,
            max_chars_per_file=args.max_chars_per_file,
            max_total_context_chars=args.max_total_chars,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: agent-run failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: agent-run failed: {exc}", file=sys.stderr)
        return 1

    if args.out_dir and not args.dry_run and args.format != "json":
        print(f"Wrote FictionOps agent-run bundle to: {report.output_dir}")
    print(render_agent_run(report, args.format))
    return 0


def handle_agent_exec(args: argparse.Namespace) -> int:
    target = Path(args.path)
    runner = list(args.runner)
    if runner and runner[0] == "--":
        runner = runner[1:]
    try:
        report = build_agent_exec(
            target,
            command=runner,
            output_name=args.output_name,
            timeout_seconds=args.timeout_seconds,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: agent-exec failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"fictionops: agent-exec failed: {exc}", file=sys.stderr)
        return 1

    if report.written and args.format != "json":
        print(f"Wrote FictionOps agent output to: {report.output_file}")
    print(render_agent_exec(report, args.format))
    return 0


def handle_agent_inbox(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_agent_inbox(
            target,
            runs_dir=args.runs_dir,
            output_name=args.output_name,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: agent-inbox failed: {exc}", file=sys.stderr)
        return 1

    print(render_agent_inbox(report, args.format))
    return 0


def handle_agent_next(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_agent_next(
            target,
            book=args.book,
            chapter=args.chapter,
            scan_text=not args.no_text_scan,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: agent-next failed: {exc}", file=sys.stderr)
        return 1

    print(render_agent_next(report, args.format))
    return 0


def handle_agent_workflow_audit(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_agent_workflow_audit(
            target,
            level=args.level,
            book=args.book,
            chapter=args.chapter,
            scan_text=args.scan_text,
            connector=args.connector,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-agent-workflow failed: {exc}", file=sys.stderr)
        return 1

    print(render_agent_workflow_audit(report, args.format))
    return 0


def handle_model_config(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_model_config_report(
            target,
            provider=args.provider,
            planning_model=args.planning_model,
            drafting_model=args.drafting_model,
            audit_model=args.audit_model,
            api_key_env=args.api_key_env,
            base_url=args.base_url,
            max_context_chars=args.max_context_chars,
            max_output_tokens=args.max_output_tokens,
            timeout_seconds=args.timeout_seconds,
            out=args.out,
            write=args.write,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: model-config failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: model-config failed: {exc}", file=sys.stderr)
        return 1

    if args.write and not args.dry_run:
        print(f"Wrote FictionOps model config to: {report.config_file}")
    print(render_model_config_report(report, args.format))
    return 0


def handle_context_pack(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_context_pack(
            target,
            task=args.task,
            book=args.book,
            chapter=args.chapter,
            include_content=not args.no_content,
            max_chars_per_file=args.max_chars_per_file,
            max_total_chars=args.max_total_chars,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: context-pack failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: context-pack failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps context pack to: {report.output_file}")
    print(render_context_pack(report, args.format))
    return 0


def handle_workflow_plan(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_workflow_plan(
            target,
            stage=args.stage,
            book=args.book,
            chapter=args.chapter,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: workflow-plan failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: workflow-plan failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps workflow plan to: {report.output_file}")
    print(render_workflow_plan(report, args.format))
    return 0


def handle_revision_plan(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_revision_plan(
            target,
            book=args.book,
            outline=args.outline,
            all_markdown=args.all,
            pattern=args.pattern,
            metric=args.metric,
            skip_standard=args.skip_standard,
            strict_standard=args.strict_standard,
            min_chapter_chars=args.min_chapter_chars,
            flat_tolerance=args.flat_tolerance,
            min_spread_ratio=args.min_spread_ratio,
            max_flat_run=args.max_flat_run,
            max_same_band_run=args.max_same_band_run,
            watch_terms=parse_watch_terms(args.watch),
            top=args.top,
            min_repeat=args.min_repeat,
            scan_text=not args.no_text_scan,
            stale_after=args.stale_after,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: revision-plan failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: revision-plan failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps revision plan to: {report.output_file}")
    print(render_revision_plan(report, args.format))
    return 0


def handle_doctor(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: doctor failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_doctor_report(
            target,
            all_markdown=args.all,
            pattern=args.pattern,
            metric=args.metric,
            skip_standard=args.skip_standard,
            strict_standard=args.strict_standard,
            min_chapter_chars=args.min_chapter_chars,
            flat_tolerance=args.flat_tolerance,
            min_spread_ratio=args.min_spread_ratio,
            max_flat_run=args.max_flat_run,
            max_same_band_run=args.max_same_band_run,
            watch_terms=parse_watch_terms(args.watch),
            top=args.top,
            min_repeat=args.min_repeat,
            scan_text=not args.no_text_scan,
            stale_after=args.stale_after,
            book=args.book,
            outline=args.outline,
        )
    except OSError as exc:
        print(f"fictionops: doctor failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(format_doctor_report(report))
    return 0


def handle_report(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"fictionops: report failed: path does not exist: {target}", file=sys.stderr)
        return 1
    try:
        report = build_doctor_report(
            target,
            all_markdown=args.all,
            pattern=args.pattern,
            metric=args.metric,
            skip_standard=args.skip_standard,
            strict_standard=args.strict_standard,
            min_chapter_chars=args.min_chapter_chars,
            flat_tolerance=args.flat_tolerance,
            min_spread_ratio=args.min_spread_ratio,
            max_flat_run=args.max_flat_run,
            max_same_band_run=args.max_same_band_run,
            watch_terms=parse_watch_terms(args.watch),
            top=args.top,
            min_repeat=args.min_repeat,
            scan_text=not args.no_text_scan,
            stale_after=args.stale_after,
            book=args.book,
            outline=args.outline,
        )
        output = render_report(report, args.format)
        if args.out:
            output_path = resolve_report_output_path(target, args.out)
            write_report_file(output_path, output, force=args.force)
            print(f"Wrote FictionOps report to: {output_path}")
        else:
            print(output)
    except FileExistsError as exc:
        print(f"fictionops: report failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"fictionops: report failed: {exc}", file=sys.stderr)
        return 1
    return 0


def handle_export_clean(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        result = export_clean_markdown(
            target,
            book=args.book,
            out=args.out,
            title=args.title,
            force=args.force,
            dry_run=args.dry_run,
        )
        if args.format == "json":
            print(render_export_clean_result(result, args.format))
        else:
            verb = "Would export" if args.dry_run else "Exported"
            print(f"{verb} FictionOps clean Markdown to: {result.output_file}")
            print(render_export_clean_result(result, args.format))
    except FileExistsError as exc:
        print(f"fictionops: export-clean failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: export-clean failed: {exc}", file=sys.stderr)
        return 1
    return 0


def handle_audit_publish(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_publish_audit_report(
            target,
            book=args.book,
            file_path=args.file,
            min_chapter_chars=args.min_chapter_chars,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-publish failed: {exc}", file=sys.stderr)
        return 1

    print(render_publish_audit_report(report, args.format))
    return 0


def handle_publish_copy(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_publish_copy(
            target,
            book=args.book,
            clean_file=args.clean_file,
            checklist_file=args.checklist_file,
            outline_file=args.outline_file,
            seed_file=args.seed_file,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: publish-copy failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: publish-copy failed: {exc}", file=sys.stderr)
        return 1

    print(render_publish_copy_report(report, args.format))
    return 0


def handle_export_metadata(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = export_publish_metadata(
            target,
            book=args.book,
            file_path=args.file,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: export-metadata failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: export-metadata failed: {exc}", file=sys.stderr)
        return 1

    print(render_publish_metadata_report(report, args.format))
    return 0


def handle_export_manifest(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = export_publish_manifest(
            target,
            book=args.book,
            clean_file=args.clean_file,
            metadata_file=args.metadata_file,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: export-manifest failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: export-manifest failed: {exc}", file=sys.stderr)
        return 1

    print(render_publish_manifest_report(report, args.format))
    return 0


def handle_export_epub(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = export_epub(
            target,
            book=args.book,
            manifest_file=args.manifest_file,
            clean_file=args.clean_file,
            metadata_file=args.metadata_file,
            cover_file=args.cover_file,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: export-epub failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: export-epub failed: {exc}", file=sys.stderr)
        return 1

    print(render_epub_report(report, args.format))
    return 0


def handle_audit_epub(args: argparse.Namespace) -> int:
    target = Path(args.path)
    try:
        report = build_epub_audit_report(
            target,
            book=args.book,
            file_path=args.file,
            manifest_file=args.manifest_file,
            clean_file=args.clean_file,
            metadata_file=args.metadata_file,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-epub failed: {exc}", file=sys.stderr)
        return 1

    print(render_epub_audit_report(report, args.format))
    return 0


def handle_release_gate(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print(f"fictionops: release-gate failed: path does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"fictionops: release-gate failed: path is not a directory: {target}", file=sys.stderr)
        return 1
    try:
        report = build_release_gate(
            target,
            book=args.book,
            min_chapter_chars=args.min_chapter_chars,
            out=args.out,
            force=args.force,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"fictionops: release-gate failed: {exc}. Use --force to overwrite.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"fictionops: release-gate failed: {exc}", file=sys.stderr)
        return 1

    if args.out and not args.dry_run:
        print(f"Wrote FictionOps release gate to: {report.output_file}")
    print(render_release_gate(report, args.format))
    return 0


def handle_audit_release_evidence(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_release_evidence_audit(
            target,
            file_path=args.file,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-release-evidence failed: {exc}", file=sys.stderr)
        return 1

    print(render_release_evidence_audit(report, args.format))
    return 0


def handle_audit_dogfood_cycle(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_dogfood_cycle_audit(
            target,
            file_path=args.file,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-dogfood-cycle failed: {exc}", file=sys.stderr)
        return 1

    print(render_dogfood_cycle_audit(report, args.format))
    return 0


def handle_audit_stability_window(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_stability_window_audit(
            target,
            file_path=args.file,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-stability-window failed: {exc}", file=sys.stderr)
        return 1

    print(render_stability_window_audit(report, args.format))
    return 0


def handle_audit_stable_core(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        report = build_stable_core_audit(
            target,
            release_file=args.release_file,
            dogfood_file=args.dogfood_file,
            stability_file=args.stability_file,
        )
    except (OSError, ValueError) as exc:
        print(f"fictionops: audit-stable-core failed: {exc}", file=sys.stderr)
        return 1

    print(render_stable_core_audit(report, args.format))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "adopt":
        return handle_adopt(args)
    if args.command == "adopt-review":
        return handle_adopt_review(args)
    if args.command == "adopt-plan":
        return handle_adopt_plan(args)
    if args.command == "import-plan":
        return handle_import_plan(args)
    if args.command == "init":
        return handle_init(args)
    if args.command == "new-book":
        return handle_new_book(args)
    if args.command == "new-chapter":
        return handle_new_chapter(args)
    if args.command == "plan-chapter":
        return handle_plan_chapter(args)
    if args.command == "scene-plan":
        return handle_scene_plan(args)
    if args.command == "draft-brief":
        return handle_draft_brief(args)
    if args.command == "post-draft":
        return handle_post_draft(args)
    if args.command == "review-gate":
        return handle_review_gate(args)
    if args.command == "book-gate":
        return handle_book_gate(args)
    if args.command == "audit-plan":
        return handle_audit_plan(args)
    if args.command == "retrospective":
        return handle_retrospective(args)
    if args.command == "stats":
        return handle_stats(args)
    if args.command == "scan-words":
        return handle_scan_words(args)
    if args.command == "check-tables":
        return handle_check_tables(args)
    if args.command == "audit-wave":
        return handle_audit_wave(args)
    if args.command == "audit-style":
        return handle_audit_style(args)
    if args.command == "audit-continuity":
        return handle_audit_continuity(args)
    if args.command == "audit-echoes":
        return handle_audit_echoes(args)
    if args.command == "audit-info":
        return handle_audit_info(args)
    if args.command == "audit-characters":
        return handle_audit_characters(args)
    if args.command == "agent-prompt":
        return handle_agent_prompt(args)
    if args.command == "agent-connect":
        return handle_agent_connect(args)
    if args.command == "agent-smoke":
        return handle_agent_smoke(args)
    if args.command == "agent-run":
        return handle_agent_run(args)
    if args.command == "agent-exec":
        return handle_agent_exec(args)
    if args.command == "agent-inbox":
        return handle_agent_inbox(args)
    if args.command == "agent-next":
        return handle_agent_next(args)
    if args.command == "audit-agent-workflow":
        return handle_agent_workflow_audit(args)
    if args.command == "model-config":
        return handle_model_config(args)
    if args.command == "context-pack":
        return handle_context_pack(args)
    if args.command == "workflow-plan":
        return handle_workflow_plan(args)
    if args.command == "revision-plan":
        return handle_revision_plan(args)
    if args.command == "doctor":
        return handle_doctor(args)
    if args.command == "report":
        return handle_report(args)
    if args.command == "export-clean":
        return handle_export_clean(args)
    if args.command == "audit-publish":
        return handle_audit_publish(args)
    if args.command == "publish-copy":
        return handle_publish_copy(args)
    if args.command == "export-metadata":
        return handle_export_metadata(args)
    if args.command == "export-manifest":
        return handle_export_manifest(args)
    if args.command == "export-epub":
        return handle_export_epub(args)
    if args.command == "audit-epub":
        return handle_audit_epub(args)
    if args.command == "release-gate":
        return handle_release_gate(args)
    if args.command == "audit-release-evidence":
        return handle_audit_release_evidence(args)
    if args.command == "audit-dogfood-cycle":
        return handle_audit_dogfood_cycle(args)
    if args.command == "audit-stability-window":
        return handle_audit_stability_window(args)
    if args.command == "audit-stable-core":
        return handle_audit_stable_core(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
