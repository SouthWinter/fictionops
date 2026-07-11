from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


CAUSAL_SIMULATION_SCHEMA = "fictionops.causal_simulation.v1"
ADVERSARIAL_REVIEW_SCHEMA = "fictionops.adversarial_draft_review.v1"
STORY_AUDIT_SCHEMA = "fictionops.deterministic_story_audit.v1"
STORY_FACT_LEDGER_SCHEMA = "fictionops.story_fact_ledger.v1"

CRITIC_PROFILES = ("continuity", "character_and_knowledge", "prose_and_reader_experience")


def parse_json_object(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model output did not contain a JSON object")
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("model output must be a JSON object")
    return payload


def review_evidence_grounding_issues(payload: dict[str, object], candidate_text: str) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    compact_candidate = re.sub(r"\s+", "", candidate_text)

    def grounded(value: str) -> bool:
        compact = re.sub(r"\s+", "", value).strip("'\"‘’“”` ")
        return len(compact) >= 4 and compact in compact_candidate

    for index, issue in enumerate(payload.get("issues") or [], start=1):
        if not isinstance(issue, dict):
            continue
        evidence = issue.get("evidence")
        values = evidence if isinstance(evidence, list) else [evidence]
        material = [str(value).strip() for value in values if str(value or "").strip()]
        if material and not any(grounded(value) for value in material):
            issues.append({"kind": "ungrounded_review_issue", "issue_index": index, "evidence": material[:3]})
    for key, identity in (("constraint_checks", "id"), ("scene_state_checks", "scene_id")):
        for item in payload.get(key) or []:
            if not isinstance(item, dict) or str(item.get("status")) == "pass":
                continue
            evidence = str(item.get("evidence") or "")
            quotations = [
                match.group(1).strip()
                for match in re.finditer(r"[‘'\"“]([^’'\"”]{4,160})[’'\"”]", evidence)
            ]
            if quotations and not any(grounded(value) for value in quotations):
                issues.append({"kind": "ungrounded_review_check", identity: item.get(identity), "quotations": quotations[:3]})
    return issues


def prepare_causal_simulation_bundle(
    run_dir: Path,
    *,
    target_file: Path,
    engine_text: str,
    outline_text: str,
    memory_text: str,
    provider: str,
    model: str,
    force: bool,
) -> Path:
    directory = run_dir / "causal_simulator"
    files = (directory / "request.json", directory / "prompt.md", directory / "context_pack.md")
    if not force:
        existing = [path for path in files if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    directory.mkdir(parents=True, exist_ok=True)
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(target_file.resolve()),
        "role": "causal-simulator",
        "task": "simulate",
        "provider": provider,
        "model": model,
        "safety": {"overwrites_manuscript": False, "writes_staging_output": True, "requires_human_apply": True},
    }
    prompt = f"""# FictionOps Causal Simulator

Simulate the chapter before prose is written. Do not write scenes and do not solve a thematic question in narration.
Identify who knows what, what each stakeholder wants and fears, which action transfers cost to whom, and which consequences remain unresolved.
Do not invent canon to hide a missing mechanism. Return status blocked when the chapter cannot operate without a new author decision.
Convert theme answers into questions or prohibited conclusions. Convert viewpoint and withholding requirements into explicit hard constraints.
Only emit story-world quantity, timeline, conversion, or object-state rules that are supported by the supplied canon/context. Writing controls such as target characters, word count, scene count, paragraph count, or token budget never belong in hard_constraints. Leave rule lists empty when irrelevant; if the story requires one but its value is unknown, return blocked instead of guessing.

Return one JSON object with no Markdown fences:
{{
  "schema": "{CAUSAL_SIMULATION_SCHEMA}",
  "status": "ready|blocked",
  "stakeholders": [{{"id": "...", "knows": [], "wants": [], "fears": [], "leverage": [], "constraints": [], "likely_error": "..."}}],
  "event_graph": [{{"id": "E1", "preconditions": [], "action": "...", "immediate_effects": [], "cost_transfer": ["who pays what"], "observable_evidence": [], "unresolved": []}}],
  "hard_constraints": {{
    "pov_whitelist": [], "forbidden_pov": [], "knowledge_limits": [],
    "theme_questions": [], "forbidden_conclusions": [],
    "special_passage_limits": [{{"label": "letter|dream|memory|speech", "marker": "...", "max_chars": 0}}],
    "quantitative_rules": [{{"id": "Q1", "description": "...", "operation": "multiply|add|subtract|divide", "operands": [0], "expected_value": 0, "expected_unit": "...", "tolerance": 0, "forbidden_claims": []}}],
    "unit_conversions": {{}},
    "timeline_rules": [{{"id": "T1", "description": "...", "start": "...", "end": "...", "min_elapsed": 0, "max_elapsed": 0, "unit": "day|hour|month"}}],
    "object_state_rules": [{{"id": "O1", "object": "...", "initial_code": "ON_CART", "initial_state": "...", "transitions": [{{"transition_id": "O1T1", "order": 1, "event_id": "E1", "from_code": "ON_CART", "to_code": "LIFTED", "from": "...", "to": "..."}}], "forbidden_states": []}}]
  }},
  "missing_mechanics": [], "summary": "..."
}}
"""
    context = "\n\n".join(
        [
            "# Causal Simulation Context",
            "## Chapter Engine\n\n" + engine_text.rstrip(),
            "## Outline\n\n" + (outline_text.rstrip() or "No explicit outline supplied."),
            "## Retrieved Project Memory\n\n" + (memory_text.rstrip() or "No typed memory was retrieved."),
        ]
    ).rstrip() + "\n"
    files[0].write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    files[1].write_text(prompt, encoding="utf-8", newline="\n")
    files[2].write_text(context, encoding="utf-8", newline="\n")
    return directory


def parse_causal_simulation(text: str) -> dict[str, object]:
    payload = parse_json_object(text)
    if payload.get("schema") != CAUSAL_SIMULATION_SCHEMA:
        raise ValueError(f"causal simulator must declare schema {CAUSAL_SIMULATION_SCHEMA}")
    if str(payload.get("status")) not in {"ready", "blocked"}:
        raise ValueError("causal simulator status must be ready or blocked")
    for key in ("stakeholders", "event_graph", "missing_mechanics"):
        if not isinstance(payload.get(key), list):
            raise ValueError(f"causal simulator {key} must be a list")
    hard = payload.get("hard_constraints")
    if not isinstance(hard, dict):
        raise ValueError("causal simulator hard_constraints must be an object")
    hard.setdefault("timeline_rules", [])
    hard.setdefault("object_state_rules", [])
    hard.setdefault("unit_conversions", {})
    normalizations: list[dict[str, object]] = []
    if hard.get("unit_conversions") == []:
        hard["unit_conversions"] = {}
        normalizations.append({"kind": "empty_unit_conversion_list_to_object"})
    filtered_quantities: list[object] = []
    for raw in hard.get("quantitative_rules") or []:
        if isinstance(raw, dict):
            description = str(raw.get("description") or "")
            unit = str(raw.get("expected_unit") or "").strip().lower()
            if unit in {"char", "chars", "character", "characters", "word", "words", "token", "tokens"} or re.search(
                r"章节.{0,8}(?:字数|体量|字符|词数|段落|场景)|(?:目标|建议).{0,8}(?:字数|体量|字符)",
                description,
            ):
                normalizations.append({"kind": "removed_writing_metadata_quantity", "rule_id": raw.get("id"), "description": description})
                continue
        filtered_quantities.append(raw)
    hard["quantitative_rules"] = filtered_quantities
    filtered_passages: list[object] = []
    for raw in hard.get("special_passage_limits") or []:
        if isinstance(raw, dict):
            try:
                maximum = int(raw.get("max_chars") or 0)
            except (TypeError, ValueError):
                maximum = 0
            if maximum <= 0:
                normalizations.append({"kind": "removed_nonpositive_special_passage_limit", "label": raw.get("label"), "marker": raw.get("marker")})
                continue
        filtered_passages.append(raw)
    hard["special_passage_limits"] = filtered_passages
    filtered_conclusions: list[object] = []
    for raw in hard.get("forbidden_conclusions") or []:
        text = str(raw).strip()
        if re.match(r"^(?:不能|不要|不得|不让|不把|不替)", text):
            hard.setdefault("knowledge_limits", []).append(text)
            normalizations.append({"kind": "moved_instruction_out_of_forbidden_conclusions", "text": text})
            continue
        filtered_conclusions.append(raw)
    hard["forbidden_conclusions"] = filtered_conclusions
    if normalizations:
        payload["normalizations"] = normalizations
    for key in (
        "pov_whitelist", "forbidden_pov", "knowledge_limits", "theme_questions", "forbidden_conclusions",
        "special_passage_limits", "quantitative_rules", "timeline_rules", "object_state_rules",
    ):
        if not isinstance(hard.get(key), list):
            raise ValueError(f"causal simulator hard_constraints.{key} must be a list")
    if not isinstance(hard.get("unit_conversions"), dict):
        raise ValueError("causal simulator hard_constraints.unit_conversions must be an object")
    if payload.get("status") == "ready" and not payload.get("event_graph"):
        raise ValueError("ready causal simulation requires an event graph")
    return payload


def validate_causal_simulation(payload: dict[str, object]) -> list[dict[str, object]]:
    hard = payload.get("hard_constraints")
    if not isinstance(hard, dict):
        return [{"kind": "missing_hard_constraints"}]
    issues: list[dict[str, object]] = []
    event_ids = {
        str(item.get("id"))
        for item in payload.get("event_graph") or []
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    for index, raw in enumerate(hard.get("quantitative_rules") or [], start=1):
        if not isinstance(raw, dict):
            continue
        rule_id = str(raw.get("id") or f"Q{index}")
        operands = [_number(value) for value in raw.get("operands") or []]
        expected = _number(raw.get("expected_value"))
        calculated = _calculated_value(str(raw.get("operation") or ""), [value for value in operands if value is not None])
        tolerance = _number(raw.get("tolerance")) or 0.0
        if len(operands) < 2 or None in operands or expected is None or calculated is None:
            issues.append({"kind": "invalid_quantitative_rule", "rule_id": rule_id})
        elif abs(calculated - expected) > tolerance:
            issues.append({"kind": "quantitative_rule_mismatch", "rule_id": rule_id, "expected": expected, "calculated": calculated})
    for index, raw in enumerate(hard.get("timeline_rules") or [], start=1):
        if not isinstance(raw, dict):
            continue
        rule_id = str(raw.get("id") or f"T{index}")
        minimum = _number(raw.get("min_elapsed"))
        maximum = _number(raw.get("max_elapsed"))
        start = re.sub(r"\s+", "", str(raw.get("start") or ""))
        end = re.sub(r"\s+", "", str(raw.get("end") or ""))
        if minimum is None or maximum is None or minimum < 0 or maximum < minimum:
            issues.append({"kind": "invalid_timeline_rule", "rule_id": rule_id, "minimum": minimum, "maximum": maximum})
        elif maximum == 0 and start != end:
            issues.append(
                {
                    "kind": "unsupported_zero_duration_timeline",
                    "rule_id": rule_id,
                    "evidence": "distinct start/end events cannot use a zero-duration assertion without canon support",
                }
            )
    for index, raw in enumerate(hard.get("object_state_rules") or [], start=1):
        if not isinstance(raw, dict):
            continue
        rule_id = str(raw.get("id") or f"O{index}")
        previous_code = str(raw.get("initial_code") or "").strip()
        if not previous_code:
            issues.append({"kind": "object_initial_code_missing", "rule_id": rule_id})
        transitions = [item for item in raw.get("transitions") or [] if isinstance(item, dict)]
        transition_ids: set[str] = set()
        orders: set[int] = set()
        sortable: list[tuple[int, dict[str, object]]] = []
        for transition in transitions:
            transition_id = str(transition.get("transition_id") or "").strip()
            try:
                order = int(transition.get("order"))
            except (TypeError, ValueError):
                order = 0
            if not transition_id or transition_id in transition_ids:
                issues.append({"kind": "object_transition_id_invalid", "rule_id": rule_id, "transition_id": transition_id})
            else:
                transition_ids.add(transition_id)
            if order <= 0 or order in orders:
                issues.append({"kind": "object_transition_order_invalid", "rule_id": rule_id, "transition_id": transition_id, "order": order})
            else:
                orders.add(order)
            sortable.append((order, transition))
        for _, transition in sorted(sortable, key=lambda item: item[0]):
            if not isinstance(transition, dict):
                continue
            event_id = str(transition.get("event_id") or "").strip()
            scene_id = str(transition.get("scene_id") or "").strip()
            if not event_id and not scene_id:
                issues.append({"kind": "object_transition_unbound", "rule_id": rule_id})
            elif event_id and event_id not in event_ids:
                issues.append({"kind": "object_transition_event_missing", "rule_id": rule_id, "event_id": event_id})
            from_code = str(transition.get("from_code") or "").strip()
            to_code = str(transition.get("to_code") or "").strip()
            if not from_code or not to_code:
                issues.append({"kind": "object_transition_code_missing", "rule_id": rule_id, "event_id": event_id})
            elif previous_code and from_code != previous_code:
                issues.append(
                    {
                        "kind": "object_transition_chain_mismatch",
                        "rule_id": rule_id,
                        "event_id": event_id,
                        "expected_from_code": previous_code,
                        "actual_from_code": from_code,
                    }
                )
            if to_code:
                previous_code = to_code
    return issues


def prepare_causal_retry(directory: Path, output_text: str, issues: list[dict[str, object]]) -> None:
    prompt_file = directory / "prompt.md"
    context_file = directory / "context_pack.md"
    prompt = prompt_file.read_text(encoding="utf-8")
    context = context_file.read_text(encoding="utf-8")
    prompt_file.write_text(
        prompt.rstrip()
        + "\n\n## Causal Contract Repair\n\nReturn a complete corrected causal simulation JSON object. "
        + "Use an empty object for unit_conversions and empty lists for irrelevant rule families. Remove writing metadata such as target characters, word count, scene count, paragraph count, and token budget from story quantitative_rules. "
        + "Do not invent a zero-duration timeline or any missing numeric fact; remove an unsupported rule, or return blocked when the chapter truly requires an author decision. "
        + "Bind object transitions to existing event_graph ids with event_id. Give every tracked state a short stable ASCII code, including initial_code and each transition's from_code/to_code; descriptions may stay natural language. Each transition also needs a unique transition_id and ascending order. Record one actual execution path, not alternative branches. If an object is lifted and put back, represent both state changes in order so the codes form a continuous chain. The later planner will map transitions to scenes.\n\n"
        + json.dumps(issues, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    context_file.write_text(
        context.rstrip() + "\n\n## Rejected Previous Causal Simulation\n\n```json\n" + output_text.strip() + "\n```\n",
        encoding="utf-8",
        newline="\n",
    )


def sanitize_theme_answers(text: str, causal: dict[str, object]) -> str:
    hard = causal.get("hard_constraints")
    if not isinstance(hard, dict):
        return text
    sanitized = text
    for question in hard.get("theme_questions") or []:
        value = str(question).strip()
        match = re.search(r"[‘'\"]?([^，。？！?]{2,16})[’'\"]?是([^，。？！?]{2,24})还是", value)
        if not match:
            continue
        subject = re.sub(r"[‘’“”'\"\s]", "", match.group(1))
        first_answer = re.sub(r"[‘’“”'\"\s的]", "", match.group(2))
        first_answer = re.sub(r"^一个", "", first_answer)
        if not subject or not first_answer:
            continue
        answer_pattern = "".join(re.escape(char) + "的?" for char in first_answer)
        pattern = re.compile(
            rf"[‘’“”'\"]?{re.escape(subject)}[‘’“”'\"]?.{{0,16}}?不是(?:一个)?{answer_pattern}",
            flags=re.DOTALL,
        )
        sanitized = pattern.sub(f"[THEME QUESTION: {value}; keep unresolved]", sanitized)
    return sanitized


def chapter_contract(plan: dict[str, object], causal: dict[str, object] | None) -> dict[str, object]:
    constraints: list[dict[str, object]] = []
    for prefix, key, kind in (("P", "preserve_constraints", "preserve"), ("F", "forbidden_reveals", "forbidden")):
        for index, value in enumerate(plan.get(key) or [], start=1):
            text = str(value).strip()
            if text:
                constraints.append({"id": f"{prefix}{index}", "kind": kind, "text": text})
    hard = causal.get("hard_constraints") if isinstance(causal, dict) else {}
    if not isinstance(hard, dict):
        hard = {}
    for prefix, key, kind in (
        ("K", "knowledge_limits", "knowledge"),
        ("C", "forbidden_conclusions", "forbidden_conclusion"),
        ("Q", "quantitative_rules", "quantity"),
        ("T", "timeline_rules", "timeline"),
        ("O", "object_state_rules", "object_state"),
    ):
        for index, value in enumerate(hard.get(key) or [], start=1):
            text = rule_text(value)
            if text:
                constraints.append({"id": f"{prefix}{index}", "kind": kind, "text": text})
    scenes: list[dict[str, object]] = []
    for index, scene in enumerate(plan.get("scenes") or [], start=1):
        if not isinstance(scene, dict):
            continue
        scenes.append(
            {
                "scene_id": str(scene.get("scene_id") or f"S{index}"),
                "event_ids": [str(value) for value in scene.get("event_ids") or []],
                "order": scene.get("order") or index,
                "viewpoint": str(scene.get("viewpoint") or plan.get("viewpoint") or ""),
                "entry_state": scene.get("entry_state") or {},
                "exit_state": scene.get("exit_state") or {},
                "information_boundary": str(scene.get("information_boundary") or ""),
            }
        )
    ledger = build_story_fact_ledger(causal or {}, plan)
    return {
        "schema": "fictionops.chapter_contract.v1",
        "constraints": constraints,
        "pov_whitelist": [str(item) for item in hard.get("pov_whitelist") or []],
        "forbidden_pov": [str(item) for item in hard.get("forbidden_pov") or []],
        "theme_questions": [str(item) for item in hard.get("theme_questions") or []],
        "special_passage_limits": hard.get("special_passage_limits") or [],
        "unit_conversions": hard.get("unit_conversions") or {},
        "fact_ledger": ledger,
        "scene_states": scenes,
    }


def rule_text(value: object) -> str:
    if isinstance(value, dict):
        description = str(value.get("description") or "").strip()
        return description or json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _calculated_value(operation: str, operands: list[float]) -> float | None:
    if not operands:
        return None
    if operation == "multiply":
        result = 1.0
        for value in operands:
            result *= value
        return result
    if operation == "add":
        return sum(operands)
    if operation == "subtract" and len(operands) == 2:
        return operands[0] - operands[1]
    if operation == "divide" and len(operands) == 2 and operands[1] != 0:
        return operands[0] / operands[1]
    return None


def _object_records(state: object) -> dict[str, set[str]]:
    if not isinstance(state, dict):
        return {}
    records: dict[str, set[str]] = {}
    for raw in state.get("objects") or []:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or raw.get("object") or "").strip()
        value = str(raw.get("code") or raw.get("state") or raw.get("holder") or raw.get("location") or "").strip()
        if name and value:
            records.setdefault(name, set()).add(value)
    return records


def build_story_fact_ledger(causal: dict[str, object], plan: dict[str, object]) -> dict[str, object]:
    hard = causal.get("hard_constraints") if isinstance(causal, dict) else {}
    if not isinstance(hard, dict):
        hard = {}
    issues: list[dict[str, object]] = []
    quantities: list[dict[str, object]] = []
    for index, raw in enumerate(hard.get("quantitative_rules") or [], start=1):
        if not isinstance(raw, dict):
            quantities.append({"id": f"Q{index}", "description": str(raw), "structured": False})
            continue
        rule = dict(raw)
        rule.setdefault("id", f"Q{index}")
        operands = [_number(value) for value in rule.get("operands") or []]
        expected = _number(rule.get("expected_value"))
        tolerance = _number(rule.get("tolerance")) or 0.0
        calculated = _calculated_value(str(rule.get("operation") or ""), [value for value in operands if value is not None])
        rule["calculated_value"] = calculated
        rule["structured"] = True
        if None in operands or expected is None or calculated is None:
            issues.append({"kind": "invalid_quantitative_rule", "rule_id": rule["id"], "evidence": "missing or unsupported arithmetic fields"})
        elif abs(calculated - expected) > tolerance:
            issues.append({"kind": "quantitative_rule_mismatch", "rule_id": rule["id"], "expected": expected, "calculated": calculated, "tolerance": tolerance})
        quantities.append(rule)

    timelines: list[dict[str, object]] = []
    assertions = plan.get("fact_assertions")
    if not isinstance(assertions, dict):
        assertions = {}
    timeline_assertions = {
        str(item.get("rule_id")): item
        for item in assertions.get("timeline") or []
        if isinstance(item, dict) and str(item.get("rule_id") or "").strip()
    }
    for index, raw in enumerate(hard.get("timeline_rules") or [], start=1):
        if not isinstance(raw, dict):
            timelines.append({"id": f"T{index}", "description": str(raw), "structured": False})
            continue
        rule = dict(raw)
        rule.setdefault("id", f"T{index}")
        minimum = _number(rule.get("min_elapsed"))
        maximum = _number(rule.get("max_elapsed"))
        rule["structured"] = True
        if minimum is None or maximum is None or minimum < 0 or maximum < minimum:
            issues.append({"kind": "invalid_timeline_rule", "rule_id": rule["id"], "minimum": minimum, "maximum": maximum})
        assertion = timeline_assertions.get(str(rule["id"]))
        if assertion is None:
            issues.append({"kind": "missing_timeline_assertion", "rule_id": rule["id"]})
        else:
            elapsed = _number(assertion.get("elapsed"))
            expected_unit = str(rule.get("unit") or "").strip()
            actual_unit = str(assertion.get("unit") or "").strip()
            if elapsed is None or (minimum is not None and elapsed < minimum) or (maximum is not None and elapsed > maximum):
                issues.append({"kind": "timeline_assertion_out_of_range", "rule_id": rule["id"], "elapsed": elapsed, "minimum": minimum, "maximum": maximum})
            if expected_unit and actual_unit != expected_unit:
                issues.append({"kind": "timeline_unit_mismatch", "rule_id": rule["id"], "expected": expected_unit, "actual": actual_unit})
            rule["plan_assertion"] = assertion
        timelines.append(rule)

    objects: list[dict[str, object]] = []
    for index, raw in enumerate(hard.get("object_state_rules") or [], start=1):
        if not isinstance(raw, dict):
            objects.append({"id": f"O{index}", "description": str(raw), "structured": False})
            continue
        rule = dict(raw)
        rule.setdefault("id", f"O{index}")
        rule["structured"] = True
        if not str(rule.get("object") or "").strip():
            issues.append({"kind": "invalid_object_state_rule", "rule_id": rule["id"], "evidence": "object is missing"})
        transitions = rule.get("transitions") or []
        if not isinstance(transitions, list) or any(not isinstance(item, dict) for item in transitions):
            issues.append({"kind": "invalid_object_state_rule", "rule_id": rule["id"], "evidence": "transitions must be objects"})
        objects.append(rule)

    scenes = [item for item in plan.get("scenes") or [] if isinstance(item, dict)]
    scenes_by_id = {str(item.get("scene_id") or f"S{index + 1}"): item for index, item in enumerate(scenes)}
    scenes_by_event: dict[str, dict[str, object]] = {}
    for scene in scenes:
        for event_id in scene.get("event_ids") or []:
            value = str(event_id).strip()
            if value:
                scenes_by_event[value] = scene
    object_assertions = {
        (str(item.get("rule_id") or "").strip(), str(item.get("transition_id") or item.get("event_id") or "").strip()): item
        for item in assertions.get("object_transitions") or []
        if isinstance(item, dict)
    }
    mapped_transitions: dict[tuple[str, str], list[dict[str, object]]] = {}
    for rule in objects:
        if not rule.get("structured"):
            continue
        rule_id = str(rule.get("id") or "")
        object_name = str(rule.get("object") or "").strip()
        transitions = [item for item in rule.get("transitions") or [] if isinstance(item, dict)]
        transitions.sort(key=lambda item: int(item.get("order") or 0))
        for transition in transitions:
            if not isinstance(transition, dict):
                continue
            event_id = str(transition.get("event_id") or "").strip()
            scene_id = str(transition.get("scene_id") or "").strip()
            from_code = str(transition.get("from_code") or "").strip()
            to_code = str(transition.get("to_code") or "").strip()
            transition_id = str(transition.get("transition_id") or event_id).strip()
            if from_code and to_code and event_id:
                assertion = object_assertions.get((rule_id, transition_id))
                if assertion is None:
                    issues.append({"kind": "missing_object_transition_assertion", "rule_id": rule_id, "transition_id": transition_id, "event_id": event_id, "object": object_name})
                    continue
                asserted_from = str(assertion.get("from_code") or "").strip()
                asserted_to = str(assertion.get("to_code") or "").strip()
                asserted_scene_id = str(assertion.get("scene_id") or "").strip()
                scene = scenes_by_id.get(asserted_scene_id)
                if asserted_from != from_code or asserted_to != to_code:
                    issues.append(
                        {
                            "kind": "object_transition_assertion_mismatch",
                            "rule_id": rule_id,
                            "transition_id": transition_id,
                            "event_id": event_id,
                            "expected": {"from_code": from_code, "to_code": to_code},
                            "actual": {"from_code": asserted_from, "to_code": asserted_to},
                        }
                    )
                if scene is None or event_id not in [str(value) for value in scene.get("event_ids") or []]:
                    issues.append({"kind": "object_transition_scene_mapping_mismatch", "rule_id": rule_id, "transition_id": transition_id, "event_id": event_id, "scene_id": asserted_scene_id})
                    continue
                mapped_transitions.setdefault((asserted_scene_id, rule_id), []).append(
                    {"object": object_name, "from_code": from_code, "to_code": to_code, "event_id": event_id, "transition_id": transition_id, "order": transition.get("order")}
                )
                continue
            scene = scenes_by_event.get(event_id) if event_id else scenes_by_id.get(scene_id)
            if scene is None:
                issues.append(
                    {
                        "kind": "object_transition_mapping_missing",
                        "rule_id": rule.get("id"),
                        "event_id": event_id,
                        "scene_id": scene_id,
                        "object": object_name,
                    }
                )
                continue
            scene_id = str(scene.get("scene_id") or scene_id)
            entry_values = _object_records(scene.get("entry_state")).get(object_name, set())
            exit_values = _object_records(scene.get("exit_state")).get(object_name, set())
            expected_from = str(transition.get("from") or "").strip()
            expected_to = str(transition.get("to") or "").strip()
            if expected_from and expected_from not in entry_values:
                issues.append({"kind": "object_transition_entry_mismatch", "rule_id": rule.get("id"), "scene_id": scene_id, "object": object_name, "expected": expected_from, "actual": sorted(entry_values)})
            if expected_to and expected_to not in exit_values:
                issues.append({"kind": "object_transition_exit_mismatch", "rule_id": rule.get("id"), "scene_id": scene_id, "object": object_name, "expected": expected_to, "actual": sorted(exit_values)})
    for (scene_id, rule_id), transitions in mapped_transitions.items():
        transitions.sort(key=lambda item: int(item.get("order") or 0))
        scene = scenes_by_id[scene_id]
        object_name = str(transitions[0].get("object") or "")
        entry_values = _object_records(scene.get("entry_state")).get(object_name, set())
        exit_values = _object_records(scene.get("exit_state")).get(object_name, set())
        first_code = str(transitions[0].get("from_code") or "")
        last_code = str(transitions[-1].get("to_code") or "")
        if first_code not in entry_values:
            issues.append({"kind": "object_scene_entry_code_mismatch", "rule_id": rule_id, "scene_id": scene_id, "object": object_name, "expected_code": first_code, "actual": sorted(entry_values)})
        if last_code not in exit_values:
            issues.append({"kind": "object_scene_exit_code_mismatch", "rule_id": rule_id, "scene_id": scene_id, "object": object_name, "expected_code": last_code, "actual": sorted(exit_values)})
    for index, scene in enumerate(scenes):
        scene_id = str(scene.get("scene_id") or f"S{index + 1}")
        for state_name in ("entry_state", "exit_state"):
            for name, values in _object_records(scene.get(state_name)).items():
                if len(values) > 1:
                    issues.append({"kind": "object_state_conflict", "scene_id": scene_id, "state": state_name, "object": name, "values": sorted(values)})
        if index == 0:
            continue
        previous = scenes[index - 1]
        previous_objects = _object_records(previous.get("exit_state"))
        entry_objects = _object_records(scene.get("entry_state"))
        for name in sorted(previous_objects.keys() & entry_objects.keys()):
            if previous_objects[name] != entry_objects[name]:
                issues.append(
                    {
                        "kind": "object_handoff_mismatch",
                        "from_scene": str(previous.get("scene_id") or f"S{index}"),
                        "to_scene": scene_id,
                        "object": name,
                        "previous_exit": sorted(previous_objects[name]),
                        "next_entry": sorted(entry_objects[name]),
                    }
                )
    return {
        "schema": STORY_FACT_LEDGER_SCHEMA,
        "quantities": quantities,
        "timelines": timelines,
        "objects": objects,
        "unit_conversions": hard.get("unit_conversions") or {},
        "issues": issues,
        "status": "pass" if not issues else "fail",
    }


def normalize_plan_fact_codes(plan: dict[str, object], causal: dict[str, object]) -> list[dict[str, object]]:
    hard = causal.get("hard_constraints")
    assertions = plan.get("fact_assertions")
    if not isinstance(hard, dict) or not isinstance(assertions, dict):
        return []
    rules = {
        str(item.get("id")): item
        for item in hard.get("object_state_rules") or []
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    scenes = {
        str(item.get("scene_id")): item
        for item in plan.get("scenes") or []
        if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
    }
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for assertion in assertions.get("object_transitions") or []:
        if not isinstance(assertion, dict):
            continue
        rule_id = str(assertion.get("rule_id") or "").strip()
        scene_id = str(assertion.get("scene_id") or "").strip()
        if rule_id in rules and scene_id in scenes:
            grouped.setdefault((scene_id, rule_id), []).append(assertion)
    normalizations: list[dict[str, object]] = []

    def update_code(scene: dict[str, object], state_key: str, object_name: str, expected: str, rule_id: str) -> None:
        state = scene.get(state_key)
        if not isinstance(state, dict):
            return
        objects = [item for item in state.get("objects") or [] if isinstance(item, dict)]
        exact = [item for item in objects if str(item.get("name") or "").strip() == object_name]
        candidates = exact or (objects if len(objects) == 1 else [])
        if not candidates:
            return
        record = candidates[0]
        actual = str(record.get("code") or "").strip()
        if expected and actual != expected:
            record["code"] = expected
            normalizations.append(
                {
                    "kind": "normalized_scene_object_code",
                    "scene_id": scene.get("scene_id"),
                    "state": state_key,
                    "rule_id": rule_id,
                    "object": object_name,
                    "before": actual,
                    "after": expected,
                }
            )

    for (scene_id, rule_id), items in grouped.items():
        rule = rules[rule_id]
        object_name = str(rule.get("object") or "").strip()
        transition_order = {
            str(item.get("transition_id")): int(item.get("order") or 0)
            for item in rule.get("transitions") or []
            if isinstance(item, dict)
        }
        items.sort(key=lambda item: transition_order.get(str(item.get("transition_id") or ""), 0))
        update_code(scenes[scene_id], "entry_state", object_name, str(items[0].get("from_code") or "").strip(), rule_id)
        update_code(scenes[scene_id], "exit_state", object_name, str(items[-1].get("to_code") or "").strip(), rule_id)
    if normalizations:
        plan.setdefault("normalizations", []).extend(normalizations)
    return normalizations


def validate_plan_against_causal(plan: dict[str, object], causal: dict[str, object]) -> list[dict[str, object]]:
    hard = causal.get("hard_constraints")
    if not isinstance(hard, dict):
        return [{"kind": "missing_hard_constraints", "evidence": "causal hard_constraints is absent"}]
    whitelist = [str(item).strip() for item in hard.get("pov_whitelist") or [] if str(item).strip()]
    forbidden = [str(item).strip() for item in hard.get("forbidden_pov") or [] if str(item).strip()]
    issues: list[dict[str, object]] = []
    for index, scene in enumerate(plan.get("scenes") or [], start=1):
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("scene_id") or f"S{index}")
        viewpoint = str(scene.get("viewpoint") or "").strip()
        if whitelist and not any(name in viewpoint or viewpoint in name for name in whitelist):
            issues.append(
                {
                    "kind": "viewpoint_not_whitelisted",
                    "scene_id": scene_id,
                    "viewpoint": viewpoint,
                    "allowed": whitelist,
                }
            )
        matched_forbidden = [name for name in forbidden if name and name in viewpoint]
        if matched_forbidden:
            issues.append(
                {
                    "kind": "forbidden_viewpoint",
                    "scene_id": scene_id,
                    "viewpoint": viewpoint,
                    "matched": matched_forbidden,
                }
            )
    plan_text = json.dumps(plan.get("scenes") or [], ensure_ascii=False)
    for question in hard.get("theme_questions") or []:
        value = str(question).strip()
        match = re.search(r"[‘'\"]?([^，。？！?]{2,16})[’'\"]?是([^，。？！?]{2,24})还是", value)
        if not match:
            continue
        subject = re.sub(r"[‘’“”'\"\s]", "", match.group(1))
        first_answer = re.sub(r"[‘’“”'\"\s的]", "", match.group(2))
        first_answer = re.sub(r"^一个", "", first_answer)
        compact_plan = re.sub(r"[‘’“”'\"\s的]", "", plan_text).replace("一个", "")
        if subject and first_answer and re.search(re.escape(subject) + r".{0,40}不是.{0,12}" + re.escape(first_answer), compact_plan):
            issues.append(
                {
                    "kind": "theme_question_answered_in_plan",
                    "question": value,
                    "evidence": f"{subject}...不是...{first_answer}",
                }
            )
    for conclusion in hard.get("forbidden_conclusions") or []:
        phrase = str(conclusion).strip()
        if normalized_contains(plan_text, phrase):
            issues.append({"kind": "forbidden_conclusion_in_plan", "conclusion": phrase})
    issues.extend(build_story_fact_ledger(causal, plan).get("issues") or [])
    return issues


def prepare_adversarial_review_bundle(
    run_dir: Path,
    *,
    target_file: Path,
    candidate_text: str,
    contract: dict[str, object],
    memory_text: str,
    provider: str,
    model: str,
    force: bool,
) -> Path:
    directory = run_dir / "adversarial_reviewer"
    files = (directory / "request.json", directory / "prompt.md", directory / "context_pack.md")
    if not force:
        existing = [path for path in files if path.exists()]
        if existing:
            raise FileExistsError(existing[0])
    directory.mkdir(parents=True, exist_ok=True)
    request = {
        "schema": "fictionops.agent_run_request.v1",
        "execution_mode": "prepare_only",
        "target": str(target_file.resolve()),
        "role": "adversarial-reviewer",
        "task": "disprove",
        "provider": provider,
        "model": model,
        "safety": {"overwrites_manuscript": False, "writes_staging_output": True, "requires_human_apply": True},
    }
    scene_ids = [str(item.get("scene_id")) for item in contract.get("scene_states") or [] if isinstance(item, dict)]
    constraint_ids = [str(item.get("id")) for item in contract.get("constraints") or [] if isinstance(item, dict)]
    prompt = f"""# FictionOps Adversarial Draft Reviewer

Try to prove that the candidate is not ready. You are independent from the planner and writer.
Use only the candidate, the chapter contract, and retrieved project memory. Do not reward surface keyword matches.
For every explicit constraint, quote the strongest evidence for pass, fail, or uncertainty. For every expected scene state, check whether the exit state was actually earned without knowledge leakage.
Report only material issues, but never suppress a P1/P2 contradiction to produce a balanced review.
Resolve apparent constraint conflicts by specificity: a concrete event explicitly required by the contract is not itself a violation of a broader prohibition. Distinguish accidental weak response from deliberate or skilled control.
Visible actions such as looking, walking, touching, or pausing do not enter another character's viewpoint. Require actual inaccessible thought, intention, memory, or judgment before reporting viewpoint leakage.
The assembled prose has no visible scene markers. Judge state transitions by event order and achieved state; do not fail only because you guessed a different invisible scene boundary.

Required critic profiles: {json.dumps(CRITIC_PROFILES)}
Required constraint ids: {json.dumps(constraint_ids, ensure_ascii=False)}
Required scene ids: {json.dumps(scene_ids, ensure_ascii=False)}

Return one JSON object with no Markdown fences:
{{
  "schema": "{ADVERSARIAL_REVIEW_SCHEMA}",
  "verdict": "pass|fail|uncertain",
  "profiles": [{{"name": "continuity", "status": "pass|issues|uncertain", "summary": "..."}}],
  "constraint_checks": [{{"id": "P1", "status": "pass|fail|uncertain", "evidence": "exact quotation and reasoning"}}],
  "scene_state_checks": [{{"scene_id": "S1", "status": "pass|fail|uncertain", "evidence": "..."}}],
  "issues": [{{"category": "continuity|character_and_knowledge|prose_and_reader_experience", "severity": "P1|P2|P3|P4|P5", "evidence": ["exact quotation"], "problem": "...", "suggested_action": "...", "constraint_ids": []}}],
  "summary": "..."
}}
"""
    context = "\n\n".join(
        [
            "# Adversarial Review Context",
            "## Chapter Contract\n\n```json\n" + json.dumps(contract, ensure_ascii=False, indent=2) + "\n```",
            "## Candidate Chapter\n\n" + candidate_text.rstrip(),
            "## Retrieved Project Memory\n\n" + (memory_text.rstrip() or "No typed memory was retrieved."),
        ]
    ).rstrip() + "\n"
    files[0].write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    files[1].write_text(prompt, encoding="utf-8", newline="\n")
    files[2].write_text(context, encoding="utf-8", newline="\n")
    return directory


def parse_adversarial_review(text: str, contract: dict[str, object]) -> dict[str, object]:
    payload = parse_json_object(text)
    if payload.get("schema") != ADVERSARIAL_REVIEW_SCHEMA:
        raise ValueError(f"adversarial reviewer must declare schema {ADVERSARIAL_REVIEW_SCHEMA}")
    if str(payload.get("verdict")) not in {"pass", "fail", "uncertain"}:
        raise ValueError("adversarial reviewer verdict must be pass, fail, or uncertain")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("adversarial reviewer profiles must be a list")
    by_profile = {str(item.get("name")): item for item in profiles if isinstance(item, dict)}
    missing_profiles = [name for name in CRITIC_PROFILES if name not in by_profile]
    if missing_profiles:
        raise ValueError(f"adversarial reviewer omitted profiles: {', '.join(missing_profiles)}")
    expected_constraints = [str(item.get("id")) for item in contract.get("constraints") or [] if isinstance(item, dict)]
    checks = payload.get("constraint_checks")
    if not isinstance(checks, list):
        raise ValueError("adversarial reviewer constraint_checks must be a list")
    by_id = {str(item.get("id")): item for item in checks if isinstance(item, dict)}
    missing = [item for item in expected_constraints if item not in by_id]
    if missing:
        raise ValueError(f"adversarial reviewer omitted constraints: {', '.join(missing)}")
    expected_scenes = [str(item.get("scene_id")) for item in contract.get("scene_states") or [] if isinstance(item, dict)]
    scene_checks = payload.get("scene_state_checks")
    if not isinstance(scene_checks, list):
        raise ValueError("adversarial reviewer scene_state_checks must be a list")
    by_scene = {str(item.get("scene_id")): item for item in scene_checks if isinstance(item, dict)}
    missing_scenes = [item for item in expected_scenes if item not in by_scene]
    if missing_scenes:
        raise ValueError(f"adversarial reviewer omitted scene states: {', '.join(missing_scenes)}")
    for collection, key in ((checks, "id"), (scene_checks, "scene_id")):
        for item in collection:
            if not isinstance(item, dict) or str(item.get("status")) not in {"pass", "fail", "uncertain"}:
                raise ValueError(f"adversarial reviewer has invalid {key} check")
            if not str(item.get("evidence") or "").strip():
                raise ValueError(f"adversarial reviewer {key} check omitted evidence")
    issues = payload.get("issues")
    if not isinstance(issues, list):
        raise ValueError("adversarial reviewer issues must be a list")
    return payload


def normalized_contains(text: str, phrase: str) -> bool:
    compact_text = re.sub(r"[\s，。、“”‘’：:；;！？!?]", "", text)
    compact_phrase = re.sub(r"[\s，。、“”‘’：:；;！？!?]", "", phrase)
    return len(compact_phrase) >= 4 and compact_phrase in compact_text


def longest_formal_quote(text: str) -> tuple[int, str]:
    longest = ""
    for match in re.finditer(r"“([^”]{20,})”", text, flags=re.DOTALL):
        content = match.group(1)
        if re.search(r"臣|谨奏|伏惟|顿首|奏", content) and len(content) > len(longest):
            longest = content
    return len(longest), compact_quote(longest)


def compact_quote(text: str, limit: int = 120) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def deterministic_story_audit(candidate_text: str, contract: dict[str, object]) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    ledger = contract.get("fact_ledger")
    if isinstance(ledger, dict):
        ledger_issues = ledger.get("issues") or []
        checks.append(
            {
                "name": "story_fact_ledger_integrity",
                "passed": not ledger_issues,
                "blocking": True,
                "evidence": {"issues": ledger_issues},
            }
        )
        for raw in ledger.get("quantities") or []:
            if not isinstance(raw, dict):
                continue
            forbidden = [str(item).strip() for item in raw.get("forbidden_claims") or [] if str(item).strip()]
            hits = [item for item in forbidden if normalized_contains(candidate_text, item)]
            checks.append(
                {
                    "name": f"quantity_claim_{raw.get('id')}",
                    "passed": not hits,
                    "blocking": True,
                    "evidence": {
                        "description": raw.get("description"),
                        "expected_value": raw.get("expected_value"),
                        "expected_unit": raw.get("expected_unit"),
                        "forbidden_claim_hits": hits,
                    },
                }
            )
        for raw in ledger.get("objects") or []:
            if not isinstance(raw, dict):
                continue
            forbidden = [str(item).strip() for item in raw.get("forbidden_states") or [] if str(item).strip()]
            hits = [item for item in forbidden if normalized_contains(candidate_text, item)]
            checks.append(
                {
                    "name": f"object_state_claim_{raw.get('id')}",
                    "passed": not hits,
                    "blocking": True,
                    "evidence": {"object": raw.get("object"), "forbidden_state_hits": hits},
                }
            )
    for item in contract.get("constraints") or []:
        if not isinstance(item, dict) or str(item.get("kind")) != "forbidden_conclusion":
            continue
        phrase = str(item.get("text") or "")
        hit = normalized_contains(candidate_text, phrase)
        checks.append(
            {
                "name": f"forbidden_conclusion_{item.get('id')}",
                "passed": not hit,
                "blocking": True,
                "evidence": {"constraint": phrase, "matched": hit},
            }
        )
    compact_candidate = re.sub(r"[‘’“”'\"\s，。？！?、的]", "", candidate_text).replace("一个", "")
    for index, question in enumerate(contract.get("theme_questions") or [], start=1):
        value = str(question).strip()
        match = re.search(r"[‘'\"]?([^，。？！?]{2,16})[’'\"]?是([^，。？！?]{2,24})还是", value)
        if not match:
            continue
        subject = re.sub(r"[‘’“”'\"\s]", "", match.group(1))
        first_answer = re.sub(r"[‘’“”'\"\s的]", "", match.group(2))
        first_answer = re.sub(r"^一个", "", first_answer)
        hit = bool(subject and first_answer and re.search(re.escape(subject) + r".{0,40}不是.{0,12}" + re.escape(first_answer), compact_candidate))
        checks.append(
            {
                "name": f"theme_question_not_closed_{index}",
                "passed": not hit,
                "blocking": True,
                "evidence": {"question": value, "matched_direct_answer": hit},
            }
        )
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", candidate_text) if item.strip()]
    interior_verbs = r"想起|心想|觉得|意识到|忽然明白|明白了|记得|不知道为什么|认定|暗自决定|心里|心中|不由得"
    for name in contract.get("forbidden_pov") or []:
        value = str(name).strip()
        if not value:
            continue
        evidence = [paragraph for paragraph in paragraphs if re.search(re.escape(value) + rf".{{0,24}}(?:{interior_verbs})", paragraph)]
        checks.append(
            {
                "name": f"forbidden_pov_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:8]}",
                "passed": len(evidence) < 2,
                "blocking": True,
                "evidence": {"character": value, "suspicious_paragraphs": evidence[:4]},
            }
        )
    quote_length, quote_excerpt = longest_formal_quote(candidate_text)
    for index, raw in enumerate(contract.get("special_passage_limits") or [], start=1):
        if not isinstance(raw, dict):
            continue
        label = str(raw.get("label") or "")
        maximum = int(raw.get("max_chars") or 0)
        if maximum <= 0 or not re.search(r"奏|letter|memorial|疏", label, flags=re.IGNORECASE):
            continue
        checks.append(
            {
                "name": f"special_passage_limit_{index}",
                "passed": quote_length <= maximum,
                "blocking": True,
                "evidence": {"label": label, "maximum": maximum, "actual": quote_length, "excerpt": quote_excerpt},
            }
        )
    nonspace = sum(1 for char in candidate_text if not char.isspace())
    average = round(nonspace / max(len(paragraphs), 1), 2)
    checks.append(
        {
            "name": "paragraph_rhythm_observed",
            "passed": True,
            "blocking": False,
            "evidence": {"paragraphs": len(paragraphs), "nonspace_chars": nonspace, "average_nonspace_per_paragraph": average},
        }
    )
    failures = [str(item.get("name")) for item in checks if item.get("blocking") and not item.get("passed")]
    return {
        "schema": STORY_AUDIT_SCHEMA,
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "blocking_failures": failures,
    }


def merge_story_verification(
    verification: dict[str, object],
    *,
    deterministic: dict[str, object],
    adversarial: dict[str, object],
) -> dict[str, object]:
    checks = list(verification.get("checks") or [])
    checks = [item for item in checks if item.get("name") not in {"deterministic_story_contract", "adversarial_review"}]
    deterministic_failures = deterministic.get("blocking_failures") or []
    checks.append(
        {
            "name": "deterministic_story_contract",
            "passed": not deterministic_failures,
            "blocking": True,
            "evidence": {"failures": deterministic_failures, "audit": deterministic},
        }
    )
    failed_constraints = [
        str(item.get("id"))
        for item in adversarial.get("constraint_checks") or []
        if isinstance(item, dict) and str(item.get("status")) != "pass"
    ]
    failed_scenes = [
        str(item.get("scene_id"))
        for item in adversarial.get("scene_state_checks") or []
        if isinstance(item, dict) and str(item.get("status")) != "pass"
    ]
    severe_issues = [
        item
        for item in adversarial.get("issues") or []
        if isinstance(item, dict) and str(item.get("severity")) in {"P1", "P2"}
    ]
    adversarial_passed = str(adversarial.get("verdict")) == "pass" and not failed_constraints and not failed_scenes and not severe_issues
    checks.append(
        {
            "name": "adversarial_review",
            "passed": adversarial_passed,
            "blocking": True,
            "evidence": {
                "verdict": adversarial.get("verdict"),
                "failed_constraints": failed_constraints,
                "failed_scenes": failed_scenes,
                "severe_issue_count": len(severe_issues),
                "summary": adversarial.get("summary"),
            },
        }
    )
    failures = [str(item.get("name")) for item in checks if item.get("blocking") and not item.get("passed")]
    return {
        **verification,
        "status": "ready_for_approval" if not failures else "needs_revision_attention",
        "ready_for_approval": not failures,
        "checks": checks,
        "blocking_failures": failures,
        "deterministic_story_audit": deterministic,
        "adversarial_review": adversarial,
    }
