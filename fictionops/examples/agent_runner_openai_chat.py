#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


REQUEST_BLOCK = re.compile(r"## Request\s+```json\s*(.*?)\s*```", re.DOTALL)
PLACEHOLDER_MODELS = {"", "-", "planner", "writer", "auditor", "gpt-planner", "gpt-writer", "gpt-auditor"}


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


def choose_model(request: dict[str, object], override: str | None, env_name: str) -> str:
    candidates = [override or "", os.environ.get(env_name, ""), text_value(request, "model")]
    for candidate in candidates:
        model = (candidate or "").strip()
        if model and model.lower() not in PLACEHOLDER_MODELS:
            return model
    raise ValueError(
        f"no concrete model configured; pass --model, set {env_name}, or write a real model name into the FictionOps run request"
    )


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
) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(
            make_request_body(payload, model=model, max_tokens=max_tokens, temperature=temperature),
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "fictionops-openai-compatible-chat-runner-example",
        },
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
    return extract_choice_text(data)


def build_dry_run_output(payload: str, request: dict[str, object], model: str, base_url: str, api_key_env: str) -> str:
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
            f"- Model: `{model}`",
            f"- Endpoint: `{base_url.rstrip('/')}/chat/completions`",
            f"- API key env: `{api_key_env}`",
            f"- Input chars: {len(payload)}",
            "",
            "## Staged Result",
            "",
            "This is a connectivity dry run. It is safe to inspect with `fictionops agent-inbox`, but it is not model output.",
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
        "--model-env",
        default="FICTIONOPS_CHAT_MODEL",
        help="Environment variable used as model fallback. Default: FICTIONOPS_CHAT_MODEL.",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="Environment variable containing the API key. Default: OPENAI_API_KEY.",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.openai.com/v1",
        help="OpenAI-compatible API base URL. Default: https://api.openai.com/v1.",
    )
    parser.add_argument("--timeout", type=int, default=300, help="HTTP timeout in seconds. Default: 300.")
    parser.add_argument("--max-tokens", type=int, help="Optional Chat Completions max_tokens value.")
    parser.add_argument("--temperature", type=float, help="Optional Chat Completions temperature value.")
    parser.add_argument("--dry-run", action="store_true", help="Parse stdin and print a staged dry-run report without calling a provider.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = sys.stdin.read()
    request = extract_request(payload)
    model = choose_model(request, args.model, args.model_env)
    if args.dry_run:
        print(build_dry_run_output(payload, request, model, args.base_url, args.api_key_env))
        return 0

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"missing API key environment variable: {args.api_key_env}")
    text = call_chat_completions(
        payload=payload,
        model=model,
        api_key=api_key,
        base_url=args.base_url,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    print(text.rstrip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"agent_runner_openai_chat: {exc}", file=sys.stderr)
        raise SystemExit(1)
