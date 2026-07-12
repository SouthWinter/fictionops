from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

from .models import AgentExecReport


DEFAULT_AGENT_EXEC_OUTPUT = "output.md"
AGENT_EXEC_RECEIPT = "execution.json"
RUNNER_RECEIPT_PREFIX = "FICTIONOPS_RUNNER_RECEIPT:"
RUNNER_RECEIPT_SCHEMA = "fictionops.runner_receipt.v1"


def require_simple_output_name(output_name: str) -> str:
    path = Path(output_name)
    if path.is_absolute() or len(path.parts) != 1 or not path.name:
        raise ValueError("agent-exec --output-name must be a file name inside the run directory.")
    return path.name


def load_agent_exec_request(run_dir: Path) -> dict[str, object]:
    request_file = run_dir / "request.json"
    if not request_file.exists():
        raise FileNotFoundError(f"agent run directory has no request.json: {request_file}")
    data = json.loads(request_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("request.json must contain a JSON object.")
    if data.get("schema") != "fictionops.agent_run_request.v1":
        raise ValueError("request.json does not declare schema fictionops.agent_run_request.v1.")
    if data.get("execution_mode") != "prepare_only":
        raise ValueError("agent-exec only accepts prepare_only agent-run bundles.")
    return data


def read_required_bundle_text(run_dir: Path, name: str) -> str:
    path = run_dir / name
    if not path.exists():
        raise FileNotFoundError(f"agent run bundle is missing {name}: {path}")
    return path.read_text(encoding="utf-8")


def build_runner_input(run_dir: Path, request: dict[str, object]) -> str:
    prompt = read_required_bundle_text(run_dir, "prompt.md")
    context_pack = read_required_bundle_text(run_dir, "context_pack.md")
    draft_brief_path = run_dir / "draft_brief.md"
    draft_brief = draft_brief_path.read_text(encoding="utf-8") if draft_brief_path.exists() else ""

    lines = [
        "# FictionOps Agent Runner Input",
        "",
        "## Request",
        "",
        "```json",
        json.dumps(request, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Prompt",
        "",
        prompt.rstrip(),
        "",
        "## Context Pack",
        "",
        context_pack.rstrip(),
    ]
    if draft_brief:
        lines.extend(["", "## Draft Brief", "", draft_brief.rstrip()])
    verification_file = run_dir / "counterevidence_verification.json"
    if request.get("task") == "bounded-revision" and verification_file.is_file():
        try:
            verification = json.loads(verification_file.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            verification = None
        if isinstance(verification, dict) and not verification.get("ready_for_approval"):
            previous_candidate_file = run_dir / DEFAULT_AGENT_EXEC_OUTPUT
            previous_candidate = previous_candidate_file.read_text(encoding="utf-8-sig") if previous_candidate_file.is_file() else ""
            feedback = {
                "status": verification.get("status"),
                "decisions": verification.get("decisions") or [],
                "unrelated_changes": verification.get("unrelated_changes") or [],
                "bounded_change_scope": verification.get("bounded_change_scope") or {},
                "local_prose_regressions": verification.get("local_prose_regressions") or [],
                "summary": verification.get("summary"),
            }
            forbidden_sequences = [
                str(item.get("forbidden_sequence") or (f"{item.get('phrase')}。{item.get('phrase')}" if item.get("phrase") else ""))
                for item in feedback["local_prose_regressions"]
                if isinstance(item, dict) and (item.get("forbidden_sequence") or item.get("phrase"))
            ]
            lines.extend(
                [
                    "",
                    "## Verification Feedback From Previous Candidate",
                    "",
                    "The previous staged candidate failed verification. Repair only the listed regression while preserving already-correct contracted changes.",
                    "Use the previous candidate below as the revision base. Do not regenerate from the original source or repeat the rejected wording.",
                    "The next candidate must differ from the previous candidate. Rewrite the smallest containing sentence so each repeated phrase occurs only once.",
                    ("Forbidden exact sequences: " + json.dumps(forbidden_sequences, ensure_ascii=False)) if forbidden_sequences else "",
                    "",
                    "```json",
                    json.dumps(feedback, ensure_ascii=False, indent=2),
                    "```",
                ]
            )
            if previous_candidate:
                lines.extend(["", "### Previous Candidate To Repair", "", previous_candidate.rstrip()])
    lines.extend(
        [
            "",
            "## Output Contract",
            "",
            "Write only the staged result to stdout. FictionOps will save stdout as a staging file and will not apply it automatically.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def request_text(request: dict[str, object], key: str, default: str = "-") -> str:
    value = request.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def request_optional_text(request: dict[str, object], key: str) -> str | None:
    value = request.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def stderr_preview(text: str, limit: int = 600) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def parse_runner_receipt(stderr: str) -> dict[str, object] | None:
    matches = [line[len(RUNNER_RECEIPT_PREFIX) :].strip() for line in stderr.splitlines() if line.startswith(RUNNER_RECEIPT_PREFIX)]
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError("agent runner emitted more than one FictionOps runner receipt")
    try:
        payload = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise ValueError("agent runner emitted an invalid FictionOps runner receipt") from exc
    if not isinstance(payload, dict) or payload.get("schema") != RUNNER_RECEIPT_SCHEMA:
        raise ValueError(f"agent runner receipt must declare schema {RUNNER_RECEIPT_SCHEMA}")
    usage = payload.get("usage")
    if usage is not None:
        if not isinstance(usage, dict):
            raise ValueError("agent runner receipt usage must be an object")
        for key, value in usage.items():
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise ValueError(f"agent runner receipt usage.{key} must be a non-negative integer")
    cost = payload.get("cost")
    if cost is not None:
        if not isinstance(cost, dict):
            raise ValueError("agent runner receipt cost must be an object")
        currency = str(cost.get("currency") or "").strip()
        if not currency:
            raise ValueError("agent runner receipt cost.currency is required")
        for key, value in cost.items():
            if key == "currency" or value is None:
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ValueError(f"agent runner receipt cost.{key} must be a non-negative number")
    return payload


def agent_exec_safety() -> dict[str, object]:
    return {
        "calls_external_command": True,
        "stores_api_keys": False,
        "fictionops_reads_api_keys": False,
        "overwrites_manuscript": False,
        "writes_staging_output": True,
        "requires_human_apply": True,
    }


def runner_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def next_actions_for_agent_exec(report: AgentExecReport) -> list[str]:
    if report.dry_run:
        return ["Rerun without `--dry-run` when the external runner command is ready."]
    actions = [
        f"Run `fictionops agent-inbox {report.run_dir}` to validate the staged output.",
    ]
    if report.task == "draft" and report.chapter:
        actions.append(f"Review the staged draft before manually applying accepted text to chapter {report.chapter}.")
        actions.append(f"After applying accepted text, run `fictionops post-draft . --book {report.book} --chapter {report.chapter}`.")
    elif report.task == "review" and report.chapter:
        actions.append(f"Convert accepted findings into revision notes or run `fictionops revision-plan . --book {report.book}`.")
    elif report.task == "canon-sync":
        actions.append("Apply accepted canon changes manually, then rerun `fictionops doctor .`.")
    elif report.task == "bounded-revision":
        actions.append(f"Run `fictionops agent counterevidence verify-revision {report.run_dir} --runner ...` before any acceptance.")
    else:
        actions.append(f"Use the staged output to update project memory, then run `fictionops workflow-plan . --stage {report.task} --book {report.book}` if unsure.")
    return actions


def build_agent_exec(
    run_dir: Path,
    *,
    command: list[str],
    output_name: str = DEFAULT_AGENT_EXEC_OUTPUT,
    timeout_seconds: int = 300,
    force: bool = False,
    dry_run: bool = False,
) -> AgentExecReport:
    if not command:
        raise ValueError("agent-exec requires an external runner command via --runner.")
    if timeout_seconds <= 0:
        raise ValueError("agent-exec --timeout-seconds must be greater than zero.")
    if not run_dir.exists():
        raise FileNotFoundError(f"path does not exist: {run_dir}")
    if not run_dir.is_dir():
        raise ValueError(f"agent-exec requires an agent-run directory: {run_dir}")

    target = run_dir.expanduser().resolve()
    request = load_agent_exec_request(target)
    output_file = target / require_simple_output_name(output_name)
    receipt_file = target / AGENT_EXEC_RECEIPT
    if not dry_run and not force:
        for path in (output_file, receipt_file):
            if path.exists():
                raise FileExistsError(path)
    if not dry_run and force and request.get("task") == "bounded-revision" and output_file.is_file():
        attempts_dir = target / "revision_attempts"
        attempts_dir.mkdir(parents=True, exist_ok=True)
        attempt_number = len(list(attempts_dir.glob("attempt-*.output.md"))) + 1
        attempt_stem = f"attempt-{attempt_number:03d}"
        shutil.copy2(output_file, attempts_dir / f"{attempt_stem}.output.md")
        if receipt_file.is_file():
            shutil.copy2(receipt_file, attempts_dir / f"{attempt_stem}.execution.json")

    runner_input = build_runner_input(target, request)
    returncode: int | None = None
    stdout = ""
    stderr = ""
    executed = False
    written = False
    previous_output_text = output_file.read_text(encoding="utf-8-sig") if force and output_file.is_file() else ""
    telemetry: dict[str, object] | None = None

    if not dry_run:
        try:
            completed = subprocess.run(
                command,
                cwd=str(target),
                input=runner_input,
                text=True,
                encoding="utf-8",
                env=runner_environment(),
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"agent runner timed out after {timeout_seconds} seconds") from exc
        executed = True
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        if completed.returncode != 0:
            preview = stderr_preview(stderr or stdout)
            raise RuntimeError(f"agent runner exited with {completed.returncode}: {preview}")
        if not stdout.strip():
            raise ValueError("agent runner produced empty stdout; no staging output was written.")
        telemetry = parse_runner_receipt(stderr)
        output_file.write_text(stdout.rstrip() + "\n", encoding="utf-8", newline="\n")
        receipt = {
            "schema": "fictionops.agent_exec_receipt.v1",
            "run_dir": str(target),
            "request_file": str(target / "request.json"),
            "output_file": str(output_file),
            "command": command,
            "returncode": returncode,
            "stdout_chars": len(stdout.strip()),
            "stderr_chars": len(stderr.strip()),
            "telemetry": telemetry,
            "safety": agent_exec_safety(),
        }
        receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        written = True
        if request.get("task") == "bounded-revision" and previous_output_text and stdout.rstrip() + "\n" == previous_output_text:
            raise RuntimeError("bounded revision retry produced a byte-identical candidate; no progress was made")

    report = AgentExecReport(
        target=str(target),
        run_dir=str(target),
        request_file=str(target / "request.json"),
        output_file=str(output_file),
        receipt_file=str(receipt_file),
        role=request_text(request, "role"),
        task=request_text(request, "task"),
        book=request_text(request, "book", "book_01"),
        chapter=request_optional_text(request, "chapter"),
        provider=request_text(request, "provider"),
        model=request_text(request, "model"),
        command=command,
        timeout_seconds=timeout_seconds,
        input_chars=len(runner_input),
        stdout_chars=len(stdout.strip()),
        stderr_chars=len(stderr.strip()),
        stderr_preview=stderr_preview(stderr),
        telemetry=telemetry,
        returncode=returncode,
        dry_run=dry_run,
        executed=executed,
        written=written,
        safety=agent_exec_safety(),
        next_actions=[],
    )
    report.next_actions = next_actions_for_agent_exec(report)
    return report


def render_agent_exec(report: AgentExecReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_exec(report)


def format_agent_exec(report: AgentExecReport) -> str:
    lines = [
        "# FictionOps Agent Exec",
        "",
        f"- Run dir: `{report.run_dir}`",
        f"- Role: `{report.role}`",
        f"- Task: `{report.task}`",
        f"- Book: `{report.book}`",
        f"- Chapter: `{report.chapter or '-'}`",
        f"- Provider: `{report.provider}`",
        f"- Model: `{report.model}`",
        f"- Executed: {'yes' if report.executed else 'no'}",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Output file: `{report.output_file}`",
        f"- Receipt file: `{report.receipt_file}`",
        f"- Return code: `{report.returncode if report.returncode is not None else '-'}`",
        f"- Input chars: {report.input_chars}",
        f"- Stdout chars: {report.stdout_chars}",
        f"- Stderr chars: {report.stderr_chars}",
        "",
        "## Safety",
        "",
        "- External command may call a model, but FictionOps does not read or store API key values.",
        "- Output is written only to a staging file and is never applied to manuscript or canon files automatically.",
        "",
        "## Command",
        "",
        "```text",
        " ".join(report.command),
        "```",
    ]
    if report.stderr_preview:
        lines.extend(["", "## Stderr Preview", "", "```text", report.stderr_preview, "```"])
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
