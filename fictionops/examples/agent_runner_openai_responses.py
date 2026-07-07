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


def extract_response_text(data: dict[str, object]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    output = data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
    if chunks:
        return "\n\n".join(chunks).strip()
    raise ValueError("OpenAI response did not contain output_text or text content")


def make_request_body(payload: str, model: str, max_output_tokens: int | None) -> dict[str, object]:
    body: dict[str, object] = {
        "model": model,
        "input": payload,
        "instructions": (
            "You are an external FictionOps runner. Follow the FictionOps output contract. "
            "Write only staged Markdown for human review. Do not claim that manuscript or canon files were edited."
        ),
    }
    if max_output_tokens:
        body["max_output_tokens"] = max_output_tokens
    return body


def call_openai_responses(
    *,
    payload: str,
    model: str,
    api_key: str,
    base_url: str,
    timeout: int,
    max_output_tokens: int | None,
) -> str:
    endpoint = base_url.rstrip("/") + "/responses"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(make_request_body(payload, model, max_output_tokens), ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "fictionops-openai-runner-example",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API returned HTTP {exc.code}: {detail[:1200]}") from exc
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("OpenAI Responses API returned non-object JSON")
    return extract_response_text(data)


def build_dry_run_output(payload: str, request: dict[str, object], model: str, base_url: str) -> str:
    role = text_value(request, "role", "-")
    task = text_value(request, "task", "-")
    book = text_value(request, "book", "book_01")
    chapter = text_value(request, "chapter", "-")
    return "\n".join(
        [
            "# OpenAI Responses Runner Dry Run",
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
            f"- Endpoint: `{base_url.rstrip('/')}/responses`",
            f"- Input chars: {len(payload)}",
            "",
            "## Staged Result",
            "",
            "This is a connectivity dry run. It is safe to inspect with `fictionops agent-inbox`, but it is not model output.",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Example external runner that sends a FictionOps agent bundle to OpenAI Responses API."
    )
    parser.add_argument("--model", help="Concrete OpenAI model name. Overrides request.json and FICTIONOPS_OPENAI_MODEL.")
    parser.add_argument(
        "--model-env",
        default="FICTIONOPS_OPENAI_MODEL",
        help="Environment variable used as model fallback. Default: FICTIONOPS_OPENAI_MODEL.",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="Environment variable containing the OpenAI API key. Default: OPENAI_API_KEY.",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.openai.com/v1",
        help="OpenAI-compatible API base URL. Default: https://api.openai.com/v1.",
    )
    parser.add_argument("--timeout", type=int, default=300, help="HTTP timeout in seconds. Default: 300.")
    parser.add_argument("--max-output-tokens", type=int, help="Optional Responses API max_output_tokens value.")
    parser.add_argument("--dry-run", action="store_true", help="Parse stdin and print a staged dry-run report without calling OpenAI.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = sys.stdin.read()
    request = extract_request(payload)
    model = choose_model(request, args.model, args.model_env)
    if args.dry_run:
        print(build_dry_run_output(payload, request, model, args.base_url))
        return 0

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"missing OpenAI API key environment variable: {args.api_key_env}")
    text = call_openai_responses(
        payload=payload,
        model=model,
        api_key=api_key,
        base_url=args.base_url,
        timeout=args.timeout,
        max_output_tokens=args.max_output_tokens,
    )
    print(text.rstrip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"agent_runner_openai_responses: {exc}", file=sys.stderr)
        raise SystemExit(1)
