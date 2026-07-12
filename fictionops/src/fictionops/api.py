from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent_revision_accept import build_agent_revision_accept
from .agent_revise_workflow import build_agent_revise_workflow
from .agent_session_control import cancel_agent_session, resume_agent_session
from .agent_write_workflow import build_agent_write_workflow


API_VERSION = "1.0"


def _payload(report: object) -> dict[str, Any]:
    payload = asdict(report)
    payload["api_version"] = API_VERSION
    return payload


def write_chapter(
    chapter_file: str | Path,
    *,
    engine_file: str | Path,
    outline_file: str | Path | None = None,
    runner: list[str] | None = None,
    out_dir: str | None = None,
    **options: Any,
) -> dict[str, Any]:
    """Plan, draft, verify, and stage a chapter through the canonical runtime."""
    report = build_agent_write_workflow(
        Path(chapter_file),
        engine=Path(engine_file),
        outline=Path(outline_file) if outline_file else None,
        runner=runner,
        out_dir=out_dir,
        **options,
    )
    return _payload(report)


def revise_chapter(
    chapter_file: str | Path,
    *,
    review_file: str | Path | None = None,
    runner: list[str] | None = None,
    out_dir: str | None = None,
    **options: Any,
) -> dict[str, Any]:
    """Review, revise, verify, and stage an existing chapter."""
    report = build_agent_revise_workflow(
        Path(chapter_file),
        review=Path(review_file) if review_file else None,
        runner=runner,
        out_dir=out_dir,
        **options,
    )
    return _payload(report)


def resume_session(run_dir: str | Path, *, runner: list[str], **options: Any) -> dict[str, Any]:
    """Resume a hash-valid supported checkpoint without replaying completed phases."""
    return _payload(resume_agent_session(Path(run_dir), runner=runner, **options))


def cancel_session(run_dir: str | Path, *, reason: str) -> dict[str, Any]:
    """Cancel a resumable session with an auditable reason."""
    return _payload(cancel_agent_session(Path(run_dir), reason=reason))


def accept_session(run_dir: str | Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Apply a verified hash-matched candidate after explicit caller authority."""
    return _payload(build_agent_revision_accept(Path(run_dir), dry_run=dry_run))
