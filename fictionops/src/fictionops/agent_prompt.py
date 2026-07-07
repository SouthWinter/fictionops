from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .context_pack import CONTEXT_TASKS, build_context_pack, render_context_pack
from .models import AgentPromptReport, ContextPackReport
from .new_chapter import normalize_chapter_number
from .plan_chapter import normalize_book_for_plan


@dataclass(frozen=True)
class AgentRoleSpec:
    key: str
    name: str
    default_task: str
    purpose: str
    inputs: list[str]
    outputs: list[str]
    must_do: list[str]
    must_not: list[str]
    workflow: list[str]
    output_contract: str


AGENT_ROLES: dict[str, AgentRoleSpec] = {
    "architect": AgentRoleSpec(
        key="architect",
        name="Architect 架构师",
        default_task="handoff",
        purpose="维护长篇结构、幕结构、不可逆事件和跨卷压力，不微操单句。",
        inputs=["总纲、卷纲、书纲", "人物终点与不可逆选择", "时间线和主要势力变化", "revision-plan 高优先级任务"],
        outputs=["结构风险", "幕/卷/书层级建议", "不可逆事件清单", "需要作者裁决的问题"],
        must_do=["先判断结构承诺是否稳定", "区分必须改、建议改和可以保留", "说明改动会影响哪些后续章节"],
        must_not=["不要替作者决定主题终局", "不要逐句润色正文", "不要为了整齐牺牲活的场景"],
        workflow=["读当前结构层材料", "列出 P1/P2 级结构风险", "提出 1-3 个可选结构方案", "标注每个方案的代价"],
        output_contract="输出结构判断、风险、备选方案和需要作者裁决的问题。",
    ),
    "canon-keeper": AgentRoleSpec(
        key="canon-keeper",
        name="Canon Keeper 正史管理员",
        default_task="canon-sync",
        purpose="维护正史、世界规则、物件位置、时间线和废弃设定边界。",
        inputs=["世界规则", "信息释放表", "伏笔回声表", "物件位置表", "正文与修订笔记"],
        outputs=["正史冲突报告", "同步建议", "归档建议", "受影响文件清单"],
        must_do=["区分作者真相、角色信念、公共谣言和官方记录", "指出证据文件", "保留废案路径"],
        must_not=["不要私自删除旧案", "不要把正文草稿误当最终正史", "不要让角色提前知道作者真相"],
        workflow=["先查时间线和正史表", "再查正文是否改出新事实", "判断是同步正史还是修正文稿", "列出受影响文件"],
        output_contract="输出冲突、证据、建议动作和需要同步或归档的文件。",
    ),
    "character-auditor": AgentRoleSpec(
        key="character-auditor",
        name="Character Auditor 人物审计",
        default_task="review",
        purpose="检查人物是否在变化中仍然是自己，避免工具人和同质聪明。",
        inputs=["人物弧线", "智慧模式", "口吻表", "关系图", "被审章节"],
        outputs=["人物失真点", "动机/盲点/情绪残留建议", "口吻修订方向"],
        must_do=["保留角色自己的错误和局限", "区分少年/成人、身份/阶层、地域/职业口吻", "指出情绪后果是否被过快消解"],
        must_not=["不要把角色磨成标准答案", "不要让所有聪明人都像谋士", "不要用作者解释替代角色反应"],
        workflow=["确认角色此刻知道什么", "确认角色此刻想要什么", "检查说话方式和行动是否属于他/她", "提出最小修订方向"],
        output_contract="按角色列出失真、证据、风险等级和修订方向。",
    ),
    "info-boundary-auditor": AgentRoleSpec(
        key="info-boundary-auditor",
        name="Info Boundary Auditor 信息边界审计",
        default_task="review",
        purpose="检查秘密、神话、规则和阴谋是否被角色、旁白或公共版本提前泄露。",
        inputs=["信息释放表", "正文", "上一章/下一章摘要", "公共版本和官方版本"],
        outputs=["泄露风险", "知识来源缺口", "误读/传闻/沉默改写建议"],
        must_do=["逐项确认谁知道、怎么知道、以什么版本知道", "优先处理作者真相提前盖章", "把可靠解释改成可承受的局部信息"],
        must_not=["不要让角色像读过设定集", "不要为了说明白而破坏悬念", "不要把所有信息都一次性解释清楚"],
        workflow=["先读信息释放表", "再定位正文命中处", "判断是泄露、误读还是安全提及", "给出低解释密度改写方向"],
        output_contract="输出信息项、位置、当前风险、建议改法和是否需要同步信息表。",
    ),
    "foreshadowing-auditor": AgentRoleSpec(
        key="foreshadowing-auditor",
        name="Foreshadowing Auditor 伏笔审计",
        default_task="review",
        purpose="维护伏笔的初种、回声、读者记忆、禁止提前解释和兑现方向。",
        inputs=["伏笔回声表", "章节正文", "章节复盘", "revision-plan"],
        outputs=["回声间隔问题", "过度解释风险", "轻触建议", "兑现/转化建议"],
        must_do=["区分轻回声和解释", "确认读者记忆是否足够", "指出久未回声或提前说穿的线程"],
        must_not=["不要每次都解释伏笔", "不要把抽象主题硬填成道具线", "不要为了表格完整而破坏留白"],
        workflow=["读伏笔表", "检查最近章节命中", "判断读者是否还能记住", "给出轻触或关闭建议"],
        output_contract="输出线程、当前状态、风险和下一次轻回声建议。",
    ),
    "chapter-planner": AgentRoleSpec(
        key="chapter-planner",
        name="Chapter Planner 章节规划",
        default_task="draft",
        purpose="把书纲压力转成可写章节发动机，而不是内容清单。",
        inputs=["书纲", "上一章", "章节发动机", "信息边界", "伏笔表"],
        outputs=["Pressure/Desire/Obstacle/Change/Remainder", "场景顺序", "信息边界", "章末余味"],
        must_do=["给视角人物一个当下欲望", "让阻碍带代价", "让章末发生不可回退变化", "留出读者自己思考的位置"],
        must_not=["不要只列剧情点", "不要靠解释收束章节", "不要把所有秘密在计划里提前说穿给正文"],
        workflow=["确认本章功能", "写五列发动机", "列场景顺序", "标出能说/不能说/只能误读"],
        output_contract="输出章节发动机、信息边界和场景顺序。",
    ),
    "draft-writer": AgentRoleSpec(
        key="draft-writer",
        name="Draft Writer 正文写手",
        default_task="draft",
        purpose="在严格视角、口吻、信息边界和章节发动机内生成可修正文草稿。",
        inputs=["章节发动机", "上一章", "人物口吻", "信息释放表", "伏笔表"],
        outputs=["正文草稿", "必要留白", "章末余味", "写后待同步提示"],
        must_do=["限制在视角人物可知范围内", "用场景推进替代旁白解释", "让角色按自己的智慧模式犯错", "保留动作、停顿和误读"],
        must_not=["不要忽视视角限制", "不要把角色写成作者代言", "不要把所有伏笔解释清楚", "不要为了字数机械填充"],
        workflow=["回答本章五个必答问题", "确认不能说的信息", "按场景写草稿", "最后列出需要复盘同步的事项"],
        output_contract="输出正文草稿；若必须说明风险，放在草稿后的修订备注中。",
    ),
    "style-auditor": AgentRoleSpec(
        key="style-auditor",
        name="Style Auditor 风格审计",
        default_task="review",
        purpose="审计高频词、句式、解释密度、节奏整齐度和 AI 模板感。",
        inputs=["正文", "style audit", "章节体量波形", "作者风格偏好"],
        outputs=["风格风险", "句式/词频建议", "解释密度建议", "可保留的功能性重复"],
        must_do=["先判断重复是否承担功能", "只减少有害密度", "保留作者有意的节奏和个人风格"],
        must_not=["不要统一抹平风格", "不要为了安全把文字磨平", "不要先修 P4 而无视 P1/P2"],
        workflow=["读正文和风格统计", "定位高密度模式", "判断功能", "给出局部修订建议"],
        output_contract="输出模式、位置、风险、保留理由或修订方向。",
    ),
    "publisher": AgentRoleSpec(
        key="publisher",
        name="Publisher 发布员",
        default_task="handoff",
        purpose="维护发布稿、元数据、manifest、EPUB 和发布前检查，不碰草稿源文件。",
        inputs=["clean Markdown", "发布清单", "metadata JSON", "manifest", "EPUB 审计"],
        outputs=["发布准备状态", "缺口清单", "导出命令建议", "发布前风险"],
        must_do=["确认发布版和草稿版分离", "确认元数据完整", "确认 manifest 和 EPUB 新鲜度", "保留可复现命令"],
        must_not=["不要覆盖草稿和规划层", "不要绕过 audit-publish/audit-epub", "不要用发布稿反向改正史"],
        workflow=["检查 clean Markdown", "检查 metadata", "检查 manifest", "检查 EPUB", "列出发布前阻断项"],
        output_contract="输出发布状态、阻断问题、建议命令和可选后续动作。",
    ),
}


AGENT_ROLE_CHOICES = sorted(AGENT_ROLES)

ROLE_ALIASES = {
    "canon": "canon-keeper",
    "keeper": "canon-keeper",
    "character": "character-auditor",
    "char": "character-auditor",
    "info": "info-boundary-auditor",
    "information": "info-boundary-auditor",
    "echo": "foreshadowing-auditor",
    "foreshadowing": "foreshadowing-auditor",
    "planner": "chapter-planner",
    "writer": "draft-writer",
    "draft": "draft-writer",
    "style": "style-auditor",
    "publish": "publisher",
}


def normalize_agent_role(role: str) -> str:
    key = re.sub(r"[\s_]+", "-", role.strip().lower())
    key = ROLE_ALIASES.get(key, key)
    if key not in AGENT_ROLES:
        choices = ", ".join(AGENT_ROLE_CHOICES)
        raise ValueError(f"unsupported agent role: {role}. Available roles: {choices}")
    return key


def normalize_prompt_task(task: str | None, spec: AgentRoleSpec) -> str:
    chosen = task or spec.default_task
    if chosen not in CONTEXT_TASKS:
        raise ValueError(f"unsupported agent prompt task: {chosen}")
    return chosen


def render_bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def suggested_context_command(*, task: str, book: str, chapter: str | None) -> str:
    parts = ["fictionops", "context-pack", ".", "--task", task, "--book", book]
    if chapter:
        parts.extend(["--chapter", chapter])
    elif task in {"draft", "review"}:
        parts.extend(["--chapter", "<chapter>"])
    return " ".join(parts)


def suggested_revision_command(*, book: str) -> str:
    return f"fictionops revision-plan . --book {book}"


def render_prompt_text(
    spec: AgentRoleSpec,
    *,
    task: str,
    book: str,
    chapter: str | None,
) -> str:
    lines = [
        "# FictionOps Agent Prompt",
        "",
        f"## Role: {spec.name}",
        "",
        spec.purpose,
        "",
        "## Current Assignment",
        "",
        f"- Task: {task}",
        f"- Book: {book}",
        f"- Chapter: {chapter or '-'}",
        "",
        "## Inputs To Prefer",
        "",
        *render_bullets(spec.inputs),
        "",
        "## Must Do",
        "",
        *render_bullets(spec.must_do),
        "",
        "## Must Not",
        "",
        *render_bullets(spec.must_not),
        "",
        "## Workflow",
        "",
    ]
    for index, step in enumerate(spec.workflow, start=1):
        lines.append(f"{index}. {step}")
    lines.extend(
        [
            "",
            "## Expected Output",
            "",
            spec.output_contract,
            "",
            "## Useful Local Commands",
            "",
            f"```bash\n{suggested_context_command(task=task, book=book, chapter=chapter)}\n{suggested_revision_command(book=book)}\n```",
            "",
            "## Operating Rule",
            "",
            "你是协作者，不是自动作者。先保护正史、信息边界、人物弧线和章节压力，再处理风格和润色。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_agent_prompt(
    project: Path,
    *,
    role: str,
    task: str | None = None,
    book: str = "book_01",
    chapter: str | None = None,
    include_context: bool = False,
    include_context_content: bool = False,
    max_chars_per_file: int = 6000,
    max_total_context_chars: int = 60000,
    out: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> AgentPromptReport:
    if not project.exists():
        raise FileNotFoundError(f"path does not exist: {project}")
    if not project.is_dir():
        raise ValueError(f"agent-prompt requires a FictionOps project directory: {project}")

    role_key = normalize_agent_role(role)
    spec = AGENT_ROLES[role_key]
    book_id = normalize_book_for_plan(book)
    chapter_number = normalize_chapter_number(chapter) if chapter else None
    task_id = normalize_prompt_task(task, spec)
    context: ContextPackReport | None = None
    if include_context:
        context = build_context_pack(
            project,
            task=task_id,
            book=book_id,
            chapter=chapter_number,
            include_content=include_context_content,
            max_chars_per_file=max_chars_per_file,
            max_total_chars=max_total_context_chars,
            out=None,
            force=False,
            dry_run=True,
        )

    prompt = render_prompt_text(spec, task=task_id, book=book_id, chapter=chapter_number)
    if context is not None:
        prompt += "\n\n---\n\n" + render_context_pack(context, "markdown")

    output_path = resolve_agent_prompt_output_path(project, out) if out else None
    report = AgentPromptReport(
        target=str(project),
        role=role_key,
        role_name=spec.name,
        task=task_id,
        book=book_id,
        chapter=chapter_number,
        output_file=str(output_path) if output_path else None,
        dry_run=dry_run,
        written=False,
        include_context=include_context,
        prompt=prompt,
        context_pack=context,
    )
    if output_path and not dry_run:
        write_agent_prompt(output_path, render_agent_prompt(report, "markdown"), force=force)
        report.written = True
    return report


def resolve_agent_prompt_output_path(project: Path, out: str) -> Path:
    candidate = Path(out).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project / candidate).resolve()


def write_agent_prompt(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def render_agent_prompt(report: AgentPromptReport, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(report), ensure_ascii=False, indent=2)
    return report.prompt
