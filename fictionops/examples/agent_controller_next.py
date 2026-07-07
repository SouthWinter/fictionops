from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Demo Level 2 FictionOps controller: call agent-next and report the selected safe command.",
    )
    parser.add_argument("project", help="FictionOps project, legacy directory, or future project path.")
    parser.add_argument("--book", default="book_01", help="Book id. Default: book_01.")
    parser.add_argument("--chapter", help="Optional chapter number for chapter-aware selection.")
    parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Pass through to agent-next for a lighter controller polling pass.",
    )
    parser.add_argument(
        "--cli",
        nargs="+",
        default=["fictionops"],
        help="FictionOps CLI command prefix. Example: --cli python fictionops/src/fictionops/cli.py",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. Default: markdown.",
    )
    return parser


def run_agent_next(args: argparse.Namespace) -> dict[str, object]:
    command = [*args.cli, "agent-next", args.project, "--book", args.book, "--format", "json"]
    if args.chapter:
        command.extend(["--chapter", args.chapter])
    if args.no_text_scan:
        command.append("--no-text-scan")

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=env)
    if completed.returncode != 0:
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")
        raise SystemExit(completed.returncode)
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        print("agent-next did not return valid JSON", file=sys.stderr)
        print(completed.stdout[:1000], file=sys.stderr)
        raise SystemExit(1) from exc
    if not isinstance(data, dict):
        print("agent-next returned a non-object JSON value", file=sys.stderr)
        raise SystemExit(1)
    return data


def as_bool(value: object) -> bool:
    return bool(value)


def format_markdown(report: dict[str, object], *, project: str) -> str:
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        candidates = []
    selected = candidates[0] if candidates and isinstance(candidates[0], dict) else {}

    lines = [
        "# FictionOps Controller Demo",
        "",
        "> This script demonstrates a Level 2 controller boundary. It selects a command but does not execute it.",
        "",
        f"- Project: `{project}`",
        f"- Status: `{report.get('status', '-')}`",
        f"- Selected command: `{report.get('selected_command', '-')}`",
        f"- Selected reason: {report.get('selected_reason', '-')}",
        f"- Safe to auto-run: `{'yes' if as_bool(selected.get('safe_to_auto_run')) else 'no'}`",
        f"- Requires human review: `{'yes' if as_bool(selected.get('requires_human_review')) else 'no'}`",
        "",
        "## Candidate Commands",
        "",
        "| Priority | Stage | Command | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for item in candidates[:8]:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| "
            f"{item.get('priority', '-')} | "
            f"{item.get('stage', '-')} | "
            f"`{item.get('command', '-')}` | "
            f"{item.get('reason', '-')} |"
        )
    lines.extend(
        [
            "",
            "## Next Boundary",
            "",
            "- A real controller may decide whether to run `selected_command`.",
            "- Staged output still belongs in `agent-inbox` and must pass human review before manuscript or canon changes.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_agent_next(args)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report, project=str(Path(args.project))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
