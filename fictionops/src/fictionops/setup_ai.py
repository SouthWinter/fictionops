from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .model_config import build_model_config_report
from .models import AiSetupFile, AiSetupReport


AI_PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "openai": {
        "provider": "openai-chat",
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
    },
    "openai-chat": {
        "provider": "openai-chat",
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
    },
    "deepseek": {
        "provider": "deepseek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
    },
    "dashscope": {
        "provider": "dashscope",
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "qwen": {
        "provider": "dashscope",
        "api_key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "moonshot": {
        "provider": "moonshot",
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "kimi": {
        "provider": "moonshot",
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "zhipu": {
        "provider": "zhipu",
        "api_key_env": "ZHIPUAI_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
    "glm": {
        "provider": "zhipu",
        "api_key_env": "ZHIPUAI_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
    "volcengine-ark": {
        "provider": "volcengine-ark",
        "api_key_env": "ARK_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-1-6",
    },
    "doubao": {
        "provider": "volcengine-ark",
        "api_key_env": "ARK_API_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-1-6",
    },
    "siliconflow": {
        "provider": "siliconflow",
        "api_key_env": "SILICONFLOW_API_KEY",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-72B-Instruct",
    },
    "local-openai": {
        "provider": "local-openai",
        "api_key_env": "",
        "base_url": "http://127.0.0.1:8000/v1",
        "model": "local-model",
    },
    "local": {
        "provider": "local-openai",
        "api_key_env": "",
        "base_url": "http://127.0.0.1:8000/v1",
        "model": "local-model",
    },
}


def provider_preset(provider: str) -> dict[str, str]:
    key = provider.strip().lower()
    if key not in AI_PROVIDER_PRESETS:
        allowed = ", ".join(sorted(AI_PROVIDER_PRESETS))
        raise ValueError(f"unknown AI provider preset: {provider}; expected one of {allowed}")
    return dict(AI_PROVIDER_PRESETS[key])


def resolve_env_example_path(project: Path, env_file: str | None) -> Path:
    selected = env_file or "00_management/ai_runner.env.example"
    candidate = Path(selected).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (project / candidate).resolve()


def format_env_example(*, provider: str, model: str, api_key_env: str, base_url: str) -> str:
    lines = [
        "# FictionOps AI runner environment example",
        "# Copy this file outside version control before adding a real API key.",
        f"FICTIONOPS_CHAT_PROVIDER={provider}",
        f"FICTIONOPS_CHAT_MODEL={model}",
        f"FICTIONOPS_CHAT_BASE_URL={base_url}",
        f"FICTIONOPS_CHAT_API_KEY_ENV={api_key_env}",
    ]
    if api_key_env:
        lines.extend(
            [
                "",
                "# Keep the real value out of project files.",
                f"{api_key_env}=",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def runner_command_prefix() -> str:
    return "python fictionops/examples/agent_runner_openai_chat.py"


def make_setup_commands(*, provider: str, model: str, book: str, chapter: str) -> tuple[str, str]:
    base = (
        f"fictionops write-chapter . --book {book} --chapter {chapter} "
        f"--runner {runner_command_prefix()} --provider {provider} --model {model}"
    )
    return base + " --dry-run", base + " --max-output-chars 12000"


def write_env_example(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_ai_setup(
    project: Path,
    *,
    provider: str = "deepseek",
    model: str | None = None,
    planning_model: str | None = None,
    drafting_model: str | None = None,
    audit_model: str | None = None,
    api_key_env: str | None = None,
    base_url: str | None = None,
    env_file: str | None = None,
    book: str = "book_01",
    chapter: str = "001",
    max_context_chars: int = 60000,
    max_output_tokens: int = 4000,
    timeout_seconds: int = 120,
    force: bool = False,
    dry_run: bool = False,
) -> AiSetupReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"setup-ai requires a FictionOps project directory: {project}")
    target = project.expanduser().resolve()
    preset = provider_preset(provider)
    selected_provider = preset["provider"]
    selected_model = model or preset["model"]
    selected_planning = planning_model or selected_model
    selected_drafting = drafting_model or selected_model
    selected_audit = audit_model or selected_model
    selected_api_key_env = api_key_env if api_key_env is not None else preset["api_key_env"]
    selected_base_url = base_url or preset["base_url"]
    env_path = resolve_env_example_path(target, env_file)
    if not dry_run and env_path.exists() and not force:
        raise FileExistsError(env_path)
    model_report = build_model_config_report(
        target,
        provider=selected_provider,
        planning_model=selected_planning,
        drafting_model=selected_drafting,
        audit_model=selected_audit,
        api_key_env=selected_api_key_env,
        base_url=selected_base_url,
        max_context_chars=max_context_chars,
        max_output_tokens=max_output_tokens,
        timeout_seconds=timeout_seconds,
        write=not dry_run,
        force=force,
        dry_run=dry_run,
    )
    dry_run_command, real_run_command = make_setup_commands(
        provider=selected_provider,
        model=selected_drafting,
        book=book,
        chapter=chapter,
    )
    files = [
        AiSetupFile(kind="model_config", path=model_report.config_file, written=model_report.written),
        AiSetupFile(kind="env_example", path=str(env_path), written=False),
    ]
    env_text = format_env_example(
        provider=selected_provider,
        model=selected_drafting,
        api_key_env=selected_api_key_env,
        base_url=selected_base_url,
    )
    if not dry_run:
        write_env_example(env_path, env_text, force=force)
        files[1].written = True
    safety = {
        "stores_api_keys": False,
        "writes_real_env_file": False,
        "calls_model": False,
        "requires_human_review": True,
    }
    next_actions = [
        f"Set {selected_api_key_env} in your shell or private env file before a real call." if selected_api_key_env else "Start your local OpenAI-compatible server before a real call.",
        f"Run dry-run first: `{dry_run_command}`",
        f"Then run a real staged call: `{real_run_command}`",
        "Inspect staged output with `fictionops agent-inbox .` before applying text.",
    ]
    return AiSetupReport(
        target=str(target),
        provider=selected_provider,
        model=selected_model,
        planning_model=selected_planning,
        drafting_model=selected_drafting,
        audit_model=selected_audit,
        api_key_env=selected_api_key_env,
        base_url=selected_base_url,
        env_example_file=str(env_path),
        dry_run=dry_run,
        written=not dry_run,
        file_count=len(files),
        files=files,
        model_config=model_report,
        dry_run_command=dry_run_command,
        real_run_command=real_run_command,
        next_actions=next_actions,
        safety=safety,
    )


def render_ai_setup(report: AiSetupReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps({"schema": "fictionops.ai_setup.v1", **asdict(report)}, ensure_ascii=False, indent=2)
    return format_ai_setup(report)


def format_ai_setup(report: AiSetupReport) -> str:
    lines = [
        "# FictionOps AI Setup",
        "",
        f"- Target: `{report.target}`",
        f"- Provider: `{report.provider}`",
        f"- Drafting model: `{report.drafting_model}`",
        f"- API key env: `{report.api_key_env or '<none for local/no-auth provider>'}`",
        f"- Base URL: `{report.base_url}`",
        f"- Env example: `{report.env_example_file}`",
        f"- Written: {'yes' if report.written else 'no'}",
        f"- Dry run: {'yes' if report.dry_run else 'no'}",
        "",
        "## Files",
        "",
        "| Kind | Path | Written |",
        "| --- | --- | --- |",
    ]
    for item in report.files:
        lines.append(f"| `{item.kind}` | `{item.path}` | {'yes' if item.written else 'no'} |")
    lines.extend(
        [
            "",
            "## Commands",
            "",
            f"- Dry run: `{report.dry_run_command}`",
            f"- Real staged call: `{report.real_run_command}`",
            "",
            "## Next Actions",
            "",
        ]
    )
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"
