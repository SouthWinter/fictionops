from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .agent_evidence_escalation import (
    ESCALATED_REVERIFICATION_SCHEMA,
    EVIDENCE_ESCALATION_SCHEMA,
    apply_reverification_grounding,
)
from .agent_issue_ledger import ISSUE_LEDGER_SCHEMA, load_issue_ledger, stable_issue_id, utc_now, write_issue_ledger


COUNTEREVIDENCE_APPLICATION_SCHEMA = "fictionops.counterevidence_application.v1"
AUTHOR_PROTECTED_STATUSES = {"accepted", "rejected", "waived"}
MACHINE_RESOLVED_STATUSES = {"addressed", "verified"}
VERDICT_STATUS = {
    "uphold": "open",
    "withdraw": "model_withdrawn",
    "still_insufficient": "evidence_blocked",
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _issue_from_sample(chapter_file: Path, sample: dict[str, Any]) -> dict[str, Any]:
    finding = sample.get("reviewer_finding") if isinstance(sample.get("reviewer_finding"), dict) else {}
    category = str(finding.get("category") or "unknown")
    semantic = {**finding, "category": category if category.startswith("semantic.") else f"semantic.{category}"}
    issue_id = str(sample.get("issue_id") or stable_issue_id(chapter_file, semantic, prefix="iss_sem"))
    return {
        "issue_id": issue_id,
        "fingerprint": hashlib.sha1(json.dumps(semantic, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
        "scope": "chapter",
        "category": semantic["category"],
        "severity": finding.get("severity") or "P2",
        "confidence": finding.get("confidence") or "medium",
        "metric_keys": finding.get("metric_keys") or [],
        "evidence": finding.get("evidence") if isinstance(finding.get("evidence"), list) else [finding.get("evidence")] if finding.get("evidence") else [],
        "why_it_matters": finding.get("why_it_matters") or finding.get("problem"),
        "problem": finding.get("problem"),
        "preserve_constraints": finding.get("preserve_constraints") or [],
        "suggested_action": finding.get("suggested_action"),
        "source": "counterevidence-reverification",
    }


def apply_counterevidence_reverification(
    reverification_file: Path,
    packet_file: Path,
    escalation_file: Path,
    run_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    reverification_file = reverification_file.expanduser().resolve()
    packet_file = packet_file.expanduser().resolve()
    escalation_file = escalation_file.expanduser().resolve()
    run_dir = run_dir.expanduser().resolve()
    report = _read_json(reverification_file)
    packet = _read_json(packet_file)
    escalation = _read_json(escalation_file)
    if report.get("schema") != ESCALATED_REVERIFICATION_SCHEMA:
        raise ValueError(f"reverification must declare schema {ESCALATED_REVERIFICATION_SCHEMA}")
    if str(report.get("packet_sha256") or "") != _sha256(packet_file):
        raise ValueError("counterevidence packet hash does not match the re-verification report")
    if escalation.get("schema") != EVIDENCE_ESCALATION_SCHEMA:
        raise ValueError(f"escalation must declare schema {EVIDENCE_ESCALATION_SCHEMA}")
    if str(report.get("escalation_sha256") or "") != _sha256(escalation_file):
        raise ValueError("counterevidence escalation hash does not match the re-verification report")
    if not run_dir.is_dir():
        raise ValueError("run_dir must be an existing revision run directory")
    application_file = run_dir / "counterevidence_application.json"
    if application_file.exists() and not dry_run:
        raise ValueError(f"counterevidence application already exists: {application_file}")
    manifest_file = run_dir / "source_manifest.json"
    session_file = run_dir / "session.json"
    if not manifest_file.is_file() or not session_file.is_file():
        raise ValueError("run_dir must contain source_manifest.json and session.json")
    manifest = _read_json(manifest_file)
    session = _read_json(session_file)
    chapter_value = str(session.get("source_file") or manifest.get("source_file") or "").strip()
    if not chapter_value:
        raise ValueError("revision run does not identify its source chapter")
    chapter_file = Path(chapter_value).expanduser().resolve()
    expected_source_hash = str(manifest.get("source_sha256") or "")
    if not chapter_file.is_file() or _sha256(chapter_file) != expected_source_hash:
        raise ValueError("source chapter is stale relative to the revision run")
    samples = {str(item.get("sample_id") or ""): item for item in packet.get("samples") or [] if isinstance(item, dict)}
    requests = {str(item.get("request_id") or ""): item for item in escalation.get("requests") or [] if isinstance(item, dict)}
    ledger = load_issue_ledger(chapter_file)
    persistent = {str(item.get("issue_id") or ""): item for item in ledger.get("issues") or [] if isinstance(item, dict)}
    now = utc_now()
    report_hash = _sha256(reverification_file)
    actions: list[dict[str, Any]] = []
    upheld_issue_ids: list[str] = []
    blocked_issue_ids: list[str] = []
    withdrawn_issue_ids: list[str] = []
    for result in report.get("results") or []:
        if not isinstance(result, dict):
            continue
        verdict = str(result.get("verdict") or "")
        if verdict not in VERDICT_STATUS:
            raise ValueError(f"unsupported effective re-verification verdict: {verdict}")
        if verdict in {"uphold", "withdraw"} and not bool(result.get("evidence_grounded")):
            raise ValueError("resolved counterevidence verdict is not grounded")
        sample_ids = [str(item) for item in result.get("sample_ids") or []]
        if not sample_ids or sample_ids[0] not in samples:
            raise ValueError("re-verification result references an unknown sample")
        request_id = str(result.get("request_id") or "")
        request = requests.get(request_id)
        if request is None or set(sample_ids) != {str(item) for item in request.get("sample_ids") or []}:
            raise ValueError("re-verification result does not match its escalation request")
        recomputed = apply_reverification_grounding(result, request, samples[sample_ids[0]])
        if recomputed["verdict"] != verdict or bool(recomputed["evidence_grounded"]) != bool(result.get("evidence_grounded")):
            raise ValueError("re-verification effective verdict does not match recomputed grounding")
        issue = _issue_from_sample(chapter_file, samples[sample_ids[0]])
        issue_id = str(issue["issue_id"])
        stored = persistent.get(issue_id)
        prior_status = str((stored or {}).get("status") or "open")
        desired_status = VERDICT_STATUS[verdict]
        action = "updated"
        effective_status = desired_status
        if prior_status in AUTHOR_PROTECTED_STATUSES:
            effective_status = prior_status
            action = "preserved_author_authority"
        elif prior_status in MACHINE_RESOLVED_STATUSES:
            effective_status = prior_status
            action = "preserved_existing_resolution"
        history_item = {
            "report_sha256": report_hash,
            "request_id": result.get("request_id"),
            "sample_ids": sample_ids,
            "model_verdict": result.get("model_verdict"),
            "effective_verdict": verdict,
            "grounded_evidence": result.get("grounded_evidence") or [],
            "reason": result.get("reason"),
            "at": now,
        }
        decisions = list((stored or {}).get("decisions") or [])
        if effective_status != prior_status:
            decisions.append(
                {
                    "from_status": prior_status,
                    "to_status": effective_status,
                    "reason": f"grounded counterevidence re-verification: {verdict}",
                    "actor": "counterevidence-controller",
                    "session_id": session.get("session_id"),
                    "at": now,
                }
            )
        updated = {
            **issue,
            **(stored or {}),
            "status": effective_status,
            "resolution": (stored or {}).get("resolution"),
            "chapter_file": str(chapter_file),
            "first_seen_at": (stored or {}).get("first_seen_at") or now,
            "last_seen_at": now,
            "first_session_id": (stored or {}).get("first_session_id") or session.get("session_id"),
            "last_session_id": session.get("session_id"),
            "decisions": decisions,
            "counterevidence": history_item,
            "counterevidence_history": [*(stored or {}).get("counterevidence_history", []), history_item],
        }
        persistent[issue_id] = updated
        if verdict == "uphold" and action == "updated":
            upheld_issue_ids.append(issue_id)
        elif verdict == "withdraw" and action == "updated":
            withdrawn_issue_ids.append(issue_id)
        elif verdict == "still_insufficient" and action == "updated":
            blocked_issue_ids.append(issue_id)
        actions.append(
            {
                "issue_id": issue_id,
                "sample_ids": sample_ids,
                "verdict": verdict,
                "prior_status": prior_status,
                "status": effective_status,
                "action": action,
            }
        )
    application = {
        "schema": COUNTEREVIDENCE_APPLICATION_SCHEMA,
        "run_dir": str(run_dir),
        "chapter_file": str(chapter_file),
        "source_sha256": expected_source_hash,
        "reverification_file": str(reverification_file),
        "reverification_sha256": report_hash,
        "packet_sha256": _sha256(packet_file),
        "escalation_sha256": _sha256(escalation_file),
        "dry_run": dry_run,
        "applied": not dry_run,
        "action_count": len(actions),
        "upheld_issue_ids": upheld_issue_ids,
        "withdrawn_issue_ids": withdrawn_issue_ids,
        "blocked_issue_ids": blocked_issue_ids,
        "actions": actions,
        "author_authority_preserved": all(item["action"] != "updated" or item["prior_status"] not in AUTHOR_PROTECTED_STATUSES for item in actions),
        "manuscript_edited": False,
        "applied_at": None if dry_run else now,
    }
    if not dry_run:
        ledger["issues"] = list(persistent.values())
        ledger_file = write_issue_ledger(chapter_file, ledger)
        issues_before_file = run_dir / "issues.before.json"
        if issues_before_file.is_file():
            run_issues = _read_json(issues_before_file)
            run_issues["issues"] = [item for item in persistent.values() if str(item.get("chapter_file") or "") == str(chapter_file)]
            run_issues["issue_count"] = len(run_issues["issues"])
            run_issues["counterevidence_application"] = str(application_file)
            issues_before_file.write_text(json.dumps(run_issues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        queue_file = run_dir / "counterevidence_reviser_queue.json"
        queue_file.write_text(
            json.dumps(
                {
                    "schema": "fictionops.counterevidence_reviser_queue.v1",
                    "issue_ids": upheld_issue_ids,
                    "issue_count": len(upheld_issue_ids),
                    "source_application": str(application_file),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        application["ledger_file"] = str(ledger_file)
        application["reviser_queue_file"] = str(queue_file)
        application_file.write_text(json.dumps(application, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return application


def render_counterevidence_application(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported counterevidence application output format: {output_format}")
    return "\n".join(
        [
            "# FictionOps Counterevidence Application",
            "",
            f"- Applied: {'yes' if payload['applied'] else 'no (dry run)'}",
            f"- Actions: {payload['action_count']}",
            f"- Open for reviser: {len(payload['upheld_issue_ids'])}",
            f"- Model withdrawn: {len(payload['withdrawn_issue_ids'])}",
            f"- Evidence blocked: {len(payload['blocked_issue_ids'])}",
            "- Manuscript edited: no",
        ]
    ) + "\n"
