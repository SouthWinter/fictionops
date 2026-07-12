from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TRAJECTORY_SCHEMA = "fictionops.agent_trajectory_step.v1"
TRAJECTORY_FILE = "trajectory.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _existing_steps(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    steps: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("schema") == TRAJECTORY_SCHEMA:
            steps.append(item)
    return steps


def append_trajectory(
    run_dir: Path,
    *,
    kind: str,
    phase: str,
    actor: str,
    observation: dict[str, Any] | None = None,
    decision: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    context: list[dict[str, Any]] | None = None,
    model_call: dict[str, Any] | None = None,
    authority: str = "controller",
) -> dict[str, Any]:
    target = run_dir / TRAJECTORY_FILE
    run_dir.mkdir(parents=True, exist_ok=True)
    previous = _existing_steps(target)
    prior_phase = str(previous[-1].get("phase") or "") if previous else ""
    transition = None
    if prior_phase and phase and prior_phase != phase:
        transition = {"from": prior_phase, "to": phase}
    step = {
        "schema": TRAJECTORY_SCHEMA,
        "step_id": len(previous) + 1,
        "timestamp": _now(),
        "kind": kind,
        "phase": phase,
        "actor": actor,
        "observation": observation or {},
        "decision": decision or {},
        "action": action or {},
        "evidence": evidence or [],
        "context": context or [],
        "model_call": model_call,
        "state_transition": transition,
        "authority": authority,
    }
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(step, ensure_ascii=False) + "\n")
    return step


def context_attribution(memory_query: dict[str, Any], *, limit: int = 32) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in memory_query.get("results") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "source": item.get("source"),
                "kind": item.get("kind"),
                "authority": item.get("authority"),
                "score": item.get("score"),
                "reason": item.get("reason") or item.get("matched_terms"),
                "chars": len(str(item.get("text") or item.get("content") or "")),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def load_trajectory(run_dir: Path) -> list[dict[str, Any]]:
    return _existing_steps(run_dir / TRAJECTORY_FILE)
