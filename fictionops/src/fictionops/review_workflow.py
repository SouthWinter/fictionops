from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .markdown import collect_markdown_files, display_path, strip_markdown_noise


@dataclass
class ReviewWorkflowMetric:
    key: str
    label: str
    count: int
    per_1000_chars: float
    threshold: float
    severity: str
    problem_family: str
    interpretation: str


@dataclass
class ReviewWorkflowEvidenceLine:
    line: int
    term: str
    text: str
    family: str
    suggested_action: str


@dataclass
class ReviewWorkflowIssue:
    severity: str
    family: str
    title: str
    evidence: str
    recommendation: str


@dataclass
class ReviewWorkflowFile:
    path: str
    chars: int
    nonspace_chars: int
    metrics: list[ReviewWorkflowMetric]
    issues: list[ReviewWorkflowIssue]
    evidence_lines: list[ReviewWorkflowEvidenceLine]
    agent_tasks: list[dict[str, str]]
    revision_queue: list[str]
    recheck_targets: dict[str, object]


@dataclass
class ReviewWorkflowReport:
    target: str
    mode: str
    file_count: int
    focus: str
    files: list[ReviewWorkflowFile]
    aggregate_issues: list[ReviewWorkflowIssue]
    next_actions: list[str]


WATCH_GROUPS: dict[str, dict[str, object]] = {
    "bushi": {
        "label": "不是",
        "pattern": r"不是",
        "threshold": 4.0,
        "family": "exclusionary_narration",
        "interpretation": "排除式旁白可能替读者判断；先区分必要辨认和可由场面承担的排除。",
    },
    "meiyou": {
        "label": "没有",
        "pattern": r"没有",
        "threshold": 4.0,
        "family": "absence_filter",
        "interpretation": "缺席/沉默句式可能形成否定滤镜；检查是否反复预设反应再否定。",
    },
    "simile": {
        "label": "像",
        "pattern": r"像",
        "threshold": 5.0,
        "family": "simile_translation",
        "interpretation": "比喻可能在替角色翻译陌生经验；检查是否削弱直接在场感。",
    },
    "sudden": {
        "label": "忽然",
        "pattern": r"忽然|突然",
        "threshold": 1.2,
        "family": "turn_signal_overuse",
        "interpretation": "转折提示词过密会让变化显得被旁白标记，而非由动作自然发生。",
    },
    "cold": {
        "label": "冷系",
        "pattern": r"冷|寒|冰|雪|冻|凉",
        "threshold": 5.0,
        "family": "sensory_default",
        "interpretation": "冷系词可能是环境/规则核心，也可能成为心理默认按钮；需做功能标注。",
    },
    "heat": {
        "label": "热系",
        "pattern": r"热|暖|烫|烧|火|温",
        "threshold": 2.5,
        "family": "sensory_default",
        "interpretation": "热系词可能承担生活、羞惭、血温或急迫；检查是否重复表达同一种情绪。",
    },
    "explain": {
        "label": "解释标记",
        "pattern": r"真正|其实|意味着|原来|明白",
        "threshold": 1.5,
        "family": "authorial_explanation",
        "interpretation": "解释标记过密会替读者盖章；优先改为动作、物件或误读。",
    },
}

DOUBLE_NEGATION = re.compile(r"不是[^。！？!?；;\n]{0,18}(?:也|又|还)?不是")


def severity_for(per_1000: float, threshold: float) -> str:
    if threshold <= 0:
        return "P4"
    ratio = per_1000 / threshold
    if ratio >= 1.75:
        return "P1"
    if ratio >= 1.25:
        return "P2"
    if ratio >= 1.0:
        return "P3"
    return "P4"


def short_line(text: str, limit: int = 96) -> str:
    stripped = re.sub(r"\s+", " ", text.strip())
    if len(stripped) > limit:
        return stripped[: limit - 1] + "…"
    return stripped


def markdown_cell(text: str) -> str:
    return text.replace("|", "\\|")


def count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text))


def line_suggestion(term: str, family: str, line: str) -> str:
    if family == "exclusionary_narration":
        if "不是灾厄" in line or "不是轻看" in line or "不是他的错" in line:
            return "likely_keep"
        return "review_keep_or_replace_with_scene"
    if family == "absence_filter":
        return "replace_with_positive_action_when_possible"
    if family == "simile_translation":
        return "keep_only_if_character_material_or_core_image"
    if family == "sensory_default":
        return "mark_function_environment_rule_body_or心理"
    return "review_context"


def collect_evidence_lines(text: str, *, top_lines: int) -> list[ReviewWorkflowEvidenceLine]:
    evidence: list[ReviewWorkflowEvidenceLine] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for key, config in WATCH_GROUPS.items():
            label = str(config["label"])
            pattern = str(config["pattern"])
            if re.search(pattern, line):
                family = str(config["family"])
                evidence.append(
                    ReviewWorkflowEvidenceLine(
                        line=line_number,
                        term=label,
                        text=short_line(line),
                        family=family,
                        suggested_action=line_suggestion(label, family, line),
                    )
                )
                break
    return evidence[:top_lines]


def build_metrics(text: str, chars: int) -> list[ReviewWorkflowMetric]:
    metrics: list[ReviewWorkflowMetric] = []
    denominator = max(chars, 1)
    for key, config in WATCH_GROUPS.items():
        count = count_pattern(text, str(config["pattern"]))
        per_1000 = round(count * 1000 / denominator, 2)
        threshold = float(config["threshold"])
        metrics.append(
            ReviewWorkflowMetric(
                key=key,
                label=str(config["label"]),
                count=count,
                per_1000_chars=per_1000,
                threshold=threshold,
                severity=severity_for(per_1000, threshold),
                problem_family=str(config["family"]),
                interpretation=str(config["interpretation"]),
            )
        )
    double_count = len(DOUBLE_NEGATION.findall(text))
    per_1000 = round(double_count * 1000 / max(chars, 1), 2)
    metrics.append(
        ReviewWorkflowMetric(
            key="double_negation",
            label="不是A也不是B",
            count=double_count,
            per_1000_chars=per_1000,
            threshold=1.0,
            severity=severity_for(per_1000, 1.0),
            problem_family="exclusionary_narration",
            interpretation="双重排除句式最容易替读者划掉错误答案；每屏只保留刀口处。",
        )
    )
    return metrics


def build_issues(metrics: list[ReviewWorkflowMetric]) -> list[ReviewWorkflowIssue]:
    issues: list[ReviewWorkflowIssue] = []
    for metric in metrics:
        if metric.severity not in {"P1", "P2", "P3"}:
            continue
        issues.append(
            ReviewWorkflowIssue(
                severity=metric.severity,
                family=metric.problem_family,
                title=f"{metric.label} density is above workflow threshold",
                evidence=(
                    f"{metric.count} hits, {metric.per_1000_chars}/1000 chars "
                    f"(threshold {metric.threshold}/1000)."
                ),
                recommendation=metric.interpretation,
            )
        )
    return issues


def build_agent_tasks(issues: list[ReviewWorkflowIssue]) -> list[dict[str, str]]:
    families = {issue.family for issue in issues}
    tasks: list[dict[str, str]] = []
    if {"exclusionary_narration", "absence_filter", "simile_translation"} & families:
        tasks.append(
            {
                "role": "style-auditor",
                "goal": "Classify repeated negation/simile patterns into keep, micro-revise, and replace-with-scene buckets.",
                "human_boundary": "Return staged review only; do not rewrite the manuscript.",
            }
        )
    if "sensory_default" in families:
        tasks.append(
            {
                "role": "style-auditor",
                "goal": "Mark sensory-field uses by function: environment, rule, foreshadowing, body, or psychological shortcut.",
                "human_boundary": "Suggest reductions only where the same emotion is repeatedly carried by one field.",
            }
        )
    if {"exclusionary_narration", "authorial_explanation"} & families:
        tasks.append(
            {
                "role": "character-auditor",
                "goal": "Check whether the viewpoint character is observing naturally or thinking in author-level categories.",
                "human_boundary": "Keep character knowledge boundaries intact.",
            }
        )
    tasks.append(
        {
            "role": "synthesis",
            "goal": "Merge static scan and agent reviews into a revision queue with preserve/change/recheck sections.",
            "human_boundary": "No source overwrite; human applies any prose edits.",
        }
    )
    return tasks


def build_revision_queue(metrics: list[ReviewWorkflowMetric], issues: list[ReviewWorkflowIssue]) -> list[str]:
    families = {issue.family for issue in issues}
    queue: list[str] = []
    if "exclusionary_narration" in families:
        queue.extend(
            [
                "Preserve negation at information-boundary or thematic knife-edge lines.",
                "Review each `不是A，也不是B` line; keep only those that cannot be replaced by action or object evidence.",
                "Move ordinary de-monster/de-mystify claims into concrete details before retaining narrator judgment.",
            ]
        )
    if "absence_filter" in families:
        queue.append("Convert low-value `没有...` lines into positive action, silence, gaze, or object state where possible.")
    if "simile_translation" in families:
        queue.append("Cut or simplify similes that explain an already visible action; reserve similes for core images.")
    if "sensory_default" in families:
        queue.append("Annotate cold/heat field uses by function and replace psychological shortcuts with viewpoint-specific materials.")
    if "turn_signal_overuse" in families:
        queue.append("Keep `忽然/突然` only for true perception shifts; let adjacent actions carry minor turns.")
    if not queue:
        queue.append("No urgent prose-pattern queue; preserve current wording unless human review finds local issues.")
    return queue


def build_recheck_targets(metrics: list[ReviewWorkflowMetric]) -> dict[str, object]:
    targets: dict[str, object] = {}
    for metric in metrics:
        if metric.severity in {"P1", "P2", "P3"}:
            if metric.key in {"bushi", "meiyou", "simile"}:
                target = max(0, int(round(metric.count * 0.7)))
                targets[metric.key] = {
                    "current": metric.count,
                    "suggested_after_revision": target,
                    "note": "Do not force this number; stop when function is restored.",
                }
            else:
                targets[metric.key] = {
                    "current": metric.count,
                    "suggested_after_revision": "functional review",
                    "note": "Classify by function rather than mechanical reduction.",
                }
    return targets


def build_review_workflow_report(
    target: Path,
    *,
    all_markdown: bool = False,
    pattern: str = "**/*.md",
    focus: str = "style",
    top_lines: int = 40,
) -> ReviewWorkflowReport:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"path does not exist: {resolved}")
    if top_lines < 1:
        raise ValueError("top_lines must be >= 1")
    files = collect_markdown_files(resolved, all_markdown=all_markdown, pattern=pattern)
    base = resolved if resolved.is_dir() else resolved.parent
    file_reports: list[ReviewWorkflowFile] = []
    aggregate_counter: Counter[tuple[str, str]] = Counter()

    for path in files:
        raw_text = path.read_text(encoding="utf-8")
        text = strip_markdown_noise(raw_text)
        chars = len(text)
        metrics = build_metrics(text, chars)
        issues = build_issues(metrics)
        for issue in issues:
            aggregate_counter[(issue.severity, issue.family)] += 1
        file_reports.append(
            ReviewWorkflowFile(
                path=display_path(path, base),
                chars=chars,
                nonspace_chars=sum(1 for char in text if not char.isspace()),
                metrics=metrics,
                issues=issues,
                evidence_lines=collect_evidence_lines(raw_text, top_lines=top_lines),
                agent_tasks=build_agent_tasks(issues),
                revision_queue=build_revision_queue(metrics, issues),
                recheck_targets=build_recheck_targets(metrics),
            )
        )

    aggregate_issues = [
        ReviewWorkflowIssue(
            severity=severity,
            family=family,
            title=f"{family} appears in {count} file(s)",
            evidence=f"{count} file(s) crossed workflow thresholds.",
            recommendation="Open the highest-density file reports first, then run staged agent review for the listed roles.",
        )
        for (severity, family), count in sorted(aggregate_counter.items(), key=lambda item: (item[0][0], item[0][1]))
    ]
    next_actions = [
        "Review the per-file revision queue before editing.",
        "Run listed agent tasks only for P1/P2 families or human-disputed findings.",
        "After edits, rerun review-workflow and compare recheck_targets; do not optimize numbers at the cost of scene function.",
    ]
    return ReviewWorkflowReport(
        target=str(resolved),
        mode="all-markdown" if all_markdown else "chapters",
        file_count=len(file_reports),
        focus=focus,
        files=file_reports,
        aggregate_issues=aggregate_issues,
        next_actions=next_actions,
    )


def render_review_workflow_report(report: ReviewWorkflowReport, format_: str) -> str:
    if format_ == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    if format_ != "markdown":
        raise ValueError(f"Unsupported review-workflow format: {format_}")
    lines = [
        "# FictionOps Review Workflow",
        "",
        f"- Target: `{report.target}`",
        f"- Mode: `{report.mode}`",
        f"- Files: {report.file_count}",
        f"- Focus: `{report.focus}`",
        "",
        "## Aggregate Issues",
        "",
    ]
    if report.aggregate_issues:
        lines.extend(["| Severity | Family | Evidence | Recommendation |", "| --- | --- | --- | --- |"])
        for issue in report.aggregate_issues:
            lines.append(f"| {issue.severity} | `{issue.family}` | {issue.evidence} | {issue.recommendation} |")
    else:
        lines.append("No workflow thresholds crossed.")
    for file in report.files:
        lines.extend(
            [
                "",
                f"## File: `{file.path}`",
                "",
                f"- Characters: {file.chars}",
                f"- Nonspace characters: {file.nonspace_chars}",
                "",
                "### Metrics",
                "",
                "| Key | Count | Per 1000 | Threshold | Severity | Family |",
                "| --- | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for metric in file.metrics:
            lines.append(
                f"| {metric.label} | {metric.count} | {metric.per_1000_chars} | "
                f"{metric.threshold} | {metric.severity} | `{metric.problem_family}` |"
            )
        lines.extend(["", "### Issues", ""])
        if file.issues:
            lines.extend(["| Severity | Family | Evidence | Recommendation |", "| --- | --- | --- | --- |"])
            for issue in file.issues:
                lines.append(f"| {issue.severity} | `{issue.family}` | {issue.evidence} | {issue.recommendation} |")
        else:
            lines.append("No file-level workflow issues.")
        lines.extend(["", "### Evidence Lines", ""])
        if file.evidence_lines:
            lines.extend(["| Line | Term | Family | Action | Text |", "| ---: | --- | --- | --- | --- |"])
            for item in file.evidence_lines:
                lines.append(
                    f"| {item.line} | {item.term} | `{item.family}` | "
                    f"`{item.suggested_action}` | {markdown_cell(item.text)} |"
                )
        else:
            lines.append("No evidence lines captured.")
        lines.extend(["", "### Agent Tasks", ""])
        for task in file.agent_tasks:
            lines.append(f"- `{task['role']}`: {task['goal']} Boundary: {task['human_boundary']}")
        lines.extend(["", "### Revision Queue", ""])
        for item in file.revision_queue:
            lines.append(f"- {item}")
        lines.extend(["", "### Recheck Targets", ""])
        if file.recheck_targets:
            lines.append("```json")
            lines.append(json.dumps(file.recheck_targets, ensure_ascii=False, indent=2))
            lines.append("```")
        else:
            lines.append("-")
    lines.extend(["", "## Next Actions", ""])
    for action in report.next_actions:
        lines.append(f"- {action}")
    return "\n".join(lines)
