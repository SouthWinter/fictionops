from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .doctor import format_doctor_report
from .models import DoctorReport


def render_report(report: DoctorReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ == "markdown":
        return format_doctor_report(report)
    raise ValueError(f"Unsupported report format: {format_}")


def resolve_report_output_path(target: Path, out_path: str) -> Path:
    output = Path(out_path).expanduser()
    if output.is_absolute():
        return output.resolve()

    base = target.expanduser().resolve()
    if base.is_file():
        base = base.parent
    return (base / output).resolve()


def write_report_file(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output file exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8")
