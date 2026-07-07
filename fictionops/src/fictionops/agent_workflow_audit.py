from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .agent_connect import DEFAULT_AGENT_CONNECT_DIR, normalize_connector_name
from .agent_inbox import build_agent_inbox
from .agent_next import build_agent_next, looks_like_fictionops_package
from .doctor import looks_like_standard_project
from .markdown import safe_cell
from .model_config import build_model_config_report
from .models import AgentWorkflowIssue, AgentWorkflowReport


AGENT_WORKFLOW_LEVELS = {"manual", "runner", "controller", "model-runner"}


def issue(severity: str, code: str, field: str, message: str) -> AgentWorkflowIssue:
    return AgentWorkflowIssue(severity=severity, code=code, field=field, message=message)


def blocking_count(issues: list[AgentWorkflowIssue]) -> int:
    return sum(1 for item in issues if item.severity in {"P0", "P1", "P2"})


def normalize_agent_workflow_level(level: str) -> str:
    normalized = level.strip().lower()
    aliases = {
        "chat": "manual",
        "manual-chat": "manual",
        "external-runner": "runner",
        "model": "model-runner",
        "model_runner": "model-runner",
        "agentic": "controller",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in AGENT_WORKFLOW_LEVELS:
        choices = ", ".join(sorted(AGENT_WORKFLOW_LEVELS))
        raise ValueError(f"unsupported agent workflow level: {level}. Available levels: {choices}")
    return normalized


def connector_dir_for(project: Path, connector: str) -> Path:
    return project / DEFAULT_AGENT_CONNECT_DIR / normalize_connector_name(connector)


def connector_manifest_issues(project: Path, connector: str, *, expected_level: str, evidence: dict[str, object]) -> list[AgentWorkflowIssue]:
    issues: list[AgentWorkflowIssue] = []
    connector_name = normalize_connector_name(connector)
    connect_dir = connector_dir_for(project, connector_name)
    manifest_file = connect_dir / "connector_manifest.json"
    required_files = {
        "manifest": manifest_file,
        "readme": connect_dir / "README.md",
        "env_example": connect_dir / ".env.example",
        "smoke": connect_dir / "smoke_commands.md",
        "runner_adapter": connect_dir / "runner_adapter.py",
    }
    missing = [kind for kind, path in required_files.items() if not path.exists()]
    evidence.update(
        {
            "connector_name": connector_name,
            "connector_dir": str(connect_dir),
            "connector_manifest_file": str(manifest_file),
            "connector_file_count": len(required_files) - len(missing),
            "connector_missing_files": missing,
        }
    )
    if missing:
        issues.append(
            issue(
                "P2",
                "connector_kit_incomplete",
                str(connect_dir),
                "Connector kit is missing required file(s): " + ", ".join(missing),
            )
        )
    if not manifest_file.exists():
        return issues

    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(issue("P2", "connector_manifest_invalid_json", str(manifest_file), f"Connector manifest is not valid JSON: {exc}"))
        return issues
    if not isinstance(manifest, dict):
        issues.append(issue("P2", "connector_manifest_not_object", str(manifest_file), "Connector manifest must be a JSON object."))
        return issues

    safety = manifest.get("safety") if isinstance(manifest.get("safety"), dict) else {}
    allowed = manifest.get("allowed_fictionops_commands") if isinstance(manifest.get("allowed_fictionops_commands"), list) else []
    smoke_commands = manifest.get("smoke_commands") if isinstance(manifest.get("smoke_commands"), list) else []
    manifest_mode = str(manifest.get("mode") or "")
    evidence.update(
        {
            "connector_manifest_schema": manifest.get("schema"),
            "connector_manifest_mode": manifest_mode,
            "connector_manifest_provider": manifest.get("provider"),
            "connector_manifest_model": manifest.get("model"),
            "connector_allowed_commands": allowed,
            "connector_smoke_command_count": len(smoke_commands),
        }
    )

    if manifest.get("schema") != "fictionops.agent_connector.v1":
        issues.append(issue("P2", "connector_manifest_schema_mismatch", str(manifest_file), "Connector manifest must declare schema fictionops.agent_connector.v1."))
    if manifest.get("connector_name") != connector_name:
        issues.append(issue("P2", "connector_manifest_name_mismatch", str(manifest_file), f"Connector manifest name does not match requested connector `{connector_name}`."))
    if manifest_mode != expected_level:
        issues.append(issue("P2", "connector_mode_mismatch", str(manifest_file), f"Connector mode is `{manifest_mode}` but audit level is `{expected_level}`."))

    required_commands = {"agent-run", "agent-exec", "agent-inbox", "audit-agent-workflow"}
    if expected_level == "controller":
        required_commands.add("agent-next")
    missing_commands = sorted(required_commands - {str(item) for item in allowed})
    if missing_commands:
        issues.append(issue("P2", "connector_missing_allowed_commands", str(manifest_file), "Connector manifest is missing allowed command(s): " + ", ".join(missing_commands)))

    required_safety = {
        "fictionops_calls_model": False,
        "fictionops_stores_api_keys": False,
        "overwrites_manuscript": False,
        "staged_output_required": True,
        "human_review_required_before_apply": True,
    }
    for key, expected in required_safety.items():
        if safety.get(key) is not expected:
            issues.append(issue("P2", "connector_safety_mismatch", f"safety.{key}", f"Connector safety flag `{key}` must be `{expected}`."))

    smoke_text = "\n".join(str(item) for item in smoke_commands)
    for token in ("audit-agent-workflow", "agent-run", "agent-exec", "agent-inbox"):
        if token not in smoke_text:
            issues.append(issue("P3", "connector_smoke_command_gap", "smoke_commands", f"Connector smoke commands should include `{token}`."))

    env_file = required_files["env_example"]
    if env_file.exists():
        env_text = env_file.read_text(encoding="utf-8")
        suspicious_secret = "sk-" in env_text
        for line in env_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if "KEY" in key.upper() and value.strip():
                suspicious_secret = True
        if suspicious_secret:
            issues.append(issue("P1", "connector_env_may_contain_secret", str(env_file), ".env.example appears to contain a secret value; keep only variable names."))
    return issues


def next_actions_for_agent_workflow(report: AgentWorkflowReport) -> list[str]:
    if report.evidence.get("fictionops_package"):
        if report.status == "needs_human_review":
            return [
                "Review the selected stable-core action item with a human maintainer; controllers must not fabricate external release, dogfood, or stability-window evidence."
            ]
        if report.status == "ready":
            return ["Run `fictionops agent-next <package-checkout> --format json` from an external controller to inspect the next stable-core governance step."]
        return ["Fix the package-governance audit findings, then rerun `fictionops audit-agent-workflow`."]
    if report.status == "missing_project":
        return ["Run `fictionops init <path> --title \"<title>\"` or migrate existing material with `fictionops adopt`."]
    if report.status == "not_standard_project":
        return ["Run `fictionops adopt <path> --format json`, then migrate into a standard FictionOps project."]
    if report.status == "needs_human_review":
        return ["Review `fictionops agent-inbox <path>` output before starting new agent work."]
    if report.status == "not_ready":
        return ["Fix the blocking audit findings, then rerun `fictionops audit-agent-workflow`."]
    if report.evidence.get("connector_name"):
        return [f"Run the smoke commands in `{report.evidence.get('connector_dir')}` before replacing the adapter with a real model connector."]
    if report.level == "manual":
        return ["Build a scoped handoff with `fictionops context-pack` or `fictionops agent-prompt`."]
    if report.level == "runner":
        return ["Prepare a task with `fictionops agent-run`, execute a runner with `fictionops agent-exec`, then inspect `fictionops agent-inbox`."]
    if report.level == "controller":
        return ["Use `fictionops agent-next --format json` from an external controller and stop at human-review boundaries."]
    return ["Run `fictionops agent-run`, then call a model-backed external runner through `fictionops agent-exec`."]


def build_agent_workflow_audit(
    target: Path,
    *,
    level: str = "runner",
    book: str = "book_01",
    chapter: str | None = None,
    scan_text: bool = False,
    connector: str | None = None,
) -> AgentWorkflowReport:
    normalized_level = normalize_agent_workflow_level(level)
    resolved = target.expanduser().resolve()
    issues: list[AgentWorkflowIssue] = []
    evidence: dict[str, object] = {
        "target_exists": resolved.exists(),
        "level": normalized_level,
        "book": book,
        "chapter": chapter or "",
        "connector_requested": connector or "",
    }

    if not resolved.exists():
        issues.append(issue("P1", "missing_project", "path", f"Target path does not exist: {resolved}"))
        status = "missing_project"
        report = AgentWorkflowReport(
            target=str(resolved),
            level=normalized_level,
            status=status,
            ready=False,
            issue_count=len(issues),
            blocking_issue_count=blocking_count(issues),
            issues=issues,
            evidence=evidence,
            next_actions=[],
        )
        report.next_actions = next_actions_for_agent_workflow(report)
        return report

    if not resolved.is_dir():
        raise ValueError(f"audit-agent-workflow requires a project directory: {resolved}")

    package_checkout = looks_like_fictionops_package(resolved)
    standard_project = looks_like_standard_project(resolved)
    evidence["standard_project"] = standard_project
    evidence["fictionops_package"] = package_checkout
    if package_checkout and normalized_level == "controller":
        agent_next = build_agent_next(resolved, book=book, chapter=chapter, scan_text=scan_text)
        first_candidate = agent_next.candidates[0] if agent_next.candidates else None
        evidence.update(
            {
                "agent_next_status": agent_next.status,
                "agent_next_selected_command": agent_next.selected_command,
                "agent_next_selected_stage": first_candidate.stage if first_candidate else "",
                "agent_next_requires_human_review": bool(first_candidate and first_candidate.requires_human_review),
                "agent_next_safe_to_auto_run": bool(first_candidate and first_candidate.safe_to_auto_run),
                "stable_core_status": agent_next.evidence.get("stable_core_status"),
                "stable_core_ready": agent_next.evidence.get("stable_core_ready"),
                "stable_core_blocking_issues": agent_next.evidence.get("stable_core_blocking_issues"),
                "stable_core_action_items": agent_next.evidence.get("stable_core_action_items", []),
            }
        )
        if agent_next.status == "needs_human_review":
            issues.append(
                issue(
                    "P2",
                    "stable_core_human_review_boundary",
                    "agent-next",
                    "FictionOps package governance selected a stable-core action item that requires human-reviewed external evidence.",
                )
            )
        elif first_candidate and not first_candidate.safe_to_auto_run:
            issues.append(
                issue(
                    "P2",
                    "stable_core_not_safe_to_auto_run",
                    "agent-next",
                    "FictionOps package governance selected a stable-core action item that should not be run automatically.",
                )
            )
        blockers = blocking_count(issues)
        status = "needs_human_review" if agent_next.status == "needs_human_review" else ("not_ready" if blockers else "ready")
        report = AgentWorkflowReport(
            target=str(resolved),
            level=normalized_level,
            status=status,
            ready=blockers == 0,
            issue_count=len(issues),
            blocking_issue_count=blockers,
            issues=issues,
            evidence=evidence,
            next_actions=[],
        )
        report.next_actions = next_actions_for_agent_workflow(report)
        return report
    if package_checkout:
        issues.append(
            issue(
                "P1",
                "package_requires_controller_level",
                "level",
                "FictionOps package governance is only supported through controller-level agent workflow audits.",
            )
        )
        status = "not_ready"
        report = AgentWorkflowReport(
            target=str(resolved),
            level=normalized_level,
            status=status,
            ready=False,
            issue_count=len(issues),
            blocking_issue_count=blocking_count(issues),
            issues=issues,
            evidence=evidence,
            next_actions=[],
        )
        report.next_actions = next_actions_for_agent_workflow(report)
        return report
    if not standard_project:
        issues.append(
            issue(
                "P1",
                "not_standard_project",
                "path",
                "Target does not look like a standard FictionOps project with project.yml and expected layers.",
            )
        )
        status = "not_standard_project"
        report = AgentWorkflowReport(
            target=str(resolved),
            level=normalized_level,
            status=status,
            ready=False,
            issue_count=len(issues),
            blocking_issue_count=blocking_count(issues),
            issues=issues,
            evidence=evidence,
            next_actions=[],
        )
        report.next_actions = next_actions_for_agent_workflow(report)
        return report

    inbox = build_agent_inbox(resolved)
    evidence.update(
        {
            "agent_inbox_status": inbox.status,
            "agent_run_count": inbox.run_count,
            "agent_ready_count": inbox.ready_count,
            "agent_awaiting_count": inbox.awaiting_count,
            "agent_needs_attention_count": inbox.needs_attention_count,
        }
    )
    if inbox.needs_attention_count:
        issues.append(
            issue(
                "P1",
                "agent_inbox_needs_attention",
                "00_management/agent_runs",
                f"{inbox.needs_attention_count} agent run(s) need attention before new agent work starts.",
            )
        )
    elif inbox.ready_count:
        issues.append(
            issue(
                "P2",
                "agent_output_waiting_for_review",
                "00_management/agent_runs",
                f"{inbox.ready_count} staged agent output(s) are ready for human review.",
            )
        )

    model_config = build_model_config_report(resolved)
    evidence.update(
        {
            "model_config_file_exists": model_config.config_file_exists,
            "model_provider": model_config.provider,
            "planning_model": model_config.planning_model,
            "drafting_model": model_config.drafting_model,
            "audit_model": model_config.audit_model,
            "api_key_env": model_config.api_key_env,
            "api_key_env_present": model_config.env_present,
            "model_config_issue_count": len(model_config.issues),
        }
    )
    for item in model_config.issues:
        severity = item.severity
        if normalized_level == "model-runner" and item.code in {
            "provider_not_configured",
            "model_not_configured",
            "api_key_env_missing",
        }:
            severity = "P2"
        if item.code == "unsafe_key_storage_policy":
            severity = "P1"
        issues.append(issue(severity, item.code, f"model_config.{item.field}", item.message))

    if connector:
        issues.extend(connector_manifest_issues(resolved, connector, expected_level=normalized_level, evidence=evidence))

    if normalized_level in {"controller", "model-runner"}:
        agent_next = build_agent_next(resolved, book=book, chapter=chapter, scan_text=scan_text)
        evidence.update(
            {
                "agent_next_status": agent_next.status,
                "agent_next_selected_command": agent_next.selected_command,
                "agent_next_requires_human_review": bool(agent_next.candidates and agent_next.candidates[0].requires_human_review),
                "agent_next_safe_to_auto_run": bool(agent_next.candidates and agent_next.candidates[0].safe_to_auto_run),
            }
        )
        if agent_next.status == "needs_human_review":
            issues.append(
                issue(
                    "P2",
                    "agent_next_human_review_boundary",
                    "agent-next",
                    "agent-next selected a human-review boundary; a controller must stop here.",
                )
            )
        elif agent_next.candidates and not agent_next.candidates[0].safe_to_auto_run:
            issues.append(
                issue(
                    "P2",
                    "agent_next_not_safe_to_auto_run",
                    "agent-next",
                    "agent-next selected a command that should not be run automatically.",
                )
            )

    blockers = blocking_count(issues)
    if inbox.ready_count or inbox.needs_attention_count:
        status = "needs_human_review"
    elif blockers:
        status = "not_ready"
    else:
        status = "ready"

    report = AgentWorkflowReport(
        target=str(resolved),
        level=normalized_level,
        status=status,
        ready=blockers == 0,
        issue_count=len(issues),
        blocking_issue_count=blockers,
        issues=issues,
        evidence=evidence,
        next_actions=[],
    )
    report.next_actions = next_actions_for_agent_workflow(report)
    return report


def format_agent_workflow_audit(report: AgentWorkflowReport) -> str:
    lines = [
        "# FictionOps Agent Workflow Audit",
        "",
        f"- Target: `{report.target}`",
        f"- Level: `{report.level}`",
        f"- Status: `{report.status}`",
        f"- Ready: {'yes' if report.ready else 'no'}",
        f"- Issues: {report.issue_count}",
        f"- Blocking issues: {report.blocking_issue_count}",
        "",
        "## Issues",
        "",
    ]
    if report.issues:
        lines.extend(["| Severity | Code | Field | Message |", "| --- | --- | --- | --- |"])
        for item in report.issues:
            lines.append(
                "| "
                + " | ".join(
                    [
                        safe_cell(item.severity),
                        f"`{safe_cell(item.code)}`",
                        safe_cell(item.field),
                        safe_cell(item.message),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No agent workflow issues found.")
    lines.extend(["", "## Evidence", ""])
    for key, value in report.evidence.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def render_agent_workflow_audit(report: AgentWorkflowReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_agent_workflow_audit(report)
