#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


REQUEST_BLOCK = re.compile(r"## Request\s+```json\s*(.*?)\s*```", re.DOTALL)
PLACEHOLDER_MODELS = {"", "-", "planner", "writer", "auditor", "gpt-planner", "gpt-writer", "gpt-auditor"}
PLACEHOLDER_PROVIDERS = {"", "-", "configurable"}
DEFAULT_PROVIDER = "openai-chat"
DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_BASE_URL = "https://api.openai.com/v1"

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "openai": {"api_key_env": "OPENAI_API_KEY", "base_url": "https://api.openai.com/v1"},
    "openai-chat": {"api_key_env": "OPENAI_API_KEY", "base_url": "https://api.openai.com/v1"},
    "deepseek": {"api_key_env": "DEEPSEEK_API_KEY", "base_url": "https://api.deepseek.com"},
    "dashscope": {"api_key_env": "DASHSCOPE_API_KEY", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    "qwen": {"api_key_env": "DASHSCOPE_API_KEY", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    "moonshot": {"api_key_env": "MOONSHOT_API_KEY", "base_url": "https://api.moonshot.cn/v1"},
    "kimi": {"api_key_env": "MOONSHOT_API_KEY", "base_url": "https://api.moonshot.cn/v1"},
    "zhipu": {"api_key_env": "ZHIPUAI_API_KEY", "base_url": "https://open.bigmodel.cn/api/paas/v4"},
    "glm": {"api_key_env": "ZHIPUAI_API_KEY", "base_url": "https://open.bigmodel.cn/api/paas/v4"},
    "volcengine-ark": {"api_key_env": "ARK_API_KEY", "base_url": "https://ark.cn-beijing.volces.com/api/v3"},
    "doubao": {"api_key_env": "ARK_API_KEY", "base_url": "https://ark.cn-beijing.volces.com/api/v3"},
    "siliconflow": {"api_key_env": "SILICONFLOW_API_KEY", "base_url": "https://api.siliconflow.cn/v1"},
    "local-openai": {"api_key_env": "", "base_url": "http://127.0.0.1:8000/v1"},
    "local": {"api_key_env": "", "base_url": "http://127.0.0.1:8000/v1"},
}


def extract_request(payload: str) -> dict[str, object]:
    match = REQUEST_BLOCK.search(payload)
    if not match:
        raise ValueError("missing FictionOps request JSON block")
    data = json.loads(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("FictionOps request must be a JSON object")
    return data


def text_value(data: dict[str, object], key: str, default: str = "") -> str:
    value = data.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def load_env_file(path: str | None) -> None:
    if not path:
        return
    env_path = Path(path).expanduser()
    if not env_path.exists():
        raise FileNotFoundError(f"env file does not exist: {env_path}")
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def read_stdin_utf8() -> str:
    return sys.stdin.buffer.read().decode("utf-8")


def choose_provider(request: dict[str, object], override: str | None) -> str:
    candidates = [override or "", os.environ.get("FICTIONOPS_CHAT_PROVIDER", ""), text_value(request, "provider")]
    for candidate in candidates:
        provider = (candidate or "").strip().lower()
        if provider and provider not in PLACEHOLDER_PROVIDERS:
            return provider
    return DEFAULT_PROVIDER


def choose_model(request: dict[str, object], override: str | None, env_name: str) -> str:
    candidates = [override or "", os.environ.get(env_name, ""), text_value(request, "model")]
    for candidate in candidates:
        model = (candidate or "").strip()
        if model and model.lower() not in PLACEHOLDER_MODELS:
            return model
    raise ValueError(
        f"no concrete model configured; pass --model, set {env_name}, or write a real model name into the FictionOps run request"
    )


def resolve_provider_setting(
    *,
    explicit: str | None,
    env_name: str,
    request: dict[str, object],
    request_key: str,
    provider: str,
    preset_key: str,
    default: str,
) -> str:
    for candidate in [explicit or "", os.environ.get(env_name, ""), text_value(request, request_key)]:
        value = (candidate or "").strip()
        if value:
            return value
    preset = PROVIDER_PRESETS.get(provider, {})
    if preset_key in preset:
        return preset[preset_key].strip()
    candidates = [default]
    for candidate in candidates:
        value = (candidate or "").strip()
        if value:
            return value
    return ""


def make_messages(payload: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an external FictionOps runner. Follow the FictionOps output contract. "
                "Write only staged Markdown for human review. Do not claim that manuscript or canon files were edited."
            ),
        },
        {"role": "user", "content": payload},
    ]


def make_request_body(
    payload: str,
    *,
    model: str,
    max_tokens: int | None,
    temperature: float | None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "model": model,
        "messages": make_messages(payload),
        "stream": False,
    }
    if max_tokens:
        body["max_tokens"] = max_tokens
    if temperature is not None:
        body["temperature"] = temperature
    return body


def request_headers(api_key: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "fictionops-openai-compatible-chat-runner-v1",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def extract_choice_text(data: dict[str, object]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("chat completions response did not contain choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("chat completions first choice is not an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("chat completions first choice did not contain a message object")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
        if chunks:
            return "\n\n".join(chunks)
    raise ValueError("chat completions response did not contain message content")


def call_chat_completions(
    *,
    payload: str,
    model: str,
    api_key: str,
    base_url: str,
    timeout: int,
    max_tokens: int | None,
    temperature: float | None,
    max_output_chars: int | None,
) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(
            make_request_body(payload, model=model, max_tokens=max_tokens, temperature=temperature),
            ensure_ascii=False,
        ).encode("utf-8"),
        headers=request_headers(api_key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI-compatible Chat Completions API returned HTTP {exc.code}: {detail[:1200]}") from exc
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("OpenAI-compatible Chat Completions API returned non-object JSON")
    text = extract_choice_text(data)
    if max_output_chars is not None and len(text) > max_output_chars:
        raise ValueError(
            f"provider output has {len(text)} chars, exceeding --max-output-chars {max_output_chars}; "
            "rerun with a larger limit only after confirming this is expected"
        )
    return text


def build_dry_run_output(
    payload: str,
    request: dict[str, object],
    *,
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
    timeout: int,
    max_tokens: int | None,
    temperature: float | None,
    max_output_chars: int | None,
) -> str:
    role = text_value(request, "role", "-")
    task = text_value(request, "task", "-")
    book = text_value(request, "book", "book_01")
    chapter = text_value(request, "chapter", "-")
    return "\n".join(
        [
            "# OpenAI-Compatible Chat Runner Dry Run",
            "",
            "> No network request was made. Rerun without `--dry-run` only after reviewing this boundary.",
            "",
            "## Request Summary",
            "",
            f"- Role: `{role}`",
            f"- Task: `{task}`",
            f"- Book: `{book}`",
            f"- Chapter: `{chapter}`",
            f"- Provider: `{provider}`",
            f"- Model: `{model}`",
            f"- Endpoint: `{base_url.rstrip('/')}/chat/completions`",
            f"- API key env: `{api_key_env or '<none for local/no-auth provider>'}`",
            f"- Timeout seconds: {timeout}",
            f"- Max tokens: {max_tokens if max_tokens is not None else '-'}",
            f"- Temperature: {temperature if temperature is not None else '-'}",
            f"- Max output chars: {max_output_chars if max_output_chars is not None else '-'}",
            f"- Input chars: {len(payload)}",
            "",
            "## Staged Result",
            "",
            "This is a connectivity dry run. It is safe to inspect with `fictionops agent-inbox`, but it is not model output.",
            "",
            "## Boundary",
            "",
            "- The runner reads stdin from `fictionops agent-exec`.",
            "- A real run writes only the provider response to stdout.",
            "- Diagnostics and secrets are not written into manuscript or canon files.",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Example external runner for OpenAI-compatible Chat Completions APIs "
            "(DeepSeek, Qwen/DashScope, Kimi, GLM, Doubao/Ark, local servers, and similar providers)."
        )
    )
    parser.add_argument("--model", help="Concrete model name. Overrides request.json and --model-env.")
    parser.add_argument(
        "--provider",
        help=(
            "Provider preset. Examples: openai-chat, deepseek, dashscope/qwen, moonshot/kimi, "
            "zhipu/glm, volcengine-ark/doubao, siliconflow, local-openai."
        ),
    )
    parser.add_argument(
        "--model-env",
        default="FICTIONOPS_CHAT_MODEL",
        help="Environment variable used as model fallback. Default: FICTIONOPS_CHAT_MODEL.",
    )
    parser.add_argument(
        "--api-key-env",
        help=(
            "Environment variable containing the API key. Defaults to the provider preset, then OPENAI_API_KEY. "
            "Use an empty provider preset such as local-openai for no-auth local servers."
        ),
    )
    parser.add_argument(
        "--base-url",
        help="OpenAI-compatible API base URL. Defaults to the provider preset, then https://api.openai.com/v1.",
    )
    parser.add_argument("--env-file", help="Optional .env-style file to load before resolving provider, model, and API key.")
    parser.add_argument("--timeout", type=int, default=300, help="HTTP timeout in seconds. Default: 300.")
    parser.add_argument("--max-tokens", type=int, help="Optional Chat Completions max_tokens value.")
    parser.add_argument("--temperature", type=float, help="Optional Chat Completions temperature value.")
    parser.add_argument(
        "--max-output-chars",
        type=int,
        help="Reject provider output longer than this many characters before writing staged stdout.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse stdin and print a staged dry-run report without calling a provider.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_output_chars is not None and args.max_output_chars <= 0:
        raise ValueError("--max-output-chars must be greater than zero when provided")
    load_env_file(args.env_file)
    payload = read_stdin_utf8()
    request = extract_request(payload)
    provider = choose_provider(request, args.provider)
    api_key_env = resolve_provider_setting(
        explicit=args.api_key_env,
        env_name="FICTIONOPS_CHAT_API_KEY_ENV",
        request=request,
        request_key="api_key_env",
        provider=provider,
        preset_key="api_key_env",
        default=DEFAULT_API_KEY_ENV,
    )
    base_url = resolve_provider_setting(
        explicit=args.base_url,
        env_name="FICTIONOPS_CHAT_BASE_URL",
        request=request,
        request_key="base_url",
        provider=provider,
        preset_key="base_url",
        default=DEFAULT_BASE_URL,
    )
    model = choose_model(request, args.model, args.model_env)
    if args.dry_run:
        print(
            build_dry_run_output(
                payload,
                request,
                provider=provider,
                model=model,
                base_url=base_url,
                api_key_env=api_key_env,
                timeout=args.timeout,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                max_output_chars=args.max_output_chars,
            )
        )
        return 0

    api_key = os.environ.get(api_key_env, "").strip() if api_key_env else ""
    if api_key_env and not api_key:
        raise ValueError(f"missing API key environment variable: {api_key_env}")
    text = call_chat_completions(
        payload=payload,
        model=model,
        api_key=api_key,
        base_url=base_url,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        max_output_chars=args.max_output_chars,
    )
    print(text.rstrip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"agent_runner_openai_chat: {exc}", file=sys.stderr)
        raise SystemExit(1)
