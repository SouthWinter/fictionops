from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .agent_author_guards import load_author_guard_registry
from .agent_counterevidence_apply import COUNTEREVIDENCE_APPLICATION_SCHEMA
from .agent_issue_ledger import load_issue_ledger


COUNTEREVIDENCE_REVISER_QUEUE_SCHEMA = "fictionops.counterevidence_reviser_queue.v1"
COUNTEREVIDENCE_REVISION_BUNDLE_SCHEMA = "fictionops.counterevidence_revision_bundle.v1"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def _active_guards(chapter_file: Path) -> list[dict[str, Any]]:
    registry = load_author_guard_registry(chapter_file)
    return [
        {
            "guard_id": item.get("guard_id"),
            "kind": item.get("kind"),
            "statement": item.get("statement"),
            "source": item.get("source"),
        }
        for item in registry.get("guards") or []
        if isinstance(item, dict) and str(item.get("status")) == "active"
    ]


def prepare_counterevidence_revision_bundle(
    run_dir: Path,
    *,
    out_dir: Path | None = None,
    provider: str | None = None,
    model: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    if not run_dir.is_dir():
        raise ValueError("run_dir must be an existing revision run directory")
    application_file = run_dir / "counterevidence_application.json"
    queue_file = run_dir / "counterevidence_reviser_queue.json"
    if not application_file.is_file() or not queue_file.is_file():
        raise ValueError("run_dir has no applied counterevidence application and reviser queue")
    application = _read_json(application_file)
    queue = _read_json(queue_file)
    if application.get("schema") != COUNTEREVIDENCE_APPLICATION_SCHEMA or not bool(application.get("applied")):
        raise ValueError("counterevidence application must be applied before revision preparation")
    if application.get("manuscript_edited") is not False:
        raise ValueError("counterevidence application does not preserve the manuscript boundary")
    if queue.get("schema") != COUNTEREVIDENCE_REVISER_QUEUE_SCHEMA:
        raise ValueError(f"reviser queue must declare schema {COUNTEREVIDENCE_REVISER_QUEUE_SCHEMA}")
    source_application = Path(str(queue.get("source_application") or "")).expanduser().resolve()
    if source_application != application_file:
        raise ValueError("reviser queue does not reference this counterevidence application")
    queue_ids = [str(item) for item in queue.get("issue_ids") or []]
    application_ids = [str(item) for item in application.get("upheld_issue_ids") or []]
    if len(queue_ids) != len(set(queue_ids)) or queue_ids != application_ids:
        raise ValueError("reviser queue does not exactly match grounded upheld application issues")
    if int(queue.get("issue_count") or 0) != len(queue_ids) or not queue_ids:
        raise ValueError("counterevidence reviser queue contains no grounded uphold issues")

    chapter_file = Path(str(application.get("chapter_file") or "")).expanduser().resolve()
    expected_hash = str(application.get("source_sha256") or "")
    if not chapter_file.is_file() or _sha256(chapter_file) != expected_hash:
        raise ValueError("source chapter is stale relative to the counterevidence application")
    ledger = load_issue_ledger(chapter_file)
    ledger_by_id = {
        str(item.get("issue_id") or ""): item
        for item in ledger.get("issues") or []
        if isinstance(item, dict)
    }
    issues: list[dict[str, Any]] = []
    for issue_id in queue_ids:
        issue = ledger_by_id.get(issue_id)
        if issue is None:
            raise ValueError(f"queued counterevidence issue is missing from the ledger: {issue_id}")
        counterevidence = issue.get("counterevidence") if isinstance(issue.get("counterevidence"), dict) else {}
        grounded = [str(item) for item in counterevidence.get("grounded_evidence") or [] if str(item).strip()]
        if str(issue.get("status")) != "open" or str(counterevidence.get("effective_verdict")) != "uphold" or not grounded:
            raise ValueError(f"queued issue is no longer a grounded open uphold: {issue_id}")
        issues.append(
            {
                "issue_id": issue_id,
                "category": issue.get("category"),
                "severity": issue.get("severity"),
                "problem": issue.get("problem") or issue.get("why_it_matters"),
                "grounded_evidence": grounded,
                "suggested_action": issue.get("suggested_action"),
                "preserve_constraints": issue.get("preserve_constraints") or [],
                "reverification_reason": counterevidence.get("reason"),
                "reverification_report_sha256": counterevidence.get("report_sha256"),
            }
        )

    output_dir = (out_dir.expanduser().resolve() if out_dir else run_dir / "counterevidence_revision_bundle")
    artifact_names = ["README.md", "request.json", "prompt.md", "context_pack.md", "issue_contract.json", "source_manifest.json"]
    if output_dir.exists() and not force:
        existing = next((output_dir / name for name in artifact_names if (output_dir / name).exists()), None)
        if existing:
            raise FileExistsError(existing)
    output_dir.mkdir(parents=True, exist_ok=True)
    guards = _active_guards(chapter_file)
    source_text = chapter_file.read_text(encoding="utf-8-sig")
    issue_contract = {
        "schema": "fictionops.counterevidence_revision_contract.v1",
        "chapter_file": str(chapter_file),
        "source_sha256": expected_hash,
        "application_file": str(application_file),
        "application_sha256": _sha256(application_file),
        "queue_file": str(queue_file),
        "queue_sha256": _sha256(queue_file),
        "issue_count": len(issues),
        "issues": issues,
        "active_author_guards": guards,
        "scope": {
            "review_again": False,
            "allowed_issue_ids": queue_ids,
            "unrelated_edits_allowed": False,
            "new_canon_allowed": False,
        },
    }
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(chapter_file),
        "role": "counterevidence-reviser",
        "role_name": "Grounded Counterevidence Reviser",
        "task": "bounded-revision",
        "book": chapter_file.parent.name,
        "chapter": chapter_file.name,
        "provider": provider or "configurable",
        "model": model or "configured-revision-model",
        "issue_count": len(issues),
        "allowed_issue_ids": queue_ids,
        "files": [
            {"kind": "prompt", "path": str(output_dir / "prompt.md")},
            {"kind": "context_pack", "path": str(output_dir / "context_pack.md")},
            {"kind": "issue_contract", "path": str(output_dir / "issue_contract.json")},
            {"kind": "source_manifest", "path": str(output_dir / "source_manifest.json")},
        ],
        "next_actions": [
            f'fictionops agent-exec "{output_dir}" --runner ...',
            f'fictionops agent-inbox "{output_dir}"',
        ],
        "safety": {
            "calls_model": False,
            "stores_api_keys": False,
            "overwrites_manuscript": False,
            "requires_human_apply": True,
            "reruns_full_review": False,
        },
    }
    prompt = """# Grounded Counterevidence Revision

Revise the supplied chapter only for the issue contracts listed below.

Rules:
1. Address every allowed issue id, and no other issue.
2. Treat grounded evidence as the repair anchor. Do not perform a new chapter review.
3. Preserve unrelated wording, scene order, character intent, information boundaries, and all active author guards.
4. Make the smallest natural prose change that resolves each problem. Do not add new canon or explanatory narration merely to prove the fix.
5. Return the complete revised chapter only. Do not include analysis, issue labels, Markdown fences, or a change log.
"""
    context_lines = [
        "# Minimal Revision Context",
        "",
        "## Allowed Issue Contracts",
        "",
        "```json",
        json.dumps({"issue_count": len(issues), "issues": issues}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Active Author Guards",
        "",
        "```json",
        json.dumps(guards, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Source Chapter",
        "",
        source_text.rstrip(),
    ]
    source_manifest = {
        "schema": "fictionops.counterevidence_revision_source.v1",
        "source_file": str(chapter_file),
        "source_sha256": expected_hash,
        "source_chars": len(source_text),
        "manuscript_edited": False,
    }
    readme = f"""# FictionOps Minimal Counterevidence Reviser Bundle

- Source: `{chapter_file}`
- Grounded uphold issues: {len(issues)}
- Full review rerun: no
- Manuscript edited during preparation: no

Run this staged bundle with:

`fictionops agent-exec "{output_dir}" --runner ...`

Inspect the candidate with `fictionops agent-inbox "{output_dir}"`. Applying it still requires the normal verification and author boundary.
"""
    _write_text(output_dir / "README.md", readme)
    _write_text(output_dir / "request.json", json.dumps(request, ensure_ascii=False, indent=2))
    _write_text(output_dir / "prompt.md", prompt)
    _write_text(output_dir / "context_pack.md", "\n".join(context_lines))
    _write_text(output_dir / "issue_contract.json", json.dumps(issue_contract, ensure_ascii=False, indent=2))
    _write_text(output_dir / "source_manifest.json", json.dumps(source_manifest, ensure_ascii=False, indent=2))
    artifact_hashes = {name: _sha256(output_dir / name) for name in artifact_names}
    report = {
        "schema": COUNTEREVIDENCE_REVISION_BUNDLE_SCHEMA,
        "run_dir": str(run_dir),
        "output_dir": str(output_dir),
        "chapter_file": str(chapter_file),
        "source_sha256": expected_hash,
        "issue_count": len(issues),
        "included_issue_ids": queue_ids,
        "active_author_guard_count": len(guards),
        "artifact_sha256": artifact_hashes,
        "agent_exec_compatible": True,
        "reran_full_review": False,
        "manuscript_edited": False,
    }
    _write_text(output_dir / "bundle_manifest.json", json.dumps(report, ensure_ascii=False, indent=2))
    return report


def render_counterevidence_revision_bundle(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported counterevidence revision output format: {output_format}")
    return "\n".join(
        [
            "# FictionOps Minimal Counterevidence Reviser Bundle",
            "",
            f"- Bundle: `{payload['output_dir']}`",
            f"- Grounded uphold issues: {payload['issue_count']}",
            "- Full review rerun: no",
            "- Manuscript edited: no",
            "- Compatible with agent-exec: yes",
        ]
    ) + "\n"
