from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fictionops.agent_exec import build_agent_exec  # noqa: E402
from fictionops.agent_inbox import build_agent_inbox  # noqa: E402
from fictionops.agent_run import build_agent_run  # noqa: E402
from fictionops.api import revise_chapter, write_chapter  # noqa: E402


DEFAULT_MAX_CONTEXT_CHARS = 60000
DEFAULT_MAX_CHARS_PER_FILE = 6000


SESSIONS: dict[str, dict[str, Any]] = {}


def goal_text(goal: dict[str, Any], key: str, default: str | None = None) -> str | None:
    value = goal.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def goal_bool(goal: dict[str, Any], key: str, default: bool = False) -> bool:
    value = goal.get(key)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def goal_int(goal: dict[str, Any], key: str, default: int) -> int:
    value = goal.get(key)
    if value is None or value == "":
        return default
    return int(value)


def default_out_dir(goal: dict[str, Any], task: str) -> str:
    book = goal_text(goal, "book", "book_01") or "book_01"
    chapter = goal_text(goal, "chapter")
    suffix = f"{book}_{task}"
    if chapter:
        suffix += f"_ch_{chapter}"
    return f"00_management/agent_runs/api_{suffix}"


def role_for_task(goal: dict[str, Any], task: str) -> str:
    explicit = goal_text(goal, "role")
    if explicit:
        return explicit
    if task == "draft":
        return "draft-writer"
    if task == "review":
        return "revision-editor"
    return "continuity-auditor"


def runner_command(goal: dict[str, Any]) -> list[str] | None:
    command = goal.get("runner_command")
    if command is None:
        return None
    if not isinstance(command, list) or not all(isinstance(item, str) and item.strip() for item in command):
        raise ValueError("runner_command must be a non-empty string array when provided.")
    return [item.strip() for item in command]


def staged_outputs_from_inbox(inbox: Any) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for run in inbox.runs:
        if not run.output_file:
            continue
        source = {
            "provider": "-",
            "model": "-",
            "runner": "runner_command",
        }
        if run.request_file:
            try:
                request = json.loads(Path(run.request_file).read_text(encoding="utf-8"))
                if isinstance(request, dict):
                    source["provider"] = str(request.get("provider") or "-")
                    source["model"] = str(request.get("model") or "-")
            except Exception:
                pass
        outputs.append(
            {
                "run_dir": run.run_dir,
                "output_file": run.output_file,
                "role": run.role,
                "task": run.task,
                "book": run.book,
                "chapter": run.chapter,
                "state": "draft" if run.task == "draft" else ("revision" if run.task == "review" else "audit"),
                "review_required": True,
                "source": source,
            }
        )
    return outputs


def session_status(*, prepared: bool, executed: bool, inbox: Any | None, failed: bool = False) -> str:
    if failed:
        return "failed"
    if inbox is not None and inbox.ready_count > 0:
        return "waiting_for_review"
    if executed:
        return "waiting_for_review"
    if prepared:
        return "planned"
    return "running"


def build_closed_loop_session(goal: dict[str, Any], *, task: str, session_id: str) -> dict[str, Any]:
    chapter_file = goal_text(goal, "chapter_file")
    if not chapter_file:
        raise ValueError("chapter_file is required for closed_loop mode")
    command = runner_command(goal)
    common: dict[str, Any] = {
        "runner": command,
        "out_dir": goal_text(goal, "out_dir"),
        "provider": goal_text(goal, "provider"),
        "model": goal_text(goal, "model"),
        "timeout_seconds": goal_int(goal, "timeout_seconds", 600 if task == "draft" else 300),
        "max_model_calls": goal_int(goal, "max_model_calls", 32 if task == "draft" else 12),
        "max_runtime_seconds": goal_int(goal, "max_runtime_seconds", 3600 if task == "draft" else 1800),
        "max_total_tokens": goal.get("max_total_tokens"),
        "max_cost": goal.get("max_cost"),
        "cost_currency": goal_text(goal, "cost_currency", "USD") or "USD",
        "dry_run": goal_bool(goal, "dry_run", False),
    }
    if task == "draft":
        engine_file = goal_text(goal, "engine_file")
        if not engine_file:
            raise ValueError("engine_file is required for closed-loop chapter writing")
        report = write_chapter(
            chapter_file,
            engine_file=engine_file,
            outline_file=goal_text(goal, "outline_file"),
            **common,
        )
    else:
        report = revise_chapter(
            chapter_file,
            review_file=goal_text(goal, "review_file"),
            semantic_verify=goal_bool(goal, "semantic_verify", True),
            review_scope=goal_text(goal, "review_scope", "comprehensive") or "comprehensive",
            **common,
        )
    staged_outputs = list(report.get("staged_outputs") or [])
    status = "waiting_for_review" if report.get("ready_for_approval") or staged_outputs else "planned"
    session = {
        "api_version": "1.0",
        "session_id": session_id,
        "status": status,
        "goal": goal,
        "steps": [{"name": f"agent_{task}", "status": "completed", "summary": str(report.get("stop_reason") or "prepared")}],
        "staged_outputs": staged_outputs,
        "stop_reason": str(report.get("stop_reason") or "closed_loop_prepared"),
        "metrics": {
            "runtime_mode": "closed_loop",
            "model_calls_used": report.get("model_calls_used"),
            "max_model_calls": report.get("max_model_calls"),
            "verification_status": report.get("verification_status"),
            "ready_for_approval": report.get("ready_for_approval"),
        },
        "runtime_report": report,
    }
    SESSIONS[session_id] = session
    return session


def build_session(goal: dict[str, Any], *, task: str | None = None) -> dict[str, Any]:
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    normalized_task = task or goal_text(goal, "task", "planning") or "planning"
    steps: list[dict[str, str]] = []
    staged_outputs: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {
        "acceptance_mode": goal_text(goal, "acceptance_mode", "human_governed"),
        "review_required": True,
    }
    stop_reason = "session_created"
    status = "planned"

    if normalized_task == "planning":
        session = {
            "api_version": "1.0",
            "session_id": session_id,
            "status": status,
            "goal": goal,
            "steps": steps,
            "staged_outputs": staged_outputs,
            "stop_reason": stop_reason,
            "metrics": metrics,
        }
        SESSIONS[session_id] = session
        return session

    project_path = goal_text(goal, "project_path")
    if not project_path:
        raise ValueError("project_path is required for write, revise, and audit tasks.")

    project = Path(project_path).expanduser()
    runtime_mode = goal_text(goal, "runtime_mode", "closed_loop") or "closed_loop"
    if normalized_task in {"draft", "review"} and runtime_mode == "closed_loop" and goal_text(goal, "chapter_file"):
        return build_closed_loop_session(goal, task=normalized_task, session_id=session_id)
    out_dir = goal_text(goal, "out_dir") or default_out_dir(goal, normalized_task)
    prepared = False
    executed = False
    inbox = None

    run = build_agent_run(
        project,
        role=role_for_task(goal, normalized_task),
        task=normalized_task,
        book=goal_text(goal, "book", "book_01") or "book_01",
        chapter=goal_text(goal, "chapter"),
        out_dir=out_dir,
        include_context_content=goal_bool(goal, "include_context_content", True),
        max_chars_per_file=goal_int(goal, "max_chars_per_file", DEFAULT_MAX_CHARS_PER_FILE),
        max_total_context_chars=goal_int(goal, "max_total_context_chars", DEFAULT_MAX_CONTEXT_CHARS),
        force=goal_bool(goal, "force", False),
        dry_run=False,
    )
    prepared = True
    steps.append(
        {
            "name": "agent_run",
            "status": "completed",
            "summary": f"Prepared bundle at {run.output_dir}.",
        }
    )
    metrics["context_files"] = getattr(run.context_pack, "file_count", None)
    metrics["model_provider"] = run.provider
    metrics["model"] = run.model

    command = runner_command(goal)
    if command:
        exec_report = build_agent_exec(
            Path(run.output_dir or out_dir),
            command=command,
            output_name=goal_text(goal, "output_name", "output.md") or "output.md",
            timeout_seconds=goal_int(goal, "timeout_seconds", 300),
            force=goal_bool(goal, "force_output", goal_bool(goal, "force", False)),
            dry_run=goal_bool(goal, "dry_run", False),
        )
        executed = True
        steps.append(
            {
                "name": "agent_exec",
                "status": "completed" if exec_report.written or exec_report.dry_run else "planned",
                "summary": f"Runner output target: {exec_report.output_file}.",
            }
        )
        metrics["runner_executed"] = exec_report.executed
        metrics["runner_dry_run"] = exec_report.dry_run
        metrics["stdout_chars"] = exec_report.stdout_chars
        inbox = build_agent_inbox(Path(run.output_dir or out_dir), output_name=goal_text(goal, "output_name"))
        steps.append(
            {
                "name": "agent_inbox",
                "status": "completed",
                "summary": f"Inbox status: {inbox.status}; ready: {inbox.ready_count}.",
            }
        )
        staged_outputs = staged_outputs_from_inbox(inbox)
        stop_reason = "staged_output_ready_for_review" if staged_outputs else "runner_completed_without_ready_output"
    else:
        stop_reason = "agent_run_ready_for_runner"
        metrics["runner_executed"] = False

    status = session_status(prepared=prepared, executed=executed, inbox=inbox)
    session = {
        "api_version": "1.0",
        "session_id": session_id,
        "status": status,
        "goal": goal,
        "steps": steps,
        "staged_outputs": staged_outputs,
        "stop_reason": stop_reason,
        "metrics": metrics,
    }
    SESSIONS[session_id] = session
    return session


def update_session_decision(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    session = SESSIONS.get(session_id)
    if session is None:
        raise KeyError(session_id)
    decision = goal_text(payload, "decision")
    if decision not in {"accept", "reject", "revise"}:
        raise ValueError("decision must be one of: accept, reject, revise.")
    session["human_decision"] = {
        "decision": decision,
        "notes": goal_text(payload, "notes", "") or "",
    }
    session["status"] = "completed" if decision in {"accept", "reject"} else "planned"
    session["stop_reason"] = f"human_decision_{decision}"
    return session


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or "0")
    raw = handler.rfile.read(length) if length else b"{}"
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("request body must be a JSON object.")
    return data


def send_json(handler: BaseHTTPRequestHandler, status_code: int, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class FictionOpsAgentHandler(BaseHTTPRequestHandler):
    server_version = "FictionOpsApiAgent/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 3 and parts[:2] == ["v1", "sessions"]:
            session = SESSIONS.get(parts[2])
            if session is None:
                send_json(self, 404, {"error": "session_not_found", "session_id": parts[2]})
                return
            send_json(self, 200, session)
            return
        send_json(self, 404, {"error": "not_found", "path": parsed.path})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        try:
            payload = read_json_body(self)
            if parts == ["v1", "sessions"]:
                send_json(self, 200, build_session(payload))
                return
            if parts == ["v1", "write-chapter"]:
                send_json(self, 200, build_session(payload, task="draft"))
                return
            if parts == ["v1", "revise-chapter"]:
                send_json(self, 200, build_session(payload, task="review"))
                return
            if parts == ["v1", "audit-chapter"]:
                send_json(self, 200, build_session(payload, task="review"))
                return
            if len(parts) == 4 and parts[:2] == ["v1", "sessions"] and parts[3] == "decision":
                send_json(self, 200, update_session_decision(parts[2], payload))
                return
            send_json(self, 404, {"error": "not_found", "path": parsed.path})
        except KeyError as exc:
            send_json(self, 404, {"error": "session_not_found", "session_id": str(exc)})
        except Exception as exc:  # pragma: no cover - HTTP boundary
            send_json(self, 400, {"error": exc.__class__.__name__, "message": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("fictionops-api-agent: " + (format % args) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the draft FictionOps API Agent thin server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    server = ThreadingHTTPServer((args.host, args.port), FictionOpsAgentHandler)
    print(f"FictionOps API Agent listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping FictionOps API Agent.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
