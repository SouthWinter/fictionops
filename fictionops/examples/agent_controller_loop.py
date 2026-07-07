from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Demo Level 2 FictionOps loop controller: poll agent-next, run only safe "
            "commands, and stop at human-review or overwrite-risk boundaries."
        ),
    )
    parser.add_argument("project", help="FictionOps project, legacy directory, or future project path.")
    parser.add_argument("--book", default="book_01", help="Book id. Default: book_01.")
    parser.add_argument("--chapter", help="Optional chapter number for chapter-aware selection.")
    parser.add_argument("--max-steps", type=int, default=3, help="Maximum commands to execute. Default: 3.")
    parser.add_argument("--dry-run", action="store_true", help="Select steps and write logs without executing commands.")
    parser.add_argument(
        "--no-text-scan",
        action="store_true",
        help="Pass through to agent-next for a lighter controller polling pass.",
    )
    parser.add_argument(
        "--log",
        help="Optional JSONL log path. Parent directories are created when needed.",
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


def run_json(command: list[str]) -> dict[str, Any]:
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
        print("command did not return valid JSON", file=sys.stderr)
        print(completed.stdout[:1000], file=sys.stderr)
        raise SystemExit(1) from exc
    if not isinstance(data, dict):
        print("command returned a non-object JSON value", file=sys.stderr)
        raise SystemExit(1)
    return data


def run_agent_next(args: argparse.Namespace) -> dict[str, Any]:
    command = [*args.cli, "agent-next", args.project, "--book", args.book, "--format", "json"]
    if args.chapter:
        command.extend(["--chapter", args.chapter])
    if args.no_text_scan:
        command.append("--no-text-scan")
    return run_json(command)


def selected_candidate(report: dict[str, Any]) -> dict[str, Any]:
    command = report.get("selected_command")
    candidates = report.get("candidates")
    if isinstance(candidates, list):
        for item in candidates:
            if isinstance(item, dict) and item.get("command") == command:
                return item
        if candidates and isinstance(candidates[0], dict):
            return candidates[0]
    return {}


def has_placeholder(command: str) -> bool:
    return "<" in command or ">" in command


def command_to_argv(command: str, cli_prefix: list[str]) -> list[str] | None:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None
    if not tokens or tokens[0] != "fictionops":
        return None
    return [*cli_prefix, *tokens[1:]]


def summarize_text(value: str, limit: int = 500) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "..."


def write_log(path: Path | None, entry: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def run_selected_command(argv: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    completed = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", env=env)
    return {
        "returncode": completed.returncode,
        "stdout": summarize_text(completed.stdout),
        "stderr": summarize_text(completed.stderr),
    }


def controller_loop(args: argparse.Namespace) -> dict[str, Any]:
    if args.max_steps < 1:
        raise SystemExit("--max-steps must be at least 1")

    log_path = Path(args.log) if args.log else None
    executed_commands: set[str] = set()
    steps: list[dict[str, Any]] = []
    stop_reason = "max_steps"

    for index in range(1, args.max_steps + 1):
        report = run_agent_next(args)
        candidate = selected_candidate(report)
        command = str(report.get("selected_command") or "")
        safe = bool(candidate.get("safe_to_auto_run"))
        human_review = bool(candidate.get("requires_human_review"))
        entry: dict[str, Any] = {
            "step": index,
            "agent_next_status": report.get("status"),
            "selected_command": command,
            "selected_reason": report.get("selected_reason"),
            "candidate_stage": candidate.get("stage"),
            "safe_to_auto_run": safe,
            "requires_human_review": human_review,
            "action": "stop",
        }

        if not command:
            stop_reason = "no_command"
            entry["stop_reason"] = stop_reason
        elif human_review:
            stop_reason = "human_review_boundary"
            entry["stop_reason"] = stop_reason
        elif not safe:
            stop_reason = "unsafe_command"
            entry["stop_reason"] = stop_reason
        elif has_placeholder(command):
            stop_reason = "placeholder_command"
            entry["stop_reason"] = stop_reason
        elif command in executed_commands:
            stop_reason = "repeated_command"
            entry["stop_reason"] = stop_reason
        else:
            argv = command_to_argv(command, args.cli)
            if argv is None:
                stop_reason = "unsupported_command"
                entry["stop_reason"] = stop_reason
            elif args.dry_run:
                stop_reason = "dry_run"
                entry["action"] = "dry_run"
                entry["argv"] = argv
                entry["stop_reason"] = stop_reason
            else:
                entry["action"] = "execute"
                entry["argv"] = argv
                result = run_selected_command(argv)
                entry["execution"] = result
                executed_commands.add(command)
                if result["returncode"] != 0:
                    stop_reason = "command_failed"
                    entry["stop_reason"] = stop_reason
                else:
                    entry["stop_reason"] = None

        steps.append(entry)
        write_log(log_path, entry)
        if entry.get("stop_reason"):
            break

    else:
        stop_reason = "max_steps"

    return {
        "project": str(Path(args.project)),
        "book": args.book,
        "chapter": args.chapter,
        "dry_run": args.dry_run,
        "max_steps": args.max_steps,
        "steps_executed": sum(1 for step in steps if step.get("action") == "execute"),
        "steps_seen": len(steps),
        "stop_reason": stop_reason,
        "log_file": str(log_path) if log_path else None,
        "steps": steps,
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# FictionOps Controller Loop Demo",
        "",
        "> This script demonstrates a no-model Level 2 controller loop. It runs only safe commands and stops at review boundaries.",
        "",
        f"- Project: `{report.get('project')}`",
        f"- Book: `{report.get('book')}`",
        f"- Chapter: `{report.get('chapter') or '-'}`",
        f"- Stop reason: `{report.get('stop_reason')}`",
        f"- Steps seen: `{report.get('steps_seen')}`",
        f"- Steps executed: `{report.get('steps_executed')}`",
        f"- Log file: `{report.get('log_file') or '-'}`",
        "",
        "## Steps",
        "",
        "| Step | Action | Stage | Stop | Command |",
        "| --- | --- | --- | --- | --- |",
    ]
    for step in report.get("steps", []):
        if not isinstance(step, dict):
            continue
        lines.append(
            "| "
            f"{step.get('step')} | "
            f"{step.get('action')} | "
            f"{step.get('candidate_stage') or '-'} | "
            f"{step.get('stop_reason') or '-'} | "
            f"`{step.get('selected_command') or '-'}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = controller_loop(args)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

