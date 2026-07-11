from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .agent_exec import parse_runner_receipt, runner_environment


BASELINE_SCHEMA = "fictionops.agent_review_baseline.v1"
MODES = ("raw", "rag", "workflow")
CONDITIONS = ("raw", "rag", "full", "workflow", "no_memory", "no_guard", "no_contract")


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "fictionops.agent_high_risk_review_cases.v1":
        raise ValueError("unsupported high-risk fixture schema")
    return [item for item in payload.get("cases") or [] if isinstance(item, dict)]


def baseline_prompt(case: dict[str, Any], mode: str, *, run_index: int = 1) -> str:
    if mode not in CONDITIONS:
        raise ValueError(f"unsupported baseline condition: {mode}")
    full = mode in {"full", "workflow"}
    lines = [
        "# FictionOps Anonymous Review Baseline",
        f"CASE_ID: {case.get('case_id')}",
        f"MODE: {mode}",
        f"RUN_INDEX: {run_index}",
        "## Request",
        "```json",
        json.dumps(
            {
                "schema": "fictionops.agent_research_baseline_request.v1",
                "role": "reviewer",
                "task": "benchmark-review",
                "case_id": case.get("case_id"),
                "condition": mode,
                "run_index": run_index,
            },
            ensure_ascii=False,
        ),
        "```",
        "Review the excerpt. Return one JSON object with an issues array; each issue needs category, evidence, problem, and suggested_action.",
        "Do not rewrite the excerpt.",
        "## Chapter Excerpt",
        str(case.get("chapter_excerpt") or ""),
    ]
    if mode in {"rag", "full", "workflow", "no_guard", "no_contract"}:
        lines.extend(["## Retrieved Project Context", str(case.get("project_context") or "")])
    if full or mode in {"no_memory", "no_contract"}:
        lines.extend(
            [
                "## False-Positive Guard",
                str(case.get("false_positive_guard") or ""),
            ]
        )
    if full or mode in {"no_memory", "no_guard"}:
        lines.extend(
            [
                "## Workflow Contract",
                "Classify continuity, character, information boundaries, foreshadowing, chapter function, and prose/reader experience. Ground every finding in the excerpt and preserve functional ambiguity or repetition.",
            ]
        )
    return "\n\n".join(lines).rstrip() + "\n"


def parse_review(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("baseline runner did not return a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict) or not isinstance(payload.get("issues"), list):
        raise ValueError("baseline review must contain an issues array")
    return payload


def normalize_category(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def evidence_fragments(value: object) -> list[str]:
    values = value if isinstance(value, list) else [value]
    fragments: list[str] = []
    for item in values:
        text = str(item or "").strip()
        if not text:
            continue
        fragments.append(text)
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"|‘([^’]+)’|“([^”]+)”", text)
        fragments.extend(fragment.strip() for groups in quoted for fragment in groups if len(fragment.strip()) >= 4)
    return list(dict.fromkeys(fragments))


def score_review(case: dict[str, Any], mode: str, review: dict[str, Any], telemetry: dict[str, Any] | None) -> dict[str, Any]:
    issues = [item for item in review.get("issues") or [] if isinstance(item, dict)]
    expected = str(case.get("expected_category") or "")
    accepted = {normalize_category(expected)}
    accepted.update(normalize_category(value) for value in case.get("accepted_categories") or [])
    matched = [item for item in issues if normalize_category(item.get("category")) in accepted]
    excerpt = str(case.get("chapter_excerpt") or "")
    sources = [excerpt]
    if mode in {"rag", "full", "workflow", "no_guard", "no_contract"}:
        sources.append(str(case.get("project_context") or ""))
    matched_evidence = [evidence_fragments(item.get("evidence")) for item in matched]
    grounded_issue_count = sum(
        any(fragment in source for fragment in fragments for source in sources) for fragments in matched_evidence
    )
    return {
        "case_id": case.get("case_id"),
        "mode": mode,
        "expected_category": expected,
        "accepted_categories": sorted(accepted),
        "matched_categories": [str(item.get("category") or "") for item in matched],
        "detected": bool(matched),
        "evidence_grounded": grounded_issue_count > 0,
        "matched_issue_count": len(matched),
        "grounded_issue_count": grounded_issue_count,
        "issue_count": len(issues),
        "extra_issue_count": max(0, len(issues) - len(matched)),
        "telemetry": telemetry,
    }


def run_baselines(
    fixtures: Path,
    *,
    runner: list[str],
    timeout_seconds: int = 300,
    conditions: list[str] | None = None,
    runs: int = 1,
) -> dict[str, Any]:
    if not runner:
        raise ValueError("baseline runner command is required")
    selected_conditions = conditions or list(MODES)
    invalid = [item for item in selected_conditions if item not in CONDITIONS]
    if invalid:
        raise ValueError("unsupported baseline conditions: " + ", ".join(invalid))
    if runs < 1 or runs > 50:
        raise ValueError("baseline runs must be between 1 and 50")
    rows: list[dict[str, Any]] = []
    for case in load_cases(fixtures):
        for mode in selected_conditions:
            for run_index in range(1, runs + 1):
                prompt = baseline_prompt(case, mode, run_index=run_index)
                completed = subprocess.run(
                    runner,
                    input=prompt,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    timeout=timeout_seconds,
                    env=runner_environment(),
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeError(f"baseline runner failed for {case.get('case_id')}/{mode}/run-{run_index}: {completed.stderr[:600]}")
                review = parse_review(completed.stdout)
                row = score_review(case, mode, review, parse_runner_receipt(completed.stderr))
                row["run_index"] = run_index
                row["prompt_sha256"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                row["review"] = review
                rows.append(row)
    aggregate: dict[str, Any] = {}
    for mode in selected_conditions:
        selected = [row for row in rows if row["mode"] == mode]
        input_tokens = sum(int(((row.get("telemetry") or {}).get("usage") or {}).get("input_tokens") or 0) for row in selected)
        output_tokens = sum(int(((row.get("telemetry") or {}).get("usage") or {}).get("output_tokens") or 0) for row in selected)
        costs: dict[str, float] = {}
        for row in selected:
            cost = (row.get("telemetry") or {}).get("cost") or {}
            currency = str(cost.get("currency") or "")
            if currency:
                costs[currency] = costs.get(currency, 0.0) + float(cost.get("total") or 0)
        aggregate[mode] = {
            "cases": len(selected),
            "detection_rate": sum(bool(row["detected"]) for row in selected) / len(selected) if selected else 0.0,
            "grounded_rate": sum(bool(row["evidence_grounded"]) for row in selected) / len(selected) if selected else 0.0,
            "extra_issue_count": sum(int(row["extra_issue_count"]) for row in selected),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_by_currency": {key: round(value, 12) for key, value in sorted(costs.items())},
        }
    return {
        "schema": BASELINE_SCHEMA,
        "fixtures": fixtures.as_posix(),
        "conditions": selected_conditions,
        "runs_per_case": runs,
        "rows": rows,
        "aggregate": aggregate,
    }


def render_baselines(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported baseline output format: {output_format}")
    lines = [
        "# FictionOps Agent Research Baseline",
        "",
        f"- Fixtures: `{payload['fixtures']}`",
        f"- Runs per case: {payload['runs_per_case']}",
        "",
        "| Condition | Samples | Detection | Grounded | Extra issues | Input tokens | Output tokens | Cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for condition in payload["conditions"]:
        item = payload["aggregate"][condition]
        lines.append(
            f"| `{condition}` | {item['cases']} | {item['detection_rate']:.3f} | {item['grounded_rate']:.3f} | "
            f"{item['extra_issue_count']} | {item['input_tokens']} | {item['output_tokens']} | "
            f"`{json.dumps(item['cost_by_currency'], ensure_ascii=False)}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare raw, RAG, and FictionOps workflow review baselines.")
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--conditions", default="raw,rag,full", help="Comma-separated conditions: raw,rag,full,no_memory,no_guard,no_contract.")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--runner", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args(argv)
    payload = run_baselines(
        args.fixtures,
        runner=list(args.runner),
        timeout_seconds=args.timeout_seconds,
        conditions=[item.strip() for item in args.conditions.split(",") if item.strip()],
        runs=args.runs,
    )
    rendered = render_baselines(payload, "json")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
