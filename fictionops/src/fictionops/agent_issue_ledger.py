from __future__ import annotations

import hashlib
import difflib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .agent_project_context import discover_project_root


ISSUE_LEDGER_SCHEMA = "fictionops.issue_ledger.v1"
ISSUE_STATUSES = {
    "open",
    "planned",
    "addressed",
    "verified",
    "accepted",
    "rejected",
    "waived",
    "reopened",
    "model_withdrawn",
    "evidence_blocked",
}
AUTHOR_DECISION_STATUSES = {"rejected", "waived", "reopened"}
RESOLVED_STATUSES = {"addressed", "verified", "accepted"}
ALLOWED_TRANSITIONS = {
    "open": {"planned", "addressed", "rejected", "waived", "model_withdrawn", "evidence_blocked"},
    "planned": {"open", "addressed", "rejected", "waived"},
    "addressed": {"open", "verified", "reopened", "rejected", "waived"},
    "verified": {"accepted", "reopened", "rejected", "waived"},
    "accepted": {"reopened"},
    "rejected": {"reopened"},
    "waived": {"reopened"},
    "reopened": {"planned", "addressed", "verified", "rejected", "waived", "model_withdrawn", "evidence_blocked"},
    "model_withdrawn": {"open", "reopened", "evidence_blocked", "rejected", "waived"},
    "evidence_blocked": {"open", "reopened", "model_withdrawn", "rejected", "waived"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def issue_ledger_path(path: Path) -> Path:
    root = discover_project_root(path.expanduser().resolve())
    return root / ".fictionops" / "issues.json"


def load_issue_ledger(path: Path) -> dict[str, object]:
    root = discover_project_root(path.expanduser().resolve())
    ledger_file = issue_ledger_path(root)
    if not ledger_file.exists():
        return {
            "schema": ISSUE_LEDGER_SCHEMA,
            "project_root": str(root),
            "updated_at": None,
            "issue_count": 0,
            "issues": [],
        }
    payload = json.loads(ledger_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != ISSUE_LEDGER_SCHEMA:
        raise ValueError(f"invalid FictionOps issue ledger: {ledger_file}")
    if not isinstance(payload.get("issues"), list):
        raise ValueError(f"issue ledger issues must be a list: {ledger_file}")
    return payload


def write_issue_ledger(path: Path, payload: dict[str, object]) -> Path:
    ledger_file = issue_ledger_path(path)
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    issues = [item for item in payload.get("issues") or [] if isinstance(item, dict)]
    issues.sort(key=lambda item: (str(item.get("chapter_file") or ""), str(item.get("issue_id") or "")))
    payload.update(
        {
            "schema": ISSUE_LEDGER_SCHEMA,
            "project_root": str(discover_project_root(path.expanduser().resolve())),
            "updated_at": utc_now(),
            "issue_count": len(issues),
            "status_counts": {
                status: sum(1 for item in issues if str(item.get("status")) == status)
                for status in sorted(ISSUE_STATUSES)
            },
            "issues": issues,
        }
    )
    ledger_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return ledger_file


def _normalize(value: object, *, limit: int = 160) -> str:
    text = re.sub(r"\s+", "", str(value or "")).lower()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)
    return text[:limit]


def _evidence_anchor(issue: dict[str, object]) -> str:
    values = issue.get("evidence")
    evidence = values if isinstance(values, list) else [values]
    anchors: list[str] = []
    for item in evidence:
        if isinstance(item, dict):
            raw = item.get("text") or item.get("term") or item.get("file")
        else:
            raw = item
        normalized = _normalize(raw, limit=96)
        if len(normalized) >= 4:
            anchors.append(normalized)
    return "|".join(sorted(set(anchors))[:3])


def _evidence_anchors(issue: dict[str, object]) -> set[str]:
    return {item for item in _evidence_anchor(issue).split("|") if item}


def _metric_keys(issue: dict[str, object]) -> set[str]:
    values = issue.get("metric_keys") or ([issue.get("metric_key")] if issue.get("metric_key") else [])
    return {_normalize(item, limit=80) for item in values if _normalize(item, limit=80)}


def issues_equivalent(left: dict[str, object], right: dict[str, object]) -> bool:
    if _normalize(left.get("category"), limit=80) != _normalize(right.get("category"), limit=80):
        return False
    left_metrics, right_metrics = _metric_keys(left), _metric_keys(right)
    if left_metrics and right_metrics and left_metrics.intersection(right_metrics):
        return True
    left_evidence, right_evidence = _evidence_anchors(left), _evidence_anchors(right)
    if left_evidence and right_evidence and left_evidence.intersection(right_evidence):
        return True
    left_problem = _normalize(left.get("problem") or left.get("why_it_matters"), limit=160)
    right_problem = _normalize(right.get("problem") or right.get("why_it_matters"), limit=160)
    return bool(
        len(left_problem) >= 8
        and len(right_problem) >= 8
        and difflib.SequenceMatcher(None, left_problem, right_problem).ratio() >= 0.82
    )


def issue_fingerprint(chapter_file: Path, issue: dict[str, object]) -> str:
    category = _normalize(issue.get("category"), limit=80)
    metric_keys = issue.get("metric_keys") or ([issue.get("metric_key")] if issue.get("metric_key") else [])
    metrics = "|".join(sorted(_normalize(item, limit=80) for item in metric_keys if _normalize(item, limit=80)))
    anchor = _evidence_anchor(issue)
    fallback = _normalize(issue.get("problem") or issue.get("why_it_matters"), limit=120)
    identity = "|".join((str(chapter_file.resolve()), category, metrics, anchor or fallback))
    return hashlib.sha1(identity.encode("utf-8")).hexdigest()


def stable_issue_id(chapter_file: Path, issue: dict[str, object], *, prefix: str = "iss_sem") -> str:
    return f"{prefix}_{issue_fingerprint(chapter_file, issue)[:16]}"


def _merge_values(left: object, right: object) -> list[object]:
    result: list[object] = []
    seen: set[str] = set()
    for value in [*(left if isinstance(left, list) else []), *(right if isinstance(right, list) else [])]:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def dedupe_current_issues(chapter_file: Path, issues: list[dict[str, object]]) -> list[dict[str, object]]:
    by_id: dict[str, dict[str, object]] = {}
    severity_rank = {"P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5}
    for issue in issues:
        issue_id = str(issue.get("issue_id") or stable_issue_id(chapter_file, issue))
        equivalent = next((item for item in by_id.values() if issues_equivalent(item, issue)), None)
        if equivalent is not None:
            issue_id = str(equivalent.get("issue_id") or issue_id)
        issue["issue_id"] = issue_id
        issue["fingerprint"] = issue_fingerprint(chapter_file, issue)
        existing = by_id.get(issue_id)
        if existing is None:
            by_id[issue_id] = dict(issue)
            continue
        existing["evidence"] = _merge_values(existing.get("evidence"), issue.get("evidence"))
        existing["metric_keys"] = _merge_values(existing.get("metric_keys"), issue.get("metric_keys"))
        existing["preserve_constraints"] = _merge_values(existing.get("preserve_constraints"), issue.get("preserve_constraints"))
        if severity_rank.get(str(issue.get("severity")), 99) < severity_rank.get(str(existing.get("severity")), 99):
            existing["severity"] = issue.get("severity")
    return list(by_id.values())


def merge_issue_observations(
    chapter_file: Path,
    *,
    session_id: str,
    run_dir: Path,
    issues: list[dict[str, object]],
) -> tuple[list[dict[str, object]], Path]:
    ledger = load_issue_ledger(chapter_file)
    persistent = {
        str(item.get("issue_id")): item
        for item in ledger.get("issues") or []
        if isinstance(item, dict) and str(item.get("issue_id") or "")
    }
    observed_at = utc_now()
    current = dedupe_current_issues(chapter_file, issues)
    for issue in current:
        issue_id = str(issue["issue_id"])
        if issue_id not in persistent:
            equivalent = next(
                (
                    item
                    for item in persistent.values()
                    if str(item.get("chapter_file") or "") == str(chapter_file.resolve())
                    and issues_equivalent(item, issue)
                ),
                None,
            )
            if equivalent is not None:
                issue_id = str(equivalent.get("issue_id") or issue_id)
                issue["issue_id"] = issue_id
        previous = persistent.get(issue_id)
        previous_status = str((previous or {}).get("status") or issue.get("status") or "open")
        same_session = bool(previous and previous.get("last_session_id") == session_id)
        requested_status = str(issue.get("status") or "open")
        if same_session and requested_status in ISSUE_STATUSES:
            status = previous_status if previous_status in {"waived", "rejected"} else requested_status
        elif previous_status in RESOLVED_STATUSES:
            status = "reopened"
        elif previous_status in {"waived", "rejected"}:
            status = previous_status
        else:
            status = previous_status if previous_status in ISSUE_STATUSES else "open"
        issue["status"] = status
        issue["resolution"] = (previous or {}).get("resolution")
        observation = {
            "session_id": session_id,
            "run_dir": str(run_dir.resolve()),
            "observed_at": observed_at,
            "severity": issue.get("severity"),
            "evidence_fingerprint": hashlib.sha1(
                json.dumps(issue.get("evidence") or [], ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()[:12],
        }
        observations = list((previous or {}).get("observations") or [])
        if not any(
            isinstance(item, dict)
            and item.get("session_id") == session_id
            and item.get("evidence_fingerprint") == observation["evidence_fingerprint"]
            for item in observations
        ):
            observations.append(observation)
        decisions = list((previous or {}).get("decisions") or [])
        if not same_session and previous_status in RESOLVED_STATUSES and not any(
            isinstance(item, dict) and item.get("session_id") == session_id and item.get("to_status") == "reopened"
            for item in decisions
        ):
            decisions.append(
                {
                    "from_status": previous_status,
                    "to_status": "reopened",
                    "reason": "issue observed again in a later revision session",
                    "actor": "controller",
                    "session_id": session_id,
                    "at": observed_at,
                }
            )
        persistent[issue_id] = {
            **(previous or {}),
            **issue,
            "chapter_file": str(chapter_file.resolve()),
            "first_seen_at": (previous or {}).get("first_seen_at") or observed_at,
            "last_seen_at": observed_at,
            "first_session_id": (previous or {}).get("first_session_id") or session_id,
            "last_session_id": session_id,
            "observations": observations,
            "decisions": decisions,
        }
    ledger["issues"] = list(persistent.values())
    ledger_file = write_issue_ledger(chapter_file, ledger)
    return current, ledger_file


def transition_issue(
    path: Path,
    *,
    issue_id: str,
    to_status: str,
    reason: str,
    actor: str,
    session_id: str | None = None,
) -> dict[str, object]:
    if to_status not in ISSUE_STATUSES:
        raise ValueError(f"unsupported issue status: {to_status}")
    if not reason.strip():
        raise ValueError("issue status transitions require a reason")
    ledger = load_issue_ledger(path)
    target = next(
        (item for item in ledger.get("issues") or [] if isinstance(item, dict) and item.get("issue_id") == issue_id),
        None,
    )
    if target is None:
        raise KeyError(f"unknown issue id: {issue_id}")
    from_status = str(target.get("status") or "open")
    if from_status == to_status:
        raise ValueError(f"issue {issue_id} is already {to_status}")
    if to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        raise ValueError(f"issue transition is not allowed: {from_status} -> {to_status}")
    decision = {
        "from_status": from_status,
        "to_status": to_status,
        "reason": reason.strip(),
        "actor": actor,
        "session_id": session_id,
        "at": utc_now(),
    }
    target["status"] = to_status
    target["resolution"] = decision if to_status in {"accepted", "rejected", "waived"} else None
    target.setdefault("decisions", []).append(decision)
    write_issue_ledger(path, ledger)
    return target


def reconcile_run_issue_states(
    run_dir: Path,
    *,
    after_issue_ids: set[str] | None = None,
    semantic_passed: bool | None = None,
    accepted: bool = False,
) -> dict[str, object]:
    issues_file = run_dir / "issues.before.json"
    session_file = run_dir / "session.json"
    if not issues_file.exists() or not session_file.exists():
        return {"updated": 0}
    payload = json.loads(issues_file.read_text(encoding="utf-8"))
    session = json.loads(session_file.read_text(encoding="utf-8"))
    chapter_file = Path(str(session.get("source_file") or payload.get("chapter_file") or "")).resolve()
    session_id = str(session.get("session_id") or run_dir.name)
    updated = 0
    for issue in payload.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        issue_id = str(issue.get("issue_id") or "")
        status = str(issue.get("status") or "open")
        if status in {"waived", "rejected"}:
            continue
        target_status: str | None = None
        if accepted and status in {"addressed", "verified"}:
            target_status = "accepted"
        elif semantic_passed is not None:
            if semantic_passed and status == "addressed":
                target_status = "verified"
            elif semantic_passed and str(issue.get("source")) == "comprehensive-reviewer":
                target_status = "verified"
            elif (
                not semantic_passed
                and str(issue.get("source")) == "comprehensive-reviewer"
                and status in {"addressed", "verified"}
            ):
                target_status = "reopened"
        elif after_issue_ids is not None and not str(issue.get("category") or "").startswith("semantic."):
            target_status = "open" if issue_id in after_issue_ids else "addressed"
        if target_status and target_status != status:
            issue["status"] = target_status
            issue.setdefault("decisions", []).append(
                {
                    "from_status": status,
                    "to_status": target_status,
                    "reason": "candidate reconciliation" if not accepted else "verified candidate accepted",
                    "actor": "controller",
                    "session_id": session_id,
                    "at": utc_now(),
                }
            )
            updated += 1
    payload["updated_at"] = utc_now()
    issues_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    current, ledger_file = merge_issue_observations(
        chapter_file,
        session_id=session_id,
        run_dir=run_dir,
        issues=[item for item in payload.get("issues") or [] if isinstance(item, dict)],
    )
    # Observation merge preserves explicit author decisions; copy reconciled machine states back.
    by_id = {str(item.get("issue_id")): item for item in current}
    for issue in payload.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        merged = by_id.get(str(issue.get("issue_id")))
        if merged and str(merged.get("status")) not in {"waived", "rejected"}:
            merged["status"] = issue.get("status")
    ledger = load_issue_ledger(chapter_file)
    persistent = {str(item.get("issue_id")): item for item in ledger.get("issues") or [] if isinstance(item, dict)}
    for issue in payload.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        stored = persistent.get(str(issue.get("issue_id")))
        if stored and str(stored.get("status")) not in {"waived", "rejected"}:
            stored["status"] = issue.get("status")
            stored["resolution"] = issue.get("resolution")
            stored["decisions"] = issue.get("decisions") or stored.get("decisions") or []
    ledger_file = write_issue_ledger(chapter_file, ledger)
    return {"updated": updated, "ledger_file": str(ledger_file), "issue_count": len(payload.get("issues") or [])}


def render_issue_ledger(payload: dict[str, object], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if output_format != "markdown":
        raise ValueError(f"unsupported issue ledger format: {output_format}")
    lines = ["# FictionOps Issue Ledger", "", f"- Issues: {payload.get('issue_count', 0)}", ""]
    for issue in payload.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        lines.append(
            f"- `{issue.get('issue_id')}` [{issue.get('status')}] {issue.get('severity')} {issue.get('category')}: "
            f"{issue.get('problem') or issue.get('why_it_matters') or '-'}"
        )
    return "\n".join(lines).rstrip() + "\n"
