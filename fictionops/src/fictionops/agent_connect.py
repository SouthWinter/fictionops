from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .agent_run import model_for_task
from .model_config import build_model_config_report
from .models import AgentConnectFile, AgentConnectReport


AGENT_CONNECT_MODES = ["manual", "runner", "controller", "model-runner"]
DEFAULT_CONNECTOR_NAME = "default"
DEFAULT_AGENT_CONNECT_DIR = "00_management/agent_connectors"


def normalize_connector_name(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "-").replace("_", "-")
    allowed = []
    for char in cleaned:
        if char.isalnum() or char == "-":
            allowed.append(char)
    result = "".join(allowed).strip("-")
    if not result:
        raise ValueError("agent-connect --name must contain at least one letter or number.")
    return result


def normalize_agent_connect_mode(mode: str) -> str:
    value = mode.strip().lower()
    if value not in AGENT_CONNECT_MODES:
        choices = ", ".join(AGENT_CONNECT_MODES)
        raise ValueError(f"unsupported agent-connect mode: {mode}. Available modes: {choices}")
    return value


def resolve_agent_connect_output_dir(project: Path, out_dir: str | None, name: str) -> Path:
    base = Path(out_dir).expanduser() if out_dir else Path(DEFAULT_AGENT_CONNECT_DIR) / name
    if base.is_absolute():
        return base.resolve()
    return (project / base).resolve()


def planned_agent_connect_files(output_dir: Path, *, include_adapter: bool) -> dict[str, Path]:
    files = {
        "readme": output_dir / "README.md",
        "manifest": output_dir / "connector_manifest.json",
        "env_example": output_dir / ".env.example",
        "smoke": output_dir / "smoke_commands.md",
    }
    if include_adapter:
        files["runner_adapter"] = output_dir / "runner_adapter.py"
    return files


def agent_connect_safety(mode: str) -> dict[str, object]:
    return {
        "mode": mode,
        "fictionops_calls_model": False,
        "fictionops_stores_api_keys": False,
        "connector_may_call_model": mode in {"model-runner", "runner"},
        "connector_may_execute_safe_commands": mode == "controller",
        "overwrites_manuscript": False,
        "writes_only_connector_files": True,
        "staged_output_required": True,
        "human_review_required_before_apply": True,
    }


def agent_connect_smoke_commands(project_arg: str, name: str, *, mode: str) -> list[str]:
    run_dir = f"00_management/agent_runs/{name}_ch_001"
    commands = [
        f"fictionops audit-agent-workflow {project_arg} --level {mode}",
        f"fictionops agent-run {project_arg} --role draft-writer --chapter 001 --out-dir {run_dir} --no-context-content",
        f"fictionops agent-exec {project_arg}/{run_dir} --runner python 00_management/agent_connectors/{name}/runner_adapter.py",
        f"fictionops agent-inbox {project_arg} --format json",
    ]
    if mode == "controller":
        commands.append(f"fictionops agent-next {project_arg} --chapter 001 --format json")
    return commands


def build_agent_connect_manifest(
    *,
    project: Path,
    connector_name: str,
    mode: str,
    provider: str,
    model: str,
    api_key_env: str,
    env_present: bool,
    smoke_commands: list[str],
    safety: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": "fictionops.agent_connector.v1",
        "connector_name": connector_name,
        "mode": mode,
        "project": str(project),
        "provider": provider,
        "model": model,
        "api_key_env": api_key_env,
        "api_key_env_present": env_present,
        "contracts": {
            "runner_input": "stdin from fictionops agent-exec",
            "runner_output": "stdout becomes a staged output file",
            "controller_input": "fictionops agent-next --format json",
            "output_review": "fictionops agent-inbox plus gates before manual apply",
        },
        "allowed_fictionops_commands": [
            "agent-run",
            "agent-exec",
            "agent-inbox",
            "agent-next",
            "audit-agent-workflow",
            "context-pack",
            "draft-brief",
            "review-gate",
            "post-draft",
            "book-gate",
            "doctor",
            "revision-plan",
            "workflow-plan",
        ],
        "forbidden_connector_actions": [
            "write raw API keys into project files",
            "edit manuscript, canon, character, or publish files directly",
            "apply staged model output without human review",
            "invent canon when context is missing",
            "continue a controller loop past an agent-inbox or gate boundary",
        ],
        "smoke_commands": smoke_commands,
        "safety": safety,
    }


def format_agent_connect_readme(report: AgentConnectReport) -> str:
    lines = [
        "# FictionOps Agent Connector Kit",
        "",
        f"- Connector: `{report.connector_name}`",
        f"- Mode: `{report.mode}`",
        f"- Provider: `{report.provider or '-'}`",
        f"- Model: `{report.model or '-'}`",
        f"- API key env: `{report.api_key_env or '-'}`",
        f"- Env present now: {'yes' if report.env_present else 'no'}",
        "",
        "## Boundary",
        "",
        "This directory is a connector handshake, not a manuscript workspace. External agents may read the manifest and task bundles, then return staged output through `agent-exec` and `agent-inbox`.",
        "",
        "## Files",
        "",
        "| Kind | Path |",
        "| --- | --- |",
    ]
    for item in report.files:
        path = Path(item.path)
        lines.append(f"| `{item.kind}` | [`{path.name}`]({path.name}) |")
    lines.extend(["", "## Smoke Commands", ""])
    for command in report.smoke_commands:
        lines.append(f"```bash\n{command}\n```")
    lines.extend(["", "## Safety", ""])
    for key, value in report.safety.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def format_env_example(report: AgentConnectReport) -> str:
    lines = [
        "# FictionOps does not read or store raw API keys.",
        "# Keep this file as documentation; put real secrets in your shell, OS keychain, or CI secret store.",
    ]
    if report.api_key_env:
        lines.append(f"{report.api_key_env}=")
    else:
        lines.append("YOUR_PROVIDER_API_KEY=")
    lines.extend(
        [
            f"FICTIONOPS_CONNECTOR_NAME={report.connector_name}",
            f"FICTIONOPS_CONNECTOR_MODE={report.mode}",
            f"FICTIONOPS_PROVIDER={report.provider}",
            f"FICTIONOPS_MODEL={report.model}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def format_smoke_commands(report: AgentConnectReport) -> str:
    lines = [
        "# FictionOps Agent Connector Smoke Commands",
        "",
        "Run these before trusting a real model connector. They prove the staging boundary, not literary quality.",
        "",
    ]
    for index, command in enumerate(report.smoke_commands, start=1):
        lines.extend([f"## {index}. Step", "", "```bash", command, "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def runner_adapter_template() -> str:
    return """#!/usr/bin/env python3
from __future__ import annotations

import sys


def main() -> int:
    request = sys.stdin.read()
    if not request.strip():
        print("empty FictionOps runner input", file=sys.stderr)
        return 2
    print("# Staged FictionOps Agent Output")
    print()
    print("This is a connector smoke-test response. Replace runner_adapter.py with your real model call.")
    print()
    print("## Input Chars")
    print()
    print(len(request))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def next_actions_for_agent_connect(report: AgentConnectReport) -> list[str]:
    actions = [
        "Review connector_manifest.json and keep real credentials outside the project.",
        "Run the smoke commands before replacing runner_adapter.py with a real model connector.",
        f"Run `fictionops audit-agent-workflow . --level {report.mode}` before trusting the connector in a project loop.",
    ]
    if report.mode == "controller":
        actions.append("Controller loops must stop at agent-inbox, gate, release, or repeated-command boundaries.")
    else:
        actions.append("Use agent-run and agent-exec for bounded tasks, then review staged output through agent-inbox.")
    return actions


def write_agent_connect_kit(report: AgentConnectReport, *, force: bool) -> list[AgentConnectFile]:
    if not report.output_dir:
        return []
    output_dir = Path(report.output_dir)
    files = planned_agent_connect_files(output_dir, include_adapter=True)
    if not force:
        existing = [path for path in files.values() if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    output_dir.mkdir(parents=True, exist_ok=True)
    files["readme"].write_text(format_agent_connect_readme(report), encoding="utf-8", newline="\n")
    files["manifest"].write_text(json.dumps(report.manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    files["env_example"].write_text(format_env_example(report), encoding="utf-8", newline="\n")
    files["smoke"].write_text(format_smoke_commands(report), encoding="utf-8", newline="\n")
    files["runner_adapter"].write_text(runner_adapter_template(), encoding="utf-8", newline="\n")
    return [AgentConnectFile(kind=kind, path=str(path), written=True) for kind, path in files.items()]


def build_agent_connect(
    project: Path,
    *,
    name: str = DEFAULT_CONNECTOR_NAME,
    mode: str = "runner",
    out_dir: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> AgentConnectReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"agent-connect requires a FictionOps project directory: {project}")

    target = project.expanduser().resolve()
    connector_name = normalize_connector_name(name)
    connect_mode = normalize_agent_connect_mode(mode)
    model_config = build_model_config_report(target)
    model = model_for_task(task="draft", role="draft-writer", model_config=model_config)
    output_dir = resolve_agent_connect_output_dir(target, out_dir, connector_name)
    project_arg = str(target)
    smoke_commands = agent_connect_smoke_commands(project_arg, connector_name, mode=connect_mode)
    safety = agent_connect_safety(connect_mode)
    manifest = build_agent_connect_manifest(
        project=target,
        connector_name=connector_name,
        mode=connect_mode,
        provider=model_config.provider,
        model=model,
        api_key_env=model_config.api_key_env,
        env_present=model_config.env_present,
        smoke_commands=smoke_commands,
        safety=safety,
    )
    planned = planned_agent_connect_files(output_dir, include_adapter=True)
    files = [AgentConnectFile(kind=kind, path=str(path), written=False) for kind, path in planned.items()]
    report = AgentConnectReport(
        target=str(target),
        connector_name=connector_name,
        mode=connect_mode,
        output_dir=str(output_dir),
        dry_run=dry_run,
        written=False,
        provider=model_config.provider,
        model=model,
        api_key_env=model_config.api_key_env,
        env_present=model_config.env_present,
        file_count=len(files),
        files=files,
        manifest=manifest,
        smoke_commands=smoke_commands,
        safety=safety,
        next_actions=[],
    )
    report.next_actions = next_actions_for_agent_connect(report)
    if not dry_run:
        report.files = write_agent_connect_kit(report, force=force)
        report.written = True
        report.file_count = len(report.files)
    return report


def render_agent_connect(report: AgentConnectReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_connect(report)


def format_agent_connect(report: AgentConnectReport) -> str:
    lines = [
        "# FictionOps Agent Connect",
        "",
        f"- Target: `{report.target}`",
        f"- Connector: `{report.connector_name}`",
        f"- Mode: `{report.mode}`",
        f"- Output dir: `{report.output_dir or '-'}`",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Provider: `{report.provider or '-'}`",
        f"- Model: `{report.model or '-'}`",
        f"- API key env: `{report.api_key_env or '-'}`",
        f"- Env present now: {'yes' if report.env_present else 'no'}",
        f"- Files: {report.file_count}",
        "",
        "## Rule",
        "",
        "This command creates a connector handshake kit. It does not call a model, store API keys, execute a runner, or apply staged output.",
        "",
        "## Files",
        "",
        "| Kind | Written | Path |",
        "| --- | --- | --- |",
    ]
    for item in report.files:
        lines.append(f"| `{item.kind}` | {'yes' if item.written else 'no'} | `{item.path}` |")
    lines.extend(["", "## Smoke Commands", ""])
    for command in report.smoke_commands:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
