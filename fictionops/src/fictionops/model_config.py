from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from .models import ModelConfigIssue, ModelConfigReport


DEFAULT_MODEL_CONFIG = {
    "schema": "fictionops.model_config.v1",
    "provider": "configurable",
    "api_key_env": "",
    "base_url": "",
    "models": {
        "planning": "configurable",
        "drafting": "configurable",
        "audit": "configurable",
    },
    "limits": {
        "max_context_chars": 60000,
        "max_output_tokens": 4000,
        "timeout_seconds": 120,
    },
    "policy": {
        "store_api_keys": False,
        "call_models_from_cli": False,
        "require_context_pack": True,
        "require_revision_plan_for_rewrite": True,
    },
}


def default_model_config_path(project: Path) -> Path:
    return project / "00_management" / "model_config.json"


def deep_copy_default_config() -> dict[str, object]:
    return json.loads(json.dumps(DEFAULT_MODEL_CONFIG))


def load_existing_model_config(path: Path) -> tuple[dict[str, object], list[ModelConfigIssue]]:
    if not path.exists():
        return deep_copy_default_config(), []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return deep_copy_default_config(), [
            ModelConfigIssue(
                severity="P2",
                code="invalid_model_config_json",
                field=str(path),
                message=f"Model config JSON could not be parsed: {exc}",
            )
        ]
    if not isinstance(data, dict):
        return deep_copy_default_config(), [
            ModelConfigIssue(
                severity="P2",
                code="invalid_model_config_shape",
                field=str(path),
                message="Model config must be a JSON object.",
            )
        ]
    merged = deep_copy_default_config()
    deep_update(merged, data)
    return merged, []


def deep_update(base: dict[str, object], updates: dict[str, object]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)  # type: ignore[index,arg-type]
        else:
            base[key] = value


def set_if_value(config: dict[str, object], key: str, value: str | None) -> None:
    if value is not None:
        config[key] = value


def models_section(config: dict[str, object]) -> dict[str, object]:
    models = config.get("models")
    if not isinstance(models, dict):
        models = {}
        config["models"] = models
    return models


def limits_section(config: dict[str, object]) -> dict[str, object]:
    limits = config.get("limits")
    if not isinstance(limits, dict):
        limits = {}
        config["limits"] = limits
    return limits


def apply_model_config_options(
    config: dict[str, object],
    *,
    provider: str | None,
    planning_model: str | None,
    drafting_model: str | None,
    audit_model: str | None,
    api_key_env: str | None,
    base_url: str | None,
    max_context_chars: int | None,
    max_output_tokens: int | None,
    timeout_seconds: int | None,
) -> None:
    set_if_value(config, "provider", provider)
    set_if_value(config, "api_key_env", api_key_env)
    set_if_value(config, "base_url", base_url)
    models = models_section(config)
    if planning_model is not None:
        models["planning"] = planning_model
    if drafting_model is not None:
        models["drafting"] = drafting_model
    if audit_model is not None:
        models["audit"] = audit_model
    limits = limits_section(config)
    if max_context_chars is not None:
        limits["max_context_chars"] = max_context_chars
    if max_output_tokens is not None:
        limits["max_output_tokens"] = max_output_tokens
    if timeout_seconds is not None:
        limits["timeout_seconds"] = timeout_seconds


def clean_string(value: object) -> str:
    return str(value or "").strip()


def model_value(config: dict[str, object], key: str) -> str:
    models = models_section(config)
    return clean_string(models.get(key))


def build_model_config_issues(config: dict[str, object], *, env_present: bool) -> list[ModelConfigIssue]:
    issues: list[ModelConfigIssue] = []
    provider = clean_string(config.get("provider"))
    if not provider or provider == "configurable":
        issues.append(
            ModelConfigIssue(
                severity="P3",
                code="provider_not_configured",
                field="provider",
                message="Model provider is still configurable. Set it before automated model calls.",
            )
        )
    for field in ("planning", "drafting", "audit"):
        value = model_value(config, field)
        if not value or value == "configurable":
            issues.append(
                ModelConfigIssue(
                    severity="P3",
                    code="model_not_configured",
                    field=f"models.{field}",
                    message=f"{field} model is not configured.",
                )
            )
    api_key_env = clean_string(config.get("api_key_env"))
    if provider and provider != "local" and not api_key_env:
        issues.append(
            ModelConfigIssue(
                severity="P3",
                code="api_key_env_missing",
                field="api_key_env",
                message="No API key environment variable name is recorded. Do not store raw API keys in the project.",
            )
        )
    elif api_key_env and not env_present:
        issues.append(
            ModelConfigIssue(
                severity="P4",
                code="api_key_env_not_set",
                field="api_key_env",
                message=f"Environment variable {api_key_env} is not set in the current shell.",
            )
        )
    policy = config.get("policy")
    if isinstance(policy, dict) and policy.get("store_api_keys") is not False:
        issues.append(
            ModelConfigIssue(
                severity="P2",
                code="unsafe_key_storage_policy",
                field="policy.store_api_keys",
                message="Model config must not store raw API keys in the project.",
            )
        )
    return issues


def build_model_config_report(
    project: Path,
    *,
    provider: str | None = None,
    planning_model: str | None = None,
    drafting_model: str | None = None,
    audit_model: str | None = None,
    api_key_env: str | None = None,
    base_url: str | None = None,
    max_context_chars: int | None = None,
    max_output_tokens: int | None = None,
    timeout_seconds: int | None = None,
    out: str | None = None,
    write: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> ModelConfigReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"model-config requires a FictionOps project directory: {project}")

    target = project.expanduser().resolve()
    output_path = resolve_model_config_output_path(target, out) if out else default_model_config_path(target)
    config, issues = load_existing_model_config(output_path)
    apply_model_config_options(
        config,
        provider=provider,
        planning_model=planning_model,
        drafting_model=drafting_model,
        audit_model=audit_model,
        api_key_env=api_key_env,
        base_url=base_url,
        max_context_chars=max_context_chars,
        max_output_tokens=max_output_tokens,
        timeout_seconds=timeout_seconds,
    )
    api_key_name = clean_string(config.get("api_key_env"))
    env_present = bool(api_key_name and os.environ.get(api_key_name))
    issues.extend(build_model_config_issues(config, env_present=env_present))

    report = ModelConfigReport(
        target=str(target),
        config_file=str(output_path),
        config_file_exists=output_path.exists(),
        provider=clean_string(config.get("provider")),
        planning_model=model_value(config, "planning"),
        drafting_model=model_value(config, "drafting"),
        audit_model=model_value(config, "audit"),
        api_key_env=api_key_name,
        base_url=clean_string(config.get("base_url")),
        env_present=env_present,
        write=write,
        dry_run=dry_run,
        written=False,
        config=config,
        issues=issues,
    )
    if write and not dry_run:
        write_model_config(output_path, config, force=force)
        report.written = True
        report.config_file_exists = True
    return report


def resolve_model_config_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_model_config(path: Path, config: dict[str, object], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def render_model_config_report(report: ModelConfigReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return format_model_config_report(report)


def format_model_config_report(report: ModelConfigReport) -> str:
    lines = [
        "# FictionOps Model Config",
        "",
        f"- Target: `{report.target}`",
        f"- Config file: `{report.config_file}`",
        f"- Config file exists: {'yes' if report.config_file_exists else 'no'}",
        f"- Provider: `{report.provider or '-'}`",
        f"- Planning model: `{report.planning_model or '-'}`",
        f"- Drafting model: `{report.drafting_model or '-'}`",
        f"- Audit model: `{report.audit_model or '-'}`",
        f"- API key env: `{report.api_key_env or '-'}`",
        f"- API key env present: {'yes' if report.env_present else 'no'}",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        "",
        "## Issues",
        "",
    ]
    if report.issues:
        lines.extend(["| Severity | Code | Field | Message |", "| --- | --- | --- | --- |"])
        for issue in report.issues:
            lines.append(f"| {issue.severity} | `{issue.code}` | `{issue.field}` | {issue.message} |")
    else:
        lines.append("No model configuration issues found.")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Raw API keys are not stored in FictionOps project files.",
            "- This command only records provider settings and environment variable names.",
            "- FictionOps CLI does not call model providers in this baseline.",
        ]
    )
    return "\n".join(lines) + "\n"
