from __future__ import annotations

import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .agent_author_guards import load_author_guard_registry
from .agent_exec import parse_runner_receipt, runner_environment
from .agent_issue_ledger import load_issue_ledger, transition_issue, utc_now
from .agent_revision_accept import atomic_apply_text


COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA = "fictionops.counterevidence_candidate_verification.v1"
COUNTEREVIDENCE_CANDIDATE_ACCEPTANCE_SCHEMA = "fictionops.counterevidence_candidate_acceptance.v1"
COUNTEREVIDENCE_CANDIDATE_REPAIR_SCHEMA = "fictionops.counterevidence_candidate_repair.v1"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _load_candidate_bundle(bundle_dir: Path) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    bundle_dir = bundle_dir.expanduser().resolve()
    manifest_file = bundle_dir / "bundle_manifest.json"
    contract_file = bundle_dir / "issue_contract.json"
    candidate_file = bundle_dir / "output.md"
    if not manifest_file.is_file() or not contract_file.is_file() or not candidate_file.is_file():
        raise ValueError("candidate bundle must contain bundle_manifest.json, issue_contract.json, and output.md")
    manifest = _read_json(manifest_file)
    contract = _read_json(contract_file)
    if manifest.get("schema") != "fictionops.counterevidence_revision_bundle.v1":
        raise ValueError("invalid counterevidence revision bundle schema")
    if contract.get("schema") != "fictionops.counterevidence_revision_contract.v1":
        raise ValueError("invalid counterevidence revision contract schema")
    for name, expected in (manifest.get("artifact_sha256") or {}).items():
        path = bundle_dir / str(name)
        if not path.is_file() or _sha256(path) != str(expected):
            raise ValueError(f"counterevidence bundle artifact is stale: {name}")
    source_file = Path(str(contract.get("chapter_file") or "")).expanduser().resolve()
    expected_source = str(contract.get("source_sha256") or "")
    if not source_file.is_file() or _sha256(source_file) != expected_source:
        raise ValueError("source chapter changed after counterevidence bundle preparation")
    current_guards = [
        {
            "guard_id": item.get("guard_id"),
            "kind": item.get("kind"),
            "statement": item.get("statement"),
            "source": item.get("source"),
        }
        for item in load_author_guard_registry(source_file).get("guards") or []
        if isinstance(item, dict) and str(item.get("status")) == "active"
    ]
    if current_guards != (contract.get("active_author_guards") or []):
        raise ValueError("active author guards changed after counterevidence bundle preparation")
    if not candidate_file.read_text(encoding="utf-8-sig").strip():
        raise ValueError("counterevidence candidate is empty")
    return manifest, contract, source_file, candidate_file


def _candidate_diff(source: str, candidate: str) -> str:
    return "".join(
        difflib.unified_diff(
            source.splitlines(keepends=True),
            candidate.splitlines(keepends=True),
            fromfile="source.md",
            tofile="candidate.md",
        )
    )


def _bounded_change_metrics(source: str, candidate: str, issue_count: int) -> dict[str, Any]:
    diff = _candidate_diff(source, candidate)
    changed_lines = sum(
        1
        for line in diff.splitlines()
        if (line.startswith("+") or line.startswith("-")) and not line.startswith(("+++", "---"))
    )
    matcher = difflib.SequenceMatcher(a=source, b=candidate, autojunk=False)
    changed_chars = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal")
    change_ratio = changed_chars / max(len(source), len(candidate), 1)
    source_title = next((line for line in source.splitlines() if line.strip()), "")
    candidate_title = next((line for line in candidate.splitlines() if line.strip()), "")
    line_limit = max(8, issue_count * 12)
    ratio_limit = min(0.6, 0.2 + issue_count * 0.1)
    return {
        "changed_line_count": changed_lines,
        "changed_line_limit": line_limit,
        "changed_chars": changed_chars,
        "change_ratio": round(change_ratio, 6),
        "change_ratio_limit": ratio_limit,
        "title_preserved": source_title == candidate_title,
        "passed": changed_lines <= line_limit and change_ratio <= ratio_limit and source_title == candidate_title,
    }


def _new_local_repetition_regressions(source: str, candidate: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"(?P<phrase>[\u4e00-\u9fff]{2,10}|[A-Za-z]+(?:\s+[A-Za-z]+){0,3})[。！？.!?；;，,]\s*(?P=phrase)",
        flags=re.IGNORECASE,
    )

    def matches(text: str) -> dict[str, str]:
        found: dict[str, str] = {}
        for match in pattern.finditer(text):
            phrase = re.sub(r"\s+", " ", match.group("phrase")).casefold()
            start, end = max(0, match.start() - 24), min(len(text), match.end() + 24)
            found.setdefault(phrase, text[start:end].replace("\n", " "))
        return found

    before = matches(source)
    after = matches(candidate)
    return [
        {
            "kind": "new_sentence_boundary_repetition",
            "phrase": phrase,
            "forbidden_sequence": f"{phrase}。{phrase}",
            "evidence": context,
        }
        for phrase, context in after.items()
        if phrase not in before
    ]


def _verification_prompt(contract: dict[str, Any], diff: str) -> str:
    issue_ids = [str(item.get("issue_id") or "") for item in contract.get("issues") or [] if isinstance(item, dict)]
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "verify_only",
        "role": "independent-counterevidence-candidate-verifier",
        "task": "bounded-revision-verification",
        "provider": "configurable",
        "model": "auditor",
    }
    output = {
        "schema": COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA,
        "decisions": [
            {
                "issue_id": issue_id,
                "resolved": False,
                "candidate_evidence": ["exact quotation from candidate"],
                "reason": "why the candidate does or does not resolve this issue",
            }
            for issue_id in issue_ids
        ],
        "unrelated_changes": [{"source": "exact old quote", "candidate": "exact new quote", "reason": "why unrelated"}],
        "active_author_guards_preserved": False,
        "new_canon_added": False,
        "overall_pass": False,
        "summary": "brief conclusion",
    }
    return "\n\n".join(
        [
            "# FictionOps Independent Counterevidence Candidate Verification",
            "## Request\n```json\n" + json.dumps(request, ensure_ascii=False, indent=2) + "\n```",
            "Judge only whether the staged candidate satisfies the listed issue contracts without unrelated edits. The unified diff is the complete change surface; unchanged chapter text is intentionally omitted. Do not rewrite prose. Do not invent defects.",
            "Every candidate_evidence quote must occur exactly on an added diff line. Return one decision for every allowed issue id and no other id. overall_pass may be true only when all issues are resolved, unrelated_changes is empty, all active author guards are preserved, and no new canon was added.",
            "## Contract\n```json\n" + json.dumps(contract, ensure_ascii=False, indent=2) + "\n```",
            "## Complete Change Surface\n```diff\n" + diff + "\n```",
            "## Output Contract\nReturn exactly one JSON object and no Markdown fence:\n" + json.dumps(output, ensure_ascii=False, indent=2),
        ]
    ).rstrip() + "\n"


def _parse_verification(text: str, issue_ids: list[str]) -> dict[str, Any]:
    cleaned = text.strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("candidate verifier did not return a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict) or payload.get("schema") != COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA:
        raise ValueError(f"candidate verifier must declare schema {COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA}")
    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or [str(item.get("issue_id") or "") for item in decisions if isinstance(item, dict)] != issue_ids:
        raise ValueError("candidate verifier decisions must exactly match ordered contract issue ids")
    for item in decisions:
        if not isinstance(item, dict) or not isinstance(item.get("resolved"), bool):
            raise ValueError("candidate verifier resolved values must be booleans")
        evidence = item.get("candidate_evidence")
        if not isinstance(evidence, list) or not all(isinstance(quote, str) for quote in evidence):
            raise ValueError("candidate verifier evidence must be a string array")
    unrelated = payload.get("unrelated_changes")
    if not isinstance(unrelated, list):
        raise ValueError("candidate verifier unrelated_changes must be an array")
    for key in ("active_author_guards_preserved", "new_canon_added", "overall_pass"):
        if not isinstance(payload.get(key), bool):
            raise ValueError(f"candidate verifier {key} must be boolean")
    return payload


def verify_counterevidence_candidate(
    bundle_dir: Path,
    *,
    runner: list[str],
    timeout_seconds: int = 300,
    force: bool = False,
) -> dict[str, Any]:
    if timeout_seconds <= 0:
        raise ValueError("counterevidence candidate verification timeout must be positive")
    manifest, contract, source_file, candidate_file = _load_candidate_bundle(bundle_dir)
    bundle_dir = bundle_dir.expanduser().resolve()
    verification_file = bundle_dir / "counterevidence_verification.json"
    if verification_file.exists() and not force:
        raise FileExistsError(verification_file)
    source = source_file.read_text(encoding="utf-8-sig")
    candidate = candidate_file.read_text(encoding="utf-8-sig")
    diff = _candidate_diff(source, candidate)
    issue_ids = [str(item.get("issue_id") or "") for item in contract.get("issues") or [] if isinstance(item, dict)]
    if not issue_ids or not diff:
        raise ValueError("candidate must contain a change for at least one contracted issue")
    change_scope = _bounded_change_metrics(source, candidate, len(issue_ids))
    local_prose_regressions = _new_local_repetition_regressions(source, candidate)
    common = {
        "schema": COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA,
        "bundle_dir": str(bundle_dir),
        "bundle_manifest_sha256": _sha256(bundle_dir / "bundle_manifest.json"),
        "contract_sha256": _sha256(bundle_dir / "issue_contract.json"),
        "source_file": str(source_file),
        "source_sha256": _sha256(source_file),
        "candidate_file": str(candidate_file),
        "candidate_sha256": _sha256(candidate_file),
        "issue_ids": issue_ids,
        "bounded_change_scope": change_scope,
        "local_prose_regressions": local_prose_regressions,
        "diff": diff,
        "manuscript_edited": False,
    }
    if not change_scope["passed"] or local_prose_regressions:
        reasons = []
        if not change_scope["passed"]:
            reasons.append("candidate exceeds the bounded deterministic change envelope")
        if local_prose_regressions:
            reasons.append("candidate introduces a local prose regression")
        report = {
            **common,
            "verification_mode": "deterministic_preflight",
            "model_call_count": 0,
            "decisions": [],
            "unrelated_changes": [],
            "active_author_guards_preserved": None,
            "new_canon_added": None,
            "model_overall_pass": None,
            "deterministic_grounding_pass": False,
            "status": "needs_revision_attention",
            "ready_for_approval": False,
            "summary": "; ".join(reasons),
            "prompt_sha256": None,
            "attempt": None,
            "telemetry": None,
            "verified_at": utc_now(),
        }
        _write_json(verification_file, report)
        return report
    if not runner:
        raise ValueError("counterevidence candidate verification requires an independent runner after deterministic preflight passes")
    prompt = _verification_prompt(contract, diff)
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
        raise RuntimeError(f"candidate verifier failed with {completed.returncode}: {(completed.stderr or completed.stdout)[:600]}")
    attempts_dir = bundle_dir / "verification_attempts"
    attempts_dir.mkdir(parents=True, exist_ok=True)
    attempt_number = len(list(attempts_dir.glob("attempt-*.raw.txt"))) + 1
    attempt_stem = f"attempt-{attempt_number:03d}"
    raw_file = attempts_dir / f"{attempt_stem}.raw.txt"
    stderr_file = attempts_dir / f"{attempt_stem}.stderr.txt"
    raw_file.write_text(completed.stdout, encoding="utf-8", newline="\n")
    stderr_file.write_text(completed.stderr, encoding="utf-8", newline="\n")
    model = _parse_verification(completed.stdout, issue_ids)
    grounded_decisions: list[dict[str, Any]] = []
    for item in model["decisions"]:
        quotes = [quote.strip() for quote in item.get("candidate_evidence") or [] if quote.strip()]
        grounded = [quote for quote in quotes if quote in candidate]
        grounded_decisions.append({**item, "grounded_candidate_evidence": grounded, "evidence_grounded": bool(grounded)})
    deterministic_pass = (
        all(item["resolved"] and item["evidence_grounded"] for item in grounded_decisions)
        and not model["unrelated_changes"]
        and model["active_author_guards_preserved"]
        and not model["new_canon_added"]
        and change_scope["passed"]
        and not local_prose_regressions
    )
    ready = bool(model["overall_pass"]) and deterministic_pass
    report = {
        **common,
        "verification_mode": "delta_only_model",
        "model_call_count": 1,
        "decisions": grounded_decisions,
        "unrelated_changes": model["unrelated_changes"],
        "active_author_guards_preserved": model["active_author_guards_preserved"],
        "new_canon_added": model["new_canon_added"],
        "model_overall_pass": model["overall_pass"],
        "deterministic_grounding_pass": deterministic_pass,
        "status": "ready_for_approval" if ready else "needs_revision_attention",
        "ready_for_approval": ready,
        "summary": model.get("summary"),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_chars": len(prompt),
        "attempt": {
            "number": attempt_number,
            "raw_file": str(raw_file),
            "raw_sha256": _sha256(raw_file),
            "stderr_file": str(stderr_file),
            "stderr_sha256": _sha256(stderr_file),
        },
        "telemetry": parse_runner_receipt(completed.stderr),
        "verified_at": utc_now(),
    }
    _write_json(verification_file, report)
    return report


def _repair_prompt(candidate: str, regressions: list[dict[str, Any]]) -> str:
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "repair_only",
        "role": "bounded-candidate-local-repairer",
        "task": "repair-verification-regression",
        "provider": "configurable",
        "model": "writer",
    }
    output = {
        "schema": COUNTEREVIDENCE_CANDIDATE_REPAIR_SCHEMA,
        "repairs": [{"old_quote": "exact unique quote from candidate", "new_quote": "natural replacement", "reason": "brief reason"}],
    }
    return "\n\n".join(
        [
            "# FictionOps Local Candidate Repair",
            "## Request\n```json\n" + json.dumps(request, ensure_ascii=False, indent=2) + "\n```",
            "Repair only the listed local prose regressions. Return one exact old_quote/new_quote replacement per regression. The old quote must occur exactly once in the candidate. Keep the replacement local and preserve meaning, viewpoint, facts, and all surrounding prose. Do not return a full chapter.",
            "## Regressions\n```json\n" + json.dumps(regressions, ensure_ascii=False, indent=2) + "\n```",
            "## Candidate\n" + candidate,
            "## Output Contract\nReturn exactly one JSON object and no Markdown fence:\n" + json.dumps(output, ensure_ascii=False, indent=2),
        ]
    ).rstrip() + "\n"


def _parse_repair(text: str, expected_count: int) -> dict[str, Any]:
    cleaned = text.strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("candidate repairer did not return a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict) or payload.get("schema") != COUNTEREVIDENCE_CANDIDATE_REPAIR_SCHEMA:
        raise ValueError(f"candidate repairer must declare schema {COUNTEREVIDENCE_CANDIDATE_REPAIR_SCHEMA}")
    repairs = payload.get("repairs")
    if not isinstance(repairs, list) or len(repairs) != expected_count:
        raise ValueError("candidate repairer must return exactly one repair per regression")
    for item in repairs:
        if not isinstance(item, dict):
            raise ValueError("candidate repairs must be objects")
        old_quote = str(item.get("old_quote") or "")
        new_quote = str(item.get("new_quote") or "")
        if not old_quote.strip() or not new_quote.strip() or old_quote == new_quote:
            raise ValueError("candidate repair quotes must be nonempty and different")
    return payload


def repair_counterevidence_candidate(
    bundle_dir: Path,
    *,
    runner: list[str],
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    if not runner:
        raise ValueError("counterevidence candidate repair requires a runner")
    if timeout_seconds <= 0:
        raise ValueError("counterevidence candidate repair timeout must be positive")
    _, contract, source_file, candidate_file = _load_candidate_bundle(bundle_dir)
    bundle_dir = bundle_dir.expanduser().resolve()
    verification_file = bundle_dir / "counterevidence_verification.json"
    verification = _read_json(verification_file)
    if verification.get("schema") != COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA or verification.get("ready_for_approval"):
        raise ValueError("candidate repair requires a failed counterevidence verification")
    if _sha256(candidate_file) != str(verification.get("candidate_sha256") or ""):
        raise ValueError("candidate changed after failed verification; verify it again before repair")
    regressions = [item for item in verification.get("local_prose_regressions") or [] if isinstance(item, dict)]
    if not regressions:
        raise ValueError("failed verification has no locally repairable prose regression")
    candidate = candidate_file.read_text(encoding="utf-8-sig")
    prompt = _repair_prompt(candidate, regressions)
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
        raise RuntimeError(f"candidate repairer failed with {completed.returncode}: {(completed.stderr or completed.stdout)[:600]}")
    attempts_dir = bundle_dir / "repair_attempts"
    attempts_dir.mkdir(parents=True, exist_ok=True)
    attempt_number = len(list(attempts_dir.glob("attempt-*.raw.txt"))) + 1
    stem = f"attempt-{attempt_number:03d}"
    raw_file = attempts_dir / f"{stem}.raw.txt"
    stderr_file = attempts_dir / f"{stem}.stderr.txt"
    prior_file = attempts_dir / f"{stem}.candidate-before.md"
    raw_file.write_text(completed.stdout, encoding="utf-8", newline="\n")
    stderr_file.write_text(completed.stderr, encoding="utf-8", newline="\n")
    prior_file.write_text(candidate, encoding="utf-8", newline="\n")
    parsed = _parse_repair(completed.stdout, len(regressions))
    repaired = candidate
    applied_repairs: list[dict[str, Any]] = []
    for item, regression in zip(parsed["repairs"], regressions):
        old_quote = str(item["old_quote"])
        new_quote = str(item["new_quote"])
        if repaired.count(old_quote) != 1:
            raise ValueError("candidate repair old_quote must occur exactly once")
        forbidden = str(regression.get("forbidden_sequence") or "")
        if forbidden and forbidden in new_quote:
            raise ValueError("candidate repair preserves the forbidden local sequence")
        if len(new_quote) > max(len(old_quote) * 2, len(old_quote) + 120):
            raise ValueError("candidate repair replacement exceeds the local scope limit")
        repaired = repaired.replace(old_quote, new_quote, 1)
        applied_repairs.append({"old_quote": old_quote, "new_quote": new_quote, "reason": item.get("reason")})
    source = source_file.read_text(encoding="utf-8-sig")
    remaining = _new_local_repetition_regressions(source, repaired)
    if remaining:
        raise ValueError("candidate repair still contains a new local prose regression")
    scope = _bounded_change_metrics(source, repaired, int(contract.get("issue_count") or 1))
    if not scope["passed"]:
        raise ValueError("candidate repair exceeds the bounded change scope")
    candidate_file.write_text(repaired.rstrip() + "\n", encoding="utf-8", newline="\n")
    report = {
        "schema": COUNTEREVIDENCE_CANDIDATE_REPAIR_SCHEMA,
        "bundle_dir": str(bundle_dir),
        "candidate_sha256_before": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
        "candidate_sha256_after": _sha256(candidate_file),
        "repair_count": len(applied_repairs),
        "repairs": applied_repairs,
        "remaining_local_prose_regressions": remaining,
        "bounded_change_scope": scope,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "raw_file": str(raw_file),
        "raw_sha256": _sha256(raw_file),
        "telemetry": parse_runner_receipt(completed.stderr),
        "manuscript_edited": False,
        "next_action": "verify_counterevidence_revision",
    }
    _write_json(bundle_dir / "counterevidence_repair.json", report)
    return report


def accept_counterevidence_candidate(bundle_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    manifest, contract, source_file, candidate_file = _load_candidate_bundle(bundle_dir)
    bundle_dir = bundle_dir.expanduser().resolve()
    verification_file = bundle_dir / "counterevidence_verification.json"
    acceptance_file = bundle_dir / "counterevidence_acceptance.json"
    if acceptance_file.exists() and not dry_run:
        raise FileExistsError(acceptance_file)
    verification = _read_json(verification_file)
    if verification.get("schema") != COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA or not verification.get("ready_for_approval"):
        raise ValueError("counterevidence candidate has not passed independent verification")
    if _sha256(bundle_dir / "bundle_manifest.json") != str(verification.get("bundle_manifest_sha256")):
        raise ValueError("bundle manifest changed after candidate verification")
    if _sha256(bundle_dir / "issue_contract.json") != str(verification.get("contract_sha256")):
        raise ValueError("issue contract changed after candidate verification")
    if _sha256(source_file) != str(verification.get("source_sha256")):
        raise ValueError("source chapter changed after candidate verification")
    if _sha256(candidate_file) != str(verification.get("candidate_sha256")):
        raise ValueError("candidate changed after independent verification")
    issue_ids = [str(item) for item in verification.get("issue_ids") or []]
    ledger = load_issue_ledger(source_file)
    by_id = {str(item.get("issue_id") or ""): item for item in ledger.get("issues") or [] if isinstance(item, dict)}
    for issue_id in issue_ids:
        issue = by_id.get(issue_id)
        counterevidence = issue.get("counterevidence") if isinstance((issue or {}).get("counterevidence"), dict) else {}
        if issue is None or str(issue.get("status")) != "open" or str(counterevidence.get("effective_verdict")) != "uphold":
            raise ValueError(f"issue is no longer an open grounded uphold: {issue_id}")
    report = {
        "schema": COUNTEREVIDENCE_CANDIDATE_ACCEPTANCE_SCHEMA,
        "bundle_dir": str(bundle_dir),
        "source_file": str(source_file),
        "source_sha256_before": _sha256(source_file),
        "candidate_file": str(candidate_file),
        "candidate_sha256": _sha256(candidate_file),
        "issue_ids": issue_ids,
        "dry_run": dry_run,
        "applied": False,
        "accepted_at": None,
    }
    if not dry_run:
        atomic_apply_text(source_file, candidate_file.read_text(encoding="utf-8-sig"), bundle_dir.name)
        if _sha256(source_file) != report["candidate_sha256"]:
            raise RuntimeError("source hash did not match candidate after atomic apply")
        for issue_id in issue_ids:
            transition_issue(source_file, issue_id=issue_id, to_status="addressed", reason="bounded counterevidence candidate applied", actor="controller", session_id=bundle_dir.name)
            transition_issue(source_file, issue_id=issue_id, to_status="verified", reason="independent candidate verification passed", actor="counterevidence-verifier", session_id=bundle_dir.name)
            transition_issue(source_file, issue_id=issue_id, to_status="accepted", reason="author invoked counterevidence accept-revision", actor="author", session_id=bundle_dir.name)
        report.update({"applied": True, "accepted_at": utc_now(), "source_sha256_after": _sha256(source_file)})
        _write_json(acceptance_file, report)
    return report


def render_counterevidence_candidate(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_format != "markdown":
        raise ValueError(f"unsupported counterevidence candidate output format: {output_format}")
    if payload.get("schema") == COUNTEREVIDENCE_CANDIDATE_VERIFICATION_SCHEMA:
        return f"# Counterevidence Candidate Verification\n\n- Status: `{payload['status']}`\n- Issues: {len(payload['issue_ids'])}\n- Manuscript edited: no\n"
    if payload.get("schema") == COUNTEREVIDENCE_CANDIDATE_REPAIR_SCHEMA:
        return f"# Counterevidence Candidate Repair\n\n- Repairs: {payload['repair_count']}\n- Manuscript edited: no\n- Next action: `{payload['next_action']}`\n"
    return f"# Counterevidence Candidate Acceptance\n\n- Dry run: {'yes' if payload['dry_run'] else 'no'}\n- Applied: {'yes' if payload['applied'] else 'no'}\n- Issues accepted: {len(payload['issue_ids'])}\n"
