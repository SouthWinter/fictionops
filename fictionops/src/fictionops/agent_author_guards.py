from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .agent_project_context import discover_project_root


AUTHOR_GUARD_SCHEMA = "fictionops.author_guard_registry.v1"
AUTHOR_GUARD_KINDS = {
    "preserve",
    "forbidden_reveal",
    "information_boundary",
    "character",
    "relationship",
    "style",
    "canon",
}
AUTHOR_GUARD_STATUSES = {"active", "retired"}
GUARD_ID_PATTERN = re.compile(r"^G-[A-Z0-9][A-Z0-9_-]{2,63}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def author_guard_registry_path(path: Path) -> Path:
    root = discover_project_root(path.expanduser().resolve())
    return root / ".fictionops" / "author_guards.json"


def empty_author_guard_registry(path: Path) -> dict[str, object]:
    root = discover_project_root(path.expanduser().resolve())
    return {
        "schema": AUTHOR_GUARD_SCHEMA,
        "project_root": str(root),
        "updated_at": None,
        "guard_count": 0,
        "guards": [],
        "events": [],
    }


def load_author_guard_registry(path: Path) -> dict[str, object]:
    registry_file = author_guard_registry_path(path)
    if not registry_file.exists():
        return empty_author_guard_registry(path)
    payload = json.loads(registry_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != AUTHOR_GUARD_SCHEMA:
        raise ValueError(f"invalid FictionOps author guard registry: {registry_file}")
    guards = payload.get("guards")
    if not isinstance(guards, list):
        raise ValueError("author guard registry guards must be a list")
    seen: set[str] = set()
    for item in guards:
        if not isinstance(item, dict):
            raise ValueError("author guards must be objects")
        guard_id = str(item.get("guard_id") or "")
        if not GUARD_ID_PATTERN.fullmatch(guard_id) or guard_id in seen:
            raise ValueError(f"invalid or duplicate author guard id: {guard_id}")
        if str(item.get("kind") or "") not in AUTHOR_GUARD_KINDS:
            raise ValueError(f"invalid author guard kind: {item.get('kind')}")
        if str(item.get("status") or "") not in AUTHOR_GUARD_STATUSES:
            raise ValueError(f"invalid author guard status: {item.get('status')}")
        seen.add(guard_id)
    return payload


def normalize_statement(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def generated_guard_id(kind: str, source: str, statement: str) -> str:
    identity = f"{kind}|{source.casefold()}|{normalize_statement(statement).casefold()}"
    return "G-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12].upper()


def write_author_guard_registry(path: Path, payload: dict[str, object]) -> Path:
    registry_file = author_guard_registry_path(path)
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    guards = [item for item in payload.get("guards") or [] if isinstance(item, dict)]
    guards.sort(key=lambda item: str(item.get("guard_id") or ""))
    payload = {
        **payload,
        "schema": AUTHOR_GUARD_SCHEMA,
        "project_root": str(discover_project_root(path.expanduser().resolve())),
        "updated_at": utc_now(),
        "guard_count": len(guards),
        "status_counts": {
            status: sum(str(item.get("status")) == status for item in guards)
            for status in sorted(AUTHOR_GUARD_STATUSES)
        },
        "guards": guards,
    }
    registry_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return registry_file


def set_author_guard(
    path: Path,
    *,
    statement: str,
    kind: str,
    source: str,
    guard_id: str | None = None,
    actor: str = "author",
) -> dict[str, object]:
    statement = normalize_statement(statement)
    source = normalize_statement(source) or "author"
    if len(statement) < 4:
        raise ValueError("author guard statement must contain at least 4 characters")
    if kind not in AUTHOR_GUARD_KINDS:
        raise ValueError(f"invalid author guard kind: {kind}")
    resolved_id = (guard_id or generated_guard_id(kind, source, statement)).strip().upper()
    if not GUARD_ID_PATTERN.fullmatch(resolved_id):
        raise ValueError("guard id must match G-[A-Z0-9][A-Z0-9_-]{2,63}")
    payload = load_author_guard_registry(path)
    guards = [item for item in payload.get("guards") or [] if isinstance(item, dict)]
    now = utc_now()
    existing = next((item for item in guards if item.get("guard_id") == resolved_id), None)
    if existing is None:
        entry = {
            "guard_id": resolved_id,
            "kind": kind,
            "statement": statement,
            "source": source,
            "authority": "author",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "history": [],
        }
        guards.append(entry)
        action = "created"
    else:
        previous = {
            key: existing.get(key)
            for key in ("kind", "statement", "source", "status", "updated_at")
        }
        existing.setdefault("history", []).append({"changed_at": now, "actor": actor, "previous": previous})
        existing.update(
            {
                "kind": kind,
                "statement": statement,
                "source": source,
                "authority": "author",
                "status": "active",
                "updated_at": now,
            }
        )
        entry = existing
        action = "updated"
    payload["guards"] = guards
    payload.setdefault("events", []).append(
        {"at": now, "actor": actor, "action": action, "guard_id": resolved_id}
    )
    write_author_guard_registry(path, payload)
    return entry


def retire_author_guard(path: Path, *, guard_id: str, reason: str, actor: str = "author") -> dict[str, object]:
    payload = load_author_guard_registry(path)
    resolved_id = guard_id.strip().upper()
    entry = next((item for item in payload.get("guards") or [] if isinstance(item, dict) and item.get("guard_id") == resolved_id), None)
    if entry is None:
        raise KeyError(f"unknown author guard id: {resolved_id}")
    if str(entry.get("status")) == "retired":
        raise ValueError(f"author guard is already retired: {resolved_id}")
    reason = normalize_statement(reason)
    if len(reason) < 4:
        raise ValueError("retirement reason must contain at least 4 characters")
    now = utc_now()
    entry.setdefault("history", []).append(
        {
            "changed_at": now,
            "actor": actor,
            "previous": {"status": entry.get("status"), "updated_at": entry.get("updated_at")},
        }
    )
    entry.update({"status": "retired", "retired_reason": reason, "updated_at": now})
    payload.setdefault("events", []).append(
        {"at": now, "actor": actor, "action": "retired", "guard_id": resolved_id, "reason": reason}
    )
    write_author_guard_registry(path, payload)
    return entry


def active_author_guards(path: Path) -> dict[str, str]:
    payload = load_author_guard_registry(path)
    return {
        str(item["guard_id"]): str(item["statement"])
        for item in payload.get("guards") or []
        if isinstance(item, dict) and item.get("status") == "active"
    }


def render_author_guard_registry(payload: dict[str, object], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported author guard format: {output_format}")
    lines = ["# FictionOps Author Guards", "", f"- Guards: {payload.get('guard_count', 0)}", ""]
    for item in payload.get("guards") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guard_id')}` [{item.get('status')}] `{item.get('kind')}`: {item.get('statement')} "
            f"(source: {item.get('source')})"
        )
    return "\n".join(lines).rstrip() + "\n"
