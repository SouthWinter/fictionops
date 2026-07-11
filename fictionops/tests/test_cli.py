from __future__ import annotations

import json
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CLI = SRC / "fictionops" / "cli.py"
sys.path.insert(0, str(SRC))

CLI_COMMANDS = [
    "agent",
    "adopt",
    "adopt-review",
    "adopt-plan",
    "import-plan",
    "init",
    "new-book",
    "new-chapter",
    "plan-chapter",
    "scene-plan",
    "draft-brief",
    "post-draft",
    "review-gate",
    "book-gate",
    "audit-plan",
    "retrospective",
    "stats",
    "scan-words",
    "check-tables",
    "audit-wave",
    "audit-style",
    "review-workflow",
    "audit-continuity",
    "audit-echoes",
    "audit-info",
    "audit-characters",
    "agent-prompt",
    "agent-connect",
    "eval-agent",
    "agent-smoke",
    "agent-run",
    "agent-exec",
    "agent-inbox",
    "agent-memory",
    "agent-revise-workflow",
    "agent-accept-revision",
    "agent-write-workflow",
    "write-chapter",
    "revise-chapter",
    "audit-chapter",
    "agent-session",
    "agent-next",
    "audit-agent-workflow",
    "setup-ai",
    "model-config",
    "context-pack",
    "workflow-plan",
    "revision-plan",
    "doctor",
    "report",
    "export-clean",
    "audit-publish",
    "publish-copy",
    "export-metadata",
    "export-manifest",
    "export-epub",
    "audit-epub",
    "release-gate",
    "audit-release-evidence",
    "audit-dogfood-cycle",
    "audit-stability-window",
    "audit-stable-core",
]

from fictionops.core import (  # noqa: E402
    build_agent_exec,
    build_agent_connect,
    build_agent_evaluation,
    build_agent_inbox,
    build_agent_next,
    build_agent_prompt,
    build_agent_revise_workflow,
    build_agent_run,
    build_agent_session,
    build_agent_smoke,
    build_agent_workflow_audit,
    build_adopt_report,
    build_adopt_review,
    build_adopt_plan,
    build_import_plan,
    build_chapter_wave_report,
    build_character_audit_report,
    build_continuity_report,
    build_context_pack,
    build_draft_brief,
    build_doctor_report,
    build_echo_report,
    build_epub_audit_report,
    build_info_report,
    build_model_config_report,
    build_post_draft_report,
    build_publish_copy,
    build_review_gate,
    build_review_workflow_report,
    build_book_gate,
    build_release_gate,
    build_release_evidence_audit,
    build_dogfood_cycle_audit,
    build_stability_window_audit,
    build_stable_core_audit,
    build_table_check_report,
    build_word_scan_report,
    build_workflow_plan,
    export_clean_markdown,
    export_epub,
    export_publish_manifest,
    export_publish_metadata,
    build_plan_audit_report,
    build_publish_audit_report,
    build_retrospective_report,
    build_revision_plan,
    build_scene_plan,
    build_stats_report,
    build_style_audit_report,
    build_ai_setup,
    create_book,
    create_chapter,
    create_project,
    normalize_book_id,
    normalize_chapter_number,
    plan_chapter,
)
from fictionops.agent_session import session_status  # noqa: E402
from fictionops.agent_exec import build_runner_input, load_agent_exec_request  # noqa: E402
from fictionops.agent_inbox import inspect_agent_run_dir  # noqa: E402
from fictionops.agent_comprehensive_review import compact_issue_ledger, parse_comprehensive_review  # noqa: E402
from fictionops.agent_issue_ledger import (  # noqa: E402
    load_issue_ledger,
    merge_issue_observations,
    stable_issue_id,
    transition_issue,
)
from fictionops.agent_revision_runtime import merge_semantic_verification  # noqa: E402
from fictionops.agent_research_baseline import (  # noqa: E402
    baseline_prompt,
    build_blind_review_artifacts,
    run_baselines,
    score_review,
)
from fictionops.agent_policy import select_agent_policy  # noqa: E402
from fictionops.agent_author_guards import active_author_guards, load_author_guard_registry, set_author_guard  # noqa: E402
from fictionops.agent_preservation_verifier import (  # noqa: E402
    PRESERVATION_VERIFICATION_SCHEMA,
    apply_preservation_verification,
    deterministic_preservation_decisions,
    parse_preservation_verification,
)
from fictionops.agent_counterevidence_review import (  # noqa: E402
    COUNTEREVIDENCE_EVALUATION_SCHEMA,
    build_counterevidence_from_run,
    evaluate_counterevidence,
)
from fictionops.agent_evidence_escalation import (  # noqa: E402
    apply_reverification_grounding,
    build_evidence_escalation,
    classify_evidence_scope,
)
from fictionops.agent_write_workflow import expected_title_from_engine, scene_target_chars  # noqa: E402
from fictionops.agent_story_reasoning import (  # noqa: E402
    build_story_fact_ledger,
    deterministic_story_audit,
    parse_causal_simulation,
    review_evidence_grounding_issues,
    sanitize_theme_answers,
    validate_plan_against_causal,
)
from fictionops.dogfood_cycle import RECOGNIZED_FICTIONOPS_COMMANDS  # noqa: E402
from fictionops.models import AgentSessionStep  # noqa: E402


class FictionOpsCliTests(unittest.TestCase):
    def make_project(self, title: str = "Demo Novel") -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name) / "demo-novel"
        create_project(target, title=title, language="zh-CN", force=False, dry_run=False)
        return temp, target

    def run_cli(
        self,
        *args: str,
        cwd: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=str(cwd or ROOT.parent),
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=check,
        )

    def write_accepted_release_evidence(self, target: Path, relative: str = "docs/release-trial-evidence.md") -> Path:
        evidence = target / relative
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            "\n".join(
                [
                    "# Release Trial Evidence",
                    "",
                    "- Date: 2026-07-07",
                    "- Version: 0.1.0",
                    "- Commit / ref / tag: abc123 / v0.1.0",
                    "- Decision: accepted",
                    "- Reviewer: maintainer",
                    "- GitHub Actions run URL: https://github.com/example/fictionops/actions/runs/123456789",
                    "- GitHub Actions run ID: 123456789",
                    "- Wheel filename: fictionops-0.1.0-py3-none-any.whl",
                    "- Wheel SHA256: " + "a" * 64,
                    "- sdist filename: fictionops-0.1.0.tar.gz",
                    "- sdist SHA256: " + "b" * 64,
                    "- Built-wheel smoke result: passed",
                    "- TestPyPI used: no",
                    "- TestPyPI skip reason: validating GitHub Actions artifact instead of publishing to TestPyPI",
                    "- TestPyPI skip accepted by: maintainer",
                    "- fictionops --version result: fictionops 0.1.0",
                    "- python -m fictionops --version result: fictionops 0.1.0",
                    "- fictionops init smoke result: passed",
                    "- fictionops doctor smoke result: passed",
                ]
            ),
            encoding="utf-8",
        )
        return evidence

    def write_accepted_dogfood_cycle(self, target: Path, relative: str = "docs/dogfood-cycle-evidence.md") -> Path:
        evidence = target / relative
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            "\n".join(
                [
                    "# Dogfood Cycle Evidence",
                    "",
                    "- Cycle ID: 2026-07-maintenance-01",
                    "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                    "- Start date: 2026-07-01",
                    "- End date: 2026-07-07",
                    "- Version / commit range: 0.1.0 / abc123..def456",
                    "- Scope: post-migration maintenance cycle",
                    "- Book / chapter scope: Book 01 ch_001-ch_033, focused review on ch_007 and ch_010",
                    "- Focused tasks: structure recovery, reader-experience triage, and bounded chapter revision",
                    "- Commands exercised: adopt-review, adopt-plan, import-plan, doctor",
                    "- AI workflow evidence: eval-agent ch_002 plus agent-run staged output in inbox",
                    "- Human review boundary: staged output stopped at human review and no source overwrite was allowed",
                    "- Day-by-day ledger: 2026-07-01 baseline; 2026-07-07 close rerun",
                    "- Initial adopt-review status: ready",
                    "- Final adopt-review status: ready",
                    "- import_queue_files: 0",
                    "- blocking_issue_count: 0",
                    "- Waiver count: 31",
                    "- Compatibility notes: stable surfaces reviewed",
                    "- Recovery notes: recovery docs reviewed",
                    "- Decision: accepted",
                    "- Reviewer: maintainer",
                ]
            ),
            encoding="utf-8",
        )
        return evidence

    def write_filled_echo_table(self, target: Path) -> None:
        table = target / "05_canon" / "foreshadowing_echo_table.md"
        table.write_text(
            textwrap.dedent(
                """\
                # Foreshadowing Echo Table

                | Thread | First Plant | Last Echo | Current State | Next Light Echo | Do Not Reveal Yet | Payoff Direction |
                | --- | --- | --- | --- | --- | --- | --- |
                | Lantern Key | ch_001 | ch_001 | planted | ch_003 | do not explain the maker | opens the old door |
                """
            ),
            encoding="utf-8",
        )

    def write_filled_information_table(self, target: Path) -> None:
        table = target / "05_canon" / "information_release_table.md"
        table.write_text(
            textwrap.dedent(
                """\
                # Information Release Table

                | Info / Secret | Author Truth | Reader Current | Character A Knows | Character B Knows | Public Version | Official Version | Next Release | Do Not Reveal |
                | --- | --- | --- | --- | --- | --- | --- | --- | --- |
                | Maker Secret | The key opens the old door | Reader has seen the object | Tester knows it matters | - | A strange trinket | Unrecorded | ch_001 | Do not explain the maker |
                """
            ),
            encoding="utf-8",
        )

    def write_filled_character_files(self, target: Path) -> None:
        characters = target / "03_characters"
        arc_dir = characters / "character_arcs"
        arc_dir.mkdir(parents=True, exist_ok=True)
        (characters / "character_index.md").write_text(
            textwrap.dedent(
                """\
                # 人物索引

                | 人物 | 身份 | 首次出现 | 当前状态 | 弧线文件 |
                | --- | --- | --- | --- | --- |
                | Tester | 持灯人 | ch_001 | 正在选择 | character_arcs/tester.md |
                """
            ),
            encoding="utf-8",
        )
        (characters / "intelligence_profiles.md").write_text(
            textwrap.dedent(
                """\
                # 人物智慧模式

                | 人物 | 看得快的东西 | 容易错过的东西 | 解决方式 | 失败方式 | 口吻 |
                | --- | --- | --- | --- | --- | --- |
                | Tester | 门缝里的机会 | 人情代价 | 先拆小问题 | 抢跑 | 短句 |
                """
            ),
            encoding="utf-8",
        )
        (characters / "voice_profiles.md").write_text(
            textwrap.dedent(
                """\
                # 人物口吻

                | 人物 | 说话节奏 | 常用判断方式 | 不会说的话 | 紧张时动作 |
                | --- | --- | --- | --- | --- |
                | Tester | 短促 | 先看证据 | 宏大空话 | 摸袖口 |
                """
            ),
            encoding="utf-8",
        )
        (arc_dir / "tester.md").write_text(
            textwrap.dedent(
                """\
                # Tester

                ## 1. 基本信息

                - 姓名：Tester
                - 初始年龄/阶段：少年
                - 公开身份：持灯人
                - 私人身份：逃亡者
                - 所属势力/家庭/阶层：底层

                ## 2. 起点

                - 起点创伤：失去住处
                - 起点欲望：保住钥匙
                - 起点恐惧：再次被抛下
                - 起点误解：以为沉默就是安全
                - 起点自我保护方式：先退一步

                ## 3. 智慧模式

                | 看得快的东西 | 容易错过的东西 | 解决问题的方式 | 典型失败方式 |
                | --- | --- | --- | --- |
                | 门缝里的机会 | 人情代价 | 拆成小问题 | 抢跑 |

                ## 4. 口吻与行为

                - 说话节奏：短促
                - 常用判断方式：先看证据
                - 不会说的话：宏大空话
                - 紧张时的动作：摸袖口
                - 撒谎方式：少说一半
                - 表达关心的方式：把路让出来

                ## 5. 关系锚点

                | 对象 | 起点关系 | 中段变化 | 终点状态 | 未说出口的东西 |
                | --- | --- | --- | --- | --- |
                | Keeper | 救助者 | 互相信任 | 分路 | 谢意 |

                ## 6. 成长路径

                | 阶段 | 他/她相信什么 | 受到什么压力 | 做出什么不可逆选择 | 留下什么代价 |
                | --- | --- | --- | --- | --- |
                | 起点 | 沉默安全 | 被追赶 | 藏起钥匙 | 孤立 |
                | 中段 | 信任要付代价 | 被误解 | 说出半个真相 | 暴露 |
                | 终局 | 选择要承担 | 失去退路 | 打开门 | 离开旧身份 |

                ## 7. 失败路径

                如果这个人物走偏，会变成：只看见钥匙，不看见人。

                这条失败路径在正文中如何诱惑他/她：每次恐惧来时都让他先藏起来。
                """
            ),
            encoding="utf-8",
        )

    def write_long_chapter_with_echo(self, target: Path) -> None:
        chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
        chapter.write_text(
            "# Chapter 001\n\n"
            + (
                "The Lantern Key was cold. He hid the Lantern Key again. "
                "This chapter is intentionally longer than a bare placeholder so FictionOps can "
                "separate draft content from template scaffolding and keep continuity checks stable. "
            )
            * 3,
            encoding="utf-8",
        )

    def write_book_outline_plan(self, target: Path, rows: str, book: str = "book_01") -> None:
        outline = target / "04_structure" / "book_outlines" / f"{book}_outline.md"
        outline.write_text(
            textwrap.dedent(
                f"""\
                # Test Outline

                | 章 | 标题 | 视角 | Pressure | Desire | Obstacle | Change | Remainder | 体量 |
                | --- | --- | --- | --- | --- | --- | --- | --- | --- |
                {rows}
                """
            ),
            encoding="utf-8",
        )

    def write_filled_chapter_retrospective(self, target: Path, chapter: str = "002") -> None:
        retrospective = target / "06_drafts" / "book_01" / "revision_notes" / f"ch_{chapter}_retrospective.md"
        retrospective.parent.mkdir(parents=True, exist_ok=True)
        retrospective.write_text(
            textwrap.dedent(
                f"""\
                # 章节复盘

                ## 章节信息

                - 书名：book_01
                - 章节：第{chapter}章
                - 标题：已完成章节
                - 完成日期：2026-07-05
                - 实际字数：8600

                ## 1. 功能复盘

                本章已经完成主要结构功能，并把人物关系推到新的压力点。这里写得足够长，避免被当作空模板。

                ## 6. 同步项

                - 需要同步到人物弧线：主角信念发生小幅转向
                - 需要同步到信息释放表：
                - 需要同步到伏笔回声表：
                - 需要同步到书纲：
                - 需要归档的旧案：
                """
            ),
            encoding="utf-8",
        )

    def write_closed_chapter_retrospective(self, target: Path, chapter: str = "001", title: str = "Closed Chapter") -> None:
        retrospective = target / "06_drafts" / "book_01" / "revision_notes" / f"ch_{chapter}_retrospective.md"
        retrospective.parent.mkdir(parents=True, exist_ok=True)
        retrospective.write_text(
            textwrap.dedent(
                f"""\
                # 第{chapter}章复盘

                - 书名：book_01
                - 章节：第{chapter}章
                - 标题：{title}
                - 完成日期：2026-07-06
                - 实际字数：620

                本章完成了既定压力转移。人物没有突然获得作者级知识，场景余波已经留给下一章。

                ## 同步项

                - 需要同步到人物弧线：
                - 需要同步到信息释放表：
                - 需要同步到伏笔回声表：
                - 需要同步到书纲：
                - 需要归档的旧案：
                """
            ),
            encoding="utf-8",
            newline="\n",
        )

    def write_closed_book_retrospective(self, target: Path, book: str = "book_01") -> None:
        retrospective = target / "07_audits" / "book_retrospectives" / f"{book}_retrospective.md"
        retrospective.parent.mkdir(parents=True, exist_ok=True)
        retrospective.write_text(
            textwrap.dedent(
                f"""\
                # {book} 书级复盘

                - 书名：{book}
                - 完成日期：2026-07-06
                - 当前状态：已完成书级收束

                ## 1. 结构回顾

                本书已经完成主要压力链路，章节之间的进入状态和离开状态可以交接给下一阶段。

                ## 2. 人物离开状态

                Tester 带着新的判断进入下一本，恐惧没有被清空，只是换成了可追踪的行动。

                ## 3. 信息与伏笔

                Lantern Key 的公开版本、读者版本和作者真相仍然分层保留。

                ## 4. 待同步事项

                无开放同步项。
                """
            ),
            encoding="utf-8",
            newline="\n",
        )

    def write_publish_checklist_metadata(self, target: Path) -> None:
        checklist = target / "08_publish" / "publish_checklist.md"
        checklist.write_text(
            textwrap.dedent(
                """\
                # 发布清单模板

                ## 1. 发布信息

                - 书名：烟雪
                - 卷名：第一卷
                - 本名：灯市暗潮
                - 版本：v1.0
                - 发布日期：2026-07-06
                - 字数：320000

                ## 3. 发布前审计

                - 是否需要内容提示：不需要

                ## 4. 元数据

                - 作者名：示例作者
                - 分类：幻想
                - 标签：权谋，成长，神话
                - 简介短版：少年在灯市暗潮里第一次看见权力的代价。
                - 简介长版：这是一部关于秩序、误读和成长的长篇开端，人物在有限信息里做选择，也在选择之后承担回声。
                - 关键词：灯市，城邦，旧城遗藏
                """
            ),
            encoding="utf-8",
        )

    def write_publish_copy_sources(self, target: Path) -> None:
        seed = target / "01_story_seed" / "story_seed.md"
        seed.write_text(
            textwrap.dedent(
                """\
                # 故事种子

                ## 1. 一句话前提

                > 一个少年在灯市之夜卷入城邦权力与旧城遗藏的缝隙，必须学会为选择付出代价。

                ## 2. 类型与子类型

                - 主类型：幻想
                - 子类型：权谋，成长，神话
                """
            ),
            encoding="utf-8",
        )
        outline = target / "04_structure" / "book_outlines" / "book_01_outline.md"
        outline.write_text(
            textwrap.dedent(
                """\
                # 灯市暗潮

                ## 1. 本书一句话

                > 少年从被权力碾过的人，变成能看见秩序裂缝的人。

                ## 2. 本书性质

                - 主要情绪：冷、紧、隐忍
                - 主要空间：灯市、内城、灯塔会
                """
            ),
            encoding="utf-8",
        )
        clean = target / "08_publish" / "clean_markdown" / "book_01.md"
        clean.parent.mkdir(parents=True, exist_ok=True)
        clean.write_text(
            textwrap.dedent(
                """\
                # 烟雪

                ## 第一章 灯市

                少年在灯市里看见城主，也看见规训如何压过一个人的名字。旧城遗藏仍像神话一样伏在暗处。

                ## 第二章 灯下

                他开始明白选择不是一句话。城邦、城主、神剑和旧藏都把他推向更窄的路。
                """
            ),
            encoding="utf-8",
        )

    def test_init_creates_layout_and_respects_force(self) -> None:
        temp, target = self.make_project("Demo Novel")
        with temp:
            self.assertTrue((target / "project.yml").exists())
            self.assertTrue((target / "05_canon" / "information_release_table.md").exists())
            self.assertTrue((target / "07_audits" / "post_draft").is_dir())
            self.assertTrue((target / "07_audits" / "review_gate").is_dir())
            self.assertTrue((target / "07_audits" / "book_gate").is_dir())
            self.assertTrue((target / "07_audits" / "release_gate").is_dir())
            self.assertTrue((target / "08_publish" / "manifest").exists())
            self.assertIn("Demo Novel", (target / "project.yml").read_text(encoding="utf-8"))

            seed = target / "01_story_seed" / "story_seed.md"
            seed.write_text("custom seed", encoding="utf-8")
            result = create_project(target, title="Demo Novel", language="zh-CN", force=False, dry_run=False)
            self.assertGreater(result.skipped_files, 0)
            self.assertEqual(seed.read_text(encoding="utf-8"), "custom seed")

            create_project(target, title="Demo Novel", language="zh-CN", force=True, dry_run=False)
            self.assertNotEqual(seed.read_text(encoding="utf-8"), "custom seed")

    def test_cli_init_and_version_entrypoints(self) -> None:
        version = self.run_cli("--version")
        self.assertIn("fictionops 0.1.1", version.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "cli-demo"
            result = self.run_cli("init", str(target), "--title", "CLI Demo")
            self.assertIn("Initialized FictionOps project", result.stdout)
            self.assertTrue((target / "project.yml").exists())

    def test_adopt_maps_legacy_project_layers_without_modifying_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "legacy"
            (target / "00_总纲与管理").mkdir(parents=True)
            (target / "01_人物弧线").mkdir(parents=True)
            (target / "卷一_风港" / "第一本_潮声").mkdir(parents=True)
            (target / "11_番外与神话").mkdir(parents=True)
            (target / "归档_旧稿").mkdir(parents=True)
            (target / "fictionops").mkdir(parents=True)

            (target / "00_总纲与管理" / "示例长篇_全书信息释放总表.md").write_text("| 信息 | 作者真相 |\n| --- | --- |\n| 灯 | 真相 |\n", encoding="utf-8")
            (target / "00_总纲与管理" / "示例长篇_当前接手摘要.md").write_text("# 当前接手摘要\n\n下一步先审第十章。\n", encoding="utf-8")
            (target / "01_人物弧线" / "示例长篇_主角人物弧线.md").write_text("# 人物弧线\n\n她想活下去。\n", encoding="utf-8")
            (target / "卷一_风港" / "第一本_潮声" / "第01章_归港.md").write_text("# 第01章\n\n正文开始。\n", encoding="utf-8")
            (target / "卷一_风港" / "第一本_潮声" / "示例长篇_卷一第一本_本书大纲.md").write_text("# 本书大纲\n\n第一章。\n", encoding="utf-8")
            (target / "11_番外与神话" / "示例长篇_神话设定.md").write_text("# 神话\n\n民间版本。\n", encoding="utf-8")
            (target / "归档_旧稿" / "旧大纲.md").write_text("# 旧稿\n\n废案。\n", encoding="utf-8")
            (target / "零散想法.md").write_text("# 想法\n\n暂存。\n", encoding="utf-8")
            (target / "fictionops" / "README.md").write_text("# should be ignored\n", encoding="utf-8")

            report = build_adopt_report(target, max_files=20)
            layers = {summary.layer: summary.files for summary in report.layer_summaries}

            self.assertGreaterEqual(report.scanned_files, 7)
            self.assertGreaterEqual(report.ignored_files, 1)
            self.assertIn("canon", layers)
            self.assertIn("management", layers)
            self.assertIn("characters", layers)
            self.assertIn("drafts", layers)
            self.assertIn("structure", layers)
            self.assertIn("world", layers)
            self.assertIn("archive", layers)
            self.assertTrue(any(risk.code == "missing_project_config" for risk in report.risks))
            self.assertTrue(any("fictionops init" in action for action in report.next_actions))
            self.assertTrue(any(item.path.endswith("示例长篇_当前接手摘要.md") and item.layer == "management" for item in report.files))
            self.assertTrue(any(item.path.endswith("示例长篇_当前接手摘要.md") and item.suggested_target_path.startswith("00_management/") for item in report.files))
            self.assertTrue(any(item.path.endswith("第01章_归港.md") and item.migration_phase == "draft-import" for item in report.files))
            self.assertFalse((target / "00_management").exists())

    def test_adopt_cli_outputs_json_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "legacy"
            target.mkdir()
            (target / "总纲.md").write_text("# 总纲\n\n这是一个旧项目。\n", encoding="utf-8")
            (target / "第01章.md").write_text("# 第01章\n\n旧正文。\n", encoding="utf-8")

            result = self.run_cli("adopt", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["scanned_files"], 2)
            self.assertTrue(any(item["layer"] == "structure" for item in data["files"]))
            self.assertTrue(any(item["layer"] == "drafts" for item in data["files"]))
            self.assertTrue(any(item["suggested_target_path"].startswith("04_structure/") for item in data["files"]))
            self.assertTrue(any(item["migration_phase"] == "draft-import" for item in data["files"]))
            self.assertTrue(any(risk["code"] == "missing_project_config" for risk in data["risks"]))

            written = self.run_cli("adopt", str(target), "--out", "adopt_report.md")
            self.assertIn("Wrote FictionOps adopt report", written.stdout)
            output = target / "adopt_report.md"
            self.assertTrue(output.exists())
            report_text = output.read_text(encoding="utf-8")
            self.assertIn("# FictionOps Adopt Report", report_text)
            self.assertIn("Suggested Target", report_text)

            failed = self.run_cli("adopt", str(target), "--out", "adopt_report.md", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_adopt_can_copy_into_initialized_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            sandbox = Path(tmp) / "sandbox"
            legacy.mkdir()
            create_project(sandbox, title="Sandbox Novel", language="zh-CN", force=False, dry_run=False)
            (legacy / "handoff.md").write_text("# Handoff\n\ncurrent state\n", encoding="utf-8")
            (legacy / "book_outline.md").write_text("# Book Outline\n\nchapter plan\n", encoding="utf-8")
            (legacy / "ch_001.md").write_text("# Chapter 001\n\nold draft\n", encoding="utf-8")

            dry_report = build_adopt_report(legacy, max_files=20, copy_to=str(sandbox), dry_run=True)
            self.assertEqual(dry_report.copy_to, str(sandbox.resolve()))
            self.assertEqual(dry_report.planned_copies, 3)
            self.assertEqual(dry_report.copied_files, 0)
            self.assertFalse((sandbox / "00_management" / "adopted_handoff" / "handoff.md").exists())

            report = build_adopt_report(legacy, max_files=20, copy_to=str(sandbox))
            self.assertEqual(report.copied_files, 3)
            self.assertEqual(report.skipped_files, 0)
            self.assertTrue((sandbox / "00_management" / "adopted_handoff" / "handoff.md").exists())
            self.assertTrue((sandbox / "04_structure" / "book_outlines" / "imported" / "book_outline.md").exists())
            self.assertEqual((sandbox / "06_drafts" / "import_queue" / "ch_001.md").read_text(encoding="utf-8"), "# Chapter 001\n\nold draft\n")
            manifest = sandbox / "00_management" / "adopted_handoff" / "adopt_manifest.json"
            self.assertTrue(manifest.exists())
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest_data["schema"], "fictionops.adopt_manifest.v1")
            self.assertTrue(any(item["target_path"].replace("\\", "/") == "06_drafts/import_queue/ch_001.md" for item in manifest_data["files"]))

            second_report = build_adopt_report(legacy, max_files=20, copy_to=str(sandbox))
            self.assertEqual(second_report.copied_files, 0)
            self.assertEqual(second_report.skipped_files, 3)
            self.assertTrue(all(item.status == "skipped_exists" for item in second_report.copy_files))

            cli_sandbox = Path(tmp) / "cli-sandbox"
            create_project(cli_sandbox, title="CLI Sandbox", language="zh-CN", force=False, dry_run=False)
            cli_result = self.run_cli("adopt", str(legacy), "--copy-to", str(cli_sandbox), "--format", "json")
            data = json.loads(cli_result.stdout)
            self.assertEqual(data["copied_files"], 3)
            self.assertEqual(data["copy_to"], str(cli_sandbox.resolve()))
            self.assertTrue((cli_sandbox / "06_drafts" / "import_queue" / "ch_001.md").exists())

    def test_adopt_copy_disambiguates_same_target_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            sandbox = Path(tmp) / "sandbox"
            (legacy / "book_a").mkdir(parents=True)
            (legacy / "book_b").mkdir(parents=True)
            create_project(sandbox, title="Collision Sandbox", language="zh-CN", force=False, dry_run=False)
            (legacy / "book_a" / "ch_001.md").write_text("# Chapter 001\n\nold draft A\n", encoding="utf-8")
            (legacy / "book_b" / "ch_001.md").write_text("# Chapter 001\n\nold draft B\n", encoding="utf-8")

            report = build_adopt_report(legacy, max_files=20, copy_to=str(sandbox))
            self.assertEqual(report.copied_files, 2)
            self.assertEqual(report.skipped_files, 0)
            target_paths = [item.target_path for item in report.copy_files]
            normalized_paths = [path.replace("\\", "/") for path in target_paths]
            self.assertEqual(len(set(target_paths)), 2)
            self.assertIn("06_drafts/import_queue/ch_001.md", normalized_paths)
            self.assertTrue(any(path.startswith("06_drafts/import_queue/ch_001.") for path in normalized_paths))
            self.assertTrue(any("unique target path" in item.message for item in report.copy_files))
            for target_path in target_paths:
                self.assertTrue((sandbox / target_path).exists())

            second_report = build_adopt_report(legacy, max_files=20, copy_to=str(sandbox))
            self.assertEqual(second_report.copied_files, 0)
            self.assertEqual(second_report.skipped_files, 2)
            self.assertTrue(all(item.status == "skipped_exists" for item in second_report.copy_files))

    def test_adopt_review_reports_migration_sandbox_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            sandbox = Path(tmp) / "sandbox"
            legacy.mkdir()
            create_project(sandbox, title="Migration Sandbox", language="zh-CN", force=False, dry_run=False)
            (legacy / "handoff.md").write_text("# Handoff\n\ncurrent state\n", encoding="utf-8")
            (legacy / "ch_001.md").write_text("# Chapter 001\n\nold draft\n", encoding="utf-8")

            build_adopt_report(legacy, max_files=20, copy_to=str(sandbox))
            report = build_adopt_review(
                sandbox,
                book="book_01",
                min_chapter_chars=20,
                scan_text=False,
                max_issues=20,
            )
            self.assertEqual(report.status, "needs_import_sorting")
            self.assertFalse(report.ready)
            self.assertEqual(report.import_queue_files, 1)
            self.assertTrue(any(issue.code == "import_queue_unsorted" for issue in report.issues))
            self.assertTrue(any(check.name == "Book gate" for check in report.checks))

            result = self.run_cli("adopt-review", str(sandbox), "--format", "json", "--min-chapter-chars", "20")
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "needs_import_sorting")
            self.assertEqual(data["import_queue_files"], 1)
            self.assertIn("doctor", data)
            self.assertIn("book_gate", data)

            written = self.run_cli("adopt-review", str(sandbox), "--out", "07_audits/adopt_review/report.md")
            self.assertIn("Wrote FictionOps adopt-review report", written.stdout)
            output = sandbox / "07_audits" / "adopt_review" / "report.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Adopt Review", output.read_text(encoding="utf-8"))

            failed = self.run_cli("adopt-review", str(sandbox), "--out", "07_audits/adopt_review/report.md", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_adopt_plan_turns_review_findings_into_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            sandbox = Path(tmp) / "sandbox"
            legacy.mkdir()
            create_project(sandbox, title="Migration Sandbox", language="zh-CN", force=False, dry_run=False)
            (legacy / "handoff.md").write_text("# Handoff\n\ncurrent state\n", encoding="utf-8")
            (legacy / "ch_001.md").write_text("# Chapter 001\n\nold draft\n", encoding="utf-8")

            build_adopt_report(legacy, max_files=20, copy_to=str(sandbox))
            report = build_adopt_plan(
                sandbox,
                book="book_01",
                min_chapter_chars=20,
                scan_text=False,
            )
            self.assertEqual(report.review_status, "needs_import_sorting")
            self.assertFalse(report.review_ready)
            self.assertGreater(report.task_count, 0)
            self.assertGreater(len(report.task_groups), 0)
            self.assertTrue(any(task.code == "import_queue_unsorted" for task in report.tasks))
            self.assertTrue(any("Move each imported draft-like file" in task.suggested_action for task in report.tasks))
            import_groups = [group for group in report.task_groups if group.code == "import_queue_unsorted"]
            self.assertEqual(len(import_groups), 1)
            self.assertEqual(import_groups[0].phase, "01_migration_shape")
            self.assertGreaterEqual(import_groups[0].blocking_count, 1)

            result = self.run_cli("adopt-plan", str(sandbox), "--format", "json", "--min-chapter-chars", "20")
            data = json.loads(result.stdout)
            self.assertEqual(data["review_status"], "needs_import_sorting")
            self.assertGreater(data["task_count"], 0)
            self.assertIn("task_groups", data)
            self.assertTrue(any(group["code"] == "import_queue_unsorted" for group in data["task_groups"]))
            self.assertIn("adopt_review", data)

            grouped = self.run_cli(
                "adopt-plan",
                str(sandbox),
                "--write-groups",
                "07_audits/adopt_review/groups",
                "--format",
                "json",
                "--min-chapter-chars",
                "20",
            )
            grouped_data = json.loads(grouped.stdout)
            self.assertGreater(grouped_data["group_files_written"], 1)
            self.assertIn("group_files", grouped_data)
            group_dir = sandbox / "07_audits" / "adopt_review" / "groups"
            self.assertTrue((group_dir / "index.md").exists())
            group_files = sorted(path for path in group_dir.glob("*.md") if path.name != "index.md")
            self.assertEqual(len(group_files), grouped_data["group_files_written"] - 1)
            group_text = group_files[0].read_text(encoding="utf-8")
            self.assertIn("## Suggested Action", group_text)
            self.assertIn("[ ]", group_text)

            failed_group_write = self.run_cli(
                "adopt-plan",
                str(sandbox),
                "--write-groups",
                "07_audits/adopt_review/groups",
                check=False,
            )
            self.assertNotEqual(failed_group_write.returncode, 0)
            self.assertIn("Use --force to overwrite", failed_group_write.stderr)

            written = self.run_cli("adopt-plan", str(sandbox), "--out", "07_audits/adopt_review/plan.md")
            self.assertIn("Wrote FictionOps adopt-plan report", written.stdout)
            output = sandbox / "07_audits" / "adopt_review" / "plan.md"
            self.assertTrue(output.exists())
            output_text = output.read_text(encoding="utf-8")
            self.assertIn("# FictionOps Adopt Plan", output_text)
            self.assertIn("## Repair Groups", output_text)

            failed = self.run_cli("adopt-plan", str(sandbox), "--out", "07_audits/adopt_review/plan.md", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_adopt_review_waivers_defer_explicit_blockers(self) -> None:
        temp, target = self.make_project("Waiver Sandbox")
        with temp:
            baseline = build_adopt_review(
                target,
                book="book_01",
                min_chapter_chars=20,
                scan_text=False,
                max_issues=500,
            )
            blocking_issues = [issue for issue in baseline.issues if issue.severity in {"P1", "P2"}]
            self.assertGreater(len(blocking_issues), 0)
            self.assertEqual(baseline.status, "needs_migration_fixes")

            waiver_dir = target / "07_audits" / "adopt_review"
            waiver_dir.mkdir(parents=True, exist_ok=True)
            waiver_file = waiver_dir / "waivers.json"
            waiver_file.write_text(
                json.dumps(
                    {
                        "waivers": [
                            {
                                "source": issue.source,
                                "code": issue.code,
                                "subject": issue.subject,
                                "path": issue.path,
                                "reason": "Deferred during migration dogfood; captured for explicit human follow-up.",
                                "owner": "author",
                                "until": "0.2 dogfood",
                            }
                            for issue in blocking_issues
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            reviewed = build_adopt_review(
                target,
                book="book_01",
                min_chapter_chars=20,
                scan_text=False,
                max_issues=500,
            )
            self.assertTrue(reviewed.ready)
            self.assertEqual(reviewed.status, "migration_notes")
            self.assertEqual(reviewed.blocking_issue_count, 0)
            self.assertEqual(reviewed.waived_issue_count, len(blocking_issues))
            self.assertGreater(reviewed.total_issue_count, reviewed.issue_count)
            self.assertEqual(reviewed.waiver_file, str(waiver_file.resolve()))
            self.assertTrue(all(issue.severity not in {"P1", "P2"} for issue in reviewed.issues))

            result = self.run_cli("adopt-review", str(target), "--format", "json", "--min-chapter-chars", "20")
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "migration_notes")
            self.assertEqual(data["blocking_issue_count"], 0)
            self.assertEqual(data["waived_issue_count"], len(blocking_issues))
            self.assertEqual(len(data["waivers"]), len(blocking_issues))

            plan = build_adopt_plan(
                target,
                book="book_01",
                min_chapter_chars=20,
                scan_text=False,
                max_issues=500,
            )
            self.assertTrue(plan.review_ready)
            self.assertEqual(plan.priority_counts["P1"], 0)
            self.assertEqual(plan.priority_counts["P2"], 0)

            explicit_plan = self.run_cli(
                "adopt-plan",
                str(target),
                "--format",
                "json",
                "--min-chapter-chars",
                "20",
                "--waivers",
                "07_audits/adopt_review/waivers.json",
            )
            plan_data = json.loads(explicit_plan.stdout)
            self.assertEqual(plan_data["adopt_review"]["waived_issue_count"], len(blocking_issues))
            self.assertEqual(plan_data["priority_counts"]["P1"], 0)
            self.assertEqual(plan_data["priority_counts"]["P2"], 0)

    def test_import_plan_suggests_and_applies_safe_import_moves(self) -> None:
        temp, target = self.make_project("Import Sandbox")
        with temp:
            queue = target / "06_drafts" / "import_queue"
            queue.mkdir(parents=True, exist_ok=True)
            (queue / "ch_001.md").write_text("# Chapter 001\n\nlegacy first chapter\n", encoding="utf-8")
            (queue / "ch_002.md").write_text("# Chapter 002\n\nold draft\n", encoding="utf-8")
            (queue / "mystery.md").write_text("# Unnumbered Scene\n\nold draft\n", encoding="utf-8")
            (queue / "ch_003.md").write_text("# Chapter 003\n\nold draft\n", encoding="utf-8")
            (queue / "ch_004.md").write_text("# Chapter 004\n\nold draft from book two\n", encoding="utf-8")
            existing = target / "06_drafts" / "book_01" / "chapters" / "ch_003.md"
            existing.write_text("# Existing Chapter 003\n\n" + ("keep this existing manuscript text because it is not a generated placeholder. " * 4), encoding="utf-8")
            manifest = target / "00_management" / "adopted_handoff" / "adopt_manifest.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "fictionops.adopt_manifest.v1",
                        "files": [
                            {
                                "source_path": "legacy/book_02/ch_004.md",
                                "target_path": "06_drafts/import_queue/ch_004.md",
                                "status": "copied",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_import_plan(target, book="book_01")
            self.assertEqual(report.import_queue_files, 5)
            self.assertEqual(report.ready_count, 2)
            self.assertEqual(report.target_exists_count, 1)
            self.assertEqual(report.placeholder_target_count, 1)
            self.assertEqual(report.needs_review_count, 3)
            ready = [item for item in report.items if item.status == "ready"]
            self.assertEqual(len(ready), 2)
            self.assertTrue(any(item.target_path.replace("\\", "/").endswith("06_drafts/book_01/chapters/ch_002.md") for item in ready))
            self.assertTrue(any(item.inferred_book == "book_02" and item.target_path.replace("\\", "/").endswith("06_drafts/book_02/chapters/ch_004.md") for item in ready))
            self.assertTrue(any(item.status == "placeholder_target" and item.inferred_chapter == "001" for item in report.items))

            result = self.run_cli("import-plan", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["import_queue_files"], 5)
            self.assertEqual(data["ready_count"], 2)
            self.assertEqual(data["placeholder_target_count"], 1)
            self.assertTrue(any(item["status"] == "needs_chapter" for item in data["items"]))

            written = self.run_cli("import-plan", str(target), "--out", "07_audits/adopt_review/import_plan.md")
            self.assertIn("Wrote FictionOps import-plan report", written.stdout)
            output = target / "07_audits" / "adopt_review" / "import_plan.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Import Plan", output.read_text(encoding="utf-8"))

            failed = self.run_cli("import-plan", str(target), "--out", "07_audits/adopt_review/import_plan.md", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

            applied = build_import_plan(target, book="book_01", apply=True, create_scaffolds=True, replace_placeholder_targets=True)
            self.assertEqual(applied.moved_files, 3)
            self.assertEqual(applied.replaced_placeholder_targets, 1)
            self.assertTrue(applied.replace_placeholder_targets)
            self.assertTrue(applied.create_scaffolds)
            self.assertEqual(applied.scaffold_created_files, 5)
            self.assertEqual(applied.scaffold_skipped_files, 4)
            self.assertFalse((queue / "ch_001.md").exists())
            self.assertEqual((target / "06_drafts" / "book_01" / "chapters" / "ch_001.md").read_text(encoding="utf-8"), "# Chapter 001\n\nlegacy first chapter\n")
            self.assertFalse((queue / "ch_002.md").exists())
            self.assertTrue((target / "06_drafts" / "book_01" / "chapters" / "ch_002.md").exists())
            self.assertTrue((target / "06_drafts" / "book_01" / "chapter_engines" / "ch_002_engine.md").exists())
            self.assertTrue((target / "06_drafts" / "book_01" / "revision_notes" / "ch_002_retrospective.md").exists())
            self.assertFalse((queue / "ch_004.md").exists())
            self.assertTrue((target / "06_drafts" / "book_02" / "chapters" / "ch_004.md").exists())
            self.assertTrue((target / "06_drafts" / "book_02" / "chapter_engines" / "ch_004_engine.md").exists())
            self.assertTrue((target / "06_drafts" / "book_02" / "revision_notes" / "ch_004_retrospective.md").exists())
            self.assertTrue((queue / "mystery.md").exists())
            self.assertTrue((queue / "ch_003.md").exists())
            self.assertIn("keep this existing manuscript text", existing.read_text(encoding="utf-8"))

    def test_cli_help_covers_all_mvp_commands(self) -> None:
        root_help = self.run_cli("--help")
        self.assertIn("FictionOps long-form fiction project toolkit", root_help.stdout)
        for command in CLI_COMMANDS:
            self.assertIn(command, root_help.stdout)
            command_help = self.run_cli(command, "--help")
            self.assertIn("usage:", command_help.stdout.lower())
            self.assertIn(command, command_help.stdout)
        self.assertTrue(set(CLI_COMMANDS).issubset(RECOGNIZED_FICTIONOPS_COMMANDS))

    def test_cli_contracts_document_all_mvp_commands(self) -> None:
        contracts = (ROOT / "docs" / "cli-contracts.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("## 1. 通用契约", contracts)
        self.assertIn("## 7. 帮助文案契约", contracts)
        for command in CLI_COMMANDS:
            self.assertIn(f"`fictionops {command}`", contracts)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        cli_doc = (ROOT / "docs" / "cli.zh-CN.md").read_text(encoding="utf-8")
        for text in (readme, readme_zh, cli_doc):
            self.assertIn("cli-contracts.zh-CN.md", text)

    def test_release_governance_files_are_documented(self) -> None:
        required = [
            "LICENSE",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "CONTRIBUTING.zh-CN.md",
            "docs/getting-started.md",
            "docs/getting-started.zh-CN.md",
            "docs/assets/quickstart-terminal.svg",
            "docs/cli.md",
            "docs/cli-contracts.md",
            "docs/agent-protocol.md",
            "docs/agent-connector-contract.md",
            "docs/agent-connector-contract.zh-CN.md",
            "docs/agent-integration.md",
            "docs/agent-integration.zh-CN.md",
            "docs/model-providers.md",
            "docs/model-providers.zh-CN.md",
            "docs/agent-workflow.md",
            "docs/agent-workflow.zh-CN.md",
            "docs/agent-evaluation.md",
            "docs/agent-evaluation.zh-CN.md",
            "docs/agent-evaluation-demo-report.md",
            "docs/tutorial-demo.md",
            "docs/migration.md",
            "docs/end-to-end-migration-publish.md",
            "docs/testing.md",
            "docs/interview-agent-research-case.zh-CN.md",
            "docs/interview-agent-script.zh-CN.md",
            "docs/evidence/failure-lab-current.json",
            "docs/release.md",
            "docs/release-trial-evidence.md",
            "docs/release-trial-evidence.zh-CN.md",
            "docs/compatibility.md",
            "docs/compatibility.zh-CN.md",
            "docs/known-limits.md",
            "docs/known-limits.zh-CN.md",
            "docs/recovery.md",
            "docs/recovery.zh-CN.md",
            "docs/release-checklist.zh-CN.md",
            "docs/pypi-release.zh-CN.md",
            "docs/release-notes-0.1.0.zh-CN.md",
            "docs/completion-audit-0.1.0.zh-CN.md",
            "docs/roadmap.md",
            "docs/roadmap.zh-CN.md",
            "docs/milestone-status.md",
            "docs/milestone-status.zh-CN.md",
            "docs/stable-core-remaining-checklist.md",
            "docs/stable-core-remaining-checklist.zh-CN.md",
            "docs/stable-core-audit.md",
            "docs/stable-core-audit.zh-CN.md",
            "docs/dogfood-legacy-adopt.zh-CN.md",
            "docs/dogfood-cycle-evidence.md",
            "docs/dogfood-cycle-evidence.zh-CN.md",
        ]
        for rel_path in required:
            self.assertTrue((ROOT / rel_path).exists(), f"missing release governance file: {rel_path}")
        self.assertTrue((ROOT.parent / ".github" / "workflows" / "fictionops-ci.yml").exists(), "missing FictionOps CI workflow")
        self.assertTrue((ROOT.parent / "README.md").exists(), "missing GitHub root README")
        self.assertTrue((ROOT.parent / "LICENSE").exists(), "missing GitHub root license")
        self.assertTrue((ROOT.parent / "CITATION.cff").exists(), "missing GitHub citation metadata")
        publish_workflow = ROOT.parent / ".github" / "workflows" / "fictionops-publish.yml"
        self.assertTrue(publish_workflow.exists(), "missing FictionOps publish workflow")
        self.assertTrue((ROOT.parent / ".github" / "pull_request_template.md").exists(), "missing PR template")

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [0.1.0]", changelog)
        self.assertIn("Packaged templates", changelog)
        self.assertIn("Book-level closing gate aggregation across plan, retrospective, revision, table structure, word-scan, and wave checks", changelog)
        self.assertIn("Final release gate aggregation across book closure, publish, metadata, manifest, and EPUB checks", changelog)
        self.assertIn("Book-gate and release-gate milestone summaries in `doctor` and `report`", changelog)
        self.assertIn("Handoff context packs now include model config, character memory, canon state, revision plans, and gate reports", changelog)
        self.assertIn("Context packs, draft briefs, and agent prompts now support total embedded-content budgets", changelog)
        self.assertIn("Agent next-step selection with `agent-next`", changelog)
        self.assertIn("examples/agent_controller_next.py", changelog)
        self.assertIn("examples/agent_controller_loop.py", changelog)
        self.assertIn("Agent integration guide", changelog)
        self.assertIn("Agent connector contract", changelog)
        self.assertIn("Runnable `examples/demo_novel` project and demo tutorial", changelog)
        self.assertIn("Runnable `examples/legacy_novel_source` project", changelog)
        self.assertIn("GitHub Actions CI plus issue and pull request templates", changelog)
        self.assertIn("Manual PyPI/TestPyPI publish workflow using trusted publishing", changelog)
        self.assertIn("Release trial evidence template", changelog)
        self.assertIn("Package release evidence auditing with `audit-release-evidence`", changelog)
        self.assertIn("Sustained real-project dogfood-cycle auditing with `audit-dogfood-cycle`", changelog)
        self.assertIn("Stable-core evidence aggregation with `audit-stable-core`", changelog)
        self.assertIn("0.1.0 release notes and completion audit", changelog)
        self.assertIn("Known-limits documentation", changelog)
        self.assertIn("Recovery playbook", changelog)
        self.assertIn("Compatibility policy", changelog)
        self.assertIn("Milestone status ledger", changelog)
        self.assertIn("Stable core audit", changelog)
        self.assertIn("English entry documentation for the core CLI, agent protocol, and demo tutorial", changelog)
        self.assertIn("English migration, testing, release, and contribution guides", changelog)
        self.assertIn("English end-to-end migration and publishing case", changelog)

        publish_text = publish_workflow.read_text(encoding="utf-8")
        ci_text = (ROOT.parent / ".github" / "workflows" / "fictionops-ci.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", publish_text)
        self.assertIn("id-token: write", publish_text)
        self.assertIn("pypa/gh-action-pypi-publish@release/v1", publish_text)
        self.assertIn("repository-url: https://test.pypi.org/legacy/", publish_text)
        self.assertIn("version mismatch", publish_text)
        self.assertIn("Write release trial evidence draft", publish_text)
        self.assertIn("sha256sum", publish_text)
        self.assertIn("GitHub Actions run URL", publish_text)
        self.assertIn("fictionops-release-trial-evidence-${{ steps.version.outputs.version }}", publish_text)
        self.assertIn("path: fictionops/release-trial-evidence/*", publish_text)
        for workflow_text in (ci_text, publish_text):
            self.assertIn("Install built wheel smoke", workflow_text)
            self.assertIn("python -m pip install --no-deps dist/fictionops-*.whl", workflow_text)
            self.assertIn("fictionops doctor", workflow_text)
            self.assertIn("fictionops eval-agent --help", workflow_text)
            self.assertIn("fictionops agent-smoke --help", workflow_text)
            self.assertIn("fictionops audit-agent-workflow --help", workflow_text)
            self.assertIn("fictionops audit-release-evidence --help", workflow_text)
            self.assertIn("fictionops audit-dogfood-cycle --help", workflow_text)
            self.assertIn("fictionops audit-stability-window --help", workflow_text)
            self.assertIn("fictionops audit-stable-core --help", workflow_text)
            self.assertIn("docs/agent-connector-contract.md", workflow_text)
            self.assertIn("docs/agent-integration.md", workflow_text)
            self.assertIn("docs/end-to-end-migration-publish.md", workflow_text)
            self.assertIn("docs/release-trial-evidence.md", workflow_text)
            self.assertIn("docs/release-trial-evidence.zh-CN.md", workflow_text)
            self.assertIn("docs/compatibility.md", workflow_text)
            self.assertIn("docs/known-limits.md", workflow_text)
            self.assertIn("docs/recovery.md", workflow_text)
            self.assertIn("docs/milestone-status.md", workflow_text)
            self.assertIn("docs/stable-core-remaining-checklist.md", workflow_text)
            self.assertIn("docs/stable-core-remaining-checklist.zh-CN.md", workflow_text)
            self.assertIn("docs/stable-core-audit.md", workflow_text)
            self.assertIn("docs/stable-core-audit.zh-CN.md", workflow_text)
            self.assertIn("docs/dogfood-cycle-evidence.md", workflow_text)
            self.assertIn("docs/dogfood-cycle-evidence.zh-CN.md", workflow_text)
            self.assertIn("docs/stability-window-evidence.md", workflow_text)
            self.assertIn("docs/stability-window-evidence.zh-CN.md", workflow_text)
            self.assertIn("docs/getting-started.md", workflow_text)
            self.assertIn("docs/model-providers.md", workflow_text)
            self.assertIn("examples/agent_runner_openai_chat.py", workflow_text)
            self.assertIn("examples/agent_runner_openai_responses.py", workflow_text)
            self.assertIn("examples/agent_controller_loop.py", workflow_text)

        root_readme = (ROOT.parent / "README.md").read_text(encoding="utf-8")
        root_citation = (ROOT.parent / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn("local-first CLI workflow system", root_readme)
        self.assertIn("30 Second Quick Start", root_readme)
        self.assertIn("python -m pip install fictionops", root_readme)
        self.assertIn("agent_runner_openai_chat.py", root_readme)
        self.assertIn("Roadmap", root_readme)
        self.assertIn("cff-version: 1.2.0", root_citation)
        self.assertIn("repository-code: \"https://github.com/SouthWinter/fictionops\"", root_citation)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for text in (readme, readme_zh):
            self.assertIn("LICENSE", text)
            self.assertIn("CHANGELOG.md", text)
            self.assertIn("CONTRIBUTING.md", text)
            self.assertIn("CONTRIBUTING.zh-CN.md", text)
            self.assertIn("getting-started", text)
            self.assertIn("model-providers", text)
            self.assertIn("docs/migration.md", text)
            self.assertIn("end-to-end-migration-publish", text)
            self.assertIn("agent-connector-contract", text)
            self.assertIn("agent-integration", text)
            self.assertIn("docs/testing.md", text)
            self.assertIn("docs/release.md", text)
            self.assertIn("release-trial-evidence", text)
            self.assertIn("release trial evidence", text)
            self.assertIn("audit-release-evidence", text)
            self.assertIn("audit-dogfood-cycle", text)
            self.assertIn("audit-stable-core", text)
            self.assertIn("dogfood-cycle-evidence", text)
            self.assertIn("stability-window-evidence", text)
            self.assertIn("compatibility", text)
            self.assertIn("known-limits", text)
            self.assertIn("recovery", text)
            self.assertIn("release-checklist.zh-CN.md", text)
            self.assertIn("pypi-release.zh-CN.md", text)
            self.assertIn("release-notes-0.1.0.zh-CN.md", text)
            self.assertIn("completion-audit-0.1.0.zh-CN.md", text)
            self.assertIn("roadmap.md", text)
            self.assertIn("roadmap.zh-CN.md", text)
            self.assertIn("milestone-status", text)
            self.assertIn("stable-core-remaining-checklist", text)
            self.assertIn("stable-core-audit", text)
            self.assertIn("dogfood-legacy-adopt.zh-CN.md", text)
            self.assertIn("legacy_novel_source", text)

        english_cli = (ROOT / "docs" / "cli.md").read_text(encoding="utf-8")
        english_cli_contracts = (ROOT / "docs" / "cli-contracts.md").read_text(encoding="utf-8")
        english_agent = (ROOT / "docs" / "agent-protocol.md").read_text(encoding="utf-8")
        english_agent_connector = (ROOT / "docs" / "agent-connector-contract.md").read_text(encoding="utf-8")
        chinese_agent_connector = (ROOT / "docs" / "agent-connector-contract.zh-CN.md").read_text(encoding="utf-8")
        english_agent_integration = (ROOT / "docs" / "agent-integration.md").read_text(encoding="utf-8")
        chinese_agent_integration = (ROOT / "docs" / "agent-integration.zh-CN.md").read_text(encoding="utf-8")
        english_model_providers = (ROOT / "docs" / "model-providers.md").read_text(encoding="utf-8")
        chinese_model_providers = (ROOT / "docs" / "model-providers.zh-CN.md").read_text(encoding="utf-8")
        english_agent_workflow = (ROOT / "docs" / "agent-workflow.md").read_text(encoding="utf-8")
        english_tutorial = (ROOT / "docs" / "tutorial-demo.md").read_text(encoding="utf-8")
        english_migration = (ROOT / "docs" / "migration.md").read_text(encoding="utf-8")
        english_end_to_end = (ROOT / "docs" / "end-to-end-migration-publish.md").read_text(encoding="utf-8")
        english_testing = (ROOT / "docs" / "testing.md").read_text(encoding="utf-8")
        english_release = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
        english_release_trial = (ROOT / "docs" / "release-trial-evidence.md").read_text(encoding="utf-8")
        chinese_release_trial = (ROOT / "docs" / "release-trial-evidence.zh-CN.md").read_text(encoding="utf-8")
        english_compatibility = (ROOT / "docs" / "compatibility.md").read_text(encoding="utf-8")
        chinese_compatibility = (ROOT / "docs" / "compatibility.zh-CN.md").read_text(encoding="utf-8")
        english_known_limits = (ROOT / "docs" / "known-limits.md").read_text(encoding="utf-8")
        chinese_known_limits = (ROOT / "docs" / "known-limits.zh-CN.md").read_text(encoding="utf-8")
        english_recovery = (ROOT / "docs" / "recovery.md").read_text(encoding="utf-8")
        chinese_recovery = (ROOT / "docs" / "recovery.zh-CN.md").read_text(encoding="utf-8")
        english_roadmap = (ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")
        chinese_roadmap = (ROOT / "docs" / "roadmap.zh-CN.md").read_text(encoding="utf-8")
        english_milestones = (ROOT / "docs" / "milestone-status.md").read_text(encoding="utf-8")
        chinese_milestones = (ROOT / "docs" / "milestone-status.zh-CN.md").read_text(encoding="utf-8")
        english_remaining = (ROOT / "docs" / "stable-core-remaining-checklist.md").read_text(encoding="utf-8")
        chinese_remaining = (ROOT / "docs" / "stable-core-remaining-checklist.zh-CN.md").read_text(encoding="utf-8")
        english_stable_core = (ROOT / "docs" / "stable-core-audit.md").read_text(encoding="utf-8")
        chinese_stable_core = (ROOT / "docs" / "stable-core-audit.zh-CN.md").read_text(encoding="utf-8")
        chinese_dogfood = (ROOT / "docs" / "dogfood-legacy-adopt.zh-CN.md").read_text(encoding="utf-8")
        english_dogfood_cycle = (ROOT / "docs" / "dogfood-cycle-evidence.md").read_text(encoding="utf-8")
        chinese_dogfood_cycle = (ROOT / "docs" / "dogfood-cycle-evidence.zh-CN.md").read_text(encoding="utf-8")
        english_stability_window = (ROOT / "docs" / "stability-window-evidence.md").read_text(encoding="utf-8")
        chinese_stability_window = (ROOT / "docs" / "stability-window-evidence.zh-CN.md").read_text(encoding="utf-8")
        english_contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("Command Groups", english_cli)
        self.assertIn("Agent Workflow", english_cli)
        self.assertIn("audit-agent-workflow", english_cli)
        self.assertIn("Read/Write Boundaries", english_cli_contracts)
        self.assertIn("Agent Safety Contract", english_cli_contracts)
        self.assertIn("audit-agent-workflow", english_cli_contracts)
        self.assertIn("outside the FictionOps 0.1.0 safety contract", english_cli_contracts)
        self.assertIn("Execute An External Runner", english_agent)
        self.assertIn("Select The Next Safe Step", english_agent)
        self.assertIn("agent_controller_next.py", english_agent)
        self.assertIn("agent_controller_loop.py", english_agent)
        self.assertIn("agent_runner_echo.py", english_agent)
        self.assertIn("agent_runner_openai_responses.py", english_agent)
        self.assertIn("agent_runner_openai_chat.py", english_agent)
        self.assertIn("Agent integration guide", english_agent)
        self.assertIn("Agent connector contract", english_agent)
        self.assertIn("Runner Contract", english_agent_connector)
        self.assertIn("Controller Contract", english_agent_connector)
        self.assertIn("Minimal Smoke Test", english_agent_connector)
        self.assertIn("agent-inbox", english_agent_connector)
        self.assertIn("agent_runner_openai_chat.py", english_agent_connector)
        self.assertIn("Agent 接入契约", chinese_agent_connector)
        self.assertIn("Runner 契约", chinese_agent_connector)
        self.assertIn("Integration Levels", english_agent_integration)
        self.assertIn("External Runner", english_agent_integration)
        self.assertIn("Controller Loop", english_agent_integration)
        self.assertIn("OpenAI-Compatible Chat Runner", english_agent_integration)
        self.assertIn("staged output", english_agent_integration)
        self.assertIn("audit-agent-workflow", english_agent_integration)
        self.assertIn("DeepSeek", english_model_providers)
        self.assertIn("Chat Completions", english_model_providers)
        self.assertIn("DeepSeek", chinese_model_providers)
        self.assertIn("通义千问", chinese_model_providers)
        self.assertIn("接入层级", chinese_agent_integration)
        self.assertIn("FictionOps agentic workflow", english_agent_workflow)
        self.assertIn("audit-agent-workflow", english_agent_workflow)
        self.assertIn("outside FictionOps safety contract", english_agent_workflow)
        self.assertIn("Prepare And Execute A Demo Agent Run", english_tutorial)
        self.assertIn("Ask A Demo Controller For The Next Step", english_tutorial)
        self.assertIn("agent_controller_loop.py", english_tutorial)
        self.assertIn("agent-inbox", english_tutorial)
        self.assertIn("Create A Clean Sandbox", english_migration)
        self.assertIn("Sort Imported Drafts", english_migration)
        self.assertIn("Included Legacy Example", english_migration)
        self.assertIn("End-To-End Migration And Publishing Case", english_end_to_end)
        self.assertIn("needs_import_sorting", english_end_to_end)
        self.assertIn("needs_migration_fixes", english_end_to_end)
        self.assertIn("export-epub", english_end_to_end)
        self.assertIn("release-gate", english_end_to_end)
        test_count = len([name for name in dir(type(self)) if name.startswith("test_")])
        self.assertIn("Current Coverage", english_testing)
        self.assertIn(f"{test_count} regression tests", english_testing)
        self.assertIn(f"{test_count} regression tests", readme)
        self.assertIn(f"{test_count} tests", english_milestones)
        self.assertIn(f"{test_count} 个测试", chinese_milestones)
        self.assertIn("Credential Isolation", english_release)
        self.assertIn("TestPyPI", english_release)
        self.assertIn("release-trial-evidence.md", english_release)
        self.assertIn("workflow-generated release trial evidence draft artifact", english_release)
        self.assertIn("fictionops-release-trial-evidence-<version>", english_release)
        self.assertIn("audit-release-evidence", english_release)
        self.assertIn("GitHub Actions run URL", english_release_trial)
        self.assertIn("TestPyPI project URL", english_release_trial)
        self.assertIn("fictionops --version", english_release_trial)
        self.assertIn("accepted/deferred/failed", english_release_trial)
        self.assertIn("not passed", english_release_trial)
        self.assertIn("YYYY-MM-DDTHH:MM:SSZ", english_release_trial)
        self.assertIn("https://github.com/<owner>/<repo>/actions/runs/<run-id>", english_release_trial)
        self.assertIn("https://test.pypi.org/project/...", english_release_trial)
        self.assertIn("Version` must match", english_release_trial)
        self.assertIn("workflow-generated release trial evidence draft", english_release_trial)
        self.assertIn("fictionops-release-trial-evidence-<version>", english_release_trial)
        self.assertIn("audit-release-evidence", english_release_trial)
        self.assertIn("GitHub Actions run URL", chinese_release_trial)
        self.assertIn("TestPyPI project URL", chinese_release_trial)
        self.assertIn("fictionops --version", chinese_release_trial)
        self.assertIn("accepted/deferred/failed", chinese_release_trial)
        self.assertIn("not passed", chinese_release_trial)
        self.assertIn("YYYY-MM-DDTHH:MM:SSZ", chinese_release_trial)
        self.assertIn("https://github.com/<owner>/<repo>/actions/runs/<run-id>", chinese_release_trial)
        self.assertIn("https://test.pypi.org/project/...", chinese_release_trial)
        self.assertIn("`Version` 必须与项目版本一致", chinese_release_trial)
        self.assertIn("Workflow-generated draft", chinese_release_trial)
        self.assertIn("fictionops-release-trial-evidence-<version>", chinese_release_trial)
        self.assertIn("audit-release-evidence", chinese_release_trial)
        self.assertIn("Stable Surfaces", english_compatibility)
        self.assertIn("Breaking Changes", english_compatibility)
        self.assertIn("Controller Guidance", english_compatibility)
        self.assertIn("稳定面", chinese_compatibility)
        self.assertIn("破坏性变化", chinese_compatibility)
        self.assertIn("Literary Judgment", english_known_limits)
        self.assertIn("Model Behavior", english_known_limits)
        self.assertIn("Security Boundary", english_known_limits)
        self.assertIn("Recovery playbook", english_known_limits)
        self.assertIn("Recovery Playbook", english_recovery)
        self.assertIn("Import Queue Is Stuck", english_recovery)
        self.assertIn("Publish Artifact Is Missing Or Stale", english_recovery)
        self.assertIn("Controller Repeats The Same Step", english_recovery)
        self.assertIn("recovery still requires human action", english_known_limits)
        self.assertIn("恢复手册", chinese_recovery)
        self.assertIn("文学判断", chinese_known_limits)
        self.assertIn("安全边界", chinese_known_limits)
        self.assertIn("0.2.0 Migration Dogfood", english_roadmap)
        self.assertIn("0.3.0 Agent Controller", english_roadmap)
        self.assertIn("1.0.0 Stable Core", english_roadmap)
        self.assertIn("docs/recovery.md", english_roadmap)
        self.assertIn("milestone-status.md", english_roadmap)
        self.assertIn("stable-core-audit.md", english_roadmap)
        self.assertIn("audit-dogfood-cycle", english_roadmap)
        self.assertIn("audit-stability-window", english_roadmap)
        self.assertIn("audit-stable-core", english_roadmap)
        self.assertIn("Stable Core Audit", english_stable_core)
        self.assertIn("Current result: **not complete**", english_stable_core)
        self.assertIn("Package release evidence exists outside the local checkout", english_stable_core)
        self.assertIn("audit-release-evidence", english_stable_core)
        self.assertIn("audit-dogfood-cycle", english_stable_core)
        self.assertIn("audit-stability-window", english_stable_core)
        self.assertIn("audit-stable-core", english_stable_core)
        self.assertIn("stable-core-remaining-checklist.md", english_stable_core)
        self.assertIn("stability-window-evidence.md", english_stable_core)
        self.assertIn("sustained real-project dogfood cycle", english_stable_core)
        self.assertIn("稳定核心审计", chinese_stable_core)
        self.assertIn("当前结论：**未完成**", chinese_stable_core)
        self.assertIn("本地 checkout 之外存在包发布证据", chinese_stable_core)
        self.assertIn("audit-dogfood-cycle", chinese_stable_core)
        self.assertIn("audit-stability-window", chinese_stable_core)
        self.assertIn("audit-stable-core", chinese_stable_core)
        self.assertIn("stable-core-remaining-checklist.zh-CN.md", chinese_stable_core)
        self.assertIn("Stable Core Remaining Checklist", english_remaining)
        self.assertIn("1.0 Stable Core 剩余执行清单", chinese_remaining)
        for text in (english_remaining, chinese_remaining):
            self.assertIn("audit-release-evidence", text)
            self.assertIn("audit-dogfood-cycle", text)
            self.assertIn("audit-stability-window", text)
            self.assertIn("audit-stable-core", text)
            self.assertIn("ready=true", text)
            self.assertIn("release-trial-evidence.md", text)
            self.assertIn("dogfood-cycle-evidence.md", text)
            self.assertIn("stability-window-evidence.md", text)
        self.assertIn("0.3.0 Agent Controller", english_milestones)
        self.assertIn("0.2.0 Migration Dogfood | Complete locally", english_milestones)
        self.assertIn("0.5.0 Documentation Parity Pass", english_milestones)
        self.assertIn("Complete locally", english_milestones)
        self.assertIn("end-to-end-migration-publish.md", english_milestones)
        self.assertIn("recovery playbook", english_milestones)
        self.assertIn("Externally blocked", english_milestones)
        self.assertIn("TestPyPI", english_milestones)
        self.assertIn("release-trial-evidence.md", english_milestones)
        self.assertIn("workflow-generated release trial evidence draft artifact", english_milestones)
        self.assertIn("audit-release-evidence", english_milestones)
        self.assertIn("audit-dogfood-cycle", english_milestones)
        self.assertIn("audit-stability-window", english_milestones)
        self.assertIn("audit-stable-core", english_milestones)
        self.assertIn("stable-core-audit.md", english_milestones)
        self.assertIn("stable-core-remaining-checklist.md", english_milestones)
        self.assertIn("blocking_issue_count: 0", chinese_milestones)
        self.assertIn("ready: true", chinese_dogfood)
        self.assertIn("import_queue_files", chinese_dogfood)
        self.assertIn("blocking_issue_count", chinese_dogfood)
        self.assertIn("TestPyPI", chinese_milestones)
        self.assertIn("release-trial-evidence.zh-CN.md", chinese_milestones)
        self.assertIn("release trial evidence draft artifact", chinese_milestones)
        self.assertIn("audit-release-evidence", chinese_milestones)
        self.assertIn("audit-dogfood-cycle", chinese_milestones)
        self.assertIn("audit-stability-window", chinese_milestones)
        self.assertIn("audit-stable-core", chinese_milestones)
        self.assertIn("stable-core-audit.zh-CN.md", chinese_milestones)
        self.assertIn("stable-core-remaining-checklist.zh-CN.md", chinese_milestones)
        self.assertIn("0.2.0 迁移 dogfood", chinese_roadmap)
        self.assertIn("1.0.0 稳定核心", chinese_roadmap)
        self.assertIn("stable-core-audit.zh-CN.md", chinese_roadmap)
        self.assertIn("audit-dogfood-cycle", chinese_roadmap)
        self.assertIn("audit-stability-window", chinese_roadmap)
        self.assertIn("audit-stable-core", chinese_roadmap)
        self.assertIn("Design Principles", english_contributing)
        self.assertIn("agent-aware", english_contributing)
        self.assertIn("audit-dogfood-cycle", english_dogfood_cycle)
        self.assertIn("Decision: deferred", english_dogfood_cycle)
        self.assertIn("at least 7 calendar days", english_dogfood_cycle)
        self.assertIn("recognized FictionOps CLI commands", english_dogfood_cycle)
        self.assertIn("audit-dogfood-cycle", chinese_dogfood_cycle)
        self.assertIn("至少覆盖 7 个自然日", chinese_dogfood_cycle)
        self.assertIn("可识别的 FictionOps CLI 命令", chinese_dogfood_cycle)
        self.assertIn("audit-stability-window", english_stability_window)
        self.assertIn("at least 7 calendar days", english_stability_window)
        self.assertIn("must themselves pass `audit-release-evidence` or `audit-dogfood-cycle`", english_stability_window)
        self.assertIn("audited target checkout", english_stability_window)
        self.assertIn("complete `https://...` URLs", english_stability_window)
        self.assertIn("generic home-page links", english_stability_window)
        self.assertIn("audit-stability-window", chinese_stability_window)
        self.assertIn("窗口至少覆盖 7 个自然日", chinese_stability_window)
        self.assertIn("必须分别通过 `audit-release-evidence` 或 `audit-dogfood-cycle`", chinese_stability_window)
        self.assertIn("目标 checkout 内", chinese_stability_window)
        self.assertIn("完整 `https://...` URL", chinese_stability_window)
        self.assertIn("泛泛首页链接", chinese_stability_window)

        release_notes = (ROOT / "docs" / "release-notes-0.1.0.zh-CN.md").read_text(encoding="utf-8")
        completion_audit = (ROOT / "docs" / "completion-audit-0.1.0.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("release-trial-evidence", release_notes)
        self.assertIn("release-trial-evidence", completion_audit)
        self.assertIn("release trial evidence draft artifact", release_notes)
        self.assertIn("release trial evidence draft artifact", completion_audit)
        self.assertIn("稳定核心审计", release_notes)
        self.assertIn("stable-core-audit", completion_audit)
        # Versioned release evidence is immutable; current-suite counts are checked
        # in README/testing/milestone documents above.
        self.assertIn("152 tests OK", release_notes)
        self.assertIn("152 tests OK", completion_audit)
        self.assertIn("audit-release-evidence", release_notes)
        self.assertIn("audit-release-evidence", completion_audit)
        self.assertIn("audit-dogfood-cycle", release_notes)
        self.assertIn("audit-dogfood-cycle", completion_audit)
        self.assertIn("audit-stability-window", release_notes)
        self.assertIn("audit-stability-window", completion_audit)
        self.assertIn("audit-stable-core", release_notes)
        self.assertIn("audit-stable-core", completion_audit)
        self.assertIn("恢复手册", release_notes)
        self.assertIn("安装烟测通过", release_notes)
        self.assertIn("adopt` 只读 dogfood", release_notes)
        self.assertIn("端到端迁移/发布案例", release_notes)
        self.assertIn("当前完成的是 **0.1.0 pre-alpha MVP**", completion_audit)
        self.assertIn("真实旧项目 adopt dogfood", completion_audit)
        self.assertIn("不纳入 0.1.0 完成定义", completion_audit)
        self.assertIn("compatibility", completion_audit)
        self.assertIn("agent-integration", completion_audit)
        self.assertIn("end-to-end-migration-publish", completion_audit)
        self.assertIn("known-limits", completion_audit)
        self.assertIn("recovery", completion_audit)
        self.assertIn("milestone-status", completion_audit)
        self.assertIn("roadmap.zh-CN.md", completion_audit)

    def test_packaged_templates_match_workspace_templates(self) -> None:
        workspace_templates = ROOT / "templates"
        packaged_templates = SRC / "fictionops" / "templates"
        workspace_files = sorted(path.name for path in workspace_templates.iterdir() if path.is_file())
        packaged_files = sorted(path.name for path in packaged_templates.iterdir() if path.is_file())

        self.assertEqual(packaged_files, workspace_files)
        for name in workspace_files:
            self.assertEqual(
                (packaged_templates / name).read_text(encoding="utf-8"),
                (workspace_templates / name).read_text(encoding="utf-8"),
                f"packaged template drifted from workspace template: {name}",
            )

    def test_installed_console_script_can_find_packaged_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            venv = tmp_path / "venv"
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            subprocess.run(
                [sys.executable, "-m", "venv", "--system-site-packages", str(venv)],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            script_dir = venv / ("Scripts" if os.name == "nt" else "bin")
            python = script_dir / ("python.exe" if os.name == "nt" else "python")
            fictionops_script = script_dir / ("fictionops.exe" if os.name == "nt" else "fictionops")

            subprocess.run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "--no-build-isolation",
                    str(ROOT),
                ],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertTrue(fictionops_script.exists(), f"missing console script: {fictionops_script}")

            version = subprocess.run(
                [str(fictionops_script), "--version"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("fictionops 0.1.1", version.stdout)

            module_version = subprocess.run(
                [str(python), "-m", "fictionops", "--version"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("fictionops 0.1.1", module_version.stdout)

            target = tmp_path / "installed-smoke"
            result = subprocess.run(
                [str(fictionops_script), "init", str(target), "--title", "Installed Smoke"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("Initialized FictionOps project", result.stdout)
            self.assertTrue((target / "project.yml").exists())
            self.assertTrue((target / "04_structure" / "book_outlines" / "book_01_outline.md").exists())
            self.assertIn("Installed Smoke", (target / "project.yml").read_text(encoding="utf-8"))

            export = subprocess.run(
                [str(fictionops_script), "export-clean", str(target), "--format", "json"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            export_data = json.loads(export.stdout)
            self.assertEqual(export_data["book"], "book_01")
            self.assertTrue(Path(export_data["output_file"]).exists())

            publish = subprocess.run(
                [str(fictionops_script), "audit-publish", str(target), "--format", "json"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            publish_data = json.loads(publish.stdout)
            self.assertEqual(publish_data["clean_file_exists"], True)
            self.assertEqual(publish_data["clean_chapters"], 1)

            self.write_publish_checklist_metadata(target)
            metadata = subprocess.run(
                [str(fictionops_script), "export-metadata", str(target), "--format", "json"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            metadata_data = json.loads(metadata.stdout)
            self.assertEqual(metadata_data["metadata"]["title"], "烟雪")
            self.assertTrue(Path(metadata_data["output_file"]).exists())

            manifest = subprocess.run(
                [str(fictionops_script), "export-manifest", str(target), "--format", "json"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            manifest_data = json.loads(manifest.stdout)
            self.assertEqual(manifest_data["manifest"]["schema"], "fictionops.publish_manifest.v1")
            self.assertTrue(Path(manifest_data["output_file"]).exists())

            epub = subprocess.run(
                [str(fictionops_script), "export-epub", str(target), "--format", "json"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            epub_data = json.loads(epub.stdout)
            self.assertEqual(epub_data["chapter_count"], 1)
            self.assertTrue(Path(epub_data["output_file"]).exists())

            audit_epub = subprocess.run(
                [str(fictionops_script), "audit-epub", str(target), "--format", "json"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            audit_epub_data = json.loads(audit_epub.stdout)
            self.assertEqual(audit_epub_data["epub_valid"], True)
            self.assertEqual(audit_epub_data["chapter_count"], 1)

    def test_built_wheel_installs_in_clean_venv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            wheelhouse = tmp_path / "wheelhouse"
            wheelhouse.mkdir()
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env.pop("PYTHONPATH", None)

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    str(ROOT),
                    "-w",
                    str(wheelhouse),
                    "--no-deps",
                    "--no-build-isolation",
                ],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            wheels = sorted(wheelhouse.glob("fictionops-0.1.1-*.whl"))
            self.assertEqual(len(wheels), 1)

            venv = tmp_path / "venv"
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv)],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            script_dir = venv / ("Scripts" if os.name == "nt" else "bin")
            python = script_dir / ("python.exe" if os.name == "nt" else "python")
            fictionops_script = script_dir / ("fictionops.exe" if os.name == "nt" else "fictionops")

            subprocess.run(
                [str(python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertTrue(fictionops_script.exists(), f"missing wheel-installed console script: {fictionops_script}")

            version = subprocess.run(
                [str(fictionops_script), "--version"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("fictionops 0.1.1", version.stdout)

            module_version = subprocess.run(
                [str(python), "-m", "fictionops", "--version"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("fictionops 0.1.1", module_version.stdout)

            agent_help = subprocess.run(
                [str(fictionops_script), "agent-next", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("agent-next", agent_help.stdout)

            agent_connect_help = subprocess.run(
                [str(fictionops_script), "agent-connect", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("agent-connect", agent_connect_help.stdout)

            eval_agent_help = subprocess.run(
                [str(fictionops_script), "eval-agent", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("eval-agent", eval_agent_help.stdout)

            agent_smoke_help = subprocess.run(
                [str(fictionops_script), "agent-smoke", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("agent-smoke", agent_smoke_help.stdout)

            agent_workflow_help = subprocess.run(
                [str(fictionops_script), "audit-agent-workflow", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("audit-agent-workflow", agent_workflow_help.stdout)

            evidence_help = subprocess.run(
                [str(fictionops_script), "audit-release-evidence", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("audit-release-evidence", evidence_help.stdout)

            dogfood_help = subprocess.run(
                [str(fictionops_script), "audit-dogfood-cycle", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("audit-dogfood-cycle", dogfood_help.stdout)

            stability_window_help = subprocess.run(
                [str(fictionops_script), "audit-stability-window", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("audit-stability-window", stability_window_help.stdout)

            stable_core_help = subprocess.run(
                [str(fictionops_script), "audit-stable-core", "--help"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("audit-stable-core", stable_core_help.stdout)

            target = tmp_path / "wheel-smoke"
            init_result = subprocess.run(
                [str(fictionops_script), "init", str(target), "--title", "Wheel Smoke"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            self.assertIn("Initialized FictionOps project", init_result.stdout)
            self.assertTrue((target / "project.yml").exists())

            doctor = subprocess.run(
                [str(fictionops_script), "doctor", str(target), "--format", "json"],
                env=env,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            doctor_data = json.loads(doctor.stdout)
            self.assertIn("status", doctor_data)
            self.assertIn("plan", doctor_data)
            self.assertIn("continuity", doctor_data)

    def test_sdist_contains_sources_templates_docs_examples_and_tests(self) -> None:
        import contextlib
        import io
        import setuptools.build_meta as build_meta

        egg_info = ROOT / "src" / "fictionops.egg-info"
        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            try:
                os.chdir(ROOT)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    sdist_name = build_meta.build_sdist(str(tmp_path))
            finally:
                os.chdir(old_cwd)
                shutil.rmtree(egg_info, ignore_errors=True)

            sdist_path = tmp_path / sdist_name
            self.assertTrue(sdist_path.exists(), f"missing sdist: {sdist_path}")
            with tarfile.open(sdist_path, "r:gz") as archive:
                names = set(archive.getnames())

        prefix = "fictionops-0.1.1/"
        required = {
            "LICENSE",
            "README.md",
            "README.zh-CN.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "CONTRIBUTING.zh-CN.md",
            "MANIFEST.in",
            "pyproject.toml",
            "src/fictionops/__main__.py",
            "src/fictionops/cli.py",
            "src/fictionops/agent_connect.py",
            "src/fictionops/agent_evaluation.py",
            "src/fictionops/agent_budget.py",
            "src/fictionops/agent_exec.py",
            "src/fictionops/agent_failure_lab.py",
            "src/fictionops/agent_revise_workflow.py",
            "src/fictionops/agent_revision_runtime.py",
            "src/fictionops/agent_revision_accept.py",
            "src/fictionops/agent_project_context.py",
            "src/fictionops/agent_policy.py",
            "src/fictionops/agent_comprehensive_review.py",
            "src/fictionops/agent_continue.py",
            "src/fictionops/agent_write_workflow.py",
            "src/fictionops/agent_run.py",
            "src/fictionops/agent_session.py",
            "src/fictionops/agent_session_control.py",
            "src/fictionops/agent_inbox.py",
            "src/fictionops/agent_issue_ledger.py",
            "src/fictionops/agent_memory.py",
            "src/fictionops/agent_story_reasoning.py",
            "src/fictionops/writing_agent.py",
            "src/fictionops/agent_next.py",
            "src/fictionops/agent_smoke.py",
            "src/fictionops/agent_workflow_audit.py",
            "src/fictionops/api.py",
            "src/fictionops/agent_research_baseline.py",
            "src/fictionops/agent_status.py",
            "src/fictionops/agent_trajectory.py",
            "src/fictionops/setup_ai.py",
            "src/fictionops/stable_core.py",
            "src/fictionops/doctor.py",
            "src/fictionops/dogfood_cycle.py",
            "src/fictionops/release_gate.py",
            "src/fictionops/release_evidence.py",
            "src/fictionops/stability_window.py",
            "src/fictionops/templates/project.yml",
            "src/fictionops/templates/chapter_engine.zh-CN.md",
            "templates/project.yml",
            "docs/getting-started.md",
            "docs/getting-started.zh-CN.md",
            "docs/cli.md",
            "docs/cli-contracts.md",
            "docs/agent-protocol.md",
            "docs/agent-system-design.zh-CN.md",
            "docs/agent-connector-contract.md",
            "docs/agent-connector-contract.zh-CN.md",
            "docs/agent-integration.md",
            "docs/agent-integration.zh-CN.md",
            "docs/model-providers.md",
            "docs/model-providers.zh-CN.md",
            "docs/agent-workflow.md",
            "docs/agent-workflow.zh-CN.md",
            "docs/agent-evaluation.md",
            "docs/agent-evaluation.zh-CN.md",
            "docs/agent-evaluation-demo-report.md",
            "docs/tutorial-demo.md",
            "docs/migration.md",
            "docs/end-to-end-migration-publish.md",
            "docs/testing.md",
            "docs/release.md",
            "docs/release-trial-evidence.md",
            "docs/release-trial-evidence.zh-CN.md",
            "docs/compatibility.md",
            "docs/compatibility.zh-CN.md",
            "docs/known-limits.md",
            "docs/known-limits.zh-CN.md",
            "docs/recovery.md",
            "docs/recovery.zh-CN.md",
            "docs/release-checklist.zh-CN.md",
            "docs/pypi-release.zh-CN.md",
            "examples/agent_runner_echo.py",
            "examples/agent_runner_openai_chat.py",
            "examples/agent_runner_openai_responses.py",
            "examples/agent_controller_next.py",
            "examples/agent_controller_loop.py",
            "docs/release-notes-0.1.0.zh-CN.md",
            "docs/roadmap.md",
            "docs/roadmap.zh-CN.md",
            "docs/milestone-status.md",
            "docs/milestone-status.zh-CN.md",
            "docs/stable-core-remaining-checklist.md",
            "docs/stable-core-remaining-checklist.zh-CN.md",
            "docs/stable-core-audit.md",
            "docs/stable-core-audit.zh-CN.md",
            "docs/dogfood-cycle-evidence.md",
            "docs/dogfood-cycle-evidence.zh-CN.md",
            "docs/stability-window-evidence.md",
            "docs/stability-window-evidence.zh-CN.md",
            "integrations/README.md",
            "integrations/codex-skill/README.md",
            "integrations/codex-skill/fictionops-writing-agent/SKILL.md",
            "integrations/codex-skill/fictionops-writing-agent/agents/openai.yaml",
            "integrations/codex-skill/fictionops-writing-agent/references/workflow.md",
            "integrations/codex-skill/fictionops-writing-agent/references/chapter-writing.md",
            "integrations/codex-skill/fictionops-writing-agent/references/audit.md",
            "integrations/codex-skill/fictionops-writing-agent/references/dogfood-metrics.md",
            "integrations/api-agent/README.md",
            "integrations/api-agent/openapi.yaml",
            "integrations/api-agent/server.py",
            "integrations/api-agent/schemas/agent_goal.schema.json",
            "integrations/api-agent/schemas/agent_session.schema.json",
            "integrations/api-agent/schemas/staged_output.schema.json",
            "integrations/api-agent/examples/write_chapter_request.json",
            "integrations/api-agent/examples/write_chapter_response.json",
            "examples/demo_novel/project.yml",
            "examples/legacy_novel_source/README.md",
            "examples/legacy_novel_source/drafts/book_01/ch_001.md",
            "tests/test_cli.py",
            "workflows/from-seed-to-publication.zh-CN.md",
        }
        missing = sorted(prefix + item for item in required if prefix + item not in names)
        self.assertEqual(missing, [])

    def test_release_smoke_runs_quickstart_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "smoke-novel"

            self.run_cli("init", str(target), "--title", "Smoke Novel")
            self.run_cli("new-book", str(target), "--book", "2", "--title", "Smoke Book Two")
            self.run_cli(
                "new-chapter",
                str(target),
                "--chapter",
                "002",
                "--title",
                "Smoke Chapter",
                "--viewpoint",
                "Tester",
                "--kind",
                "转折",
                "--target-chars",
                "8200",
            )
            self.write_book_outline_plan(
                target,
                "| 02 | Smoke Chapter | Tester | A door closes | Keep the key | Locked room | Chooses action | A quiet doubt | 8200 |",
            )
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_002.md"
            chapter.write_text(
                "# 第002章 Smoke Chapter\n\n"
                + "Lantern Key opens one door and closes another. Tester keeps the Lantern Key hidden. " * 4,
                encoding="utf-8",
            )
            self.write_filled_echo_table(target)
            self.write_filled_information_table(target)
            self.write_filled_character_files(target)

            plan = self.run_cli("plan-chapter", str(target), "--chapter", "002")
            self.assertIn("Updated chapter engine", plan.stdout)
            scene_plan = json.loads(
                self.run_cli("scene-plan", str(target), "--chapter", "002", "--format", "json").stdout
            )
            self.assertEqual(scene_plan["chapter"], "002")
            self.assertGreaterEqual(scene_plan["scene_count"], 1)
            draft_brief = json.loads(
                self.run_cli("draft-brief", str(target), "--chapter", "002", "--format", "json").stdout
            )
            self.assertEqual(draft_brief["chapter"], "002")
            self.assertEqual(draft_brief["scene_count"], scene_plan["scene_count"])
            self.assertGreaterEqual(draft_brief["context_file_count"], 1)
            post_draft = json.loads(
                self.run_cli("post-draft", str(target), "--chapter", "002", "--format", "json").stdout
            )
            self.assertEqual(post_draft["chapter"], "002")
            self.assertIn(post_draft["status"], {"needs_retrospective", "sync_needed", "ready_for_review"})
            review_gate = json.loads(
                self.run_cli("review-gate", str(target), "--chapter", "002", "--format", "json").stdout
            )
            self.assertEqual(review_gate["chapter"], "002")
            self.assertIn(
                review_gate["status"],
                {"needs_post_draft", "needs_review_fixes", "review_notes", "review_passed"},
            )
            self.assertGreaterEqual(len(review_gate["checks"]), 1)

            audit_plan = json.loads(
                self.run_cli("audit-plan", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertEqual(audit_plan["planned_chapters"], 1)
            self.assertEqual(audit_plan["synced_engines"], 1)

            self.assertGreater(json.loads(self.run_cli("stats", str(target), "--format", "json").stdout)["file_count"], 0)
            self.assertGreater(
                json.loads(self.run_cli("scan-words", str(target), "--watch", "Lantern", "--format", "json").stdout)["file_count"],
                0,
            )
            self.assertGreater(
                json.loads(self.run_cli("check-tables", str(target), "--all", "--format", "json").stdout)["file_count"],
                0,
            )
            self.assertGreaterEqual(
                json.loads(self.run_cli("audit-style", str(target), "--format", "json").stdout)["file_count"],
                1,
            )
            self.assertGreaterEqual(
                json.loads(self.run_cli("audit-continuity", str(target), "--format", "json").stdout)["chapter_count"],
                2,
            )
            self.assertEqual(
                json.loads(self.run_cli("audit-echoes", str(target), "--format", "json").stdout)["thread_count"],
                1,
            )
            self.assertEqual(
                json.loads(self.run_cli("audit-info", str(target), "--format", "json").stdout)["item_count"],
                1,
            )
            self.assertEqual(
                json.loads(self.run_cli("audit-characters", str(target), "--format", "json").stdout)["character_count"],
                1,
            )
            agent_prompt = json.loads(
                self.run_cli(
                    "agent-prompt",
                    str(target),
                    "--role",
                    "draft-writer",
                    "--chapter",
                    "002",
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(agent_prompt["role"], "draft-writer")
            model_config = json.loads(
                self.run_cli(
                    "model-config",
                    str(target),
                    "--provider",
                    "local",
                    "--planning-model",
                    "planner",
                    "--drafting-model",
                    "writer",
                    "--audit-model",
                    "auditor",
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(model_config["provider"], "local")
            self.assertEqual(model_config["planning_model"], "planner")
            self.assertEqual(model_config["written"], False)
            context = json.loads(
                self.run_cli(
                    "context-pack",
                    str(target),
                    "--task",
                    "draft",
                    "--chapter",
                    "002",
                    "--no-content",
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(context["task"], "draft")
            self.assertEqual(context["chapter"], "002")
            workflow = json.loads(
                self.run_cli(
                    "workflow-plan",
                    str(target),
                    "--stage",
                    "review",
                    "--chapter",
                    "002",
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(workflow["stage"], "review")
            self.assertTrue(any("revision-plan" in command for command in workflow["commands"]))
            revision = json.loads(
                self.run_cli("revision-plan", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertIn("task_count", revision)

            retrospective_path = "07_audits/book_retrospectives/book_01_smoke_report.md"
            retrospective = self.run_cli("retrospective", str(target), "--book", "book_01", "--out", retrospective_path)
            self.assertIn("Wrote FictionOps retrospective", retrospective.stdout)
            self.assertTrue((target / retrospective_path).exists())
            book_gate = json.loads(self.run_cli("book-gate", str(target), "--book", "book_01", "--format", "json").stdout)
            self.assertEqual(book_gate["book"], "book_01")
            self.assertIn(
                book_gate["status"],
                {"needs_book_material", "needs_book_closure", "book_notes", "ready_for_clean_export"},
            )

            doctor = json.loads(self.run_cli("doctor", str(target), "--book", "book_01", "--format", "json").stdout)
            self.assertEqual(doctor["plan"]["enabled"], True)
            self.assertEqual(doctor["plan"]["synced_engines"], 1)
            self.assertEqual(doctor["retrospective"]["enabled"], True)
            self.assertEqual(doctor["characters"]["characters"], 1)
            self.assertEqual(doctor["characters"]["issues"], 0)
            self.assertIn("word_scan", doctor)
            self.assertIn("tables", doctor)

            report_path = "07_audits/doctor_smoke_report.md"
            report = self.run_cli("report", str(target), "--book", "book_01", "--out", report_path)
            self.assertIn("Wrote FictionOps report", report.stdout)
            report_text = (target / report_path).read_text(encoding="utf-8")
            self.assertIn("| Wave |", report_text)
            self.assertIn("| Word Scan |", report_text)
            self.assertIn("| Tables |", report_text)
            self.assertIn("| Characters |", report_text)
            self.assertIn("| Information |", report_text)
            self.assertIn("| Plan |", report_text)
            self.assertIn("| Retrospective |", report_text)
            self.assertIn("| Model Config |", report_text)

            export = self.run_cli("export-clean", str(target), "--book", "book_01")
            self.assertIn("Exported FictionOps clean Markdown", export.stdout)
            clean = target / "08_publish" / "clean_markdown" / "book_01.md"
            self.assertTrue(clean.exists())
            clean_text = clean.read_text(encoding="utf-8")
            self.assertIn("# 第002章 Smoke Chapter", clean_text)
            self.assertNotIn("Draft starts here", clean_text)

            publish = json.loads(
                self.run_cli("audit-publish", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertEqual(publish["clean_file_exists"], True)
            self.assertGreaterEqual(publish["clean_chapters"], 1)

            publish_copy = json.loads(
                self.run_cli("publish-copy", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertEqual(publish_copy["book"], "book_01")
            self.assertTrue((target / "08_publish" / "synopsis" / "book_01_publish_copy.md").exists())

            self.write_publish_checklist_metadata(target)
            metadata = json.loads(
                self.run_cli("export-metadata", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertEqual(metadata["metadata"]["author"], "示例作者")
            self.assertEqual(metadata["metadata"]["tags"], ["权谋", "成长", "神话"])
            self.assertTrue((target / "08_publish" / "metadata" / "book_01_metadata.json").exists())

            manifest = json.loads(
                self.run_cli("export-manifest", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertEqual(manifest["manifest"]["schema"], "fictionops.publish_manifest.v1")
            self.assertEqual(manifest["manifest"]["metadata"]["title"], "烟雪")
            self.assertTrue((target / "08_publish" / "manifest" / "book_01_manifest.json").exists())

            epub = json.loads(
                self.run_cli("export-epub", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertGreaterEqual(epub["chapter_count"], 1)
            self.assertTrue((target / "08_publish" / "epub" / "book_01.epub").exists())

            audit_epub = json.loads(
                self.run_cli("audit-epub", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertEqual(audit_epub["epub_valid"], True)
            self.assertGreaterEqual(audit_epub["chapter_count"], 1)
            release_gate = json.loads(
                self.run_cli("release-gate", str(target), "--book", "book_01", "--format", "json").stdout
            )
            self.assertEqual(release_gate["book"], "book_01")
            self.assertIn(
                release_gate["status"],
                {"needs_release_artifacts", "needs_release_fixes", "release_notes", "ready_for_release"},
            )
            self.assertGreaterEqual(len(release_gate["checks"]), 1)

    def test_demo_novel_example_runs_core_workflow(self) -> None:
        source = ROOT / "examples" / "demo_novel"
        self.assertTrue(source.exists(), "demo_novel example is missing")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo_novel"
            shutil.copytree(source, target)

            plan = self.run_cli("plan-chapter", str(target), "--chapter", "002", "--force")
            self.assertIn("Updated fields: title, viewpoint, target_chars, kind, pressure, desire, obstacle, change, remainder", plan.stdout)

            scene = json.loads(self.run_cli("scene-plan", str(target), "--chapter", "002", "--format", "json").stdout)
            self.assertEqual(scene["chapter"], "002")
            self.assertEqual(scene["title"], "借灯")
            self.assertEqual(scene["scene_count"], 5)
            self.assertEqual(scene["issues"], [])

            brief = json.loads(
                self.run_cli(
                    "draft-brief",
                    str(target),
                    "--chapter",
                    "002",
                    "--include-context-content",
                    "--max-total-chars",
                    "4000",
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(brief["title"], "借灯")
            self.assertEqual(brief["issue_count"], 0)
            self.assertLessEqual(brief["context_pack"]["included_total_chars"], 4000)

            handoff = json.loads(
                self.run_cli("context-pack", str(target), "--task", "handoff", "--no-content", "--format", "json").stdout
            )
            self.assertEqual(handoff["task"], "handoff")
            self.assertEqual(handoff["issues"], [])

            info = json.loads(self.run_cli("audit-info", str(target), "--format", "json").stdout)
            self.assertEqual(info["item_count"], 2)
            self.assertEqual(info["issues"], [])

            characters = json.loads(self.run_cli("audit-characters", str(target), "--format", "json").stdout)
            self.assertEqual(characters["character_count"], 2)
            self.assertEqual(characters["issues"], [])

            doctor = json.loads(self.run_cli("doctor", str(target), "--book", "book_01", "--format", "json").stdout)
            self.assertEqual(doctor["plan"]["planned_chapters"], 2)
            self.assertEqual(doctor["plan"]["synced_engines"], 2)
            self.assertEqual(doctor["continuity"]["placeholder_standard_files"], 0)
            self.assertEqual(doctor["characters"]["issues"], 0)

    def test_demo_controller_example_reads_demo_project(self) -> None:
        source = ROOT / "examples" / "demo_novel"
        self.assertTrue(source.exists(), "demo_novel example is missing")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo_novel"
            shutil.copytree(source, target)

            controller = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_next.py"),
                    str(target),
                    "--chapter",
                    "002",
                    "--no-text-scan",
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(CLI),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            data = json.loads(controller.stdout)
            self.assertEqual(data["chapter"], "002")
            self.assertIn("agent-run", data["selected_command"])
            self.assertEqual(data["candidates"][0]["stage"], "draft")
            self.assertEqual(data["candidates"][0]["requires_human_review"], True)

    def test_legacy_migration_example_runs_sandbox_workflow(self) -> None:
        source = ROOT / "examples" / "legacy_novel_source"
        self.assertTrue(source.exists(), "legacy_novel_source example is missing")
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy_novel_source"
            sandbox = Path(tmp) / "migrated_novel"
            shutil.copytree(source, legacy)

            adopt = json.loads(self.run_cli("adopt", str(legacy), "--format", "json").stdout)
            self.assertEqual(adopt["scanned_files"], 8)
            self.assertIn("drafts", {item["layer"] for item in adopt["files"]})
            self.assertTrue(any(risk["code"] == "missing_project_config" for risk in adopt["risks"]))

            self.run_cli("init", str(sandbox), "--title", "Migrated Legacy")
            copied = json.loads(self.run_cli("adopt", str(legacy), "--copy-to", str(sandbox), "--format", "json").stdout)
            self.assertEqual(copied["copied_files"], 8)
            self.assertEqual(copied["skipped_files"], 0)
            self.assertTrue((sandbox / "00_management" / "adopted_handoff" / "adopt_manifest.json").exists())

            review = json.loads(self.run_cli("adopt-review", str(sandbox), "--format", "json").stdout)
            self.assertEqual(review["status"], "needs_import_sorting")
            self.assertEqual(review["import_queue_files"], 2)

            plan = json.loads(self.run_cli("import-plan", str(sandbox), "--format", "json").stdout)
            self.assertEqual(plan["import_queue_files"], 2)
            self.assertEqual(plan["ready_count"], 1)
            self.assertEqual(plan["placeholder_target_count"], 1)

            applied = json.loads(
                self.run_cli(
                    "import-plan",
                    str(sandbox),
                    "--apply",
                    "--create-scaffolds",
                    "--replace-placeholder-targets",
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(applied["moved_files"], 2)
            self.assertEqual(applied["replaced_placeholder_targets"], 1)
            self.assertTrue((sandbox / "06_drafts" / "book_01" / "chapters" / "ch_001.md").exists())
            self.assertTrue((sandbox / "06_drafts" / "book_01" / "chapters" / "ch_002.md").exists())
            self.assertFalse(any((sandbox / "06_drafts" / "import_queue").glob("*.md")))

            reviewed = json.loads(self.run_cli("adopt-review", str(sandbox), "--format", "json").stdout)
            self.assertEqual(reviewed["status"], "needs_migration_fixes")
            self.assertEqual(reviewed["import_queue_files"], 0)

    def test_new_chapter_normalizes_chapter_number(self) -> None:
        self.assertEqual(normalize_chapter_number("1"), "001")
        self.assertEqual(normalize_chapter_number("001"), "001")
        self.assertEqual(normalize_chapter_number("ch_12"), "012")
        self.assertEqual(normalize_chapter_number("第3章"), "003")

    def test_new_book_normalizes_book_id(self) -> None:
        self.assertEqual(normalize_book_id("2"), "book_02")
        self.assertEqual(normalize_book_id("02"), "book_02")
        self.assertEqual(normalize_book_id("book_2"), "book_02")
        self.assertEqual(normalize_book_id("book-12"), "book_12")

    def test_new_book_creates_outline_dirs_and_retrospective(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = create_book(
                target,
                book="2",
                title="Second Book",
                force=False,
                dry_run=False,
            )
            self.assertEqual(result.created_dirs, 4)
            self.assertEqual(result.created_files, 2)
            outline = target / "04_structure" / "book_outlines" / "book_02_outline.md"
            retrospective = target / "07_audits" / "book_retrospectives" / "book_02_retrospective.md"
            self.assertTrue(outline.exists())
            self.assertTrue(retrospective.exists())
            self.assertTrue((target / "06_drafts" / "book_02" / "chapters").is_dir())
            self.assertTrue((target / "06_drafts" / "book_02" / "chapter_engines").is_dir())
            self.assertTrue((target / "06_drafts" / "book_02" / "draft_briefs").is_dir())
            self.assertTrue((target / "06_drafts" / "book_02" / "revision_notes").is_dir())
            self.assertIn("# Second Book 大纲", outline.read_text(encoding="utf-8"))
            retrospective_text = retrospective.read_text(encoding="utf-8")
            self.assertIn("- 书名：book_02", retrospective_text)
            self.assertIn("- 标题：Second Book", retrospective_text)

    def test_new_book_cli_skips_existing_files_without_force(self) -> None:
        temp, target = self.make_project()
        with temp:
            first = self.run_cli("new-book", str(target), "--book", "3", "--title", "Book Three")
            self.assertIn("Created files: 2", first.stdout)
            second = self.run_cli("new-book", str(target), "--book", "3", "--title", "Changed")
            self.assertIn("Skipped existing files: 2", second.stdout)
            outline = target / "04_structure" / "book_outlines" / "book_03_outline.md"
            self.assertIn("# Book Three 大纲", outline.read_text(encoding="utf-8"))

            forced = self.run_cli("new-book", str(target), "--book", "3", "--title", "Changed", "--force")
            self.assertIn("Created files: 2", forced.stdout)
            self.assertIn("# Changed 大纲", outline.read_text(encoding="utf-8"))

    def test_new_chapter_creates_draft_engine_and_retrospective(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = create_chapter(
                target,
                book="book_01",
                chapter="2",
                title="Second Turn",
                viewpoint="A",
                kind="turning point",
                target_chars=8200,
                force=False,
                dry_run=False,
            )
            self.assertEqual(result.created_files, 3)
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_002.md"
            engine = target / "06_drafts" / "book_01" / "chapter_engines" / "ch_002_engine.md"
            retrospective = target / "06_drafts" / "book_01" / "revision_notes" / "ch_002_retrospective.md"
            self.assertTrue(chapter.exists())
            self.assertTrue(engine.exists())
            self.assertTrue(retrospective.exists())
            self.assertIn("# 第002章 Second Turn", chapter.read_text(encoding="utf-8"))
            engine_text = engine.read_text(encoding="utf-8")
            self.assertIn("- 章节：第002章", engine_text)
            self.assertIn("- 标题：Second Turn", engine_text)
            self.assertIn("- 视角人物：A", engine_text)
            self.assertIn("- 建议体量：8200", engine_text)

            report = build_continuity_report(
                target,
                pattern="**/*.md",
                skip_standard=True,
                min_chapter_chars=10,
            )
            chapter_002 = next(chapter for chapter in report.chapters if chapter.key == "002")
            self.assertTrue(chapter_002.engine_file and chapter_002.engine_file.endswith("ch_002_engine.md"))
            self.assertTrue(
                chapter_002.retrospective_file
                and chapter_002.retrospective_file.endswith("ch_002_retrospective.md")
            )

    def test_new_chapter_cli_skips_existing_files_without_force(self) -> None:
        temp, target = self.make_project()
        with temp:
            first = self.run_cli("new-chapter", str(target), "--chapter", "3", "--title", "CLI Chapter")
            self.assertIn("Created files: 3", first.stdout)
            second = self.run_cli("new-chapter", str(target), "--chapter", "3", "--title", "Changed")
            self.assertIn("Skipped existing files: 3", second.stdout)
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_003.md"
            self.assertIn("# 第003章 CLI Chapter", chapter.read_text(encoding="utf-8"))

            forced = self.run_cli(
                "new-chapter",
                str(target),
                "--chapter",
                "3",
                "--title",
                "Changed",
                "--force",
            )
            self.assertIn("Created files: 3", forced.stdout)
            self.assertIn("# 第003章 Changed", chapter.read_text(encoding="utf-8"))

    def test_plan_chapter_fills_engine_from_book_outline(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | Opening Gate | A | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            result = plan_chapter(
                target,
                book="book_01",
                chapter="1",
                outline=None,
                force=False,
                dry_run=False,
            )
            self.assertIn("title", result.updated_fields)
            self.assertIn("pressure", result.updated_fields)
            engine = target / "06_drafts" / "book_01" / "chapter_engines" / "ch_001_engine.md"
            text = engine.read_text(encoding="utf-8")
            self.assertIn("- 标题：Opening Gate", text)
            self.assertIn("- 视角人物：A", text)
            self.assertIn("- 建议体量：8200", text)
            self.assertIn("| pressure enters | wants proof | locked door | door opens | key remains |", text)

    def test_plan_chapter_preserves_existing_fields_unless_forced(self) -> None:
        temp, target = self.make_project()
        with temp:
            create_chapter(
                target,
                book="book_01",
                chapter="2",
                title="Existing Title",
                viewpoint="Existing POV",
                kind=None,
                target_chars=8000,
                force=False,
                dry_run=False,
            )
            self.write_book_outline_plan(
                target,
                "| 02 | Outline Title | Outline POV | p | d | o | c | r | 1000 |",
            )

            result = plan_chapter(
                target,
                book="book_01",
                chapter="2",
                outline=None,
                force=False,
                dry_run=False,
            )
            self.assertIn("title", result.skipped_fields)
            self.assertIn("viewpoint", result.skipped_fields)
            engine = target / "06_drafts" / "book_01" / "chapter_engines" / "ch_002_engine.md"
            text = engine.read_text(encoding="utf-8")
            self.assertIn("- 标题：Existing Title", text)
            self.assertIn("- 视角人物：Existing POV", text)
            self.assertIn("| p | d | o | c | r |", text)

            forced = plan_chapter(
                target,
                book="book_01",
                chapter="2",
                outline=None,
                force=True,
                dry_run=False,
            )
            self.assertIn("title", forced.updated_fields)
            forced_text = engine.read_text(encoding="utf-8")
            self.assertIn("- 标题：Outline Title", forced_text)
            self.assertIn("- 视角人物：Outline POV", forced_text)
            self.assertIn("- 建议体量：1000", forced_text)

    def test_plan_chapter_cli_updates_engine(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| ch_001 | CLI Planned | CLI POV | p | d | o | c | r | 8100 |",
            )
            result = self.run_cli("plan-chapter", str(target), "--chapter", "001")
            self.assertIn("Updated chapter engine", result.stdout)
            self.assertIn("Updated fields:", result.stdout)
            engine = target / "06_drafts" / "book_01" / "chapter_engines" / "ch_001_engine.md"
            self.assertIn("- 标题：CLI Planned", engine.read_text(encoding="utf-8"))

    def test_scene_plan_builds_skeleton_from_chapter_engine(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | Scene Gate | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)
            default_report = build_scene_plan(target, book="book_01", chapter="001")
            self.assertEqual(default_report.scene_count, 5)
            self.assertIn("generated_scene_order", {issue.code for issue in default_report.issues})
            self.assertEqual(default_report.pressure, "pressure enters")

            engine = target / "06_drafts" / "book_01" / "chapter_engines" / "ch_001_engine.md"
            text = engine.read_text(encoding="utf-8")
            text = text.replace(
                "|  |  |  |  |  |",
                "| Maker Secret | Tester | Reader | only as rumor | do not explain maker |",
                1,
            )
            text = text.replace(
                "|  | 埋下 / 轻回声 / 误读 / 变形 / 兑现 / 暂不处理 | 物件 / 动作 / 谣言 / 沉默 / 身体反应 / 对话 |",
                "| Lantern Key | 轻回声 | 物件 |",
            )
            text = text.replace(
                "1. \n2. \n3. ",
                "1. Door pressure arrives\n2. Tester bargains with cost\n3. Key leaves a doubt",
            )
            engine.write_text(text, encoding="utf-8", newline="\n")

            report = build_scene_plan(target, book="book_01", chapter="001")
            self.assertEqual(report.scene_count, 3)
            self.assertEqual(report.scenes[0].title, "Door pressure arrives")
            self.assertTrue(any("Maker Secret" in item for item in report.scenes[0].info_boundary))
            self.assertTrue(any("Lantern Key" in item for item in report.scenes[0].foreshadowing))
            self.assertNotIn("generated_scene_order", {issue.code for issue in report.issues})

    def test_scene_plan_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | CLI Scene | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)

            result = self.run_cli("scene-plan", str(target), "--chapter", "001", "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["chapter"], "001")
            self.assertEqual(data["pressure"], "pressure enters")
            self.assertGreaterEqual(data["scene_count"], 1)

            written = self.run_cli("scene-plan", str(target), "--chapter", "001", "--out", "07_audits/scene_plan.md")
            self.assertIn("Wrote FictionOps scene plan", written.stdout)
            output = target / "07_audits" / "scene_plan.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Scene Plan", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "scene-plan",
                str(target),
                "--chapter",
                "001",
                "--out",
                "07_audits/scene_plan.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_draft_brief_builds_task_ready_brief(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | Brief Gate | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)

            report = build_draft_brief(target, book="book_01", chapter="001")
            self.assertEqual(report.chapter, "001")
            self.assertEqual(report.title, "Brief Gate")
            self.assertEqual(report.scene_count, 5)
            self.assertGreaterEqual(report.context_file_count, 1)
            self.assertEqual(report.missing_required_context_count, 0)
            self.assertTrue(any("视角人物" in item for item in report.premise_checks))
            self.assertTrue(any("视角人物可知" in item for item in report.must_do))
            self.assertEqual(report.scene_tasks[0].title, "pressure enters")
            self.assertTrue(any(issue.source == "scene-plan" for issue in report.issues))

    def test_draft_brief_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | CLI Brief | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)

            result = self.run_cli(
                "draft-brief",
                str(target),
                "--chapter",
                "001",
                "--include-context-content",
                "--max-chars-per-file",
                "120",
                "--max-total-chars",
                "180",
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["chapter"], "001")
            self.assertEqual(data["title"], "CLI Brief")
            self.assertTrue(data["include_context_content"])
            self.assertEqual(data["max_total_context_chars"], 180)
            self.assertLessEqual(data["context_pack"]["included_total_chars"], 180)
            self.assertGreaterEqual(data["context_file_count"], 1)
            self.assertTrue(any(item["included_chars"] > 0 for item in data["context_pack"]["files"] if item["exists"]))

            written = self.run_cli("draft-brief", str(target), "--chapter", "001", "--out", "07_audits/draft_brief.md")
            self.assertIn("Wrote FictionOps draft brief", written.stdout)
            output = target / "07_audits" / "draft_brief.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Draft Brief", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "draft-brief",
                str(target),
                "--chapter",
                "001",
                "--out",
                "07_audits/draft_brief.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_post_draft_reports_ready_and_sync_needed_status(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | Closed Gate | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text(
                "# 第001章 Closed Gate\n\n"
                + "Tester crossed the threshold with the Lantern Key hidden in one sleeve. "
                + "The room changed because the witness refused to name what had happened. "
                + "By dawn, the door was open, but the cost had moved into the next chapter. "
                * 2,
                encoding="utf-8",
                newline="\n",
            )
            retrospective = target / "06_drafts" / "book_01" / "revision_notes" / "ch_001_retrospective.md"
            retrospective.write_text(
                textwrap.dedent(
                    """\
                    # 第001章复盘

                    - 书名：book_01
                    - 章节：第001章
                    - 标题：Closed Gate
                    - 完成日期：2026-07-06
                    - 实际字数：420

                    本章完成了门打开后的代价转移。Tester 的恐惧没有被解释完，只以藏钥匙的动作留下。

                    ## 同步项

                    - 需要同步到人物弧线：
                    - 需要同步到信息释放表：
                    - 需要同步到伏笔回声表：
                    - 需要同步到书纲：
                    - 需要归档的旧案：
                    """
                ),
                encoding="utf-8",
                newline="\n",
            )

            ready = build_post_draft_report(target, book="book_01", chapter="001")
            self.assertEqual(ready.status, "ready_for_review")
            self.assertTrue(ready.ready)
            self.assertEqual(ready.issue_count, 0)

            retrospective.write_text(
                retrospective.read_text(encoding="utf-8").replace(
                    "- 需要同步到人物弧线：",
                    "- 需要同步到人物弧线：Tester 学会把恐惧转成动作。",
                ),
                encoding="utf-8",
                newline="\n",
            )
            sync_needed = build_post_draft_report(target, book="book_01", chapter="001")
            self.assertEqual(sync_needed.status, "sync_needed")
            self.assertFalse(sync_needed.ready)
            self.assertIn("open_sync_item", {issue.code for issue in sync_needed.issues})

    def test_post_draft_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("post-draft", str(target), "--chapter", "001", "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["chapter"], "001")
            self.assertEqual(data["status"], "needs_draft")
            self.assertFalse(data["ready"])
            self.assertIn("placeholder_chapter", {issue["code"] for issue in data["issues"]})

            written = self.run_cli("post-draft", str(target), "--chapter", "001", "--out", "07_audits/post_draft.md")
            self.assertIn("Wrote FictionOps post-draft gate", written.stdout)
            output = target / "07_audits" / "post_draft.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Post-Draft Gate", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "post-draft",
                str(target),
                "--chapter",
                "001",
                "--out",
                "07_audits/post_draft.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_review_gate_aggregates_single_chapter_review_signals(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | Review Gate | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)
            self.write_long_chapter_with_echo(target)
            retrospective = target / "06_drafts" / "book_01" / "revision_notes" / "ch_001_retrospective.md"
            retrospective.write_text(
                textwrap.dedent(
                    """\
                    # 第001章复盘

                    - 书名：book_01
                    - 章节：第001章
                    - 标题：Review Gate
                    - 完成日期：2026-07-06
                    - 实际字数：620

                    本章完成了门打开后的代价转移。Tester 的恐惧没有被解释完，只以藏钥匙的动作留下。

                    ## 同步项

                    - 需要同步到人物弧线：
                    - 需要同步到信息释放表：
                    - 需要同步到伏笔回声表：
                    - 需要同步到书纲：
                    - 需要归档的旧案：
                    """
                ),
                encoding="utf-8",
                newline="\n",
            )
            self.write_filled_echo_table(target)
            self.write_filled_information_table(target)
            self.write_filled_character_files(target)

            report = build_review_gate(target, book="book_01", chapter="001")
            self.assertEqual(report.chapter, "001")
            self.assertEqual(report.post_draft.status, "ready_for_review")
            self.assertNotEqual(report.status, "needs_post_draft")
            self.assertEqual(len(report.checks), 7)
            self.assertTrue(any(item.name == "Post-draft gate" for item in report.checks))
            self.assertGreaterEqual(len(report.next_actions), 1)

    def test_review_gate_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("review-gate", str(target), "--chapter", "001", "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["chapter"], "001")
            self.assertEqual(data["status"], "needs_post_draft")
            self.assertFalse(data["ready"])
            self.assertGreaterEqual(len(data["checks"]), 1)

            written = self.run_cli("review-gate", str(target), "--chapter", "001", "--out", "07_audits/review_gate.md")
            self.assertIn("Wrote FictionOps review gate", written.stdout)
            output = target / "07_audits" / "review_gate.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Review Gate", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "review-gate",
                str(target),
                "--chapter",
                "001",
                "--out",
                "07_audits/review_gate.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_book_gate_reports_book_closure_status(self) -> None:
        temp, target = self.make_project()
        with temp:
            blocked = build_book_gate(target, book="book_01")
            self.assertEqual(blocked.book, "book_01")
            self.assertFalse(blocked.ready)
            self.assertIn(blocked.status, {"needs_book_material", "needs_book_closure"})
            self.assertGreater(blocked.blocking_issue_count, 0)

            self.write_book_outline_plan(
                target,
                "| 01 | Book Gate | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)
            self.write_long_chapter_with_echo(target)
            self.write_closed_chapter_retrospective(target, "001", "Book Gate")
            self.write_closed_book_retrospective(target, "book_01")
            self.write_filled_echo_table(target)
            self.write_filled_information_table(target)
            self.write_filled_character_files(target)

            ready = build_book_gate(target, book="book_01")
            self.assertTrue(ready.ready)
            self.assertIn(ready.status, {"book_notes", "ready_for_clean_export"})
            self.assertEqual(len(ready.checks), 6)
            self.assertTrue(any(item.name == "Plan coverage" for item in ready.checks))
            self.assertTrue(any(item.name == "Project tables" for item in ready.checks))
            self.assertTrue(any(item.name == "Word scan" for item in ready.checks))
            self.assertTrue(any("export-clean" in action for action in ready.next_actions) or ready.status == "book_notes")

    def test_book_gate_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("book-gate", str(target), "--book", "book_01", "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["book"], "book_01")
            self.assertIn(data["status"], {"needs_book_material", "needs_book_closure", "book_notes", "ready_for_clean_export"})
            self.assertGreaterEqual(len(data["checks"]), 1)

            written = self.run_cli("book-gate", str(target), "--book", "book_01", "--out", "07_audits/book_gate.md")
            self.assertIn("Wrote FictionOps book gate", written.stdout)
            output = target / "07_audits" / "book_gate.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Book Gate", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "book-gate",
                str(target),
                "--book",
                "book_01",
                "--out",
                "07_audits/book_gate.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_release_gate_reports_final_publish_status(self) -> None:
        temp, target = self.make_project()
        with temp:
            blocked = build_release_gate(target, book="book_01")
            self.assertEqual(blocked.book, "book_01")
            self.assertFalse(blocked.ready)
            self.assertEqual(blocked.status, "needs_release_artifacts")
            self.assertGreater(blocked.blocking_issue_count, 0)

            self.write_book_outline_plan(
                target,
                "| 01 | Release Gate | Tester | pressure enters | wants proof | locked door | door opens | key remains | 8200 |",
            )
            plan_chapter(target, book="book_01", chapter="001", outline=None, force=False, dry_run=False)
            self.write_long_chapter_with_echo(target)
            self.write_closed_chapter_retrospective(target, "001", "Release Gate")
            self.write_closed_book_retrospective(target, "book_01")
            self.write_filled_echo_table(target)
            self.write_filled_information_table(target)
            self.write_filled_character_files(target)
            export_clean_markdown(target, book="book_01", out=None, title=None, force=False, dry_run=False)
            self.write_publish_checklist_metadata(target)
            export_publish_metadata(target, book="book_01", file_path=None, out=None, force=False, dry_run=False)
            export_publish_manifest(
                target,
                book="book_01",
                clean_file=None,
                metadata_file=None,
                out=None,
                force=False,
                dry_run=False,
            )
            export_epub(
                target,
                book="book_01",
                manifest_file=None,
                clean_file=None,
                metadata_file=None,
                cover_file=None,
                out=None,
                force=False,
                dry_run=False,
            )

            ready = build_release_gate(target, book="book_01")
            self.assertTrue(ready.ready)
            self.assertIn(ready.status, {"release_notes", "ready_for_release"})
            self.assertEqual(len(ready.checks), 5)
            self.assertTrue(any(item.name == "Book closure" for item in ready.checks))
            self.assertTrue(any(item.name == "EPUB package" for item in ready.checks))

    def test_release_gate_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("release-gate", str(target), "--book", "book_01", "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["book"], "book_01")
            self.assertEqual(data["status"], "needs_release_artifacts")
            self.assertFalse(data["ready"])
            self.assertIn("book_gate", data)
            self.assertGreaterEqual(len(data["checks"]), 1)

            written = self.run_cli("release-gate", str(target), "--book", "book_01", "--out", "07_audits/release_gate.md")
            self.assertIn("Wrote FictionOps release gate", written.stdout)
            output = target / "07_audits" / "release_gate.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Release Gate", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "release-gate",
                str(target),
                "--book",
                "book_01",
                "--out",
                "07_audits/release_gate.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_release_evidence_audit_reports_default_record_as_accepted(self) -> None:
        report = build_release_evidence_audit(ROOT)
        self.assertEqual(report.status, "accepted")
        self.assertTrue(report.ready)
        self.assertEqual(report.missing_required_fields, [])
        self.assertEqual(report.blocking_issue_count, 0)

        result = self.run_cli("audit-release-evidence", str(ROOT), "--format", "json")
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["ready"], True)
        self.assertEqual(data["blocking_issue_count"], 0)

    def test_release_evidence_audit_reports_template_as_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "release-trial-evidence-template.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date:",
                        "- Version:",
                        "- Commit / ref / tag:",
                        "- Decision: accepted / deferred / failed",
                        "- Reviewer:",
                        "- GitHub Actions run URL:",
                        "- GitHub Actions run ID:",
                        "- Wheel filename:",
                        "- Wheel SHA256:",
                        "- sdist filename:",
                        "- sdist SHA256:",
                        "- Built-wheel smoke result:",
                        "- TestPyPI used: yes / no",
                        "- fictionops --version result:",
                        "- python -m fictionops --version result:",
                        "- fictionops init smoke result:",
                        "- fictionops doctor smoke result:",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cli("audit-release-evidence", str(target), "--file", str(evidence), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "incomplete")
            self.assertEqual(data["ready"], False)
            self.assertIn("missing_required_evidence", {issue["code"] for issue in data["issues"]})

    def test_release_evidence_audit_accepts_filled_external_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "release-trial-evidence-filled.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date: 2026-07-07T00:00:00Z",
                        "- Version: 0.1.0",
                        "- Commit / ref / tag: abc123 / v0.1.0",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                        "- GitHub Actions run URL: https://github.com/example/fictionops/actions/runs/123456789",
                        "- GitHub Actions run ID: 123456789",
                        "- Distribution artifact name: fictionops-dist-0.1.0",
                        "- Wheel filename: fictionops-0.1.0-py3-none-any.whl",
                        "- Wheel SHA256: " + "a" * 64,
                        "- sdist filename: fictionops-0.1.0.tar.gz",
                        "- sdist SHA256: " + "b" * 64,
                        "- Built-wheel smoke result: passed",
                        "- TestPyPI used: no",
                        "- TestPyPI skip reason: validating GitHub Actions artifact instead of publishing to TestPyPI",
                        "- TestPyPI skip accepted by: maintainer",
                        "- fictionops --version result: fictionops 0.1.0",
                        "- python -m fictionops --version result: fictionops 0.1.0",
                        "- fictionops init smoke result: passed",
                        "- fictionops doctor smoke result: passed",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "audit-release-evidence",
                str(target),
                "--file",
                str(evidence),
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "accepted")
            self.assertEqual(data["ready"], True)
            self.assertEqual(data["blocking_issue_count"], 0)

    def test_release_evidence_rejects_failed_smoke_or_unexplained_testpypi_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "release-trial-evidence-weak.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date: 2026-07-07T00:00:00Z",
                        "- Version: 0.1.0",
                        "- Commit / ref / tag: abc123 / v0.1.0",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                        "- GitHub Actions run URL: https://github.com/example/fictionops/actions/runs/123456789",
                        "- GitHub Actions run ID: 123456789",
                        "- Wheel filename: fictionops-0.1.0-py3-none-any.whl",
                        "- Wheel SHA256: " + "a" * 64,
                        "- sdist filename: fictionops-0.1.0.tar.gz",
                        "- sdist SHA256: " + "b" * 64,
                        "- Built-wheel smoke result: failed",
                        "- TestPyPI used: no",
                        "- fictionops --version result: fictionops 0.1.0",
                        "- python -m fictionops --version result: fictionops 0.1.0",
                        "- fictionops init smoke result: passed",
                        "- fictionops doctor smoke result: banana",
                    ]
                ),
                encoding="utf-8",
            )
            data = json.loads(
                self.run_cli(
                    "audit-release-evidence",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(data["status"], "incomplete")
            self.assertEqual(data["ready"], False)
            codes = {issue["code"] for issue in data["issues"]}
            self.assertIn("release_smoke_not_passed", codes)
            self.assertIn("missing_testpypi_skip_record", codes)

            negated_evidence = target / "release-trial-evidence-negated-smoke.md"
            negated_evidence.write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date: 2026-07-07T00:00:00Z",
                        "- Version: 0.1.0",
                        "- Commit / ref / tag: abc123 / v0.1.0",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                        "- GitHub Actions run URL: https://github.com/example/fictionops/actions/runs/123456789",
                        "- GitHub Actions run ID: 123456789",
                        "- Wheel filename: fictionops-0.1.0-py3-none-any.whl",
                        "- Wheel SHA256: " + "a" * 64,
                        "- sdist filename: fictionops-0.1.0.tar.gz",
                        "- sdist SHA256: " + "b" * 64,
                        "- Built-wheel smoke result: not passed",
                        "- TestPyPI used: no",
                        "- TestPyPI skip reason: validating GitHub Actions artifact instead of publishing to TestPyPI",
                        "- TestPyPI skip accepted by: maintainer",
                        "- fictionops --version result: fictionops 0.1.0",
                        "- python -m fictionops --version result: fictionops 0.1.0",
                        "- fictionops init smoke result: compass",
                        "- fictionops doctor smoke result: passed",
                    ]
                ),
                encoding="utf-8",
            )
            negated = json.loads(
                self.run_cli(
                    "audit-release-evidence",
                    str(target),
                    "--file",
                    str(negated_evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(negated["status"], "incomplete")
            self.assertEqual(negated["ready"], False)
            negated_smoke_fields = {
                issue["field"] for issue in negated["issues"] if issue["code"] == "release_smoke_not_passed"
            }
            self.assertIn("Built-wheel smoke result", negated_smoke_fields)
            self.assertIn("fictionops init smoke result", negated_smoke_fields)

    def test_release_evidence_rejects_invalid_run_id_and_distribution_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "pyproject.toml").write_text('[project]\nname = "fictionops"\nversion = "0.1.0"\n', encoding="utf-8")
            evidence = target / "release-trial-evidence-bad-artifacts.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date: July 7 2026",
                        "- Version: 0.2.0",
                        "- Commit / ref / tag: abc123 / v0.1.0",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                        "- GitHub Actions run URL: https://github.com/example/fictionops/actions/runs/123456789",
                        "- GitHub Actions run ID: run-123",
                        "- Wheel filename: fictionops-0.1.0.zip",
                        "- Wheel SHA256: " + "a" * 64,
                        "- sdist filename: fictionops-0.1.0.whl",
                        "- sdist SHA256: " + "b" * 64,
                        "- Built-wheel smoke result: passed",
                        "- TestPyPI used: no",
                        "- TestPyPI skip reason: validating GitHub Actions artifact instead of publishing to TestPyPI",
                        "- TestPyPI skip accepted by: maintainer",
                        "- fictionops --version result: fictionops 0.1.0",
                        "- python -m fictionops --version result: fictionops 0.1.0",
                        "- fictionops init smoke result: passed",
                        "- fictionops doctor smoke result: passed",
                    ]
                ),
                encoding="utf-8",
            )
            data = json.loads(
                self.run_cli(
                    "audit-release-evidence",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(data["status"], "incomplete")
            self.assertFalse(data["ready"])
            codes = {issue["code"] for issue in data["issues"]}
            self.assertIn("invalid_release_date", codes)
            self.assertIn("release_version_mismatch", codes)
            self.assertIn("version_result_mismatch", codes)
            self.assertIn("invalid_github_run_id", codes)
            self.assertIn("invalid_distribution_filename", codes)

            external_url_evidence = target / "release-trial-evidence-bad-external-urls.md"
            external_url_evidence.write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date: 2026-07-07",
                        "- Version: 0.1.0",
                        "- Commit / ref / tag: abc123 / v0.1.0",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                        "- GitHub Actions run URL: https://example.com/example/fictionops/actions/runs/123456789",
                        "- GitHub Actions run ID: 987654321",
                        "- Wheel filename: fictionops-0.1.0-py3-none-any.whl",
                        "- Wheel SHA256: " + "a" * 64,
                        "- sdist filename: fictionops-0.1.0.tar.gz",
                        "- sdist SHA256: " + "b" * 64,
                        "- Built-wheel smoke result: passed",
                        "- TestPyPI used: yes",
                        "- TestPyPI project URL: https://example.com/project/fictionops/",
                        "- TestPyPI version URL: https://pypi.org/project/fictionops/0.1.0/",
                        "- Publish result: passed",
                        "- Clean venv install command: python -m pip install --index-url https://test.pypi.org/simple/ --no-deps fictionops==0.1.0",
                        "- fictionops --version result: fictionops 0.1.0",
                        "- python -m fictionops --version result: fictionops 0.1.0",
                        "- fictionops init smoke result: passed",
                        "- fictionops doctor smoke result: passed",
                    ]
                ),
                encoding="utf-8",
            )
            external_url_data = json.loads(
                self.run_cli(
                    "audit-release-evidence",
                    str(target),
                    "--file",
                    str(external_url_evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(external_url_data["status"], "incomplete")
            self.assertFalse(external_url_data["ready"])
            external_url_codes = {issue["code"] for issue in external_url_data["issues"]}
            self.assertIn("invalid_github_run_url", external_url_codes)
            self.assertIn("missing_testpypi_url", external_url_codes)

            mismatch_evidence = target / "release-trial-evidence-run-id-mismatch.md"
            mismatch_evidence.write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date: 2026-07-07",
                        "- Version: 0.1.0",
                        "- Commit / ref / tag: abc123 / v0.1.0",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                        "- GitHub Actions run URL: https://github.com/example/fictionops/actions/runs/123456789",
                        "- GitHub Actions run ID: 987654321",
                        "- Wheel filename: fictionops-0.1.0-py3-none-any.whl",
                        "- Wheel SHA256: " + "a" * 64,
                        "- sdist filename: fictionops-0.1.0.tar.gz",
                        "- sdist SHA256: " + "b" * 64,
                        "- Built-wheel smoke result: passed",
                        "- TestPyPI used: no",
                        "- TestPyPI skip reason: validating GitHub Actions artifact instead of publishing to TestPyPI",
                        "- TestPyPI skip accepted by: maintainer",
                        "- fictionops --version result: fictionops 0.1.0",
                        "- python -m fictionops --version result: fictionops 0.1.0",
                        "- fictionops init smoke result: passed",
                        "- fictionops doctor smoke result: passed",
                    ]
                ),
                encoding="utf-8",
            )
            mismatch_data = json.loads(
                self.run_cli(
                    "audit-release-evidence",
                    str(target),
                    "--file",
                    str(mismatch_evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(mismatch_data["status"], "incomplete")
            self.assertFalse(mismatch_data["ready"])
            self.assertIn("github_run_id_mismatch", {issue["code"] for issue in mismatch_data["issues"]})

    def test_dogfood_cycle_audit_reports_active_cycle_as_deferred(self) -> None:
        report = build_dogfood_cycle_audit(ROOT)
        self.assertEqual(report.status, "incomplete")
        self.assertFalse(report.ready)
        self.assertEqual(report.missing_required_fields, [])
        self.assertEqual(report.decision, "deferred")
        self.assertIn("decision_deferred", {issue.code for issue in report.issues})
        self.assertIn("final_status_not_ready", {issue.code for issue in report.issues})

        result = self.run_cli("audit-dogfood-cycle", str(ROOT), "--format", "json")
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "incomplete")
        self.assertEqual(data["ready"], False)
        self.assertEqual(data["missing_required_fields"], [])
        self.assertIn("decision_deferred", {issue["code"] for issue in data["issues"]})

    def test_dogfood_cycle_audit_accepts_filled_sustained_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "dogfood-cycle-filled.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Dogfood Cycle Evidence",
                        "",
                        "- Cycle ID: 2026-07-maintenance-01",
                        "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version / commit range: 0.1.0 / abc123..def456",
                        "- Scope: post-migration maintenance cycle for a real long-form project",
                        "- Book / chapter scope: Book 01 ch_001-ch_033, focused review on ch_007, ch_010, ch_012",
                        "- Focused tasks: structure recovery, context handoff, AI staged-output review, and bounded prose maintenance",
                        "- Commands exercised: adopt-review, adopt-plan, import-plan, doctor, report, context-pack",
                        "- AI workflow evidence: eval-agent ch_002 and agent-run/agent-inbox staged-output checks",
                        "- Human review boundary: model or tool output stayed staged for human review and no source overwrite was allowed",
                        "- Day-by-day ledger: 2026-07-01 baseline audit; 2026-07-07 close audit and reviewer decision",
                        "- Initial adopt-review status: ready",
                        "- Final adopt-review status: ready",
                        "- import_queue_files: 0",
                        "- blocking_issue_count: 0",
                        "- Waiver count: 31",
                        "- Compatibility notes: no command names or core JSON keys changed without docs",
                        "- Recovery notes: recovery docs reviewed for changed commands",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "audit-dogfood-cycle",
                str(target),
                "--file",
                str(evidence),
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "accepted")
            self.assertEqual(data["ready"], True)
            self.assertEqual(data["blocking_issue_count"], 0)

    def test_dogfood_cycle_audit_rejects_invalid_date_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "dogfood-cycle-bad-dates.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Dogfood Cycle Evidence",
                        "",
                        "- Cycle ID: 2026-07-maintenance-01",
                        "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                        "- Start date: 2026-07-07",
                        "- End date: 2026-07-01",
                        "- Version / commit range: 0.1.0 / abc123..def456",
                        "- Scope: post-migration maintenance cycle for a real long-form project",
                        "- Book / chapter scope: Book 01 ch_001-ch_033, focused review on ch_007",
                        "- Focused tasks: structure recovery and chapter review",
                        "- Commands exercised: adopt-review, adopt-plan, import-plan, doctor",
                        "- AI workflow evidence: eval-agent ch_002 and agent-inbox staged-output checks",
                        "- Human review boundary: staged output stopped at human review",
                        "- Day-by-day ledger: 2026-07-07 close audit; 2026-07-01 baseline audit",
                        "- Initial adopt-review status: ready",
                        "- Final adopt-review status: ready",
                        "- import_queue_files: 0",
                        "- blocking_issue_count: 0",
                        "- Waiver count: 31",
                        "- Compatibility notes: stable surfaces reviewed",
                        "- Recovery notes: recovery docs reviewed",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            data = json.loads(
                self.run_cli(
                    "audit-dogfood-cycle",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(data["status"], "incomplete")
            self.assertFalse(data["ready"])
            self.assertIn("date_range_reversed", {issue["code"] for issue in data["issues"]})

            short_cycle = target / "dogfood-cycle-too-short.md"
            short_cycle.write_text(
                "\n".join(
                    [
                        "# Dogfood Cycle Evidence",
                        "",
                        "- Cycle ID: 2026-07-maintenance-02",
                        "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-03",
                        "- Version / commit range: 0.1.0 / abc123..def456",
                        "- Scope: post-migration maintenance cycle for a real long-form project",
                        "- Book / chapter scope: Book 01 ch_001-ch_033, focused review on ch_007",
                        "- Focused tasks: structure recovery and chapter review",
                        "- Commands exercised: adopt-review, adopt-plan, import-plan, doctor",
                        "- AI workflow evidence: eval-agent ch_002 and agent-inbox staged-output checks",
                        "- Human review boundary: staged output stopped at human review",
                        "- Day-by-day ledger: 2026-07-01 baseline; 2026-07-03 close audit",
                        "- Initial adopt-review status: ready",
                        "- Final adopt-review status: ready",
                        "- import_queue_files: 0",
                        "- blocking_issue_count: 0",
                        "- Waiver count: 31",
                        "- Compatibility notes: stable surfaces reviewed",
                        "- Recovery notes: recovery docs reviewed",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            short_data = json.loads(
                self.run_cli(
                    "audit-dogfood-cycle",
                    str(target),
                    "--file",
                    str(short_cycle),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(short_data["status"], "incomplete")
            self.assertFalse(short_data["ready"])
            self.assertIn("dogfood_cycle_too_short", {issue["code"] for issue in short_data["issues"]})

    def test_dogfood_cycle_audit_rejects_thin_command_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "dogfood-cycle-thin-coverage.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Dogfood Cycle Evidence",
                        "",
                        "- Cycle ID: 2026-07-maintenance-01",
                        "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version / commit range: 0.1.0 / abc123..def456",
                        "- Scope: post-migration maintenance cycle for a real long-form project",
                        "- Book / chapter scope: Book 01 ch_001-ch_033, focused review on ch_007",
                        "- Focused tasks: structure recovery and chapter review",
                        "- Commands exercised: doctor, report",
                        "- AI workflow evidence: eval-agent ch_002 and agent-inbox staged-output checks",
                        "- Human review boundary: staged output stopped at human review",
                        "- Day-by-day ledger: 2026-07-01 baseline; 2026-07-07 close audit",
                        "- Initial adopt-review status: ready",
                        "- Final adopt-review status: ready",
                        "- import_queue_files: 0",
                        "- blocking_issue_count: 0",
                        "- Waiver count: 31",
                        "- Compatibility notes: stable surfaces reviewed",
                        "- Recovery notes: recovery docs reviewed",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            data = json.loads(
                self.run_cli(
                    "audit-dogfood-cycle",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(data["status"], "incomplete")
            self.assertFalse(data["ready"])
            self.assertIn("thin_command_coverage", {issue["code"] for issue in data["issues"]})

            vague_evidence = target / "dogfood-cycle-vague-coverage.md"
            vague_evidence.write_text(
                "\n".join(
                    [
                        "# Dogfood Cycle Evidence",
                        "",
                        "- Cycle ID: 2026-07-maintenance-02",
                        "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version / commit range: 0.1.0 / abc123..def456",
                        "- Scope: post-migration maintenance cycle for a real long-form project",
                        "- Book / chapter scope: Book 01 ch_001-ch_033, focused review on ch_007",
                        "- Focused tasks: structure recovery and chapter review",
                        "- Commands exercised: alpha, beta, gamma",
                        "- AI workflow evidence: eval-agent ch_002 and agent-inbox staged-output checks",
                        "- Human review boundary: staged output stopped at human review",
                        "- Day-by-day ledger: 2026-07-01 baseline; 2026-07-07 close audit",
                        "- Initial adopt-review status: ready",
                        "- Final adopt-review status: ready",
                        "- import_queue_files: 0",
                        "- blocking_issue_count: 0",
                        "- Waiver count: 31",
                        "- Compatibility notes: stable surfaces reviewed",
                        "- Recovery notes: recovery docs reviewed",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            vague_data = json.loads(
                self.run_cli(
                    "audit-dogfood-cycle",
                    str(target),
                    "--file",
                    str(vague_evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(vague_data["status"], "incomplete")
            self.assertFalse(vague_data["ready"])
            self.assertIn("unrecognized_command_coverage", {issue["code"] for issue in vague_data["issues"]})

    def test_dogfood_cycle_audit_rejects_vague_task_and_ai_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "dogfood-cycle-vague-task-evidence.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Dogfood Cycle Evidence",
                        "",
                        "- Cycle ID: 2026-07-maintenance-01",
                        "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version / commit range: 0.1.0 / abc123..def456",
                        "- Scope: post-migration maintenance cycle",
                        "- Book / chapter scope: real project maintenance",
                        "- Focused tasks: smoke",
                        "- Commands exercised: adopt-review, doctor, context-pack, revision-plan",
                        "- AI workflow evidence: no AI used",
                        "- Human review boundary: normal process",
                        "- Day-by-day ledger: 2026-07-01 baseline only",
                        "- Initial adopt-review status: ready",
                        "- Final adopt-review status: ready",
                        "- import_queue_files: 0",
                        "- blocking_issue_count: 0",
                        "- Waiver count: 0",
                        "- Compatibility notes: stable surfaces reviewed",
                        "- Recovery notes: recovery docs reviewed",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            data = json.loads(
                self.run_cli(
                    "audit-dogfood-cycle",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            codes = {issue["code"] for issue in data["issues"]}
            self.assertEqual(data["status"], "incomplete")
            self.assertFalse(data["ready"])
            self.assertIn("missing_book_chapter_scope", codes)
            self.assertIn("thin_focused_tasks", codes)
            self.assertIn("missing_ai_workflow_evidence", codes)
            self.assertIn("missing_human_review_boundary", codes)
            self.assertIn("thin_day_by_day_ledger", codes)

    def test_stability_window_audit_reports_template_as_incomplete(self) -> None:
        report = build_stability_window_audit(ROOT)
        self.assertEqual(report.status, "incomplete")
        self.assertFalse(report.ready)
        self.assertIn("Window ID", report.missing_required_fields)
        self.assertIn("Reviewer", report.missing_required_fields)
        self.assertGreater(report.blocking_issue_count, 0)

        result = self.run_cli("audit-stability-window", str(ROOT), "--format", "json")
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "incomplete")
        self.assertEqual(data["ready"], False)
        self.assertIn("missing_stability_window_field", {issue["code"] for issue in data["issues"]})

    def test_stability_window_audit_accepts_filled_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.write_accepted_release_evidence(target)
            self.write_accepted_dogfood_cycle(target)
            evidence = target / "stability-window-filled.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-01",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: docs/release-trial-evidence.md",
                        "- Dogfood cycle reference: docs/dogfood-cycle-evidence.md",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "audit-stability-window",
                str(target),
                "--file",
                str(evidence),
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "accepted")
            self.assertEqual(data["ready"], True)
            self.assertEqual(data["blocking_issue_count"], 0)

    def test_stability_window_audit_rejects_missing_or_unready_local_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "stability-window-missing-references.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-01",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: docs/release-trial-evidence.md",
                        "- Dogfood cycle reference: docs/dogfood-cycle-evidence.md",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            missing_data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(missing_data["status"], "incomplete")
            self.assertFalse(missing_data["ready"])
            self.assertIn("missing_evidence_reference_file", {issue["code"] for issue in missing_data["issues"]})

            (target / "docs").mkdir(exist_ok=True)
            (target / "docs" / "release-trial-evidence.md").write_text(
                "# Release Trial Evidence\n\n- Decision: deferred\n",
                encoding="utf-8",
            )
            (target / "docs" / "dogfood-cycle-evidence.md").write_text(
                "# Dogfood Cycle Evidence\n\n- Decision: deferred\n",
                encoding="utf-8",
            )
            unready_data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            codes = {issue["code"] for issue in unready_data["issues"]}
            self.assertEqual(unready_data["status"], "incomplete")
            self.assertFalse(unready_data["ready"])
            self.assertIn("release_reference_not_ready", codes)
            self.assertIn("dogfood_reference_not_ready", codes)

            outside = target.parent / "outside-evidence"
            self.write_accepted_release_evidence(outside, relative="release-trial-evidence.md")
            self.write_accepted_dogfood_cycle(outside, relative="dogfood-cycle-evidence.md")
            outside_window = target / "stability-window-outside-references.md"
            outside_window.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-02",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version range: 0.1.0",
                        f"- Release evidence reference: {outside / 'release-trial-evidence.md'}",
                        f"- Dogfood cycle reference: {outside / 'dogfood-cycle-evidence.md'}",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            outside_data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(outside_window),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(outside_data["status"], "incomplete")
            self.assertFalse(outside_data["ready"])
            self.assertIn("evidence_reference_outside_target", {issue["code"] for issue in outside_data["issues"]})

    def test_stability_window_audit_rejects_invalid_date_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "stability-window-bad-dates.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-01",
                        "- Start date: 2026-13-01",
                        "- End date: 2026-07-01",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: docs/release-trial-evidence.md",
                        "- Dogfood cycle reference: docs/dogfood-cycle-evidence.md",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(data["status"], "incomplete")
            self.assertFalse(data["ready"])
            self.assertIn("invalid_date", {issue["code"] for issue in data["issues"]})

            reversed_window = target / "stability-window-reversed.md"
            reversed_window.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-02",
                        "- Start date: 2026-07-07",
                        "- End date: 2026-07-01",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: docs/release-trial-evidence.md",
                        "- Dogfood cycle reference: docs/dogfood-cycle-evidence.md",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            reversed_data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(reversed_window),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(reversed_data["status"], "incomplete")
            self.assertFalse(reversed_data["ready"])
            self.assertIn("date_range_reversed", {issue["code"] for issue in reversed_data["issues"]})

            short_window = target / "stability-window-too-short.md"
            short_window.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-03",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-03",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: docs/release-trial-evidence.md",
                        "- Dogfood cycle reference: docs/dogfood-cycle-evidence.md",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            short_data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(short_window),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(short_data["status"], "incomplete")
            self.assertFalse(short_data["ready"])
            self.assertIn("stability_window_too_short", {issue["code"] for issue in short_data["issues"]})

    def test_stability_window_audit_rejects_weak_evidence_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            evidence = target / "stability-window-weak-references.md"
            evidence.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-01",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: release memo",
                        "- Dogfood cycle reference: dogfood note",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(data["status"], "incomplete")
            self.assertFalse(data["ready"])
            self.assertIn("weak_evidence_reference", {issue["code"] for issue in data["issues"]})

            malformed_url_evidence = target / "stability-window-malformed-url-references.md"
            malformed_url_evidence.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-02",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: http",
                        "- Dogfood cycle reference: http://example.com/dogfood-cycle-evidence",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            malformed_data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(malformed_url_evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(malformed_data["status"], "incomplete")
            self.assertFalse(malformed_data["ready"])
            self.assertIn("invalid_evidence_reference_url", {issue["code"] for issue in malformed_data["issues"]})

            generic_url_evidence = target / "stability-window-generic-url-references.md"
            generic_url_evidence.write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-03",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: https://example.com",
                        "- Dogfood cycle reference: https://example.com/notes",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            generic_url_data = json.loads(
                self.run_cli(
                    "audit-stability-window",
                    str(target),
                    "--file",
                    str(generic_url_evidence),
                    "--format",
                    "json",
                ).stdout
            )
            self.assertEqual(generic_url_data["status"], "incomplete")
            self.assertFalse(generic_url_data["ready"])
            self.assertIn("weak_evidence_reference_url", {issue["code"] for issue in generic_url_data["issues"]})

    def test_stable_core_audit_reports_current_external_gaps(self) -> None:
        report = build_stable_core_audit(ROOT)
        self.assertEqual(report.status, "not_ready")
        self.assertFalse(report.ready)
        self.assertTrue(report.local_foundation_ready)
        codes = {item.code for item in report.issues}
        self.assertNotIn("release_evidence_not_ready", codes)
        self.assertIn("dogfood_cycle_not_ready", codes)
        self.assertIn("stability_window_not_accepted", codes)
        actions = {item.item_id: item for item in report.action_items}
        self.assertEqual(actions["local-foundation"].status, "complete")
        self.assertEqual(actions["release-trial-evidence"].status, "complete")
        self.assertEqual(actions["sustained-dogfood-cycle"].status, "external_required")
        self.assertEqual(actions["stability-window"].status, "external_required")
        self.assertIn("audit-release-evidence", actions["release-trial-evidence"].audit_command)

        result = self.run_cli("audit-stable-core", str(ROOT), "--format", "json")
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "not_ready")
        self.assertEqual(data["ready"], False)
        self.assertEqual(data["evidence"]["release_evidence_status"], "accepted")
        self.assertIn("release_evidence_status", data["evidence"])
        self.assertIn("action_items", data)
        self.assertIn("release-trial-evidence", {item["item_id"] for item in data["action_items"]})

    def test_stable_core_audit_accepts_complete_evidence_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for relative in [
                "docs/cli-contracts.md",
                "docs/compatibility.md",
                "docs/compatibility.zh-CN.md",
                "docs/known-limits.md",
                "docs/known-limits.zh-CN.md",
                "docs/recovery.md",
                "docs/recovery.zh-CN.md",
                ".github/workflows/fictionops-ci.yml",
                ".github/workflows/fictionops-publish.yml",
                "tests/test_cli.py",
                "CHANGELOG.md",
            ]:
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"# {relative}\n", encoding="utf-8")
            (target / "docs" / "stable-core-audit.md").write_text(
                "# Stable Core Audit\n\nCurrent result: **complete**.\n",
                encoding="utf-8",
            )
            (target / "docs" / "stable-core-audit.zh-CN.md").write_text("# 稳定核心审计\n", encoding="utf-8")
            (target / "docs" / "milestone-status.md").write_text(
                "| Milestone | Status |\n| --- | --- |\n| 1.0.0 Stable Core | Complete |\n",
                encoding="utf-8",
            )
            (target / "docs" / "milestone-status.zh-CN.md").write_text("# 里程碑\n", encoding="utf-8")
            (target / "docs" / "release-trial-evidence.md").write_text(
                "\n".join(
                    [
                        "# Release Trial Evidence",
                        "",
                        "- Date: 2026-07-07",
                        "- Version: 0.1.0",
                        "- Commit / ref / tag: abc123 / v0.1.0",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                        "- GitHub Actions run URL: https://github.com/example/fictionops/actions/runs/123456789",
                        "- GitHub Actions run ID: 123456789",
                        "- Wheel filename: fictionops-0.1.0-py3-none-any.whl",
                        "- Wheel SHA256: " + "a" * 64,
                        "- sdist filename: fictionops-0.1.0.tar.gz",
                        "- sdist SHA256: " + "b" * 64,
                        "- Built-wheel smoke result: passed",
                        "- TestPyPI used: no",
                        "- TestPyPI skip reason: validating GitHub Actions artifact instead of publishing to TestPyPI",
                        "- TestPyPI skip accepted by: maintainer",
                        "- fictionops --version result: fictionops 0.1.0",
                        "- python -m fictionops --version result: fictionops 0.1.0",
                        "- fictionops init smoke result: passed",
                        "- fictionops doctor smoke result: passed",
                    ]
                ),
                encoding="utf-8",
            )
            (target / "docs" / "dogfood-cycle-evidence.md").write_text(
                "\n".join(
                    [
                        "# Dogfood Cycle Evidence",
                        "",
                        "- Cycle ID: 2026-07-maintenance-01",
                        "- Project / sandbox: C:/tmp/fictionops-real-project-cycle",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version / commit range: 0.1.0 / abc123..def456",
                        "- Scope: post-migration maintenance cycle",
                        "- Book / chapter scope: Book 01 ch_001-ch_033, focused review on ch_007 and ch_010",
                        "- Focused tasks: structure recovery, AI staged-output review, and bounded prose maintenance",
                        "- Commands exercised: adopt-review, adopt-plan, import-plan, doctor",
                        "- AI workflow evidence: eval-agent ch_002 and agent-run/agent-inbox staged-output checks",
                        "- Human review boundary: staged output stopped at human review and no source overwrite was allowed",
                        "- Day-by-day ledger: 2026-07-01 baseline audit; 2026-07-07 close audit and reviewer decision",
                        "- Initial adopt-review status: ready",
                        "- Final adopt-review status: ready",
                        "- import_queue_files: 0",
                        "- blocking_issue_count: 0",
                        "- Waiver count: 31",
                        "- Compatibility notes: stable surfaces reviewed",
                        "- Recovery notes: recovery docs reviewed",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            (target / "docs" / "stability-window-evidence.md").write_text(
                "\n".join(
                    [
                        "# Stability Window Evidence",
                        "",
                        "- Window ID: 2026-07-stability-01",
                        "- Start date: 2026-07-01",
                        "- End date: 2026-07-07",
                        "- Version range: 0.1.0",
                        "- Release evidence reference: docs/release-trial-evidence.md",
                        "- Dogfood cycle reference: docs/dogfood-cycle-evidence.md",
                        "- Compatibility notes: no undocumented breaking changes",
                        "- Breaking changes: none",
                        "- Recovery notes: recovery docs current",
                        "- Decision: accepted",
                        "- Reviewer: maintainer",
                    ]
                ),
                encoding="utf-8",
            )
            (target / "docs" / "stability-window-evidence.zh-CN.md").write_text("# 稳定窗口证据\n", encoding="utf-8")

            report = build_stable_core_audit(target)
            self.assertEqual(report.status, "ready")
            self.assertTrue(report.ready)
            self.assertEqual(report.blocking_issue_count, 0)
            actions = {item.item_id: item for item in report.action_items}
            self.assertEqual(actions["release-trial-evidence"].status, "complete")
            self.assertEqual(actions["sustained-dogfood-cycle"].status, "complete")
            self.assertEqual(actions["stability-window"].status, "complete")
            self.assertEqual(actions["stable-core-ledger"].status, "complete")

    def test_audit_plan_reports_plan_file_coverage(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "\n".join(
                    [
                        "| 01 | Opening Gate | A | p1 | d1 | o1 | c1 | r1 | 8200 |",
                        "| 02 | Missing Draft | B | p2 | d2 | o2 | c2 | r2 | 7800 |",
                    ]
                ),
            )
            plan_chapter(target, book="book_01", chapter="1", outline=None, force=False, dry_run=False)
            create_chapter(
                target,
                book="book_01",
                chapter="3",
                title="Unplanned",
                viewpoint=None,
                kind=None,
                target_chars=None,
                force=False,
                dry_run=False,
            )

            report = build_plan_audit_report(target, book="book_01", outline=None)
            self.assertEqual(report.planned_chapters, 2)
            self.assertEqual(report.synced_engines, 1)
            codes = {issue.code for issue in report.issues}
            self.assertIn("missing_chapter_file", codes)
            self.assertIn("missing_chapter_engine", codes)
            self.assertIn("unplanned_chapter_file", codes)

    def test_audit_plan_cli_outputs_json(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "| 01 | JSON Planned | A | p | d | o | c | r | 8000 |",
            )
            result = self.run_cli("audit-plan", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["planned_chapters"], 1)
            self.assertEqual(data["book"], "book_01")
            self.assertIn("issues", data)

    def test_retrospective_reports_missing_and_open_sync_items(self) -> None:
        temp, target = self.make_project()
        with temp:
            create_chapter(
                target,
                book="book_01",
                chapter="2",
                title="Retrospective Ready",
                viewpoint=None,
                kind=None,
                target_chars=None,
                force=False,
                dry_run=False,
            )
            self.write_filled_chapter_retrospective(target, "002")

            report = build_retrospective_report(target, book="book_01")
            self.assertEqual(report.chapter_count, 2)
            self.assertEqual(report.missing_retrospectives, 1)
            self.assertEqual(report.sync_item_count, 1)
            codes = {issue.code for issue in report.issues}
            self.assertIn("missing_chapter_retrospective", codes)
            self.assertIn("open_sync_item", codes)

    def test_retrospective_cli_outputs_json_and_writes_markdown(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("retrospective", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["book"], "book_01")
            self.assertIn("chapters", data)

            output = target / "07_audits" / "book_retrospectives" / "book_01_generated_report.md"
            written = self.run_cli("retrospective", str(target), "--out", str(output))
            self.assertIn("Wrote FictionOps retrospective", written.stdout)
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Retrospective", output.read_text(encoding="utf-8"))

    def test_export_clean_merges_chapters_without_overwriting_drafts(self) -> None:
        temp, target = self.make_project()
        with temp:
            create_chapter(
                target,
                book="book_01",
                chapter="2",
                title="Second",
                viewpoint=None,
                kind=None,
                target_chars=None,
                force=False,
                dry_run=False,
            )
            first = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            second = target / "06_drafts" / "book_01" / "chapters" / "ch_002.md"
            first.write_text("# 第一章\n\n第一章正文。", encoding="utf-8")
            second.write_text("# 第二章\n\n> Draft starts here.\n\n第二章正文。", encoding="utf-8")

            result = export_clean_markdown(
                target,
                book="book_01",
                out=None,
                title="Clean Book",
                force=False,
                dry_run=False,
            )
            output = Path(result.output_file)
            self.assertEqual(result.chapter_count, 2)
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# Clean Book"))
            self.assertIn("# 第一章", text)
            self.assertIn("# 第二章", text)
            self.assertNotIn("Draft starts here", text)
            self.assertIn("> Draft starts here.", second.read_text(encoding="utf-8"))

    def test_export_clean_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# 第一章\n\n正文。", encoding="utf-8")

            result = self.run_cli("export-clean", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["book"], "book_01")
            self.assertEqual(data["chapter_count"], 1)
            output = Path(data["output_file"])
            self.assertTrue(output.exists())

            refused = self.run_cli("export-clean", str(target), check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("Use --force to overwrite", refused.stderr)

            dry_run = self.run_cli("export-clean", str(target), "--dry-run", "--format", "json")
            dry_data = json.loads(dry_run.stdout)
            self.assertEqual(dry_data["dry_run"], True)

    def test_audit_publish_reports_missing_file_and_publish_gaps(self) -> None:
        temp, target = self.make_project()
        with temp:
            missing = build_publish_audit_report(
                target,
                book="book_01",
                file_path=None,
                min_chapter_chars=200,
            )
            self.assertEqual(missing.clean_file_exists, False)
            self.assertIn("missing_clean_markdown", {issue.code for issue in missing.issues})

            output = target / "08_publish" / "clean_markdown" / "book_01.md"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                "# 第001章\n\n正文很短。\n\n# 第003章\n\n> Draft starts here.\n\n正文也很短。",
                encoding="utf-8",
            )
            report = build_publish_audit_report(
                target,
                book="book_01",
                file_path=None,
                min_chapter_chars=20,
            )
            codes = {issue.code for issue in report.issues}
            self.assertEqual(report.clean_chapters, 2)
            self.assertIn("draft_marker_left", codes)
            self.assertIn("chapter_number_gap", codes)
            self.assertIn("short_chapter", codes)
            self.assertIn("draft_clean_count_mismatch", codes)

    def test_audit_publish_cli_outputs_json_after_export_clean(self) -> None:
        temp, target = self.make_project()
        with temp:
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# 第001章\n\n" + "正文内容。" * 40, encoding="utf-8")
            self.run_cli("export-clean", str(target), "--book", "book_01")

            result = self.run_cli(
                "audit-publish",
                str(target),
                "--book",
                "book_01",
                "--min-chapter-chars",
                "10",
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["clean_file_exists"], True)
            self.assertEqual(data["draft_chapters"], 1)
            self.assertEqual(data["clean_chapters"], 1)
            self.assertEqual(data["issues"], [])

    def test_publish_copy_drafts_synopsis_tags_and_keywords(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_publish_copy_sources(target)

            report = build_publish_copy(
                target,
                book="book_01",
                clean_file=None,
                checklist_file=None,
                outline_file=None,
                seed_file=None,
                out=None,
                force=False,
                dry_run=False,
            )
            self.assertEqual(report.book, "book_01")
            self.assertTrue(report.written)
            self.assertTrue(Path(report.output_file or "").exists())
            self.assertIn("烟雪", report.title_candidates)
            self.assertIn("权谋", report.tag_candidates)
            self.assertIn("成长", report.tag_candidates)
            self.assertIn("神话", report.tag_candidates)
            self.assertIn("旧藏", "".join(report.keyword_candidates))
            self.assertIn("少年从被权力碾过的人", str(report.suggested_metadata["short_synopsis"]))
            self.assertEqual(report.chapter_titles, ["第一章 灯市", "第二章 灯下"])

    def test_publish_copy_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_publish_copy_sources(target)

            result = self.run_cli("publish-copy", str(target), "--book", "book_01", "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["book"], "book_01")
            self.assertTrue(data["written"])
            self.assertIn("权谋", data["tag_candidates"])
            output = Path(data["output_file"])
            self.assertTrue(output.exists())

            refused = self.run_cli("publish-copy", str(target), "--book", "book_01", check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("Use --force to overwrite", refused.stderr)

            dry_run = self.run_cli("publish-copy", str(target), "--book", "book_01", "--dry-run", "--format", "json")
            dry_data = json.loads(dry_run.stdout)
            self.assertEqual(dry_data["dry_run"], True)
            self.assertEqual(dry_data["written"], False)

    def test_export_metadata_parses_checklist_and_writes_json(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_publish_checklist_metadata(target)
            report = export_publish_metadata(
                target,
                book="book_01",
                file_path=None,
                out=None,
                force=False,
                dry_run=False,
            )
            self.assertEqual(report.metadata["title"], "烟雪")
            self.assertEqual(report.metadata["tags"], ["权谋", "成长", "神话"])
            self.assertEqual(report.issues, [])
            self.assertEqual(report.written, True)
            output = Path(report.output_file or "")
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["metadata"]["author"], "示例作者")

    def test_export_metadata_reports_missing_required_fields(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = export_publish_metadata(
                target,
                book="book_01",
                file_path=None,
                out=None,
                force=False,
                dry_run=True,
            )
            codes = {issue.code for issue in report.issues}
            self.assertIn("missing_required_metadata", codes)
            self.assertIn("content_warning_unspecified", codes)
            self.assertEqual(report.written, False)

    def test_export_metadata_accepts_checklist_file_target(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_publish_checklist_metadata(target)
            checklist = target / "08_publish" / "publish_checklist.md"
            checklist.write_text(
                checklist.read_text(encoding="utf-8").replace("是否需要内容提示：不需要", "是否需要内容提示：无"),
                encoding="utf-8",
            )
            report = export_publish_metadata(
                checklist,
                book="book_01",
                file_path=None,
                out=None,
                force=False,
                dry_run=True,
            )
            self.assertEqual(report.output_file, str(target / "08_publish" / "metadata" / "book_01_metadata.json"))
            self.assertNotIn("content_warning_unspecified", {issue.code for issue in report.issues})

    def test_export_metadata_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_publish_checklist_metadata(target)

            result = self.run_cli("export-metadata", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["metadata"]["category"], "幻想")
            self.assertEqual(data["written"], True)
            self.assertTrue(Path(data["output_file"]).exists())

            refused = self.run_cli("export-metadata", str(target), check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("Use --force to overwrite", refused.stderr)

            dry_run = self.run_cli("export-metadata", str(target), "--dry-run", "--format", "json")
            dry_data = json.loads(dry_run.stdout)
            self.assertEqual(dry_data["dry_run"], True)
            self.assertEqual(dry_data["written"], False)

    def test_export_manifest_reports_missing_package_files(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = export_publish_manifest(
                target,
                book="book_01",
                clean_file=None,
                metadata_file=None,
                out=None,
                force=False,
                dry_run=True,
            )
            codes = {issue.code for issue in report.issues}
            self.assertIn("missing_clean_markdown", codes)
            self.assertIn("missing_metadata_json", codes)
            self.assertEqual(report.written, False)
            self.assertEqual(report.manifest["schema"], "fictionops.publish_manifest.v1")

    def test_export_manifest_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# 第001章\n\n" + "正文内容。" * 40, encoding="utf-8")
            self.run_cli("export-clean", str(target), "--book", "book_01")
            self.write_publish_checklist_metadata(target)
            self.run_cli("export-metadata", str(target), "--book", "book_01")

            result = self.run_cli("export-manifest", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["manifest"]["schema"], "fictionops.publish_manifest.v1")
            self.assertEqual(data["manifest"]["metadata"]["title"], "烟雪")
            self.assertEqual(data["written"], True)
            self.assertEqual(data["issues"], [])
            self.assertTrue(Path(data["output_file"]).exists())
            clean_hash = data["manifest"]["files"]["clean_markdown"]["sha256"]
            self.assertEqual(len(clean_hash), 64)

            refused = self.run_cli("export-manifest", str(target), check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("Use --force to overwrite", refused.stderr)

            dry_run = self.run_cli("export-manifest", str(target), "--dry-run", "--format", "json")
            dry_data = json.loads(dry_run.stdout)
            self.assertEqual(dry_data["dry_run"], True)
            self.assertEqual(dry_data["written"], False)

    def test_export_epub_reports_missing_inputs(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = export_epub(
                target,
                book="book_01",
                manifest_file=None,
                clean_file=None,
                metadata_file=None,
                cover_file=None,
                out=None,
                force=False,
                dry_run=False,
            )
            codes = {issue.code for issue in report.issues}
            self.assertIn("missing_manifest", codes)
            self.assertIn("missing_clean_markdown", codes)
            self.assertEqual(report.written, False)
            self.assertFalse((target / "08_publish" / "epub" / "book_01.epub").exists())

    def test_export_epub_cli_writes_valid_epub_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# 第001章\n\n" + "正文内容。" * 40, encoding="utf-8")
            self.run_cli("export-clean", str(target), "--book", "book_01")
            self.write_publish_checklist_metadata(target)
            self.run_cli("export-metadata", str(target), "--book", "book_01")
            self.run_cli("export-manifest", str(target), "--book", "book_01")

            result = self.run_cli("export-epub", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["chapter_count"], 1)
            self.assertEqual(data["metadata"]["title"], "烟雪")
            self.assertEqual(data["written"], True)
            output = Path(data["output_file"])
            self.assertTrue(output.exists())

            with zipfile.ZipFile(output) as zf:
                self.assertEqual(zf.namelist()[0], "mimetype")
                self.assertEqual(zf.read("mimetype").decode("utf-8"), "application/epub+zip")
                self.assertIn("META-INF/container.xml", zf.namelist())
                self.assertIn("OEBPS/content.opf", zf.namelist())
                self.assertIn("OEBPS/nav.xhtml", zf.namelist())
                self.assertIn("OEBPS/styles/fictionops.css", zf.namelist())
                self.assertIn("OEBPS/chapters/chapter_001.xhtml", zf.namelist())
                opf = zf.read("OEBPS/content.opf").decode("utf-8")
                chapter_xhtml = zf.read("OEBPS/chapters/chapter_001.xhtml").decode("utf-8")
                self.assertIn("烟雪", opf)
                self.assertIn('href="../styles/fictionops.css"', chapter_xhtml)

            refused = self.run_cli("export-epub", str(target), check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("Use --force to overwrite", refused.stderr)

            dry_run = self.run_cli("export-epub", str(target), "--dry-run", "--format", "json")
            dry_data = json.loads(dry_run.stdout)
            self.assertEqual(dry_data["dry_run"], True)
            self.assertEqual(dry_data["written"], False)

    def test_export_epub_includes_optional_cover_from_metadata(self) -> None:
        temp, target = self.make_project()
        with temp:
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# Chapter 001\n\n" + "正文内容。" * 40, encoding="utf-8")
            self.run_cli("export-clean", str(target), "--book", "book_01")
            cover = target / "08_publish" / "assets" / "cover.png"
            cover.parent.mkdir(parents=True, exist_ok=True)
            cover.write_bytes(b"\x81PNG\r\n\x1a\nfictionops-cover")
            self.write_publish_checklist_metadata(target)
            checklist = target / "08_publish" / "publish_checklist.md"
            checklist.write_text(
                checklist.read_text(encoding="utf-8") + "\n- cover image: 08_publish/assets/cover.png\n",
                encoding="utf-8",
            )
            self.run_cli("export-metadata", str(target), "--book", "book_01")

            manifest = json.loads(self.run_cli("export-manifest", str(target), "--format", "json").stdout)
            self.assertTrue(manifest["manifest"]["files"]["cover_image"]["exists"])
            self.assertEqual(len(manifest["manifest"]["files"]["cover_image"]["sha256"]), 64)

            result = self.run_cli("export-epub", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["cover_file_exists"], True)
            output = Path(data["output_file"])
            with zipfile.ZipFile(output) as zf:
                self.assertIn("OEBPS/cover.xhtml", zf.namelist())
                self.assertIn("OEBPS/images/cover.png", zf.namelist())
                self.assertIn("OEBPS/styles/fictionops.css", zf.namelist())
                opf = zf.read("OEBPS/content.opf").decode("utf-8")
                cover_xhtml = zf.read("OEBPS/cover.xhtml").decode("utf-8")
                self.assertIn('properties="cover-image"', opf)
                self.assertIn("<dc:description>", opf)
                self.assertIn("<dc:subject>", opf)
                self.assertIn('src="images/cover.png"', cover_xhtml)

    def test_audit_epub_cli_reports_valid_and_stale_epub(self) -> None:
        temp, target = self.make_project()
        with temp:
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# Chapter 001\n\n" + "正文内容。" * 40, encoding="utf-8")
            self.run_cli("export-clean", str(target), "--book", "book_01")
            self.write_publish_checklist_metadata(target)
            self.run_cli("export-metadata", str(target), "--book", "book_01")
            self.run_cli("export-manifest", str(target), "--book", "book_01")
            self.run_cli("export-epub", str(target), "--book", "book_01")

            result = self.run_cli("audit-epub", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["epub_file_exists"], True)
            self.assertEqual(data["epub_valid"], True)
            self.assertEqual(data["has_css"], True)
            self.assertEqual(data["chapter_count"], 1)
            self.assertEqual(data["issues"], [])

            clean_file = target / "08_publish" / "clean_markdown" / "book_01.md"
            epub_file = target / "08_publish" / "epub" / "book_01.epub"
            bumped_time = max(clean_file.stat().st_mtime, epub_file.stat().st_mtime) + 10
            os.utime(clean_file, (bumped_time, bumped_time))
            stale = build_epub_audit_report(
                target,
                book="book_01",
                file_path=None,
                manifest_file=None,
                clean_file=None,
                metadata_file=None,
            )
            self.assertEqual(stale.epub_valid, True)
            self.assertEqual(stale.stale, True)
            self.assertIn("stale_epub", {issue.code for issue in stale.issues})

    def test_audit_epub_reports_invalid_archive(self) -> None:
        temp, target = self.make_project()
        with temp:
            epub = target / "08_publish" / "epub" / "book_01.epub"
            epub.parent.mkdir(parents=True, exist_ok=True)
            epub.write_text("not a zip archive", encoding="utf-8")

            result = self.run_cli("audit-epub", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["epub_file_exists"], True)
            self.assertEqual(data["epub_valid"], False)
            codes = {issue["code"] for issue in data["issues"]}
            self.assertIn("invalid_epub_archive", codes)

    def test_stats_counts_chapters_but_not_engines(self) -> None:
        temp, target = self.make_project()
        with temp:
            extra = target / "06_drafts" / "book_01" / "chapters" / "第02章_测试.md"
            extra.write_text("# 第二章\n\n这是一章正文。", encoding="utf-8")

            report = build_stats_report(target, all_markdown=False, pattern="**/*.md", metric="nonspace")
            self.assertEqual(report.file_count, 2)
            paths = {item.path for item in report.files}
            self.assertTrue(any(path.endswith("ch_001.md") for path in paths))
            self.assertTrue(any("第02章_测试.md" in path for path in paths))
            self.assertFalse(any("engine" in path.lower() for path in paths))

    def test_scan_words_reports_terms_and_watch_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            chapter_dir = target / "chapters"
            chapter_dir.mkdir()
            (chapter_dir / "ch_001.md").write_text(
                "# 第一章\n\n旧城遗藏在雪里。旧城遗藏不说话。权力在灯下，权力也在沉默里。",
                encoding="utf-8",
            )

            report = build_word_scan_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                watch="旧城遗藏,权力",
                min_count=2,
                top=8,
            )
            self.assertEqual(report.file_count, 1)
            self.assertIn("旧城遗藏", {item.item for item in report.aggregate_terms})
            self.assertEqual({item.item for item in report.watch_hits}, {"旧城遗藏", "权力"})

            data = json.loads(
                self.run_cli("scan-words", str(target), "--watch", "旧城遗藏,权力", "--format", "json").stdout
            )
            self.assertEqual(data["file_count"], 1)
            self.assertIn("旧城遗藏", {item["item"] for item in data["watch_hits"]})

    def test_check_tables_reports_structural_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            chapter_dir = target / "chapters"
            chapter_dir.mkdir()
            (chapter_dir / "ch_001.md").write_text(
                textwrap.dedent(
                    """\
                    # 第一章

                    | 人物 | 状态 |
                    | --- | --- |
                    | 林遥 |  |
                    |  |  |
                    | 周澄 | 北上 |
                    """
                ),
                encoding="utf-8",
            )

            report = build_table_check_report(target, all_markdown=False, pattern="**/*.md", min_filled_cells=2)
            self.assertEqual(report.table_count, 1)
            codes = {issue.code for issue in report.issues}
            self.assertIn("mostly_empty_row", codes)

            data = json.loads(
                self.run_cli("check-tables", str(target), "--min-filled-cells", "2", "--format", "json").stdout
            )
            self.assertEqual(data["table_count"], 1)
            self.assertIn("mostly_empty_row", {issue["code"] for issue in data["issues"]})

    def test_audit_wave_reports_flat_chapter_lengths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            chapter_dir = target / "chapters"
            chapter_dir.mkdir()
            for index, size in enumerate([1000, 1010, 1015, 1005, 1008], start=1):
                (chapter_dir / f"ch_{index:03d}.md").write_text(
                    "# Chapter\n\n" + ("A" * size),
                    encoding="utf-8",
                )

            report = build_chapter_wave_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                flat_tolerance=20,
                min_spread_ratio=10,
                max_flat_run=4,
                max_same_band_run=5,
            )
            self.assertEqual(report.file_count, 5)
            self.assertEqual(report.longest_flat_run, 5)
            self.assertEqual(report.longest_same_band_run, 5)
            codes = {issue.code for issue in report.issues}
            self.assertIn("too_uniform_wave", codes)
            self.assertIn("flat_chapter_run", codes)
            self.assertIn("same_band_run", codes)

    def test_audit_wave_cli_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            chapter_dir = target / "chapters"
            chapter_dir.mkdir()
            for index, size in enumerate([800, 2200, 1200], start=1):
                (chapter_dir / f"ch_{index:03d}.md").write_text(
                    "# Chapter\n\n" + ("B" * size),
                    encoding="utf-8",
                )

            data = json.loads(
                self.run_cli("audit-wave", str(target), "--flat-tolerance", "50", "--format", "json").stdout
            )
            self.assertEqual(data["file_count"], 3)
            self.assertEqual(len(data["chapters"]), 3)
            self.assertIn("short", data["band_counts"])
            self.assertEqual(data["chapters"][0]["delta_from_previous"], None)

    def test_doctor_includes_chapter_wave_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            chapter_dir = target / "chapters"
            chapter_dir.mkdir()
            for index, size in enumerate([1000, 1008, 1003, 1012, 1007], start=1):
                (chapter_dir / f"ch_{index:03d}.md").write_text(
                    "# Chapter\n\n" + ("C" * size),
                    encoding="utf-8",
                )

            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=True,
                stale_after=8,
                flat_tolerance=20,
                min_spread_ratio=10,
                max_flat_run=4,
                max_same_band_run=5,
            )
            self.assertEqual(report.wave["files"], 5)
            self.assertGreater(report.wave["issues"], 0)
            self.assertGreaterEqual(report.wave["longest_flat_run"], 4)
            self.assertTrue(any("chapter length wave" in item for item in report.recommendations))

    def test_audit_style_reports_watch_terms_and_repeated_openings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            chapter_dir = target / "chapters"
            chapter_dir.mkdir()
            (chapter_dir / "ch_001.md").write_text(
                "# Chapter\n\n他说：没有雨。\n他说：没有风。\n他说：没有路。\n",
                encoding="utf-8",
            )

            report = build_style_audit_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
            )
            self.assertEqual(report.file_count, 1)
            self.assertEqual(report.watch_total, 3)
            self.assertTrue(any(item.item.startswith("他说") and item.count == 3 for item in report.repeated_openings))

    def test_review_workflow_builds_agent_revision_queue_from_pattern_families(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            chapter = target / "第26章_冰中四人.md"
            chapter.write_text(
                "# 第二十六章 冰中四人\n\n"
                "不是怪物的黑，也不是死人的黑。\n"
                "他不是想帮这些人。他只是看见那条布。\n"
                "没有声音。没有嘲笑。没有人动。\n"
                "白影像雪粒一样过去。\n"
                "风声好似旧纸擦过石面。\n"
                "远处仿佛落下一小片盐。\n"
                "那点余光宛如无声的灰。\n"
                "冰屑是贴着袖口游走的薄盐。\n"
                "可它不是灾厄。它有名字。\n",
                encoding="utf-8",
            )

            report = build_review_workflow_report(chapter, top_lines=20)
            self.assertEqual(report.file_count, 1)
            file_report = report.files[0]
            families = {issue.family for issue in file_report.issues}
            self.assertIn("exclusionary_narration", families)
            self.assertIn("absence_filter", families)
            simile_metric = next(item for item in file_report.metrics if item.key == "simile")
            self.assertEqual(simile_metric.count, 4)
            self.assertEqual(
                simile_metric.details["marker_counts"],
                {"像": 1, "好似": 1, "仿佛": 1, "宛如": 1},
            )
            self.assertIn("implicit_metaphor", simile_metric.details["semantic_review_required_for"])
            self.assertTrue({"像", "好似", "仿佛", "宛如"} <= {item.term for item in file_report.evidence_lines})
            self.assertTrue(any(task["role"] == "style-auditor" for task in file_report.agent_tasks))
            self.assertTrue(any("不是A，也不是B" in item or "不是A" in item for item in file_report.revision_queue))

            cli = self.run_cli("review-workflow", str(chapter), "--format", "json")
            data = json.loads(cli.stdout)
            self.assertEqual(data["file_count"], 1)
            self.assertEqual(data["files"][0]["path"], chapter.name)

    def test_agent_revise_workflow_stages_revision_from_review_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            management = target / "00_总纲与管理"
            chapter_dir = target / "卷一" / "第一本"
            management.mkdir()
            chapter_dir.mkdir(parents=True)
            chapter = chapter_dir / "ch_026.md"
            chapter.write_text(
                "# Chapter 26\n\n"
                "不是风，也不是雪。没有声音，没有人动。\n"
                "白影像雪一样过去，剑光像针一样亮。\n",
                encoding="utf-8",
            )
            review = management / "ch_026_review_workflow.md"
            review.write_text(
                "# FictionOps Review Workflow\n\n"
                "## Revision Queue\n\n"
                "- Review low-value `不是A，也不是B` negation patterns.\n"
                "- Convert ordinary `没有...` lines into action, silence, or object evidence.\n",
                encoding="utf-8",
            )

            report = build_agent_revise_workflow(
                chapter,
                review=review,
                out_dir="00_总纲与管理/agent_runs/revise_026",
            )
            self.assertTrue(report.prepared)
            self.assertFalse(report.executed)
            run_dir = Path(report.run_dir)
            self.assertTrue((run_dir / "source_chapter.md").exists())
            self.assertTrue((run_dir / "review_workflow.md").exists())
            self.assertIn("Write only the revised chapter text", (run_dir / "revision_contract.md").read_text(encoding="utf-8"))
            request = json.loads((run_dir / "request.json").read_text(encoding="utf-8"))
            self.assertEqual(request["schema"], "fictionops.agent_run_request.v1")
            self.assertEqual(request["source_chapter_file"], str(chapter.resolve()))
            self.assertTrue(request["source_chapter_sha256"])
            self.assertTrue((run_dir / "session.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "issues.before.json").exists())
            self.assertTrue((run_dir / "audits.before.json").exists())

            runner = ROOT / "examples" / "agent_runner_echo.py"
            cli = self.run_cli(
                "agent-revise-workflow",
                str(chapter),
                "--review",
                str(review),
                "--out-dir",
                "00_总纲与管理/agent_runs/revise_026_cli",
                "--format",
                "json",
                "--review-scope",
                "style",
                "--runner",
                sys.executable,
                str(runner),
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["command"], "agent-revise-workflow")
            self.assertTrue(data["prepared"])
            self.assertTrue(data["executed"])
            self.assertEqual(data["stop_reason"], "needs_revision_attention")
            self.assertEqual(data["ready_count"], 1)
            self.assertFalse(data["ready_for_approval"])
            self.assertEqual(data["retry_count"], 1)
            output = Path(data["staged_outputs"][0]["output_file"])
            self.assertTrue(output.exists())
            self.assertIn("Echo Agent Staging Output", output.read_text(encoding="utf-8"))
            cli_run_dir = Path(data["run_dir"])
            self.assertTrue((cli_run_dir / "candidate.md").exists())
            self.assertTrue((cli_run_dir / "changes.diff").exists())
            self.assertTrue((cli_run_dir / "candidate.v1.md").exists())
            self.assertTrue((cli_run_dir / "verification.v1.json").exists())
            verification = json.loads((cli_run_dir / "verification.json").read_text(encoding="utf-8"))
            self.assertEqual(verification["status"], "needs_revision_attention")
            self.assertIn("title_preserved", verification["blocking_failures"])
            self.assertIn("不是风", chapter.read_text(encoding="utf-8"))

    def test_agent_revision_closes_verification_and_acceptance_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            management = target / "00_总纲与管理"
            chapter_dir = target / "卷一" / "第一本"
            management.mkdir()
            chapter_dir.mkdir(parents=True)
            chapter = chapter_dir / "ch_026.md"
            source = (
                "# Chapter 26\n\n"
                "不是风，也不是雪。没有声音，没有人动。\n"
                "白影像雪一样过去，剑光像针一样亮。\n"
            )
            first_candidate = (
                "# Chapter 26\n\n"
                "风雪贴着窗纸游走。他决定背弃众人，目光落在门边。\n"
                "白影掠过檐下，剑光一闪便沉进夜色。\n"
            )
            candidate = (
                "# Chapter 26\n\n"
                "风雪贴着窗纸游走。屋里静着，众人的目光都落在门边。\n"
                "白影掠过檐下，剑光一闪便沉进夜色。\n"
            )
            semantic_pass = {
                "schema": "fictionops.semantic_revision_verification.v1",
                "verdict": "pass",
                "invariants": [
                    {"name": name, "status": "pass", "evidence": "preserved"}
                    for name in (
                        "plot_events",
                        "point_of_view",
                        "chronology",
                        "character_intentions",
                        "information_boundaries",
                        "ambiguity_and_withholding",
                        "review_findings_addressed",
                    )
                ],
                "new_issues": [],
                "summary": "All required invariants are preserved.",
            }
            semantic_fail = {
                "schema": "fictionops.semantic_revision_verification.v1",
                "verdict": "fail",
                "invariants": [
                    {
                        "name": name,
                        "status": "fail" if name == "character_intentions" else "pass",
                        "evidence": "The first candidate invents a decision to betray the group." if name == "character_intentions" else "preserved",
                    }
                    for name in (
                        "plot_events",
                        "point_of_view",
                        "chronology",
                        "character_intentions",
                        "information_boundaries",
                        "ambiguity_and_withholding",
                        "review_findings_addressed",
                    )
                ],
                "new_issues": ["invented_character_intention"],
                "summary": "The candidate invents a new character intention.",
            }
            chapter.write_text(source, encoding="utf-8")
            runner = target / "valid_revision_runner.py"
            runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"semantic_pass = {semantic_pass!r}\n"
                f"semantic_fail = {semantic_fail!r}\n"
                f"first_candidate = {first_candidate!r}\n"
                f"candidate = {candidate!r}\n"
                "if 'semantic-verifier' in payload:\n"
                "    result = semantic_fail if '背弃众人' in payload else semantic_pass\n"
                "    sys.stdout.write(json.dumps(result, ensure_ascii=False))\n"
                "elif 'Targeted Retry' in payload:\n"
                "    sys.stdout.write(candidate)\n"
                "else:\n"
                "    sys.stdout.write(first_candidate)\n",
                encoding="utf-8",
            )
            run_dir = management / "agent_runs" / "revise_026"
            result = self.run_cli(
                "agent-revise-workflow",
                str(chapter),
                "--out-dir",
                str(run_dir),
                "--format",
                "json",
                "--review-scope",
                "style",
                "--runner",
                sys.executable,
                str(runner),
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["stop_reason"], "ready_for_approval")
            self.assertTrue(data["ready_for_approval"], data)
            self.assertEqual(data["retry_count"], 1)
            self.assertEqual(data["semantic_call_count"], 2)
            self.assertEqual(data["model_calls_used"], 4)
            self.assertEqual(data["max_model_calls"], 12)
            model_budget = json.loads((run_dir / "model_budget.json").read_text(encoding="utf-8"))
            self.assertEqual(model_budget["status"], "completed")
            self.assertEqual(model_budget["used_calls"], 4)
            self.assertEqual(
                [item["role"] for item in model_budget["calls"]],
                ["chapter-reviser", "semantic-verifier", "chapter-reviser-retry", "semantic-verifier"],
            )
            self.assertTrue((run_dir / "verification.v1.json").exists())
            run_issues = json.loads((run_dir / "issues.before.json").read_text(encoding="utf-8"))
            self.assertTrue(any(item["status"] == "verified" for item in run_issues["issues"]))
            self.assertTrue((target / ".fictionops" / "issues.json").exists())
            first_verification = json.loads((run_dir / "verification.v1.json").read_text(encoding="utf-8"))
            self.assertIn("semantic_invariants_preserved", first_verification["blocking_failures"])
            self.assertEqual(chapter.read_text(encoding="utf-8"), source)
            self.assertTrue((run_dir / "changes.diff").read_text(encoding="utf-8"))
            self.assertTrue((run_dir / "audits.after.json").exists())
            self.assertTrue((run_dir / "issues.after.json").exists())

            verification_resume_runner = target / "verification_resume_runner.py"
            verification_resume_runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"semantic = {semantic_pass!r}\n"
                "if 'semantic-verifier' not in payload:\n"
                "    raise SystemExit('resume unexpectedly reran chapter revision: ' + payload[:500].replace('\\n', ' '))\n"
                "print(json.dumps(semantic, ensure_ascii=False))\n",
                encoding="utf-8",
            )
            interrupted_dir = management / "agent_runs" / "resume_verification_026"
            interrupted = self.run_cli(
                "agent-revise-workflow",
                str(chapter),
                "--out-dir",
                str(interrupted_dir),
                "--format",
                "json",
                "--review-scope",
                "style",
                "--max-model-calls",
                "1",
                "--runner",
                sys.executable,
                str(runner),
                check=False,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertEqual(json.loads((interrupted_dir / "checkpoint.json").read_text(encoding="utf-8"))["phase"], "verification_ready")
            resumed = self.run_cli(
                "agent",
                "resume",
                str(interrupted_dir),
                "--max-model-calls",
                "1",
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(verification_resume_runner),
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            resumed_payload = json.loads(resumed.stdout)
            self.assertEqual(resumed_payload["resumed_from_phase"], "verification_ready")
            self.assertEqual(resumed_payload["final_phase"], "ready_for_approval")
            self.assertEqual(
                [item["role"] for item in json.loads((interrupted_dir / "model_budget.json").read_text(encoding="utf-8"))["calls"]],
                ["semantic-verifier"],
            )

            preflight = self.run_cli("agent-accept-revision", str(run_dir), "--dry-run", "--format", "json")
            preflight_data = json.loads(preflight.stdout)
            self.assertFalse(preflight_data["applied"])
            self.assertEqual(preflight_data["stop_reason"], "acceptance_preflight_passed")
            self.assertEqual(chapter.read_text(encoding="utf-8"), source)

            accepted = self.run_cli("agent-accept-revision", str(run_dir), "--format", "json")
            accepted_data = json.loads(accepted.stdout)
            self.assertTrue(accepted_data["applied"])
            self.assertEqual(accepted_data["stop_reason"], "revision_applied")
            self.assertEqual(chapter.read_text(encoding="utf-8"), candidate)
            acceptance = json.loads((run_dir / "acceptance.json").read_text(encoding="utf-8"))
            self.assertTrue(acceptance["applied"])
            session = json.loads((run_dir / "session.json").read_text(encoding="utf-8"))
            self.assertEqual(session["state"], "applied")
            project_issues = load_issue_ledger(target)
            self.assertTrue(any(item["status"] == "accepted" for item in project_issues["issues"]))
            trajectory = [json.loads(line) for line in (run_dir / "trajectory.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(all(item["schema"] == "fictionops.agent_trajectory_step.v1" for item in trajectory))
            self.assertEqual(
                len([item for item in trajectory if item["kind"] == "model_call_started"]),
                len([item for item in trajectory if item["kind"] == "model_call_finished"]),
            )
            self.assertTrue(any(item["authority"] == "author" and item["phase"] == "applied" for item in trajectory))

    def test_agent_revision_accept_refuses_stale_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_总纲与管理").mkdir()
            chapter = target / "ch_026.md"
            source = "# Chapter 26\n\n不是风。屋里没有人动，剑光像雪。\n"
            candidate = "# Chapter 26\n\n风贴着窗纸。屋里静着，剑光掠过墙面。\n"
            semantic = {
                "schema": "fictionops.semantic_revision_verification.v1",
                "verdict": "pass",
                "invariants": [
                    {"name": name, "status": "pass", "evidence": "preserved"}
                    for name in (
                        "plot_events",
                        "point_of_view",
                        "chronology",
                        "character_intentions",
                        "information_boundaries",
                        "ambiguity_and_withholding",
                        "review_findings_addressed",
                    )
                ],
                "new_issues": [],
                "summary": "All required invariants are preserved.",
            }
            chapter.write_text(source, encoding="utf-8")
            runner = target / "runner.py"
            runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"semantic = {semantic!r}\n"
                f"candidate = {candidate!r}\n"
                "sys.stdout.write(json.dumps(semantic, ensure_ascii=False) if 'semantic-verifier' in payload else candidate)\n",
                encoding="utf-8",
            )
            run_dir = target / "00_总纲与管理" / "agent_runs" / "stale"
            result = self.run_cli(
                "agent-revise-workflow",
                str(chapter),
                "--out-dir",
                str(run_dir),
                "--format",
                "json",
                "--review-scope",
                "style",
                "--runner",
                sys.executable,
                str(runner),
            )
            self.assertTrue(json.loads(result.stdout)["ready_for_approval"])
            chapter.write_text(source + "\n作者刚补的一句。\n", encoding="utf-8")
            refused = self.run_cli("agent-accept-revision", str(run_dir), "--format", "json", check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("source chapter changed", refused.stderr)
            self.assertIn("作者刚补的一句", chapter.read_text(encoding="utf-8"))

    def test_agent_revise_workflow_uses_project_aware_comprehensive_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_总纲与管理").mkdir()
            character_dir = target / "01_人物弧线"
            chapter_dir = target / "卷一" / "第一本"
            character_dir.mkdir()
            chapter_dir.mkdir(parents=True)
            chapter = chapter_dir / "第26章_冰中四人.md"
            chapter.write_text(
                "# 第26章 冰中四人\n\n"
                "耶儿并不害怕，也不是犹豫。他没有看仁孜，只觉得胸口很冷。\n"
                "他忽然抬剑，像早已想明白了一切。\n",
                encoding="utf-8",
            )
            (character_dir / "耶儿_人物弧线.md").write_text(
                "# 耶儿\n\n他会迅速行动，但此时仍不擅长辨认自己的恐惧，不应由旁白替他总结。\n",
                encoding="utf-8",
            )
            (target / "style.md").write_text(
                "# Style\n\nRepeated negation must be classified in context rather than deleted mechanically.\n",
                encoding="utf-8",
            )
            set_author_guard(
                target,
                guard_id="G-STYLE-NEGATION",
                kind="style",
                statement="保留具有场景功能的单次否定，不按词频机械删除。",
                source="style.md",
            )
            review = {
                "schema": "fictionops.comprehensive_chapter_review.v1",
                "overall_risk": "high",
                "dimensions": [
                    {
                        "name": name,
                        "status": "issues" if name in {"character", "prose_and_reader_experience"} else "pass",
                        "summary": "The narrator over-explains the character." if name == "character" else "checked",
                    }
                    for name in (
                        "continuity",
                        "character",
                        "information_boundaries",
                        "foreshadowing",
                        "chapter_function",
                        "prose_and_reader_experience",
                    )
                ],
                "issues": [
                    {
                        "category": "character",
                        "severity": "P2",
                        "confidence": 0.94,
                        "metric_keys": [],
                        "evidence": ["像早已想明白了一切"],
                        "problem": "Narration gives the character a settled self-explanation.",
                        "why_it_matters": "It skips the character's uncertainty.",
                        "preserve_constraints": ["Keep the sword raise and Renzi's presence."],
                        "suggested_action": "Replace the conclusion with bodily action and incomplete perception.",
                    }
                ],
                "revision_priorities": ["Restore character uncertainty before reducing repeated negation."],
                "summary": "One character-level issue should drive revision.",
            }
            semantic = {
                "schema": "fictionops.semantic_revision_verification.v1",
                "verdict": "pass",
                "invariants": [
                    {"name": name, "status": "pass", "evidence": "preserved"}
                    for name in (
                        "plot_events",
                        "point_of_view",
                        "chronology",
                        "character_intentions",
                        "information_boundaries",
                        "ambiguity_and_withholding",
                        "review_findings_addressed",
                    )
                ],
                "new_issues": [],
                "summary": "The review finding is addressed without changing the event.",
            }
            preservation = {
                "schema": "fictionops.preservation_verification.v1",
                "decisions": [
                    {
                        "issue_index": 0,
                        "verdict": "uphold",
                        "evidence": ["宏大宣言"],
                        "guard_ids": [],
                        "reason": "The finding is material and does not conflict with a preservation constraint.",
                    }
                ],
                "summary": "The issue should remain actionable.",
            }
            candidate = (
                "# 第26章 冰中四人\n\n"
                "耶儿避开仁孜的目光，胸口那点寒意沿着肋骨往上爬。\n"
                "剑抬起来时，他的手腕先顿了一下，随即压住了那点颤。\n"
            )
            runner = target / "comprehensive_runner.py"
            runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"review = {review!r}\n"
                f"semantic = {semantic!r}\n"
                f"preservation = {preservation!r}\n"
                f"candidate = {candidate!r}\n"
                "if 'semantic-verifier' in payload:\n"
                "    sys.stdout.write(json.dumps(semantic, ensure_ascii=False))\n"
                "elif 'Preservation Verifier Output Repair' in payload:\n"
                "    sys.stdout.write(json.dumps(preservation, ensure_ascii=False))\n"
                "elif 'preservation-verifier' in payload:\n"
                "    sys.stdout.write('{\"schema\": \"fictionops.preservation_verification.v1\", \"decisions\": [')\n"
                "elif 'Comprehensive Review Output Repair' in payload:\n"
                "    sys.stdout.write(json.dumps(review, ensure_ascii=False))\n"
                "elif 'comprehensive-reviewer' in payload:\n"
                "    sys.stdout.write('{\"schema\": \"fictionops.comprehensive_chapter_review.v1\", \"dimensions\": [')\n"
                "else:\n"
                "    sys.stdout.write(candidate)\n",
                encoding="utf-8",
            )
            run_dir = target / "00_总纲与管理" / "agent_runs" / "comprehensive_026"
            result = self.run_cli(
                "agent-revise-workflow",
                str(chapter),
                "--out-dir",
                str(run_dir),
                "--format",
                "json",
                "--max-project-context-chars",
                "160",
                "--runner",
                sys.executable,
                str(runner),
            )
            data = json.loads(result.stdout)
            self.assertTrue(data["ready_for_approval"])
            self.assertEqual(data["review_scope"], "comprehensive")
            self.assertGreater(data["context_file_count"], 0)
            self.assertGreater(data["memory_record_count"], 0)
            self.assertEqual(data["author_guard_count"], 1)
            self.assertEqual(data["comprehensive_review"]["overall_risk"], "high")
            self.assertEqual(data["preservation_call_count"], 2)
            self.assertEqual(data["preservation_verification"]["upheld_count"], 1)
            self.assertTrue((run_dir / "preservation_verification.json").exists())
            self.assertTrue((run_dir / "preservation_verifier_retry_1" / "output.md").exists())
            self.assertTrue((run_dir / "comprehensive_reviewer_retry_1" / "output.md").exists())
            reviewer_outputs = {item["kind"]: item["path"] for item in data["files"]}
            self.assertEqual(Path(reviewer_outputs["comprehensive_reviewer_output"]).parent.name, "comprehensive_reviewer")
            self.assertEqual(Path(reviewer_outputs["comprehensive_reviewer_retry_output"]).parent.name, "comprehensive_reviewer_retry_1")
            self.assertTrue((run_dir / "project_context.md").exists())
            self.assertTrue((run_dir / "memory_query.json").exists())
            self.assertTrue((run_dir / "memory_context.md").exists())
            self.assertIn("耶儿_人物弧线.md", (run_dir / "project_context.md").read_text(encoding="utf-8"))
            self.assertIn("style.md", (run_dir / "project_context.md").read_text(encoding="utf-8"))
            self.assertIn("G-STYLE-NEGATION", (run_dir / "project_context.md").read_text(encoding="utf-8"))
            ledger = json.loads((run_dir / "issues.before.json").read_text(encoding="utf-8"))
            self.assertTrue(any(item["category"] == "semantic.character" for item in ledger["issues"]))
            self.assertIn("review_findings_addressed", [item["name"] for item in data["verification"]["semantic_verification"]["invariants"]])
            trajectory = [json.loads(line) for line in (run_dir / "trajectory.jsonl").read_text(encoding="utf-8").splitlines()]
            context_steps = [item for item in trajectory if item["kind"] == "context_selected"]
            self.assertEqual(len(context_steps), 1)
            self.assertTrue(any(item.get("source") and item.get("reason") for item in context_steps[0]["context"]))
            reviewer_context = (run_dir / "comprehensive_reviewer" / "context_pack.md").read_text(encoding="utf-8")
            self.assertIn("## Static Prose Issue Ledger", reviewer_context)
            self.assertIn("prose.exclusionary_narration", reviewer_context)
            preservation_context = (run_dir / "preservation_verifier" / "context_pack.md").read_text(encoding="utf-8")
            self.assertIn("G-STYLE-NEGATION", preservation_context)
            verifier_context = (run_dir / "semantic_verifier" / "context_pack.md").read_text(encoding="utf-8")
            self.assertIn("### Comprehensive Review", verifier_context)
            self.assertIn("### Static Issue Ledger", verifier_context)

            resume_runner = target / "resume_revision_runner.py"
            resume_runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"review = {review!r}\n"
                f"candidate = {candidate!r}\n"
                "if 'comprehensive-reviewer' in payload:\n"
                "    sys.stdout.write(json.dumps(review, ensure_ascii=False))\n"
                "else:\n"
                "    sys.stdout.write(candidate)\n",
                encoding="utf-8",
            )
            resume_only_runner = target / "resume_only_revision_runner.py"
            resume_only_runner.write_text(
                "import sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"candidate = {candidate!r}\n"
                "if 'comprehensive-reviewer' in payload:\n"
                "    raise SystemExit('resume unexpectedly reran comprehensive review')\n"
                "sys.stdout.write(candidate)\n",
                encoding="utf-8",
            )
            resumable_dir = target / "agent_runs" / "resume_comprehensive_026"
            interrupted = self.run_cli(
                "agent-revise-workflow",
                str(chapter),
                "--out-dir",
                str(resumable_dir),
                "--format",
                "json",
                "--no-semantic-verify",
                "--no-preservation-verify",
                "--max-model-calls",
                "1",
                "--runner",
                sys.executable,
                str(resume_runner),
                check=False,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            checkpoint = json.loads((resumable_dir / "checkpoint.json").read_text(encoding="utf-8"))
            self.assertEqual(checkpoint["phase"], "review_ready")
            resumed = self.run_cli(
                "agent",
                "resume",
                str(resumable_dir),
                "--max-model-calls",
                "1",
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(resume_only_runner),
            )
            resumed_payload = json.loads(resumed.stdout)
            self.assertEqual(resumed_payload["resumed_from_phase"], "review_ready")
            self.assertEqual(resumed_payload["final_phase"], "ready_for_approval")
            self.assertTrue(resumed_payload["ready_for_approval"])
            self.assertEqual(resumed_payload["model_calls_used"], 1)
            self.assertEqual(resumed_payload["cumulative_model_calls"], 2)
            resumed_budget = json.loads((resumable_dir / "model_budget.json").read_text(encoding="utf-8"))
            self.assertEqual([item["role"] for item in resumed_budget["calls"]], ["chapter-reviser"])

    def test_agent_write_workflow_drafts_rewrites_and_accepts_new_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_总纲与管理").mkdir()
            chapter_dir = target / "卷一" / "第三本"
            character_dir = target / "01_人物弧线"
            chapter_dir.mkdir(parents=True)
            character_dir.mkdir()
            chapter = chapter_dir / "第01章_新章.md"
            engine = chapter_dir / "第01章_章节发动机.md"
            outline = chapter_dir / "第三本_大纲.md"
            engine.write_text(
                "# 章节发动机\n\n"
                "- 标题：新章\n"
                "- 视角人物：殷允\n"
                "- 建议体量：100\n\n"
                "| Pressure 压力 | Desire 欲望 | Obstacle 阻碍 | Change 变化 | Remainder 余味 |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| 商会将散 | 记下无席者姓名 | 众人互不信任 | 她留下第一册名录 | 空席仍在增加 |\n\n"
                "- 哪些话不说完：她不谈弟弟。\n",
                encoding="utf-8",
            )
            outline.write_text("# 第三本大纲\n\n殷允从被救助者走向记录者，本章只迈出留下名录的一步。\n", encoding="utf-8")
            (character_dir / "殷允_人物弧线.md").write_text("# 殷允\n\n她先记具体姓名，不发表宏大宣言。\n", encoding="utf-8")
            first_candidate = (
                "# 第01章 新章\n\n"
                "殷允站起来发表了一番宏大宣言，众人同声答应。她当场建立了完整名册制度。\n"
            )
            final_candidate = (
                "# 第01章 新章\n\n"
                "殷允把纸压在膝上，先问了离她最近那人的姓名。那人迟疑许久，只报了一个乳名。\n"
                "她照样写下。身后仍有人争吵，纸上却终于多出第一行。\n"
            )
            dimension_names = (
                "chapter_engine",
                "scene_progression",
                "character_voice",
                "information_boundaries",
                "continuity",
                "foreshadowing",
                "prose_freshness",
                "ending_change",
            )
            chapter_plan = {
                "schema": "fictionops.chapter_execution_plan.v1",
                "status": "ready",
                "title": "新章",
                "viewpoint": "殷允",
                "kind": "情绪承重",
                "target_chars": 100,
                "engine": {
                    "pressure": "商会将散",
                    "desire": "记下无席者姓名",
                    "obstacle": "众人互不信任",
                    "change": "她留下第一册名录",
                    "remainder": "空席仍在增加",
                },
                "scenes": [
                    {
                        "scene_id": "S1",
                        "order": 1,
                        "viewpoint": "殷允",
                        "function": "concrete first action",
                        "goal": "ask one name",
                        "conflict": "the person hesitates",
                        "information_boundary": "do not discuss her brother",
                        "entry_state": {"facts": ["the ledger is empty"], "knowledge": [], "objects": ["blank paper"], "residue": []},
                        "exit_state": {"facts": ["the first line exists"], "knowledge": [], "objects": ["ledger"], "residue": ["more names remain"]},
                        "exit": "the first line exists",
                    }
                ],
                "preserve_constraints": ["No grand declaration."],
                "forbidden_reveals": ["Do not discuss her brother."],
                "foreshadowing": ["The first ledger can later become a network."],
                "missing_context": [],
                "summary": "Begin with one concrete name rather than an institution.",
            }
            causal_simulation = {
                "schema": "fictionops.causal_simulation.v1",
                "status": "ready",
                "stakeholders": [
                    {"id": "殷允", "knows": ["one person vanished"], "wants": ["record one name"], "fears": ["public attention"], "leverage": ["paper"], "constraints": ["low trust"], "likely_error": "generalize too early"}
                ],
                "event_graph": [
                    {"id": "E1", "preconditions": ["blank ledger"], "action": "ask one name", "immediate_effects": ["one line exists"], "cost_transfer": ["the speaker risks recognition"], "observable_evidence": ["written name"], "unresolved": ["more names remain"]}
                ],
                "hard_constraints": {
                    "pov_whitelist": ["殷允"],
                    "forbidden_pov": [],
                    "knowledge_limits": ["Do not discuss her brother."],
                    "theme_questions": ["What can one recorded name preserve?"],
                    "forbidden_conclusions": [],
                    "special_passage_limits": [],
                    "quantitative_rules": [],
                    "unit_conversions": {},
                },
                "missing_mechanics": [],
                "summary": "One risky name creates the first durable state change.",
            }
            adversarial_fail = {
                "schema": "fictionops.adversarial_draft_review.v1",
                "verdict": "fail",
                "profiles": [
                    {"name": name, "status": "issues" if name == "character_and_knowledge" else "pass", "summary": "grand declaration" if name == "character_and_knowledge" else "checked"}
                    for name in ("continuity", "character_and_knowledge", "prose_and_reader_experience")
                ],
                "constraint_checks": [
                    {"id": "P1", "status": "fail", "evidence": "Candidate explicitly gives a grand public declaration."},
                    {"id": "F1", "status": "pass", "evidence": "Her brother is not discussed."},
                    {"id": "K1", "status": "pass", "evidence": "Her brother is not discussed."},
                ],
                "scene_state_checks": [{"scene_id": "S1", "status": "fail", "evidence": "A complete institution replaces the first-line exit state."}],
                "issues": [{"category": "character_and_knowledge", "severity": "P2", "evidence": ["宏大宣言"], "problem": "The state change is too large.", "suggested_action": "Return to one name.", "constraint_ids": ["P1"]}],
                "summary": "The draft violates the concrete scale.",
            }
            adversarial_pass = {
                "schema": "fictionops.adversarial_draft_review.v1",
                "verdict": "pass",
                "profiles": [
                    {"name": name, "status": "pass", "summary": "checked"}
                    for name in ("continuity", "character_and_knowledge", "prose_and_reader_experience")
                ],
                "constraint_checks": [
                    {"id": "P1", "status": "pass", "evidence": "The candidate begins with one name."},
                    {"id": "F1", "status": "pass", "evidence": "Her brother is not discussed."},
                    {"id": "K1", "status": "pass", "evidence": "Her brother is not discussed."},
                ],
                "scene_state_checks": [{"scene_id": "S1", "status": "pass", "evidence": "The first ledger line exists and more names remain."}],
                "issues": [],
                "summary": "No material counterexample remains.",
            }
            evaluation_fail = {
                "schema": "fictionops.draft_evaluation.v1",
                "verdict": "pass",
                "dimensions": [{"name": name, "status": "pass", "evidence": "broad dimension passed"} for name in dimension_names],
                "constraint_checks": [
                    {"id": "P1", "status": "fail", "evidence": "Candidate explicitly gives a grand public declaration."},
                    {"id": "F1", "status": "pass", "evidence": "Her brother is not discussed."},
                ],
                "issues": [{"category": "character_voice", "severity": "P2", "problem": "Grand declaration replaces concrete naming.", "evidence": ["宏大宣言"], "suggested_action": "Begin with one name.", "preserve_constraints": ["Keep the first ledger entry."]}],
                "retrospective": {},
                "canon_sync_suggestions": [],
                "summary": "Rewrite from concrete action.",
            }
            evaluation_pass = {
                "schema": "fictionops.draft_evaluation.v1",
                "verdict": "pass",
                "dimensions": [{"name": name, "status": "pass", "evidence": "fulfilled"} for name in dimension_names],
                "constraint_checks": [
                    {"id": "P1", "status": "pass", "evidence": "The candidate begins with one person's name, not a declaration."},
                    {"id": "F1", "status": "pass", "evidence": "Her brother is not discussed."},
                ],
                "issues": [],
                "retrospective": {
                    "chapter_change": "殷允留下第一行名录。",
                    "residue": "更多空席仍等待被记下。",
                    "character_updates": ["殷允开始以具体姓名抵抗消失。"],
                    "information_updates": [],
                    "foreshadowing_updates": ["第一册名录成为后续网络的起点。"],
                },
                "canon_sync_suggestions": [{"area": "character", "suggestion": "记录殷允第一次主动记名。", "evidence": "名录第一行"}],
                "summary": "The candidate fulfills the engine at the intended scale.",
            }
            runner = target / "write_runner.py"
            runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"first_candidate = {first_candidate!r}\n"
                f"final_candidate = {final_candidate!r}\n"
                f"evaluation_fail = {evaluation_fail!r}\n"
                f"evaluation_pass = {evaluation_pass!r}\n"
                f"chapter_plan = {chapter_plan!r}\n"
                f"causal_simulation = {causal_simulation!r}\n"
                f"adversarial_fail = {adversarial_fail!r}\n"
                f"adversarial_pass = {adversarial_pass!r}\n"
                "if 'causal-simulator' in payload:\n"
                "    sys.stdout.write(json.dumps(causal_simulation, ensure_ascii=False))\n"
                "elif 'chapter-planner' in payload:\n"
                "    sys.stdout.write(json.dumps(chapter_plan, ensure_ascii=False))\n"
                "elif 'adversarial-reviewer' in payload:\n"
                "    result = adversarial_fail if '完整名册制度' in payload else adversarial_pass\n"
                "    sys.stdout.write(json.dumps(result, ensure_ascii=False) if 'JSON Contract Repair' in payload else '{invalid')\n"
                "elif 'draft-evaluator' in payload:\n"
                "    result = evaluation_fail if '完整名册制度' in payload else evaluation_pass\n"
                "    sys.stdout.write(json.dumps(result, ensure_ascii=False) if 'JSON Contract Repair' in payload else '{invalid')\n"
                "elif 'Targeted Rewrite' in payload:\n"
                "    sys.stdout.write(final_candidate)\n"
                "else:\n"
                "    sys.stdout.write(first_candidate)\n",
                encoding="utf-8",
            )
            run_dir = target / "00_总纲与管理" / "agent_runs" / "write_new_chapter"
            result = self.run_cli(
                "agent-write-workflow",
                str(chapter),
                "--engine",
                str(engine),
                "--outline",
                str(outline),
                "--out-dir",
                str(run_dir),
                "--min-chars",
                "20",
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
            )
            data = json.loads(result.stdout)
            self.assertTrue(data["ready_for_approval"], data)
            self.assertFalse(data["source_existed"])
            self.assertEqual(data["retry_count"], 1)
            self.assertEqual(data["evaluator_call_count"], 4)
            self.assertEqual(data["planner_call_count"], 1)
            self.assertEqual(data["causal_simulator_call_count"], 1)
            self.assertEqual(data["adversarial_reviewer_call_count"], 4)
            self.assertGreater(data["memory_record_count"], 0)
            self.assertEqual(data["chapter_plan"]["status"], "ready")
            first_verification = json.loads((run_dir / "verification.v1.json").read_text(encoding="utf-8"))
            self.assertIn("draft_plan_constraints", first_verification["blocking_failures"])
            self.assertFalse(chapter.exists())
            self.assertIn("殷允_人物弧线.md", (run_dir / "project_context.md").read_text(encoding="utf-8"))
            self.assertTrue((run_dir / "retrospective.draft.md").exists())
            self.assertTrue((run_dir / "canon_sync_suggestions.json").exists())
            trajectory = [json.loads(line) for line in (run_dir / "trajectory.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(any(item["kind"] == "context_selected" and item["context"] for item in trajectory))
            model_steps = [item for item in trajectory if item["kind"].startswith("model_call_")]
            self.assertEqual(len(model_steps), data["model_calls_used"] * 2)
            self.assertTrue(any(item.get("state_transition") for item in trajectory))

            preflight = self.run_cli("agent-accept-revision", str(run_dir), "--dry-run", "--format", "json")
            self.assertEqual(json.loads(preflight.stdout)["stop_reason"], "acceptance_preflight_passed")
            chapter.write_text("# 并发创建的新稿\n", encoding="utf-8")
            refused = self.run_cli("agent-accept-revision", str(run_dir), "--format", "json", check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("target chapter was created", refused.stderr)
            chapter.unlink()
            accepted = self.run_cli("agent-accept-revision", str(run_dir), "--format", "json")
            accepted_payload = json.loads(accepted.stdout)
            self.assertTrue(accepted_payload["applied"])
            self.assertTrue(accepted_payload["learning_recorded"])
            self.assertEqual(chapter.read_text(encoding="utf-8"), final_candidate)

    def test_agent_write_title_falls_back_to_engine_heading_before_filename(self) -> None:
        engine = "# 第五章《开仓雨》章节发动机\n"
        self.assertEqual(expected_title_from_engine(engine, Path("ch_05_target.md")), "开仓雨")
        self.assertEqual(sum(scene_target_chars({"scenes": [{"target_chars": 6000}, {"target_chars": 3000}]}, 8200)), 8200)

    def test_agent_memory_build_query_and_explicit_preference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_management").mkdir()
            characters = target / "01_characters"
            characters.mkdir()
            (characters / "luyu.md").write_text(
                "# 鹿煜\n\n鹿煜先从具体饥饿与物件理解百姓，不提前形成成熟理论。\n",
                encoding="utf-8",
            )
            (characters / "legacy_utf16.md").write_text("# 旧人物资料\n\n旧文件仍应进入记忆索引。\n", encoding="utf-16")
            archived = target / "归档_旧稿"
            archived.mkdir()
            (archived / "obsolete.md").write_text("# 旧版\n\n鹿煜已经形成成熟理论。\n", encoding="utf-8")
            (target / "00_management" / "Codex接手日志.md").write_text("# 接手日志\n\n这不是正史或书纲。\n", encoding="utf-8")
            built = self.run_cli("agent-memory", "build", str(target), "--format", "json")
            built_payload = json.loads(built.stdout)
            self.assertGreater(built_payload["record_count"], 1)
            index_payload = json.loads((target / ".fictionops" / "memory" / "index.json").read_text(encoding="utf-8"))
            indexed_sources = {item["source"] for item in index_payload["records"]}
            self.assertFalse(any("归档_旧稿" in source for source in indexed_sources))
            self.assertFalse(any("接手日志" in source for source in indexed_sources))
            added = self.run_cli(
                "agent-memory",
                "add-preference",
                str(target),
                "--rule",
                "旁白不要替人物完成成熟理论",
                "--prefer",
                "让具体物件承担认识变化",
                "--avoid",
                "人物直接总结主题",
                "--scope",
                "character_growth",
                "--evidence",
                "作者确认的《开仓雨》比较",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(added.stdout)["authority"], "author_explicit")
            queried = self.run_cli(
                "agent-memory",
                "query",
                str(target),
                "--query",
                "鹿煜如何通过具体物件理解百姓",
                "--format",
                "json",
            )
            query_payload = json.loads(queried.stdout)
            self.assertTrue(any(item["kind"] == "preference" for item in query_payload["results"]))
            self.assertTrue(any("luyu.md" in item["source"] for item in query_payload["results"]))
            status = json.loads(self.run_cli("agent-memory", "status", str(target), "--format", "json").stdout)
            self.assertEqual(status["preference_count"], 1)
            self.assertFalse(status["stale"])

    def test_deterministic_story_audit_catches_dogfood_failure_shapes(self) -> None:
        contract = {
            "constraints": [{"id": "C1", "kind": "forbidden_conclusion", "text": "百姓不是一个整齐的称呼"}],
            "forbidden_pov": ["承曦"],
            "theme_questions": ["百姓是一个整齐称呼还是具体饥饿的集合？"],
            "special_passage_limits": [{"label": "奏疏", "marker": "臣", "max_chars": 30}],
        }
        candidate = (
            "# 第五章 开仓雨\n\n"
            "百姓不是一个整齐的称呼。\n\n"
            "承曦坐在御书房里，想起粟阳。他拿起笔，决定写下一行字。\n\n"
            "承曦点了点头，觉得此事还不着急。\n\n"
            "“臣谨奏：粟阳雨雪压仓，百姓饥馑，臣先开仓，再请朝廷治臣抗命之罪，伏惟圣鉴。”\n"
        )
        audit = deterministic_story_audit(candidate, contract)
        self.assertEqual(audit["status"], "fail")
        self.assertGreaterEqual(len(audit["blocking_failures"]), 4)

    def test_causal_contract_rejects_disguised_forbidden_viewpoint_and_theme_answer(self) -> None:
        causal = {
            "hard_constraints": {
                "pov_whitelist": ["辛照渠", "鹿煜"],
                "forbidden_pov": ["承曦"],
                "theme_questions": ["百姓是一个整齐称呼还是具体饥饿的集合？"],
                "forbidden_conclusions": ["不能判定承曦的诏令邪恶"],
            }
        }
        plan = {
            "preserve_constraints": ["不能判定承曦的诏令邪恶"],
            "scenes": [
                {
                    "scene_id": "S5",
                    "viewpoint": "鹿煜",
                    "entry_state": {},
                    "exit_state": {"knowledge": ["鹿煜知道百姓不是一个整齐称呼"]},
                },
                {
                    "scene_id": "S6",
                    "viewpoint": "第三人称有限（不进入承曦内心）",
                    "entry_state": {},
                    "exit_state": {},
                },
            ]
        }
        issues = validate_plan_against_causal(plan, causal)
        kinds = {item["kind"] for item in issues}
        self.assertIn("viewpoint_not_whitelisted", kinds)
        self.assertIn("forbidden_viewpoint", kinds)
        self.assertIn("theme_question_answered_in_plan", kinds)
        self.assertNotIn("forbidden_conclusion_in_plan", kinds)
        sanitized = sanitize_theme_answers(
            "鹿煜从具体物证理解‘百姓’不是一个整齐的称呼。",
            causal,
        )
        self.assertNotIn("不是一个整齐", sanitized)
        self.assertIn("THEME QUESTION", sanitized)

    def test_story_fact_ledger_rejects_bad_arithmetic_and_object_handoff(self) -> None:
        causal = {
            "hard_constraints": {
                "quantitative_rules": [
                    {
                        "id": "Q1",
                        "description": "Two thousand people receive three sheng each.",
                        "operation": "multiply",
                        "operands": [2000, 3],
                        "expected_value": 5000,
                        "expected_unit": "sheng",
                    }
                ],
                "timeline_rules": [
                    {"id": "T1", "description": "message travel", "start": "sent", "end": "received", "min_elapsed": 3, "max_elapsed": 7, "unit": "day"}
                ],
                "object_state_rules": [
                    {"id": "O1", "object": "key", "initial_state": "clerk", "transitions": [{"scene_id": "S1", "from": "clerk", "to": "Yin Yun"}], "forbidden_states": []}
                ],
                "unit_conversions": {},
            }
        }
        plan = {
            "fact_assertions": {"timeline": [{"rule_id": "T1", "elapsed": 9, "unit": "day"}]},
            "scenes": [
                {
                    "scene_id": "S1",
                    "entry_state": {"objects": [{"name": "key", "holder": "clerk"}]},
                    "exit_state": {"objects": [{"name": "key", "holder": "Yin Yun"}]},
                },
                {
                    "scene_id": "S2",
                    "entry_state": {"objects": [{"name": "key", "holder": "clerk"}]},
                    "exit_state": {"objects": [{"name": "key", "holder": "clerk"}]},
                },
            ]
        }
        ledger = build_story_fact_ledger(causal, plan)
        kinds = {item["kind"] for item in ledger["issues"]}
        self.assertEqual(ledger["status"], "fail")
        self.assertIn("quantitative_rule_mismatch", kinds)
        self.assertIn("timeline_assertion_out_of_range", kinds)
        self.assertIn("object_handoff_mismatch", kinds)

    def test_scene_targets_and_model_contract_normalization_are_deterministic(self) -> None:
        explicit_plan = {
            "scenes": [
                {"target_chars": 1800},
                {"target_chars": 2100},
                {"target_chars": 1900},
                {"target_chars": 1800},
            ]
        }
        explicit_targets = scene_target_chars(explicit_plan, 8200)
        self.assertEqual(sum(explicit_targets), 8200)
        self.assertGreater(explicit_targets[1], explicit_targets[0])
        weighted_targets = scene_target_chars(
            {"scenes": [{"weight": 1}, {"weight": 3}, {"weight": 2}]},
            8200,
        )
        self.assertEqual(sum(weighted_targets), 8200)
        self.assertGreater(weighted_targets[1], weighted_targets[2])
        self.assertGreater(weighted_targets[2], weighted_targets[0])

        causal = {
            "schema": "fictionops.causal_simulation.v1",
            "status": "ready",
            "stakeholders": [],
            "event_graph": [{"id": "E1"}],
            "hard_constraints": {
                "pov_whitelist": [],
                "forbidden_pov": [],
                "knowledge_limits": [],
                "theme_questions": [],
                "forbidden_conclusions": ["不替读者总结本章主题", "仁孜已经懂得完整规则"],
                "special_passage_limits": [{"label": "speech", "marker": "说", "max_chars": 0}],
                "quantitative_rules": [
                    {
                        "id": "Q1",
                        "description": "章节目标体量 8200 字符",
                        "operation": "add",
                        "operands": [8000, 200],
                        "expected_value": 8200,
                        "expected_unit": "characters",
                    }
                ],
                "unit_conversions": [],
                "timeline_rules": [],
                "object_state_rules": [],
            },
            "missing_mechanics": [],
            "summary": "ready",
        }
        normalized = parse_causal_simulation(json.dumps(causal, ensure_ascii=False))
        hard = normalized["hard_constraints"]
        self.assertEqual(hard["unit_conversions"], {})
        self.assertEqual(hard["quantitative_rules"], [])
        self.assertEqual(hard["special_passage_limits"], [])
        self.assertEqual(hard["forbidden_conclusions"], ["仁孜已经懂得完整规则"])
        self.assertIn("不替读者总结本章主题", hard["knowledge_limits"])

        candidate = "仁孜的手停在裹布上方，没有落下。"
        grounded = {
            "issues": [
                {"evidence": ["手停在裹布上方"], "problem": "动作重复"},
            ]
        }
        hallucinated = {
            "issues": [
                {"evidence": ["仁孜已经明白自己守住了秩序"], "problem": "主题代答"},
            ]
        }
        self.assertEqual(review_evidence_grounding_issues(grounded, candidate), [])
        self.assertEqual(
            review_evidence_grounding_issues(hallucinated, candidate)[0]["kind"],
            "ungrounded_review_issue",
        )

    def test_agent_write_workflow_can_draft_and_assemble_scenes_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_management").mkdir()
            chapter_dir = target / "book_01"
            chapter_dir.mkdir()
            chapter = chapter_dir / "ch_01_rain.md"
            engine = chapter_dir / "ch_01_engine.md"
            engine.write_text(
                "# Chapter Engine\n\n- Title: Rain Ledger\n- target chars: 40\n",
                encoding="utf-8",
            )
            dimensions = [
                "chapter_engine", "scene_progression", "character_voice", "information_boundaries",
                "continuity", "foreshadowing", "prose_freshness", "ending_change",
            ]
            causal = {
                "schema": "fictionops.causal_simulation.v1",
                "status": "ready",
                "stakeholders": [],
                "event_graph": [
                    {"id": "E1", "preconditions": [], "action": "open ledger", "immediate_effects": [], "cost_transfer": [], "observable_evidence": [], "unresolved": []},
                    {"id": "E2", "preconditions": ["E1"], "action": "write first name", "immediate_effects": [], "cost_transfer": [], "observable_evidence": [], "unresolved": []},
                ],
                "hard_constraints": {
                    "pov_whitelist": ["Yin Yun"], "forbidden_pov": [], "knowledge_limits": [],
                    "theme_questions": [], "forbidden_conclusions": [], "special_passage_limits": [],
                    "quantitative_rules": [], "unit_conversions": {}, "timeline_rules": [],
                    "object_state_rules": [
                        {"id": "O1", "object": "ledger", "initial_code": "CLOSED", "initial_state": "closed", "transitions": [{"transition_id": "O1T1", "order": 1, "event_id": "E1", "from_code": "CLOSED", "to_code": "OPEN", "from": "closed", "to": "open"}, {"transition_id": "O1T2", "order": 2, "event_id": "E2", "from_code": "OPEN", "to_code": "MARKED", "from": "open", "to": "first line written"}], "forbidden_states": []}
                    ],
                },
                "missing_mechanics": [], "summary": "ready",
            }
            causal_invalid = json.loads(json.dumps(causal))
            causal_invalid["hard_constraints"]["unit_conversions"] = []
            causal_invalid["hard_constraints"]["timeline_rules"] = [
                {"id": "T1", "description": "unsupported duration", "start": "sent", "end": "received", "min_elapsed": 0, "max_elapsed": 0, "unit": "day"}
            ]
            plan = {
                "schema": "fictionops.chapter_execution_plan.v1",
                "status": "ready", "title": "Rain Ledger", "viewpoint": "Yin Yun", "kind": "bridge", "target_chars": 40,
                "engine": {"pressure": "rain", "desire": "record", "obstacle": "distrust", "change": "two names", "remainder": "more remain"},
                "scenes": [
                    {"scene_id": "S1", "event_ids": ["E1", "E2"], "order": 1, "viewpoint": "Yin Yun", "weight": 1, "function": "ask", "goal": "first name", "conflict": "silence", "information_boundary": "local", "entry_state": {"facts": [], "knowledge": [], "objects": [{"name": "ledger", "code": "CLOSED", "state": "closed on her knee"}], "residue": []}, "exit_state": {"facts": ["first name"], "knowledge": [], "objects": [{"name": "ledger", "code": "WRONG", "state": "open with one line"}], "residue": []}, "exit": "ink dries"},
                    {"scene_id": "S2", "event_ids": [], "order": 2, "viewpoint": "Yin Yun", "weight": 1, "function": "continue", "goal": "second name", "conflict": "rain", "information_boundary": "local", "entry_state": {"facts": ["first name"], "knowledge": [], "objects": [{"name": "ledger", "code": "MARKED", "state": "open under rain"}], "residue": []}, "exit_state": {"facts": ["second name"], "knowledge": [], "objects": [{"name": "ledger", "code": "MARKED", "state": "still open"}], "residue": ["more remain"]}, "exit": "page stays open"},
                ],
                "fact_assertions": {"timeline": [], "object_transitions": [{"rule_id": "O1", "transition_id": "O1T1", "event_id": "E1", "scene_id": "S1", "from_code": "CLOSED", "to_code": "OPEN"}, {"rule_id": "O1", "transition_id": "O1T2", "event_id": "E2", "scene_id": "S1", "from_code": "OPEN", "to_code": "MARKED"}]},
                "preserve_constraints": [], "forbidden_reveals": [], "foreshadowing": [], "missing_context": [], "summary": "two uneven contacts",
            }
            evaluation = {
                "schema": "fictionops.draft_evaluation.v1", "verdict": "pass",
                "dimensions": [{"name": name, "status": "pass", "evidence": "fulfilled"} for name in dimensions],
                "constraint_checks": [], "issues": [], "retrospective": {}, "canon_sync_suggestions": [], "summary": "pass",
            }
            evaluation_fail = json.loads(json.dumps(evaluation))
            evaluation_fail["verdict"] = "fail"
            evaluation_fail["dimensions"][2] = {"name": "character_voice", "status": "fail", "evidence": "LEAK is explanatory"}
            evaluation_fail["issues"] = [{"category": "character_voice", "severity": "P2", "problem": "Remove LEAK", "evidence": ["LEAK"], "suggested_action": "Keep action only", "preserve_constraints": []}]
            evaluation_fail["summary"] = "rewrite scenes"
            runner = target / "runner.py"
            runner.write_text(
                "import json, sys\nfrom pathlib import Path\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"causal = {causal!r}\n"
                f"causal_invalid = {causal_invalid!r}\n"
                f"plan = {plan!r}\n"
                f"evaluation = {evaluation!r}\n"
                f"evaluation_fail = {evaluation_fail!r}\n"
                "if 'causal-simulator' in payload:\n"
                "    print(json.dumps(causal if 'Causal Contract Repair' in payload else causal_invalid))\n"
                "elif 'chapter-planner' in payload:\n"
                "    print(json.dumps(plan))\n"
                "elif 'draft-evaluator' in payload:\n"
                "    print(json.dumps(evaluation_fail if 'LEAK' in payload else evaluation))\n"
                "elif Path.cwd().name == 'S1':\n"
                "    print('Rain pressed the paper flat while Yin Yun waited for the first name. Ink entered the empty line.' if 'scene-rewriter' in payload else 'Rain pressed the paper flat. LEAK explained the first name before ink entered the line.')\n"
                "elif Path.cwd().name == 'S2':\n"
                "    print('The second voice came after the eaves overflowed. She left the page open for those still silent.')\n"
                "else:\n"
                "    raise SystemExit(2)\n",
                encoding="utf-8",
            )
            run_dir = target / "00_management" / "agent_runs" / "scene_write"
            result = self.run_cli(
                "agent-write-workflow", str(chapter), "--engine", str(engine), "--out-dir", str(run_dir),
                "--min-chars", "20", "--max-retries", "1", "--no-memory", "--no-adversarial-review",
                "--scene-by-scene", "--format", "json", "--runner", sys.executable, str(runner),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(data["ready_for_approval"], data)
            self.assertTrue(data["scene_by_scene"])
            self.assertEqual(data["scene_writer_call_count"], 9)
            self.assertEqual(data["causal_simulator_call_count"], 2)
            self.assertEqual(data["retry_count"], 1)
            self.assertTrue(data["chapter_plan"]["normalizations"])
            candidate = (run_dir / "candidate.md").read_text(encoding="utf-8")
            self.assertIn("# Rain Ledger", candidate)
            self.assertLess(candidate.index("first name"), candidate.index("second voice"))
            self.assertNotIn("LEAK", candidate)
            execution = json.loads((run_dir / "scene_execution.json").read_text(encoding="utf-8"))
            self.assertEqual([item["scene_id"] for item in execution["scenes"]], ["S1", "S2"])
            self.assertTrue((run_dir / "scene_execution.retry1.json").exists())
            retry_execution = json.loads((run_dir / "scene_execution.retry1.json").read_text(encoding="utf-8"))
            self.assertEqual(retry_execution["selected_scene_ids"], ["S1"])
            self.assertTrue(next(item for item in retry_execution["scenes"] if item["scene_id"] == "S1")["rewritten"])
            self.assertFalse(next(item for item in retry_execution["scenes"] if item["scene_id"] == "S2")["rewritten"])

    def test_agent_write_workflow_stops_on_observed_token_budget_and_resumes_with_cumulative_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_management").mkdir()
            chapter_dir = target / "book_01"
            chapter_dir.mkdir()
            chapter = chapter_dir / "ch_01_budget.md"
            engine = chapter_dir / "ch_01_engine.md"
            engine.write_text("# Budget Chapter\n\n- target chars: 200\n", encoding="utf-8")
            plan = {
                "schema": "fictionops.chapter_execution_plan.v1",
                "status": "ready",
                "title": "Budget Chapter",
                "viewpoint": "Yin Yun",
                "kind": "bridge",
                "target_chars": 200,
                "engine": {"pressure": "rain", "desire": "record", "obstacle": "silence", "change": "one name", "remainder": "more remain"},
                "scenes": [
                    {
                        "scene_id": "S1",
                        "order": 1,
                        "viewpoint": "Yin Yun",
                        "weight": 1,
                        "function": "record",
                        "goal": "one name",
                        "conflict": "silence",
                        "information_boundary": "local",
                        "entry_state": {},
                        "exit_state": {},
                        "exit": "ink dries",
                    }
                ],
                "preserve_constraints": [],
                "forbidden_reveals": [],
                "foreshadowing": [],
                "missing_context": [],
                "summary": "ready",
            }
            runner = target / "budget_runner.py"
            runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"plan = {plan!r}\n"
                "if 'chapter-planner' not in payload:\n"
                "    raise SystemExit('unexpected second model call')\n"
                "receipt = {'schema': 'fictionops.runner_receipt.v1', 'provider': 'test', 'model': 'planner', 'request_id': 'req-plan', 'usage': {'input_tokens': 100, 'output_tokens': 20, 'total_tokens': 120}, 'cost': {'currency': 'USD', 'total': 0.001}}\n"
                "print('FICTIONOPS_RUNNER_RECEIPT:' + json.dumps(receipt), file=sys.stderr)\n"
                "print(json.dumps(plan))\n",
                encoding="utf-8",
            )
            run_dir = target / "00_management" / "agent_runs" / "budget_stop"
            result = self.run_cli(
                "agent-write-workflow",
                str(chapter),
                "--engine",
                str(engine),
                "--out-dir",
                str(run_dir),
                "--no-memory",
                "--no-causal-simulation",
                "--no-adversarial-review",
                "--max-model-calls",
                "5",
                "--max-total-tokens",
                "100",
                "--runner",
                sys.executable,
                str(runner),
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("model_token_budget_exhausted", result.stderr)
            budget = json.loads((run_dir / "model_budget.json").read_text(encoding="utf-8"))
            self.assertEqual(budget["status"], "exhausted")
            self.assertEqual(budget["used_calls"], 1)
            self.assertEqual(budget["attempted_role"], "draft-writer")
            self.assertEqual(budget["calls"][0]["role"], "chapter-planner")
            self.assertEqual(budget["segment_usage"]["total_tokens"], 120)
            self.assertEqual(budget["segment_cost_by_currency"]["USD"], 0.001)
            self.assertEqual(json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))["phase"], "plan_ready")
            self.assertFalse(chapter.exists())

            dimensions = [
                "chapter_engine",
                "scene_progression",
                "character_voice",
                "information_boundaries",
                "continuity",
                "foreshadowing",
                "prose_freshness",
                "ending_change",
            ]
            evaluation = {
                "schema": "fictionops.draft_evaluation.v1",
                "verdict": "pass",
                "dimensions": [{"name": name, "status": "pass", "evidence": "fulfilled"} for name in dimensions],
                "constraint_checks": [],
                "issues": [],
                "retrospective": {"chapter_change": "one name entered", "residue": "more remain", "character_updates": [], "information_updates": [], "foreshadowing_updates": []},
                "canon_sync_suggestions": [],
                "summary": "pass",
            }
            candidate = "# Budget Chapter\n\n" + ("Rain pressed the ledger while Yin Yun waited for a name. " * 28) + "\n"
            resume_runner = target / "resume_runner.py"
            resume_runner.write_text(
                "import json, sys\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                f"evaluation = {evaluation!r}\n"
                f"candidate = {candidate!r}\n"
                "if 'chapter-planner' in payload:\n"
                "    raise SystemExit('planner must not be called again')\n"
                "receipt = {'schema': 'fictionops.runner_receipt.v1', 'provider': 'test', 'model': 'writer', 'request_id': 'req-resume', 'usage': {'input_tokens': 200, 'output_tokens': 50, 'total_tokens': 250}, 'cost': {'currency': 'USD', 'total': 0.002}}\n"
                "print('FICTIONOPS_RUNNER_RECEIPT:' + json.dumps(receipt), file=sys.stderr)\n"
                "print(json.dumps(evaluation) if 'draft-evaluator' in payload else candidate)\n",
                encoding="utf-8",
            )
            resumed = self.run_cli(
                "agent",
                "resume",
                str(run_dir),
                "--max-model-calls",
                "2",
                "--max-total-tokens",
                "1000",
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(resume_runner),
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            resumed_payload = json.loads(resumed.stdout)
            self.assertTrue(resumed_payload["resumed"])
            self.assertEqual(resumed_payload["resumed_from_phase"], "plan_ready")
            self.assertEqual(resumed_payload["final_phase"], "ready_for_approval", resumed_payload)
            self.assertTrue(resumed_payload["ready_for_approval"])
            self.assertEqual(resumed_payload["model_calls_used"], 2)
            self.assertEqual(resumed_payload["cumulative_model_calls"], 3)
            self.assertTrue((run_dir / "model_budget.segment1.json").exists())
            resumed_budget = json.loads((run_dir / "model_budget.json").read_text(encoding="utf-8"))
            self.assertEqual([item["role"] for item in resumed_budget["calls"]], ["draft-writer", "draft-evaluator"])
            self.assertEqual(resumed_budget["segment_usage"]["total_tokens"], 500)
            self.assertEqual(resumed_budget["cumulative_usage"]["total_tokens"], 620)
            self.assertEqual(resumed_budget["segment_cost_by_currency"]["USD"], 0.004)
            self.assertEqual(resumed_budget["cumulative_cost_by_currency"]["USD"], 0.005)
            self.assertEqual(json.loads((run_dir / "session.json").read_text(encoding="utf-8"))["resume_count"], 1)
            self.assertFalse(chapter.exists())

    def test_unified_agent_entry_and_continue_respect_authority_boundaries(self) -> None:
        policy_cases = [
            ({"state": "ready_for_approval"}, "review_candidate", "author"),
            ({"state": "drafting", "budget_status": "exhausted"}, "replan_budget", "author"),
            ({"state": "needs_revision_attention"}, "inspect_failed_candidate", "author"),
            ({"state": "cancelled"}, "start_new_session_after_cancellation", "author"),
            ({"state": "applied", "canon_sync_pending": True}, "review_canon_sync", "author"),
            ({"state": None, "memory_stale": True}, "rebuild_memory", "controller"),
            ({"state": None, "counterevidence_open_count": 1}, "prepare_counterevidence_revision", "controller"),
            ({"state": None, "counterevidence_open_count": 1, "counterevidence_candidate_state": "awaiting_verification"}, "verify_counterevidence_revision", "controller"),
            ({"state": None, "counterevidence_open_count": 1, "counterevidence_candidate_state": "needs_revision_attention"}, "revise_counterevidence_candidate", "controller"),
            ({"state": None, "counterevidence_open_count": 1, "counterevidence_candidate_state": "ready_for_approval"}, "review_counterevidence_candidate", "author"),
            ({"state": None, "counterevidence_blocked_count": 1}, "retrieve_counterevidence", "controller"),
            ({"state": None, "counterevidence_withdrawn_count": 1}, "review_model_withdrawals", "author"),
            ({"state": None}, "inspect_project", "controller"),
        ]
        for inputs, expected_action, expected_authority in policy_cases:
            decision = select_agent_policy(**inputs)
            self.assertEqual(decision.action, expected_action)
            self.assertEqual(decision.authority, expected_authority)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_management").mkdir()
            chapter_dir = target / "book_01"
            chapter_dir.mkdir()
            chapter = chapter_dir / "ch_01_unified.md"
            engine = chapter_dir / "ch_01_engine.md"
            engine.write_text("# Unified Chapter\n\n- target chars: 200\n", encoding="utf-8")

            prepared = self.run_cli(
                "agent",
                "write",
                str(chapter),
                "--engine",
                str(engine),
                "--no-memory",
                "--dry-run",
                "--format",
                "json",
            )
            prepared_payload = json.loads(prepared.stdout)
            self.assertEqual(prepared_payload["command"], "agent-write-workflow")
            self.assertFalse(prepared_payload["executed"])

            memory_dir = target / ".fictionops" / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "stale.json").write_text('{"reason":"accepted"}\n', encoding="utf-8")
            continued = self.run_cli("agent", "continue", str(target), "--execute", "--format", "json")
            continued_payload = json.loads(continued.stdout)
            self.assertEqual(continued_payload["selected_action"], "rebuild_memory")
            self.assertTrue(continued_payload["executed"])
            self.assertFalse(continued_payload["memory"]["stale"])

            run_dir = target / "00_management" / "agent_runs" / "ready"
            run_dir.mkdir(parents=True)
            (run_dir / "session.json").write_text(
                json.dumps(
                    {
                        "session_id": "ready-session",
                        "state": "ready_for_approval",
                        "ready_for_approval": True,
                        "source_file": str(chapter),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            stopped = self.run_cli("agent", "continue", str(target), "--execute", "--format", "json")
            stopped_payload = json.loads(stopped.stdout)
            self.assertEqual(stopped_payload["selected_action"], "review_candidate")
            self.assertTrue(stopped_payload["requires_human"])
            self.assertFalse(stopped_payload["executed"])
            self.assertEqual(stopped_payload["stop_reason"], "human_authority_required")
            self.assertIn("agent accept", stopped_payload["suggested_command"])

            status = json.loads(self.run_cli("agent", "status", str(target), "--format", "json").stdout)
            self.assertEqual(status["schema"], "fictionops.agent_project_status.v1")
            self.assertGreaterEqual(status["session_count"], 1)
            self.assertEqual(status["author_actions"]["ready_for_approval"], 1)
            self.assertEqual(status["author_actions"]["resumable"], 0)

    def test_agent_checkpoint_and_cancel_are_persistent_authority_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_management").mkdir()
            chapter_dir = target / "book_01"
            chapter_dir.mkdir()
            chapter = chapter_dir / "ch_02_cancelled.md"
            engine = chapter_dir / "ch_02_engine.md"
            engine.write_text("# Cancelled Chapter\n\n- target chars: 200\n", encoding="utf-8")
            run_dir = target / "00_management" / "agent_runs" / "cancel_me"
            prepared = self.run_cli(
                "agent",
                "write",
                str(chapter),
                "--engine",
                str(engine),
                "--out-dir",
                str(run_dir),
                "--no-memory",
                "--format",
                "json",
            )
            self.assertTrue(json.loads(prepared.stdout)["prepared"])
            checkpoint = json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))
            self.assertEqual(checkpoint["phase"], "context_ready")
            self.assertTrue(checkpoint["resumable"])
            self.assertTrue(all(item["exists"] and item["sha256"] for item in checkpoint["artifacts"]))

            cancelled = self.run_cli(
                "agent",
                "cancel",
                str(run_dir),
                "--reason",
                "author changed the chapter premise",
                "--format",
                "json",
            )
            cancelled_payload = json.loads(cancelled.stdout)
            self.assertTrue(cancelled_payload["cancelled"])
            self.assertEqual(json.loads((run_dir / "session.json").read_text(encoding="utf-8"))["state"], "cancelled")
            cancelled_checkpoint = json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))
            self.assertEqual(cancelled_checkpoint["phase"], "cancelled")
            self.assertFalse(cancelled_checkpoint["resumable"])
            self.assertTrue((run_dir / "cancellation.json").exists())

            continued = self.run_cli("agent", "continue", str(target), "--execute", "--format", "json")
            continued_payload = json.loads(continued.stdout)
            self.assertEqual(continued_payload["selected_action"], "start_new_session_after_cancellation")
            self.assertTrue(continued_payload["requires_human"])
            self.assertFalse(continued_payload["executed"])
            refused = self.run_cli(
                "agent",
                "cancel",
                str(run_dir),
                "--reason",
                "duplicate",
                "--format",
                "json",
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertFalse(chapter.exists())
            trajectory = [json.loads(line) for line in (run_dir / "trajectory.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(any(item["authority"] == "author" and item["phase"] == "cancelled" for item in trajectory))

            lab = json.loads(self.run_cli("agent", "failure-lab", "--format", "json").stdout)
            self.assertEqual(lab["schema"], "fictionops.agent_failure_lab.v1")
            self.assertEqual(lab["scenario_count"], 7)
            self.assertEqual(lab["detection_rate"], 1.0)
            self.assertEqual(lab["protected_hash_success_rate"], 1.0)
            self.assertEqual(lab["recovery_success_rate"], 1.0)

    def test_persistent_issue_identity_survives_rewording_and_author_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "00_management").mkdir()
            chapter = target / "chapter.md"
            chapter.write_text("# Chapter\n\n他抬剑时没有看仁孜。\n", encoding="utf-8")
            run1 = target / "00_management" / "agent_runs" / "run1"
            run2 = target / "00_management" / "agent_runs" / "run2"
            run3 = target / "00_management" / "agent_runs" / "run3"
            run4 = target / "00_management" / "agent_runs" / "run4"
            for run_dir in (run1, run2, run3, run4):
                run_dir.mkdir(parents=True)
            issue_a = {
                "category": "semantic.character",
                "severity": "P2",
                "confidence": 0.9,
                "metric_keys": [],
                "evidence": ["他抬剑时没有看仁孜"],
                "problem": "旁白替人物完成了确定判断",
                "status": "open",
            }
            issue_b = {
                "category": "semantic.character",
                "severity": "P2",
                "confidence": 0.88,
                "metric_keys": [],
                "evidence": ["他抬剑时没有看仁孜", "剑锋停在半寸外"],
                "problem": "叙述提前给出了人物尚未形成的结论",
                "status": "open",
            }
            first, _ = merge_issue_observations(
                chapter,
                session_id="session-1",
                run_dir=run1,
                issues=[issue_a],
            )
            issue_id = str(first[0]["issue_id"])
            self.assertEqual(issue_id, stable_issue_id(chapter, issue_a))

            waived = self.run_cli(
                "agent",
                "issue",
                str(target),
                "--id",
                issue_id,
                "--status",
                "waived",
                "--reason",
                "此处保留为人物自我遮蔽",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(waived.stdout)["issues"][0]["status"], "waived")
            second, _ = merge_issue_observations(
                chapter,
                session_id="session-2",
                run_dir=run2,
                issues=[issue_b, dict(issue_b)],
            )
            self.assertEqual(len(second), 1)
            self.assertEqual(second[0]["issue_id"], issue_id)
            self.assertEqual(second[0]["status"], "waived")
            self.assertEqual(len(second[0]["evidence"]), 2)
            (run2 / "issues.before.json").write_text(
                json.dumps({"schema": "fictionops.revision_issues.v1", "issues": second}, ensure_ascii=False),
                encoding="utf-8",
            )
            compact = compact_issue_ledger(run2)
            self.assertEqual(compact["issue_count"], 0)
            self.assertEqual(compact["excluded_issue_count"], 1)
            self.assertEqual(compact["excluded_issues"][0]["issue_id"], issue_id)

            reopened = self.run_cli(
                "agent",
                "issue",
                str(target),
                "--id",
                issue_id,
                "--status",
                "reopened",
                "--reason",
                "新上下文表明此处不再承担遮蔽功能",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(reopened.stdout)["issues"][0]["status"], "reopened")
            transition_issue(target, issue_id=issue_id, to_status="addressed", reason="candidate removed the conclusion", actor="controller")
            transition_issue(target, issue_id=issue_id, to_status="verified", reason="semantic verifier passed", actor="controller")
            transition_issue(target, issue_id=issue_id, to_status="accepted", reason="author accepted candidate", actor="controller")
            fourth, _ = merge_issue_observations(
                chapter,
                session_id="session-4",
                run_dir=run4,
                issues=[issue_b],
            )
            self.assertEqual(fourth[0]["issue_id"], issue_id)
            self.assertEqual(fourth[0]["status"], "reopened")
            ledger = load_issue_ledger(target)
            stored = next(item for item in ledger["issues"] if item["issue_id"] == issue_id)
            self.assertEqual(len(stored["observations"]), 3)
            self.assertTrue(any(item["to_status"] == "waived" for item in stored["decisions"]))
            self.assertTrue(any(item["to_status"] == "reopened" for item in stored["decisions"]))

    def test_high_risk_review_fixture_covers_three_semantic_profiles(self) -> None:
        fixture = json.loads(
            (ROOT / "tests" / "fixtures" / "agent_high_risk_review_cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(fixture["schema"], "fictionops.agent_high_risk_review_cases.v1")
        cases = fixture["cases"]
        self.assertEqual(
            {item["risk"] for item in cases},
            {"information_boundaries", "character", "prose_and_reader_experience"},
        )
        issue_ids: set[str] = set()
        for case in cases:
            review = parse_comprehensive_review(json.dumps(case["review"], ensure_ascii=False))
            self.assertEqual(len(review["dimensions"]), 6)
            self.assertEqual(review["issues"][0]["category"], case["expected_category"])
            self.assertTrue(case["false_positive_guard"])
            chapter = Path(f"fixture/{case['case_id']}.md")
            issue = {**review["issues"][0], "category": f"semantic.{review['issues'][0]['category']}"}
            issue_id = stable_issue_id(chapter, issue)
            reworded = {**issue, "problem": "A differently worded diagnosis of the same quoted evidence."}
            self.assertEqual(stable_issue_id(chapter, reworded), issue_id)
            issue_ids.add(issue_id)
            raw_prompt = baseline_prompt(case, "raw")
            self.assertIn("fictionops.agent_research_baseline_request.v1", raw_prompt)
            self.assertNotIn("## Retrieved Project Context", raw_prompt)
            self.assertNotIn("## False-Positive Guard", raw_prompt)
            self.assertNotIn("## Workflow Contract", raw_prompt)
            self.assertNotIn(case["project_context"], raw_prompt)
        self.assertEqual(len(issue_ids), 3)
        alias_score = score_review(
            cases[0],
            "raw",
            {
                "issues": [
                    {
                        "category": "narrative intrusion",
                        "evidence": "The narrator states: ‘她早已决定今夜背叛主人’.",
                    }
                ]
            },
            None,
        )
        self.assertTrue(alias_score["detected"])
        self.assertTrue(alias_score["evidence_grounded"])
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp) / "baseline_runner.py"
            expected = {case.get("prompt_id", case["case_id"]): case["review"] for case in cases}
            runner.write_text(
                "import json, re, sys\n"
                f"expected = {expected!r}\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                "case_id = re.search(r'^CASE_ID: (.+)$', payload, re.MULTILINE).group(1).strip()\n"
                "print(json.dumps(expected[case_id], ensure_ascii=False))\n",
                encoding="utf-8",
            )
            baseline = run_baselines(
                ROOT / "tests" / "fixtures" / "agent_high_risk_review_cases.json",
                runner=[sys.executable, str(runner)],
            )
            self.assertEqual(baseline["schema"], "fictionops.agent_review_baseline.v2")
            self.assertEqual(len(baseline["rows"]), 9)
            self.assertEqual(baseline["rows"][0]["review"], cases[0]["review"])
            self.assertEqual(len(baseline["rows"][0]["prompt_sha256"]), 64)
            self.assertIn("information_boundary", baseline["rows"][0]["accepted_categories"])
            for mode in ("raw", "rag", "workflow"):
                self.assertEqual(baseline["aggregate"][mode]["detection_rate"], 1.0)
                self.assertEqual(baseline["aggregate"][mode]["grounded_rate"], 1.0)
            cli_baseline = self.run_cli(
                "agent",
                "benchmark",
                str(ROOT / "tests" / "fixtures" / "agent_high_risk_review_cases.json"),
                "--conditions",
                "raw,full,no_memory",
                "--runs",
                "2",
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
            )
            cli_payload = json.loads(cli_baseline.stdout)
            self.assertEqual(cli_payload["conditions"], ["raw", "full", "no_memory"])
            self.assertEqual(cli_payload["runs_per_case"], 2)
            self.assertEqual(len(cli_payload["rows"]), 18)

    def test_benchmark_v2_scores_negative_controls_and_builds_blind_packet(self) -> None:
        fixture_path = ROOT / "tests" / "fixtures" / "agent_benchmark_v2_cases.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        cases = fixture["cases"]
        self.assertEqual(len(cases), 10)
        self.assertEqual(sum(bool(case.get("expected_issue", bool(case.get("expected_category")))) for case in cases), 6)
        opaque_prompt = baseline_prompt(cases[0], "raw")
        self.assertIn("CASE_ID: B01", opaque_prompt)
        self.assertNotIn(cases[0]["case_id"], opaque_prompt)
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp) / "benchmark_v2_runner.py"
            expected = {case.get("prompt_id", case["case_id"]): case["review"] for case in cases}
            runner.write_text(
                "import json, re, sys\n"
                f"expected = {expected!r}\n"
                "payload = sys.stdin.buffer.read().decode('utf-8')\n"
                "case_id = re.search(r'^CASE_ID: (.+)$', payload, re.MULTILINE).group(1).strip()\n"
                "print(json.dumps(expected[case_id], ensure_ascii=False))\n",
                encoding="utf-8",
            )
            report = run_baselines(
                fixture_path,
                runner=[sys.executable, str(runner)],
                conditions=["raw", "full"],
            )
            for condition in ("raw", "full"):
                metrics = report["aggregate"][condition]
                self.assertEqual(metrics["positive_cases"], 6)
                self.assertEqual(metrics["negative_cases"], 4)
                self.assertEqual(metrics["precision"], 1.0)
                self.assertEqual(metrics["recall"], 1.0)
                self.assertEqual(metrics["accuracy"], 1.0)
                self.assertEqual(metrics["false_positive_rate"], 0.0)
            packet, key = build_blind_review_artifacts(report, fixture_path)
            self.assertEqual(len(packet["samples"]), 20)
            self.assertEqual(len(key["samples"]), 20)
            self.assertEqual(len({sample["sample_id"] for sample in packet["samples"]}), 20)
            self.assertNotIn("condition", packet["samples"][0])
            self.assertIn("condition", key["samples"][0])

            blind_path = Path(tmp) / "blind.json"
            key_path = Path(tmp) / "blind-key.json"
            completed = self.run_cli(
                "agent",
                "benchmark",
                str(fixture_path),
                "--conditions",
                "raw,full",
                "--format",
                "json",
                "--blind-out",
                str(blind_path),
                "--blind-key-out",
                str(key_path),
                "--runner",
                sys.executable,
                str(runner),
            )
            self.assertEqual(completed.returncode, 0)
            self.assertTrue(blind_path.exists())
            self.assertTrue(key_path.exists())
            self.assertEqual(len(json.loads(blind_path.read_text(encoding="utf-8"))["samples"]), 20)

    def test_counterevidence_blind_export_and_scoring_keep_labels_private(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = Path(tmp) / "counterevidence.json"
            key_path = Path(tmp) / "counterevidence-key.json"
            exported = self.run_cli(
                "agent",
                "counterevidence",
                "export",
                str(ROOT / "docs" / "evidence" / "deepseek-preservation-verifier-v1.json"),
                "--benchmark",
                str(ROOT / "docs" / "evidence" / "deepseek-benchmark-v2.json"),
                "--fixtures",
                str(ROOT / "tests" / "fixtures" / "agent_benchmark_v2_cases.json"),
                "--out",
                str(packet_path),
                "--key-out",
                str(key_path),
            )
            self.assertEqual(exported.returncode, 0, exported.stderr)
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            key = json.loads(key_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["sample_count"], 16)
            self.assertEqual(packet["sample_count"], key["sample_count"])
            serialized_packet = json.dumps(packet, ensure_ascii=False)
            self.assertNotIn('"prompt_id"', serialized_packet)
            self.assertNotIn('"control_class"', serialized_packet)
            self.assertIn('"control_class"', json.dumps(key))
            with self.assertRaisesRegex(ValueError, "valid annotation decision"):
                evaluate_counterevidence(packet_path, key_path)

            control_by_id = {item["sample_id"]: item["control_class"] for item in key["samples"]}
            for sample in packet["samples"]:
                control = control_by_id[sample["sample_id"]]
                sample["annotation"] = {
                    "decision": "withdraw" if control == "preserve" else "uphold" if control == "detect" else "insufficient",
                    "evidence_grounded": control != "unevaluable",
                    "repair_harm_risk": "high" if control == "preserve" else "low",
                    "effort_minutes": 1.5,
                    "notes": "synthetic regression annotation",
                }
            packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            packet_path.write_bytes(b"\xef\xbb\xbf" + packet_path.read_bytes())
            evaluation = evaluate_counterevidence(packet_path, key_path)
            self.assertEqual(evaluation["schema"], COUNTEREVIDENCE_EVALUATION_SCHEMA)
            self.assertEqual(evaluation["control_agreement_rate"], 1.0)
            self.assertEqual(evaluation["control_summary"]["preserve_label_challenge"], 0)
            self.assertEqual(evaluation["total_effort_minutes"], 24.0)
            self.assertGreater(evaluation["decision_counts"]["insufficient"], 0)

            run_dir = Path(tmp) / "revision-run"
            run_dir.mkdir()
            (run_dir / "source_chapter.md").write_text("# Chapter\n\nOriginal text.\n", encoding="utf-8")
            (run_dir / "project_context.md").write_text("Authoritative context.\n", encoding="utf-8")
            (run_dir / "comprehensive_review.json").write_text(
                json.dumps({"reviewer_issues": [{"category": "style", "evidence": ["Original text"], "problem": "Maybe flat.", "suggested_action": "Inspect it."}]}),
                encoding="utf-8",
            )
            (run_dir / "preservation_verification.json").write_text(
                json.dumps({"decisions": [{"issue_index": 0, "verdict": "needs_counterevidence", "evidence": ["Original text"], "reason": "More context needed."}]}),
                encoding="utf-8",
            )
            run_packet, run_key = build_counterevidence_from_run(run_dir)
            self.assertEqual(run_packet["sample_count"], 1)
            self.assertEqual(run_key["samples"][0]["control_class"], "unevaluable")
            self.assertEqual(run_packet["samples"][0]["source_scope"], "full_chapter")

            run_packet["samples"][0]["annotation"] = {
                "decision": "insufficient",
                "evidence_grounded": False,
                "repair_harm_risk": "medium",
                "effort_minutes": 1,
                "notes": "needs chapter-scale evidence",
            }
            run_packet["samples"][0]["reviewer_finding"]["category"] = "chapter function"
            run_packet_file = run_dir / "counterevidence.annotated.json"
            run_packet_file.write_text(json.dumps(run_packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            escalation = build_evidence_escalation(run_packet_file)
            self.assertEqual(escalation["selected_sample_count"], 1)
            self.assertEqual(escalation["ready_for_reverification_count"], 1)
            self.assertEqual(escalation["requests"][0]["route"]["scope"], "full_chapter")
            self.assertEqual(classify_evidence_scope({"reviewer_finding": {"category": "information boundaries", "problem": "How did she know the exact inventory?"}})["scope"], "knowledge_source")

            adjacent_packet = json.loads(json.dumps(run_packet))
            adjacent_packet["samples"][0]["sample_id"] = "adjacent-1"
            adjacent_packet["samples"][0]["reviewer_finding"] = {
                "category": "prose rhythm",
                "evidence": ["Original text."],
                "problem": "The adjacent paragraphs repeat the same syntactic pattern.",
                "suggested_action": "Compare the neighboring paragraphs before revising.",
            }
            duplicate = json.loads(json.dumps(adjacent_packet["samples"][0]))
            duplicate["sample_id"] = "adjacent-2"
            adjacent_packet["samples"].append(duplicate)
            adjacent_packet["sample_count"] = 2
            adjacent_packet_file = run_dir / "counterevidence-adjacent.json"
            adjacent_packet_file.write_text(json.dumps(adjacent_packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            adjacent_escalation = build_evidence_escalation(adjacent_packet_file, chapter_file=run_dir / "source_chapter.md")
            self.assertEqual(adjacent_escalation["request_count"], 1)
            self.assertEqual(adjacent_escalation["duplicates_collapsed"], 1)
            self.assertEqual(adjacent_escalation["requests"][0]["route"]["scope"], "adjacent_paragraphs")
            self.assertIn("Original text.", adjacent_escalation["requests"][0]["evidence_items"][0]["content"])

            escalated_path = run_dir / "escalation.json"
            escalated = self.run_cli(
                "agent",
                "counterevidence",
                "escalate",
                str(run_packet_file),
                "--out",
                str(escalated_path),
                "--format",
                "json",
            )
            self.assertEqual(escalated.returncode, 0, escalated.stderr)
            escalation_payload = json.loads(escalated_path.read_text(encoding="utf-8"))
            self.assertEqual(escalation_payload["request_count"], 1)

            reverify_runner = run_dir / "reverify_runner.py"
            reverify_runner.write_text(
                "import json, sys\n"
                "_ = sys.stdin.read()\n"
                f"request_id = {escalation_payload['requests'][0]['request_id']!r}\n"
                "print(json.dumps({'schema':'fictionops.escalated_reverification.v1','request_id':request_id,'verdict':'uphold','evidence':['Original text.'],'reason':'The full chapter supports the finding.','remaining_gap':'','confidence':'high'}))\n"
                "receipt={'schema':'fictionops.runner_receipt.v1','provider':'fixture','model':'reverifier','usage':{'input_tokens':20,'output_tokens':10,'total_tokens':30,'cached_input_tokens':0}}\n"
                "print('FICTIONOPS_RUNNER_RECEIPT:'+json.dumps(receipt), file=sys.stderr)\n",
                encoding="utf-8",
            )
            reverification_path = run_dir / "reverification.json"
            reverification = self.run_cli(
                "agent",
                "counterevidence",
                "reverify",
                str(escalated_path),
                "--packet",
                str(run_packet_file),
                "--out",
                str(reverification_path),
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(reverify_runner),
            )
            self.assertEqual(reverification.returncode, 0, reverification.stderr)
            reverification_payload = json.loads(reverification_path.read_text(encoding="utf-8"))
            self.assertEqual(reverification_payload["verdict_counts"]["uphold"], 1)
            self.assertEqual(reverification_payload["usage"]["total_tokens"], 30)
            self.assertFalse(reverification_payload["safety"]["edits_manuscript"])
            ungrounded = apply_reverification_grounding(
                {
                    "schema": "fictionops.escalated_reverification.v1",
                    "request_id": "x",
                    "verdict": "withdraw",
                    "evidence": ["A quotation that is nowhere in the supplied evidence."],
                    "reason": "unsupported",
                    "remaining_gap": "",
                    "confidence": "high",
                },
                escalation_payload["requests"][0],
                run_packet["samples"][0],
            )
            self.assertEqual(ungrounded["verdict"], "still_insufficient")
            self.assertTrue(ungrounded["grounding_override"])

    def test_counterevidence_application_updates_machine_states_without_overwriting_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "ledger-project"
            (project / "00_management").mkdir(parents=True)
            chapter = project / "chapter.md"
            chapter_text = "# Chapter\n\nThe door stayed closed.\n"
            chapter.write_text(chapter_text, encoding="utf-8")
            source_hash = hashlib.sha256(chapter.read_bytes()).hexdigest()
            run_dir = project / "agent_runs" / "run-001"
            run_dir.mkdir(parents=True)
            (run_dir / "source_manifest.json").write_text(
                json.dumps({"schema": "fictionops.revision_source_manifest.v1", "source_file": str(chapter), "source_sha256": source_hash}),
                encoding="utf-8",
            )
            (run_dir / "session.json").write_text(
                json.dumps({"schema": "fictionops.agent_session.v1", "session_id": "session-001", "source_file": str(chapter)}),
                encoding="utf-8",
            )
            (run_dir / "issues.before.json").write_text(
                json.dumps({"schema": "fictionops.revision_issues.v1", "issues": []}),
                encoding="utf-8",
            )
            findings = [
                ("chapter_function", "uphold", True),
                ("character", "withdraw", True),
                ("information_boundaries", "still_insufficient", False),
                ("prose_and_reader_experience", "uphold", True),
            ]
            samples = []
            results = []
            for index, (category, verdict, grounded) in enumerate(findings, start=1):
                sample_id = f"application-{index}"
                sample = {
                        "sample_id": sample_id,
                        "source_scope": "full_chapter",
                        "chapter_excerpt": "The door stayed closed.",
                        "authoritative_context": "Controlled ledger application test.",
                        "active_author_guards": {},
                        "reviewer_finding": {
                            "category": category,
                            "severity": "P2",
                            "confidence": "high",
                            "evidence": ["The door stayed closed."],
                            "problem": f"Controlled problem {index}",
                            "suggested_action": f"Controlled action {index}",
                        },
                        "verifier_assessment": {},
                        "annotation": {"decision": "insufficient"},
                    }
                if index == 4:
                    sample["issue_id"] = "iss-author-protected"
                samples.append(sample)
                results.append(
                    {
                        "request_id": f"request-{index}",
                        "sample_ids": [sample_id],
                        "verdict": verdict,
                        "model_verdict": verdict,
                        "evidence": ["The door stayed closed."] if grounded else [],
                        "evidence_grounded": grounded,
                        "grounded_evidence": ["The door stayed closed."] if grounded else [],
                        "reason": f"Controlled result {index}",
                    }
                )
            packet = {"schema": "fictionops.counterevidence_blind_packet.v1", "sample_count": 4, "samples": samples}
            packet_file = run_dir / "counterevidence.packet.json"
            packet_file.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = {
                "schema": "fictionops.escalated_reverification.v1",
                "packet_sha256": hashlib.sha256(packet_file.read_bytes()).hexdigest(),
                "results": results,
            }
            escalation = {
                "schema": "fictionops.counterevidence_escalation.v1",
                "requests": [
                    {
                        "request_id": f"request-{index}",
                        "sample_ids": [f"application-{index}"],
                        "status": "ready_for_reverification",
                        "route": {"scope": "full_chapter"},
                        "evidence_items": [{"content": "The door stayed closed."}],
                    }
                    for index in range(1, 5)
                ],
            }
            escalation_file = run_dir / "counterevidence.escalation.json"
            escalation_file.write_text(json.dumps(escalation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report["escalation_sha256"] = hashlib.sha256(escalation_file.read_bytes()).hexdigest()
            report_file = run_dir / "counterevidence.reverification.json"
            report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (project / ".fictionops").mkdir()
            (project / ".fictionops" / "issues.json").write_text(
                json.dumps(
                    {
                        "schema": "fictionops.issue_ledger.v1",
                        "project_root": str(project),
                        "issues": [
                            {
                                "issue_id": "iss-author-protected",
                                "chapter_file": str(chapter),
                                "status": "waived",
                                "category": "semantic.prose_and_reader_experience",
                                "decisions": [{"actor": "author", "to_status": "waived", "reason": "intentional prose"}],
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            dry_run = self.run_cli(
                "agent", "counterevidence", "apply", str(report_file), "--packet", str(packet_file), "--escalation", str(escalation_file), "--run-dir", str(run_dir), "--dry-run", "--format", "json"
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse((run_dir / "counterevidence_application.json").exists())
            applied = self.run_cli(
                "agent", "counterevidence", "apply", str(report_file), "--packet", str(packet_file), "--escalation", str(escalation_file), "--run-dir", str(run_dir), "--format", "json"
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            applied_payload = json.loads(applied.stdout)
            self.assertFalse(applied_payload["manuscript_edited"])
            self.assertEqual(chapter.read_text(encoding="utf-8"), chapter_text)
            ledger = load_issue_ledger(project)
            self.assertEqual({item["status"] for item in ledger["issues"]}, {"open", "model_withdrawn", "evidence_blocked", "waived"})
            protected = next(item for item in ledger["issues"] if item["issue_id"] == "iss-author-protected")
            self.assertEqual(protected["status"], "waived")
            self.assertEqual(applied_payload["actions"][3]["action"], "preserved_author_authority")
            compact = compact_issue_ledger(run_dir)
            self.assertEqual(compact["issue_count"], 1)
            self.assertEqual(compact["excluded_issue_count"], 3)
            queue = json.loads((run_dir / "counterevidence_reviser_queue.json").read_text(encoding="utf-8"))
            self.assertEqual(queue["issue_count"], 1)
            continued_open = json.loads(self.run_cli("agent", "continue", str(project), "--format", "json").stdout)
            self.assertEqual(continued_open["selected_action"], "prepare_counterevidence_revision")
            self.assertEqual(continued_open["counterevidence"]["open_count"], 1)
            self.assertFalse(continued_open["requires_human"])
            self.assertIn("counterevidence prepare-revision", continued_open["suggested_command"])
            prepared = self.run_cli(
                "agent", "counterevidence", "prepare-revision", str(run_dir), "--provider", "deepseek", "--model", "deepseek-chat", "--format", "json"
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            prepared_payload = json.loads(prepared.stdout)
            self.assertEqual(prepared_payload["issue_count"], 1)
            self.assertFalse(prepared_payload["reran_full_review"])
            self.assertFalse(prepared_payload["manuscript_edited"])
            bundle_dir = Path(prepared_payload["output_dir"])
            request = json.loads((bundle_dir / "request.json").read_text(encoding="utf-8"))
            contract = json.loads((bundle_dir / "issue_contract.json").read_text(encoding="utf-8"))
            context_pack = (bundle_dir / "context_pack.md").read_text(encoding="utf-8")
            self.assertEqual(request["schema"], "fictionops.agent_run_request.v1")
            self.assertEqual(request["execution_mode"], "prepare_only")
            self.assertEqual(request["provider"], "deepseek")
            loaded_request = load_agent_exec_request(bundle_dir)
            runner_input = build_runner_input(bundle_dir, loaded_request)
            self.assertIn("# FictionOps Agent Runner Input", runner_input)
            self.assertIn("Controlled problem 1", runner_input)
            inbox = inspect_agent_run_dir(bundle_dir, output_name=None)
            self.assertEqual(inbox.state, "awaiting_output")
            self.assertEqual([item.code for item in inbox.issues], ["missing_output"])
            self.assertEqual(contract["issue_count"], 1)
            self.assertEqual(contract["issues"][0]["problem"], "Controlled problem 1")
            self.assertIn("Controlled problem 1", context_pack)
            self.assertNotIn("Controlled problem 2", context_pack)
            self.assertNotIn("Controlled problem 3", context_pack)
            self.assertNotIn("Controlled problem 4", context_pack)
            self.assertEqual(chapter.read_text(encoding="utf-8"), chapter_text)
            open_issue = next(item for item in ledger["issues"] if item["status"] == "open")
            transition_issue(project, issue_id=open_issue["issue_id"], to_status="model_withdrawn", reason="controlled state routing", actor="controller")
            drifted_queue = self.run_cli(
                "agent", "counterevidence", "prepare-revision", str(run_dir), "--force", "--format", "json", check=False
            )
            self.assertNotEqual(drifted_queue.returncode, 0)
            self.assertIn("no longer a grounded open uphold", drifted_queue.stderr)
            continued_blocked = json.loads(self.run_cli("agent", "continue", str(project), "--format", "json").stdout)
            self.assertEqual(continued_blocked["selected_action"], "retrieve_counterevidence")
            blocked_issue = next(item for item in load_issue_ledger(project)["issues"] if item["status"] == "evidence_blocked")
            transition_issue(project, issue_id=blocked_issue["issue_id"], to_status="model_withdrawn", reason="controlled state routing", actor="controller")
            continued_withdrawn = json.loads(self.run_cli("agent", "continue", str(project), "--execute", "--format", "json").stdout)
            self.assertEqual(continued_withdrawn["selected_action"], "review_model_withdrawals")
            self.assertTrue(continued_withdrawn["requires_human"])
            self.assertEqual(continued_withdrawn["stop_reason"], "human_authority_required")
            status = json.loads(self.run_cli("agent", "status", str(project), "--format", "json").stdout)
            self.assertEqual(status["author_actions"]["review_model_withdrawals"], 3)
            self.assertEqual(status["author_actions"]["evidence_blocked"], 0)
            duplicate = self.run_cli(
                "agent", "counterevidence", "apply", str(report_file), "--packet", str(packet_file), "--escalation", str(escalation_file), "--run-dir", str(run_dir), "--format", "json", check=False
            )
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("already exists", duplicate.stderr)

            stale_run = project / "agent_runs" / "run-stale"
            stale_run.mkdir()
            shutil.copy2(run_dir / "source_manifest.json", stale_run / "source_manifest.json")
            shutil.copy2(run_dir / "session.json", stale_run / "session.json")
            chapter.write_text(chapter_text + "Changed after review.\n", encoding="utf-8")
            stale = self.run_cli(
                "agent", "counterevidence", "apply", str(report_file), "--packet", str(packet_file), "--escalation", str(escalation_file), "--run-dir", str(stale_run), "--format", "json", check=False
            )
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("source chapter is stale", stale.stderr)

    def test_counterevidence_candidate_verification_and_acceptance_are_hash_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "candidate-project"
            (project / "00_management").mkdir(parents=True)
            chapter = project / "chapter.md"
            source_text = "# Rain\n\nGu Chuan lost his left arm.\n\nHe raised his left hand.\n"
            candidate_text = source_text.replace("raised his left hand", "raised his right hand")
            chapter.write_text(source_text, encoding="utf-8")
            source_hash = hashlib.sha256(chapter.read_bytes()).hexdigest()
            issue_id = "iss-counterevidence-candidate"
            (project / ".fictionops").mkdir()
            (project / ".fictionops" / "issues.json").write_text(
                json.dumps(
                    {
                        "schema": "fictionops.issue_ledger.v1",
                        "project_root": str(project),
                        "issues": [
                            {
                                "issue_id": issue_id,
                                "chapter_file": str(chapter),
                                "status": "open",
                                "category": "semantic.continuity",
                                "counterevidence": {
                                    "effective_verdict": "uphold",
                                    "grounded_evidence": ["lost his left arm", "raised his left hand"],
                                },
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            bundle = project / "agent_runs" / "run-001" / "counterevidence_revision_bundle"
            bundle.mkdir(parents=True)
            (bundle.parent / "counterevidence_reviser_queue.json").write_text(
                json.dumps(
                    {
                        "schema": "fictionops.counterevidence_reviser_queue.v1",
                        "issue_ids": [issue_id],
                        "issue_count": 1,
                        "source_application": str(bundle.parent / "counterevidence_application.json"),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            contract = {
                "schema": "fictionops.counterevidence_revision_contract.v1",
                "chapter_file": str(chapter),
                "source_sha256": source_hash,
                "issue_count": 1,
                "issues": [
                    {
                        "issue_id": issue_id,
                        "problem": "The final action contradicts the missing left arm.",
                        "grounded_evidence": ["lost his left arm", "raised his left hand"],
                        "suggested_action": "Use the right hand only in the final action.",
                    }
                ],
                "active_author_guards": [],
            }
            contract_file = bundle / "issue_contract.json"
            contract_file.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
            (bundle / "output.md").write_text(candidate_text, encoding="utf-8", newline="\n")
            (bundle / "bundle_manifest.json").write_text(
                json.dumps(
                    {
                        "schema": "fictionops.counterevidence_revision_bundle.v1",
                        "artifact_sha256": {"issue_contract.json": hashlib.sha256(contract_file.read_bytes()).hexdigest()},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            verifier = project / "verifier.py"
            verifier.write_text(
                "import json\n"
                f"print(json.dumps({{'schema':'fictionops.counterevidence_candidate_verification.v1','decisions':[{{'issue_id':'{issue_id}','resolved':True,'candidate_evidence':['He raised his right hand.'],'reason':'fixed'}}],'unrelated_changes':[],'active_author_guards_preserved':True,'new_canon_added':False,'overall_pass':True,'summary':'bounded fix'}}))\n",
                encoding="utf-8",
            )
            awaiting_verification = json.loads(self.run_cli("agent", "continue", str(project), "--format", "json").stdout)
            self.assertEqual(awaiting_verification["selected_action"], "verify_counterevidence_revision")
            guard_file = project / ".fictionops" / "author_guards.json"
            guard_file.write_text(
                json.dumps(
                    {
                        "schema": "fictionops.author_guard_registry.v1",
                        "guards": [
                            {
                                "guard_id": "G-TEST",
                                "kind": "style",
                                "statement": "Preserve the original hand reference intentionally.",
                                "source": "author",
                                "status": "active",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            guard_drift = self.run_cli(
                "agent", "counterevidence", "verify-revision", str(bundle), "--format", "json", "--runner", sys.executable, str(verifier), check=False
            )
            self.assertNotEqual(guard_drift.returncode, 0)
            self.assertIn("author guards changed", guard_drift.stderr)
            guard_file.unlink()
            verified = self.run_cli(
                "agent", "counterevidence", "verify-revision", str(bundle), "--format", "json", "--runner", sys.executable, str(verifier)
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)
            verification = json.loads(verified.stdout)
            self.assertTrue(verification["ready_for_approval"])
            self.assertTrue(verification["bounded_change_scope"]["passed"])
            self.assertTrue(verification["decisions"][0]["evidence_grounded"])
            self.assertTrue(Path(verification["attempt"]["raw_file"]).is_file())
            awaiting_author = json.loads(self.run_cli("agent", "continue", str(project), "--execute", "--format", "json").stdout)
            self.assertEqual(awaiting_author["selected_action"], "review_counterevidence_candidate")
            self.assertTrue(awaiting_author["requires_human"])
            self.assertEqual(awaiting_author["stop_reason"], "human_authority_required")
            candidate_file = bundle / "output.md"
            candidate_file.write_text(candidate_text + "drift\n", encoding="utf-8", newline="\n")
            drifted = self.run_cli("agent", "counterevidence", "accept-revision", str(bundle), "--dry-run", "--format", "json", check=False)
            self.assertNotEqual(drifted.returncode, 0)
            self.assertIn("candidate changed", drifted.stderr)
            candidate_file.write_text(candidate_text, encoding="utf-8", newline="\n")
            dry = self.run_cli("agent", "counterevidence", "accept-revision", str(bundle), "--dry-run", "--format", "json")
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertEqual(chapter.read_text(encoding="utf-8"), source_text)
            accepted = self.run_cli("agent", "counterevidence", "accept-revision", str(bundle), "--format", "json", check=False)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual(chapter.read_text(encoding="utf-8"), candidate_text)
            stored = next(item for item in load_issue_ledger(project)["issues"] if item["issue_id"] == issue_id)
            self.assertEqual(stored["status"], "accepted")
            self.assertEqual([item["to_status"] for item in stored["decisions"]], ["addressed", "verified", "accepted"])

    def test_preservation_verifier_withdraws_self_abstaining_issues_without_erasing_evidence(self) -> None:
        review = {
            "issues": [
                {
                    "category": "prose_and_reader_experience",
                    "evidence": ["归土。"],
                    "problem": "The repetition is intentional.",
                    "suggested_action": "No change needed; preserve it as is.",
                },
                {
                    "category": "character",
                    "evidence": [],
                    "problem": "The child may sound too clever.",
                    "suggested_action": "Simplify the line.",
                },
                {
                    "category": "continuity",
                    "evidence": ["鹿煜抬起左手"],
                    "problem": "The established left-hand loss is contradicted.",
                    "suggested_action": "Use the right hand.",
                },
            ],
            "revision_priorities": ["old untrusted priority"],
        }
        deterministic = deterministic_preservation_decisions(review)
        self.assertEqual([item["verdict"] for item in deterministic], ["withdraw", "needs_counterevidence", "uphold"])
        model_text = json.dumps(
            {
                "schema": PRESERVATION_VERIFICATION_SCHEMA,
                "decisions": [
                    {"issue_index": 0, "verdict": "uphold", "evidence": ["归土。"], "guard_ids": [], "reason": "model disagrees"},
                    {"issue_index": 1, "verdict": "needs_counterevidence", "evidence": [], "guard_ids": [], "reason": "no quote"},
                    {"issue_index": 2, "verdict": "uphold", "evidence": ["鹿煜抬起左手"], "guard_ids": [], "reason": "canon contradiction"},
                ],
                "summary": "one issue survives",
            },
            ensure_ascii=False,
        )
        model = parse_preservation_verification(model_text, issue_count=3)
        filtered, verification = apply_preservation_verification(review, model)
        self.assertEqual(verification["withdrawn_count"], 1)
        self.assertEqual(verification["needs_counterevidence_count"], 1)
        self.assertEqual(verification["upheld_count"], 1)
        self.assertEqual(len(filtered["reviewer_issues"]), 3)
        self.assertEqual(len(filtered["issues"]), 1)
        self.assertEqual(len(filtered["withdrawn_issues"]), 1)
        self.assertEqual(len(filtered["needs_counterevidence_issues"]), 1)
        self.assertEqual(filtered["revision_priorities"], ["Use the right hand."])

        unguarded_review = {
            "issues": [
                {
                    "category": "prose_and_reader_experience",
                    "evidence": ["不是雨，不是风，不是脚步"],
                    "problem": "Three template families repeat.",
                    "suggested_action": "Keep one and vary the rest.",
                    "preserve_constraints": [],
                }
            ]
        }
        unguarded_model = {
            "decisions": [
                {
                    "issue_index": 0,
                    "verdict": "withdraw",
                    "evidence": ["The pressure is intentional."],
                    "guard_ids": [],
                    "reason": "preserve the rhythm",
                    "authority": "model",
                }
            ]
        }
        unguarded_filtered, unguarded_verification = apply_preservation_verification(unguarded_review, unguarded_model)
        self.assertEqual(unguarded_verification["withdrawn_count"], 0)
        self.assertEqual(unguarded_verification["needs_counterevidence_count"], 1)
        self.assertEqual(len(unguarded_filtered["needs_counterevidence_issues"]), 1)

    def test_author_guard_registry_keeps_stable_ids_history_and_withdraw_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "00_management").mkdir()
            created = self.run_cli(
                "agent",
                "guard",
                "set",
                str(project),
                "--id",
                "G-STYLE-001",
                "--kind",
                "style",
                "--statement",
                "保留葬礼中三次‘归土’的仪式递进。",
                "--source",
                "写作设定/葬礼节奏",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(created.stdout)["guards"][0]["guard_id"], "G-STYLE-001")
            updated = self.run_cli(
                "agent",
                "guard",
                "set",
                str(project),
                "--id",
                "G-STYLE-001",
                "--kind",
                "style",
                "--statement",
                "保留葬礼中三次‘归土’，每次必须推动不同人物动作。",
                "--source",
                "写作设定/葬礼节奏",
                "--format",
                "json",
            )
            self.assertEqual(len(json.loads(updated.stdout)["guards"][0]["history"]), 1)
            registry = load_author_guard_registry(project)
            self.assertEqual(registry["guard_count"], 1)
            guards = active_author_guards(project)
            self.assertIn("G-STYLE-001", guards)

            review = {
                "issues": [
                    {
                        "category": "prose_and_reader_experience",
                        "evidence": ["归土。"],
                        "problem": "The three repetitions should be reduced.",
                        "suggested_action": "Keep only one repetition.",
                    }
                ]
            }
            model = {
                "decisions": [
                    {
                        "issue_index": 0,
                        "verdict": "withdraw",
                        "evidence": [guards["G-STYLE-001"]],
                        "guard_ids": ["G-STYLE-001"],
                        "reason": "The registered author guard requires all three beats.",
                        "authority": "model",
                    }
                ]
            }
            filtered, verification = apply_preservation_verification(review, model, author_guards=guards)
            self.assertEqual(verification["withdrawn_count"], 1)
            self.assertEqual(verification["authorized_guard_count"], 1)
            self.assertEqual(filtered["issues"], [])

            retired = self.run_cli(
                "agent",
                "guard",
                "retire",
                str(project),
                "--id",
                "G-STYLE-001",
                "--reason",
                "该仪式段已从当前版本删除。",
                "--format",
                "json",
            )
            self.assertEqual(json.loads(retired.stdout)["guards"][0]["status"], "retired")
            self.assertEqual(active_author_guards(project), {})

    def test_semantic_pass_cannot_override_missing_required_metric_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "verification.json").write_text(
                json.dumps(
                    {
                        "checks": [],
                        "metric_deltas": {
                            "prose.exclusionary_narration": {
                                "before_count": 35,
                                "after_count": 35,
                                "before_severity": "P2",
                                "after_severity": "P2",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "session.json").write_text(json.dumps({"state": "verifying"}), encoding="utf-8")
            (run_dir / "comprehensive_review.json").write_text(
                json.dumps(
                    {
                        "issues": [
                            {
                                "severity": "P2",
                                "metric_keys": ["prose.exclusionary_narration"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            semantic = {
                "verdict": "pass",
                "invariants": [
                    {"name": name, "status": "pass", "evidence": "model claims it is fixed"}
                    for name in (
                        "plot_events",
                        "point_of_view",
                        "chronology",
                        "character_intentions",
                        "information_boundaries",
                        "ambiguity_and_withholding",
                        "review_findings_addressed",
                    )
                ],
                "summary": "The model reports success.",
            }
            verification = merge_semantic_verification(run_dir, semantic)
            self.assertFalse(verification["ready_for_approval"])
            self.assertIn("review_metric_progress_consistent", verification["blocking_failures"])

    def test_audit_continuity_detects_standard_project_gaps(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = build_continuity_report(
                target,
                pattern="**/*.md",
                skip_standard=False,
                min_chapter_chars=200,
            )
            self.assertEqual(report.chapter_count, 1)
            self.assertEqual(report.missing_standard_files, 0)
            self.assertGreater(report.placeholder_standard_files, 0)
            self.assertEqual(report.missing_engine_count, 0)
            self.assertEqual(report.missing_retrospective_count, 1)
            self.assertEqual(report.placeholder_chapters, 1)

    def test_audit_echoes_parses_table_and_scans_text(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_echo_table(target)
            self.write_filled_information_table(target)
            self.write_long_chapter_with_echo(target)

            report = build_echo_report(
                target,
                pattern="**/*.md",
                table_path=None,
                scan_text=True,
                stale_after=8,
            )
            self.assertEqual(report.thread_count, 1)
            self.assertEqual(report.threads[0].text_hits, 6)
            self.assertEqual(report.issues, [])

    def test_audit_info_reports_boundary_table_and_text_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            canon = target / "05_canon"
            chapters = target / "06_drafts" / "book_01" / "chapters"
            canon.mkdir(parents=True)
            chapters.mkdir(parents=True)
            (canon / "information_release_table.md").write_text(
                textwrap.dedent(
                    """\
                    # Information Release Table

                    | Info / Secret | Author Truth | Reader Current | Character A Knows | Public Version | Official Version | Next Release | Do Not Reveal |
                    | --- | --- | --- | --- | --- | --- | --- | --- |
                    | Imperial Blood | Heir truth | Reader knows only a rumor | No one reliable | Tavern myth | Court denial | ch_010 | Imperial Blood |
                    """
                ),
                encoding="utf-8",
            )
            (chapters / "ch_001.md").write_text(
                "# Chapter\n\nSomeone whispered Imperial Blood before the court could bury the words.",
                encoding="utf-8",
            )

            report = build_info_report(target, pattern="**/*.md", table_path=None, scan_text=True)
            self.assertEqual(report.item_count, 1)
            self.assertEqual(report.items[0].text_hits, 2)
            codes = {issue.code for issue in report.issues}
            self.assertIn("forbidden_text_hit", codes)
            self.assertIn("early_text_hit_before_release", codes)

    def test_audit_info_cli_outputs_json(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_information_table(target)
            result = self.run_cli("audit-info", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["item_count"], 1)
            self.assertEqual(data["table_files"][0].replace("\\", "/"), "05_canon/information_release_table.md")

    def test_audit_characters_reports_missing_and_filled_profiles(self) -> None:
        temp, target = self.make_project()
        with temp:
            default_report = build_character_audit_report(target, pattern="**/*.md")
            default_codes = {issue.code for issue in default_report.issues}
            self.assertIn("missing_character_arcs", default_codes)
            self.assertIn("no_character_index_rows", default_codes)

            self.write_filled_character_files(target)
            clean_report = build_character_audit_report(target, pattern="**/*.md")
            self.assertEqual(clean_report.character_count, 1)
            self.assertEqual(clean_report.arc_count, 1)
            self.assertEqual(clean_report.index_count, 1)
            self.assertEqual(clean_report.intelligence_count, 1)
            self.assertEqual(clean_report.voice_count, 1)
            self.assertEqual(clean_report.issues, [])

    def test_audit_characters_cli_outputs_json(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_character_files(target)
            result = self.run_cli("audit-characters", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["character_count"], 1)
            self.assertEqual(data["characters"][0]["character"], "Tester")
            self.assertEqual(data["issues"], [])

    def test_agent_prompt_builds_role_prompt_with_context(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = build_agent_prompt(
                target,
                role="draft-writer",
                chapter="001",
                include_context=True,
                include_context_content=False,
            )

            self.assertEqual(report.role, "draft-writer")
            self.assertEqual(report.task, "draft")
            self.assertEqual(report.chapter, "001")
            self.assertIn("Draft Writer 正文写手", report.prompt)
            self.assertIn("## Must Not", report.prompt)
            self.assertIsNotNone(report.context_pack)
            self.assertEqual(report.context_pack.task, "draft")
            self.assertFalse(report.context_pack.include_content)

    def test_agent_prompt_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli(
                "agent-prompt",
                str(target),
                "--role",
                "info-boundary-auditor",
                "--task",
                "review",
                "--chapter",
                "001",
                "--include-context",
                "--include-context-content",
                "--max-total-chars",
                "180",
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["role"], "info-boundary-auditor")
            self.assertEqual(data["task"], "review")
            self.assertIn("Info Boundary Auditor", data["prompt"])
            self.assertEqual(data["context_pack"]["task"], "review")
            self.assertLessEqual(data["context_pack"]["included_total_chars"], 180)

            output = "00_management/agent_prompt.md"
            written = self.run_cli(
                "agent-prompt",
                str(target),
                "--role",
                "draft-writer",
                "--chapter",
                "001",
                "--out",
                output,
            )
            self.assertIn("Wrote FictionOps agent prompt", written.stdout)
            output_path = target / output
            self.assertTrue(output_path.exists())
            self.assertIn("# FictionOps Agent Prompt", output_path.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "agent-prompt",
                str(target),
                "--role",
                "draft-writer",
                "--chapter",
                "001",
                "--out",
                output,
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_agent_run_prepares_bundle_without_calling_model(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_model_config_report(
                target,
                provider="local",
                planning_model="plan-model",
                drafting_model="draft-model",
                audit_model="audit-model",
                write=True,
            )
            report = build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/ch_001",
                include_context_content=False,
            )
            self.assertEqual(report.execution_mode, "prepare_only")
            self.assertTrue(report.written)
            self.assertEqual(report.role, "draft-writer")
            self.assertEqual(report.task, "draft")
            self.assertEqual(report.model, "draft-model")
            self.assertIsNotNone(report.draft_brief)
            self.assertGreaterEqual(report.file_count, 5)
            bundle_dir = target / "00_management" / "agent_runs" / "ch_001"
            self.assertTrue((bundle_dir / "README.md").exists())
            self.assertTrue((bundle_dir / "request.json").exists())
            self.assertTrue((bundle_dir / "prompt.md").exists())
            self.assertTrue((bundle_dir / "context_pack.md").exists())
            self.assertTrue((bundle_dir / "draft_brief.md").exists())
            request = json.loads((bundle_dir / "request.json").read_text(encoding="utf-8"))
            self.assertFalse(request["safety"]["calls_model"])
            self.assertFalse(request["safety"]["overwrites_manuscript"])

            result = self.run_cli(
                "agent-run",
                str(target),
                "--role",
                "info-boundary-auditor",
                "--task",
                "review",
                "--chapter",
                "001",
                "--out-dir",
                "00_management/agent_runs/review_001",
                "--no-context-content",
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["role"], "info-boundary-auditor")
            self.assertEqual(data["task"], "review")
            self.assertEqual(data["execution_mode"], "prepare_only")
            self.assertEqual(data["model"], "audit-model")
            self.assertTrue((target / "00_management" / "agent_runs" / "review_001" / "request.json").exists())

            failed = self.run_cli(
                "agent-run",
                str(target),
                "--role",
                "info-boundary-auditor",
                "--task",
                "review",
                "--chapter",
                "001",
                "--out-dir",
                "00_management/agent_runs/review_001",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_agent_connect_writes_connector_handshake_kit(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_model_config_report(
                target,
                provider="openai",
                planning_model="plan-model",
                drafting_model="draft-model",
                audit_model="audit-model",
                api_key_env="OPENAI_API_KEY",
                write=True,
            )
            dry = build_agent_connect(target, name="OpenAI Local", mode="model-runner", dry_run=True)
            self.assertEqual(dry.connector_name, "openai-local")
            self.assertEqual(dry.mode, "model-runner")
            self.assertEqual(dry.written, False)
            self.assertEqual(dry.manifest["schema"], "fictionops.agent_connector.v1")
            self.assertTrue(dry.safety["staged_output_required"])

            report = build_agent_connect(target, name="OpenAI Local", mode="model-runner")
            self.assertEqual(report.written, True)
            kit_dir = target / "00_management" / "agent_connectors" / "openai-local"
            manifest_path = kit_dir / "connector_manifest.json"
            self.assertTrue(manifest_path.exists())
            self.assertTrue((kit_dir / "README.md").exists())
            self.assertTrue((kit_dir / ".env.example").exists())
            self.assertTrue((kit_dir / "smoke_commands.md").exists())
            self.assertTrue((kit_dir / "runner_adapter.py").exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "model-runner")
            self.assertIn("agent-exec", manifest["allowed_fictionops_commands"])
            self.assertIn("OPENAI_API_KEY", (kit_dir / ".env.example").read_text(encoding="utf-8"))

            failed = self.run_cli("agent-connect", str(target), "--name", "OpenAI Local", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

            cli = self.run_cli(
                "agent-connect",
                str(target),
                "--name",
                "OpenAI Local",
                "--mode",
                "controller",
                "--force",
                "--format",
                "json",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["connector_name"], "openai-local")
            self.assertEqual(data["mode"], "controller")
            self.assertEqual(data["written"], True)
            self.assertTrue(data["safety"]["connector_may_execute_safe_commands"])

    def test_agent_smoke_runs_connector_stub_through_inbox(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_connect(target, name="local-runner", mode="runner")

            dry = build_agent_smoke(target, connector="local-runner", dry_run=True)
            self.assertEqual(dry.status, "dry_run")
            self.assertTrue(dry.ready)
            self.assertEqual(dry.level, "runner")
            self.assertEqual(dry.agent_run, None)

            report = build_agent_smoke(target, connector="local-runner")
            self.assertEqual(report.status, "smoke_passed")
            self.assertTrue(report.ready)
            self.assertTrue(report.written)
            self.assertIsNotNone(report.agent_run)
            self.assertIsNotNone(report.agent_exec)
            self.assertIsNotNone(report.inbox)
            run_dir = target / "00_management" / "agent_runs" / "local-runner_smoke_ch_001"
            self.assertTrue((run_dir / "request.json").exists())
            self.assertTrue((run_dir / "output.md").exists())
            self.assertTrue((run_dir / "execution.json").exists())
            self.assertEqual(report.inbox.status, "ready_for_review")

            rerun = build_agent_smoke(target, connector="local-runner", force=True)
            self.assertEqual(rerun.status, "smoke_passed")
            self.assertTrue(any(item.name == "force-current-smoke-run" for item in rerun.steps))

        cli_temp, cli_target = self.make_project()
        with cli_temp:
            build_agent_connect(cli_target, name="local-runner", mode="runner")
            cli = self.run_cli(
                "agent-smoke",
                str(cli_target),
                "--connector",
                "local-runner",
                "--format",
                "json",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["status"], "smoke_passed")
            self.assertEqual(data["connector_name"], "local-runner")
            self.assertEqual(data["inbox"]["status"], "ready_for_review")

    def test_api_agent_server_builds_staged_session_with_echo_runner(self) -> None:
        module_path = ROOT / "integrations" / "api-agent" / "server.py"
        spec = importlib.util.spec_from_file_location("fictionops_api_agent_server", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        temp, target = self.make_project()
        with temp:
            payload = {
                "project_path": str(target),
                "goal": "Write chapter 001 and stage the result for review.",
                "book": "book_01",
                "chapter": "001",
                "role": "draft-writer",
                "runner_command": [sys.executable, str(ROOT / "examples" / "agent_runner_echo.py")],
                "out_dir": "00_management/agent_runs/api_ch_001",
                "force": True,
                "acceptance_mode": "human_governed",
            }
            session = module.build_session(payload, task="draft")

            self.assertEqual(session["status"], "waiting_for_review")
            self.assertEqual(session["stop_reason"], "staged_output_ready_for_review")
            self.assertEqual(len(session["staged_outputs"]), 1)
            output = Path(session["staged_outputs"][0]["output_file"])
            self.assertTrue(output.exists())
            self.assertIn(session["session_id"], module.SESSIONS)

            decided = module.update_session_decision(session["session_id"], {"decision": "reject", "notes": "smoke"})
            self.assertEqual(decided["status"], "completed")
            self.assertEqual(decided["human_decision"]["decision"], "reject")

            chapter = target / "closed_loop_chapter.md"
            engine = target / "closed_loop_engine.md"
            engine.write_text("# Closed Loop Chapter\n\n- target chars: 200\n", encoding="utf-8")
            closed_loop = module.build_session(
                {
                    "project_path": str(target),
                    "goal": "Prepare a canonical closed-loop chapter run.",
                    "chapter_file": str(chapter),
                    "engine_file": str(engine),
                    "runtime_mode": "closed_loop",
                    "dry_run": True,
                    "acceptance_mode": "human_governed",
                },
                task="draft",
            )
            self.assertEqual(closed_loop["api_version"], "1.0")
            self.assertEqual(closed_loop["metrics"]["runtime_mode"], "closed_loop")
            self.assertEqual(closed_loop["runtime_report"]["api_version"], "1.0")
            self.assertEqual(closed_loop["runtime_report"]["command"], "agent-write-workflow")

    def test_ai_first_chapter_commands_stage_or_prepare_outputs(self) -> None:
        temp, target = self.make_project()
        with temp:
            runner = ROOT / "examples" / "agent_runner_echo.py"
            write = self.run_cli(
                "write-chapter",
                str(target),
                "--chapter",
                "001",
                "--out-dir",
                "00_management/agent_runs/write_cli_ch_001",
                "--force",
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
            )
            write_data = json.loads(write.stdout)
            self.assertEqual(write_data["command"], "write-chapter")
            self.assertEqual(write_data["role"], "draft-writer")
            self.assertEqual(write_data["task"], "draft")
            self.assertEqual(write_data["stop_reason"], "staged_output_ready_for_review")
            self.assertEqual(write_data["ready_count"], 1)
            self.assertTrue((target / "00_management" / "agent_runs" / "write_cli_ch_001" / "output.md").exists())

            revise = self.run_cli(
                "revise-chapter",
                str(target),
                "--chapter",
                "001",
                "--out-dir",
                "00_management/agent_runs/revise_cli_ch_001",
                "--force",
                "--format",
                "json",
            )
            revise_data = json.loads(revise.stdout)
            self.assertEqual(revise_data["command"], "revise-chapter")
            self.assertEqual(revise_data["role"], "style-auditor")
            self.assertEqual(revise_data["task"], "review")
            self.assertEqual(revise_data["stop_reason"], "agent_run_ready_for_runner")

            audit = self.run_cli(
                "audit-chapter",
                str(target),
                "--chapter",
                "001",
                "--out-dir",
                "00_management/agent_runs/audit_cli_ch_001",
                "--force",
                "--format",
                "json",
            )
            audit_data = json.loads(audit.stdout)
            self.assertEqual(audit_data["command"], "audit-chapter")
            self.assertEqual(audit_data["role"], "info-boundary-auditor")
            self.assertEqual(audit_data["task"], "review")

    def test_agent_session_tracks_multistep_writing_workflow(self) -> None:
        temp, target = self.make_project()
        with temp:
            session = build_agent_session(
                target,
                book="book_01",
                chapter="001",
                goal="Draft, revise, and audit chapter 001.",
                session_id="demo-session",
            )
            session_dir = target / "00_management" / "agent_sessions" / "demo-session"
            self.assertEqual(session.status, "planned")
            self.assertEqual(session.step_count, 3)
            self.assertTrue((session_dir / "session.json").exists())
            self.assertTrue((session_dir / "README.md").exists())
            self.assertIn("write-chapter", session.steps[0].next_command)

            runner = ROOT / "examples" / "agent_runner_echo.py"
            self.run_cli(
                "write-chapter",
                str(target),
                "--chapter",
                "001",
                "--out-dir",
                "00_management/agent_runs/demo-session_write_book_01_ch_001",
                "--force",
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
            )
            updated = self.run_cli(
                "agent-session",
                str(target),
                "--book",
                "book_01",
                "--chapter",
                "001",
                "--goal",
                "Draft, revise, and audit chapter 001.",
                "--session-id",
                "demo-session",
                "--force",
                "--format",
                "json",
            )
            data = json.loads(updated.stdout)
            self.assertEqual(data["schema"], "fictionops.agent_session.v1")
            self.assertEqual(data["status"], "waiting_for_review")
            self.assertEqual(data["ready_count"], 1)
            self.assertEqual(data["steps"][0]["status"], "ready_for_review")
            self.assertIn("agent-inbox", data["next_actions"][0])

    def test_agent_session_status_prioritizes_terminal_completion(self) -> None:
        steps = [
            AgentSessionStep(
                stage="write",
                command="write-chapter",
                role="draft-writer",
                task="draft",
                run_dir="00_management/agent_runs/demo_write",
                status="completed",
                next_command="fictionops write-chapter .",
            ),
            AgentSessionStep(
                stage="revise",
                command="revise-chapter",
                role="style-auditor",
                task="review",
                run_dir="00_management/agent_runs/demo_revise",
                status="completed",
                next_command="fictionops revise-chapter .",
            ),
        ]
        self.assertEqual(session_status(steps), "completed")

    def test_agent_exec_runs_external_runner_into_staging_output(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "ch_001"

            dry = build_agent_exec(
                run_dir,
                command=[sys.executable, "-c", "raise SystemExit(7)"],
                dry_run=True,
            )
            self.assertEqual(dry.executed, False)
            self.assertEqual(dry.written, False)
            self.assertFalse((run_dir / "output.md").exists())

            report = build_agent_exec(
                run_dir,
                command=[
                    sys.executable,
                    "-c",
                    "import json, sys; data = sys.stdin.read(); receipt={'schema':'fictionops.runner_receipt.v1','provider':'test','model':'test-model','request_id':'req-123','usage':{'input_tokens':11,'output_tokens':7,'total_tokens':18},'cost':{'currency':'USD','total':0.0003}}; print('FICTIONOPS_RUNNER_RECEIPT:'+json.dumps(receipt), file=sys.stderr); print('# Runner Output'); print('has prompt', 'FictionOps' in data)",
                ],
            )
            self.assertEqual(report.executed, True)
            self.assertEqual(report.written, True)
            self.assertEqual(report.returncode, 0)
            self.assertGreater(report.input_chars, 0)
            self.assertEqual(report.telemetry["request_id"], "req-123")
            self.assertEqual(report.telemetry["usage"]["total_tokens"], 18)
            self.assertIn("has prompt True", (run_dir / "output.md").read_text(encoding="utf-8"))
            self.assertTrue((run_dir / "execution.json").exists())
            receipt = json.loads((run_dir / "execution.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["telemetry"]["cost"]["total"], 0.0003)

            ready = build_agent_inbox(target)
            self.assertEqual(ready.status, "ready_for_review")
            self.assertEqual(ready.runs[0].output_file, str(run_dir / "output.md"))

            failed = self.run_cli(
                "agent-exec",
                str(run_dir),
                "--format",
                "json",
                "--runner",
                sys.executable,
                "-c",
                "print('should not overwrite')",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

            cli = self.run_cli(
                "agent-exec",
                str(run_dir),
                "--force",
                "--format",
                "json",
                "--runner",
                sys.executable,
                "-c",
                "import sys; sys.stdin.read(); print('# CLI Output')",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["written"], True)
            self.assertEqual(data["safety"]["requires_human_apply"], True)
            self.assertIn("# CLI Output", (run_dir / "output.md").read_text(encoding="utf-8"))

    def test_agent_exec_example_runner_is_usable(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "ch_001"
            runner = ROOT / "examples" / "agent_runner_echo.py"

            cli = self.run_cli(
                "agent-exec",
                str(run_dir),
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["written"], True)
            self.assertEqual(data["returncode"], 0)

            output = (run_dir / "output.md").read_text(encoding="utf-8")
            self.assertIn("# Echo Agent Staging Output", output)
            self.assertIn("- Role: `draft-writer`", output)
            self.assertIn("- Task: `draft`", output)

            ready = build_agent_inbox(target)
            self.assertEqual(ready.status, "ready_for_review")

    def test_openai_responses_runner_dry_run_is_usable(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/openai_ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "openai_ch_001"
            runner = ROOT / "examples" / "agent_runner_openai_responses.py"

            cli = self.run_cli(
                "agent-exec",
                str(run_dir),
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
                "--dry-run",
                "--model",
                "fictionops-test-model",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["written"], True)
            self.assertEqual(data["returncode"], 0)

            output = (run_dir / "output.md").read_text(encoding="utf-8")
            self.assertIn("# OpenAI Responses Runner Dry Run", output)
            self.assertIn("- Role: `draft-writer`", output)
            self.assertIn("- Model: `fictionops-test-model`", output)
            self.assertIn("No network request was made", output)

            ready = build_agent_inbox(target)
            self.assertEqual(ready.status, "ready_for_review")

    def test_openai_compatible_chat_runner_retries_transient_transport_failure(self) -> None:
        runner = ROOT / "examples" / "agent_runner_openai_chat.py"
        spec = importlib.util.spec_from_file_location("fictionops_chat_runner_retry_test", runner)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "recovered"}}]}).encode("utf-8")

        with mock.patch.object(
            module.urllib.request,
            "urlopen",
            side_effect=[module.urllib.error.URLError("temporary reset"), Response()],
        ) as opened:
            output, receipt = module.call_chat_completions(
                payload="bundle",
                model="test-model",
                api_key="secret",
                base_url="https://example.invalid/v1",
                timeout=1,
                max_tokens=10,
                temperature=0.2,
                max_output_chars=100,
                retries=1,
                retry_backoff=0,
                provider="test-provider",
                input_cost_per_million=1.0,
                output_cost_per_million=2.0,
                currency="USD",
            )
        self.assertEqual(output, "recovered")
        self.assertEqual(receipt["provider"], "test-provider")
        self.assertEqual(receipt["usage"], {})
        self.assertEqual(receipt["cost"]["total"], 0.0)
        self.assertEqual(opened.call_count, 2)

    def test_openai_compatible_chat_runner_dry_run_is_usable(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/chat_ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "chat_ch_001"
            runner = ROOT / "examples" / "agent_runner_openai_chat.py"

            cli = self.run_cli(
                "agent-exec",
                str(run_dir),
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
                "--dry-run",
                "--model",
                "deepseek-test-model",
                "--api-key-env",
                "DEEPSEEK_API_KEY",
                "--base-url",
                "https://api.deepseek.com",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["written"], True)
            self.assertEqual(data["returncode"], 0)

            output = (run_dir / "output.md").read_text(encoding="utf-8")
            self.assertIn("# OpenAI-Compatible Chat Runner Dry Run", output)
            self.assertIn("- Role: `draft-writer`", output)
            self.assertIn("- Provider: `openai-chat`", output)
            self.assertIn("- Model: `deepseek-test-model`", output)
            self.assertIn("- Endpoint: `https://api.deepseek.com/chat/completions`", output)
            self.assertIn("- API key env: `DEEPSEEK_API_KEY`", output)
            self.assertIn("No network request was made", output)

            ready = build_agent_inbox(target)
            self.assertEqual(ready.status, "ready_for_review")

    def test_openai_compatible_chat_runner_provider_preset_is_usable(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/chat_ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "chat_ch_001"
            runner = ROOT / "examples" / "agent_runner_openai_chat.py"

            cli = self.run_cli(
                "agent-exec",
                str(run_dir),
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
                "--dry-run",
                "--provider",
                "deepseek",
                "--model",
                "deepseek-chat",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["written"], True)
            self.assertEqual(data["returncode"], 0)

            output = (run_dir / "output.md").read_text(encoding="utf-8")
            self.assertIn("- Provider: `deepseek`", output)
            self.assertIn("- Model: `deepseek-chat`", output)
            self.assertIn("- Endpoint: `https://api.deepseek.com/chat/completions`", output)
            self.assertIn("- API key env: `DEEPSEEK_API_KEY`", output)

    def test_openai_compatible_chat_runner_env_file_and_local_preset_are_usable(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/local_ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "local_ch_001"
            (run_dir / "runner.env").write_text("FICTIONOPS_CHAT_MODEL=local-test-model\n", encoding="utf-8")
            runner = ROOT / "examples" / "agent_runner_openai_chat.py"

            cli = self.run_cli(
                "agent-exec",
                str(run_dir),
                "--format",
                "json",
                "--runner",
                sys.executable,
                str(runner),
                "--dry-run",
                "--provider",
                "local-openai",
                "--env-file",
                "runner.env",
                "--max-output-chars",
                "12000",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["written"], True)
            self.assertEqual(data["returncode"], 0)

            output = (run_dir / "output.md").read_text(encoding="utf-8")
            self.assertIn("- Provider: `local-openai`", output)
            self.assertIn("- Model: `local-test-model`", output)
            self.assertIn("- Endpoint: `http://127.0.0.1:8000/v1/chat/completions`", output)
            self.assertIn("- API key env: `<none for local/no-auth provider>`", output)
            self.assertIn("- Max output chars: 12000", output)

    def test_agent_inbox_tracks_staged_agent_outputs(self) -> None:
        temp, target = self.make_project()
        with temp:
            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "ch_001"

            awaiting = build_agent_inbox(target)
            self.assertEqual(awaiting.status, "awaiting_output")
            self.assertEqual(awaiting.run_count, 1)
            self.assertEqual(awaiting.runs[0].state, "awaiting_output")
            self.assertEqual(awaiting.runs[0].issues[0].code, "missing_output")

            (run_dir / "output.md").write_text("# Agent Draft\n\nA staged chapter draft.\n", encoding="utf-8")
            ready = build_agent_inbox(target)
            self.assertEqual(ready.status, "ready_for_review")
            self.assertEqual(ready.ready_count, 1)
            self.assertEqual(ready.runs[0].output_file, str(run_dir / "output.md"))
            self.assertGreater(ready.runs[0].output_chars, 0)
            self.assertTrue(any("post-draft" in action for action in ready.runs[0].next_actions))

            cli_ready = self.run_cli("agent-inbox", str(run_dir), "--format", "json")
            data = json.loads(cli_ready.stdout)
            self.assertEqual(data["mode"], "run_dir")
            self.assertEqual(data["runs"][0]["state"], "ready_for_review")

            (run_dir / "response.md").write_text("Second candidate.\n", encoding="utf-8")
            ambiguous = build_agent_inbox(target)
            self.assertEqual(ambiguous.status, "needs_attention")
            self.assertTrue(any(item.code == "ambiguous_output" for item in ambiguous.issues))
            doctor = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=["没有"],
                top=5,
                min_repeat=2,
                scan_text=False,
                stale_after=8,
            )
            self.assertEqual(doctor.agent_inbox["enabled"], True)
            self.assertEqual(doctor.agent_inbox["status"], "needs_attention")
            self.assertGreaterEqual(doctor.agent_inbox["issues"], 1)
            self.assertTrue(any("agent inbox" in item.lower() for item in doctor.recommendations))

            selected = self.run_cli("agent-inbox", str(target), "--output-name", "output.md", "--format", "json")
            selected_data = json.loads(selected.stdout)
            self.assertEqual(selected_data["status"], "ready_for_review")
            self.assertEqual(selected_data["runs"][0]["output_file"], str(run_dir / "output.md"))

    def test_agent_next_selects_safe_controller_step(self) -> None:
        package_report = build_agent_next(ROOT)
        self.assertEqual(package_report.status, "needs_human_review")
        self.assertEqual(package_report.candidates[0].stage, "stable-core")
        self.assertIn("audit-dogfood-cycle", package_report.selected_command)
        self.assertIn(str(ROOT), package_report.selected_command)
        self.assertNotIn("audit-dogfood-cycle . --file", package_report.selected_command)
        self.assertEqual(package_report.evidence["fictionops_package"], True)
        self.assertNotIn("release-trial-evidence", package_report.evidence["stable_core_action_items"])
        self.assertIn("sustained-dogfood-cycle", package_report.evidence["stable_core_action_items"])
        package_cli = self.run_cli("agent-next", str(ROOT.relative_to(ROOT.parent)), "--format", "json")
        package_cli_data = json.loads(package_cli.stdout)
        self.assertEqual(package_cli_data["candidates"][0]["stage"], "stable-core")
        self.assertIn(str(ROOT), package_cli_data["selected_command"])
        self.assertNotIn("audit-dogfood-cycle fictionops --file", package_cli_data["selected_command"])

        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            legacy.mkdir()
            (legacy / "outline.md").write_text("# Old Outline\n", encoding="utf-8")
            legacy_report = build_agent_next(legacy)
            self.assertEqual(legacy_report.status, "ready_for_agent_step")
            self.assertIn("fictionops adopt", legacy_report.selected_command)
            self.assertEqual(legacy_report.candidates[0].stage, "migration")

        temp, target = self.make_project()
        with temp:
            chapter_report = build_agent_next(target, chapter="007", scan_text=False)
            self.assertEqual(chapter_report.status, "ready_for_agent_step")
            self.assertIn("new-chapter", chapter_report.selected_command)
            self.assertEqual(chapter_report.chapter, "007")

            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/ch_001",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "ch_001"
            (run_dir / "output.md").write_text("# Staged Draft\n\nNeeds review.\n", encoding="utf-8")

            inbox_report = build_agent_next(target, chapter="001", scan_text=False)
            self.assertEqual(inbox_report.status, "needs_human_review")
            self.assertIn("agent-inbox", inbox_report.selected_command)
            self.assertTrue(inbox_report.candidates[0].requires_human_review)

            cli = self.run_cli("agent-next", str(target), "--chapter", "001", "--no-text-scan", "--format", "json")
            data = json.loads(cli.stdout)
            self.assertEqual(data["status"], "needs_human_review")
            self.assertIn("selected_command", data)
            self.assertEqual(data["candidates"][0]["stage"], "agent-inbox")

            controller = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_next.py"),
                    str(target),
                    "--chapter",
                    "001",
                    "--no-text-scan",
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(CLI),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            controller_data = json.loads(controller.stdout)
            self.assertEqual(controller_data["selected_command"], data["selected_command"])
            self.assertEqual(controller_data["candidates"][0]["requires_human_review"], True)

    def test_eval_agent_generates_reproducible_agent_harness_report(self) -> None:
        fixture = ROOT / "examples" / "demo_novel"
        report = build_agent_evaluation(fixture, chapter="002")
        self.assertEqual(report.status, "pass")
        self.assertTrue(report.ready)
        self.assertEqual(report.runner, "echo")
        self.assertIn("T1", report.task_ids)
        self.assertEqual(report.observations["agent_inbox_ready_count"], 1)
        self.assertEqual(report.observations["controller_stop_reason"], "human_review_boundary")
        self.assertTrue(str(report.fixture_copy).endswith("(deleted after run)"))
        metric_names = {item.name for item in report.metrics}
        self.assertIn("staged_output_rate", metric_names)
        self.assertIn("controller_step_validity", metric_names)

        cli = self.run_cli("eval-agent", str(fixture), "--chapter", "002", "--format", "json")
        data = json.loads(cli.stdout)
        self.assertEqual(data["status"], "pass")
        self.assertTrue(data["ready"])
        self.assertEqual(data["observations"]["controller_stop_reason"], "human_review_boundary")
        self.assertIn("<temporary fixture copy>", data["commands"][0])

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "eval.md"
            written = self.run_cli("eval-agent", str(fixture), "--chapter", "002", "--out", str(out))
            self.assertIn("Wrote FictionOps agent evaluation report", written.stdout)
            self.assertTrue(out.exists())
            self.assertIn("# FictionOps Agent Evaluation Report", out.read_text(encoding="utf-8"))

            failed = self.run_cli("eval-agent", str(fixture), "--chapter", "002", "--out", str(out), check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_agent_workflow_audit_checks_agent_boundaries(self) -> None:
        package_report = build_agent_workflow_audit(ROOT, level="controller")
        self.assertEqual(package_report.status, "needs_human_review")
        self.assertFalse(package_report.ready)
        self.assertEqual(package_report.evidence["fictionops_package"], True)
        self.assertEqual(package_report.evidence["standard_project"], False)
        self.assertEqual(package_report.evidence["agent_next_selected_stage"], "stable-core")
        self.assertEqual(package_report.evidence["agent_next_requires_human_review"], True)
        self.assertIn(str(ROOT), package_report.evidence["agent_next_selected_command"])
        self.assertTrue(any(item.code == "stable_core_human_review_boundary" for item in package_report.issues))
        self.assertFalse(any(item.code == "not_standard_project" for item in package_report.issues))

        package_cli = self.run_cli("audit-agent-workflow", str(ROOT), "--level", "controller", "--format", "json")
        package_data = json.loads(package_cli.stdout)
        self.assertEqual(package_data["status"], "needs_human_review")
        self.assertEqual(package_data["evidence"]["fictionops_package"], True)
        self.assertEqual(package_data["evidence"]["agent_next_selected_stage"], "stable-core")

        temp, target = self.make_project()
        with temp:
            runner_report = build_agent_workflow_audit(target, level="runner")
            self.assertEqual(runner_report.status, "ready")
            self.assertTrue(runner_report.ready)
            self.assertEqual(runner_report.evidence["agent_inbox_status"], "no_runs")

            missing_connector = build_agent_workflow_audit(target, level="runner", connector="local-runner")
            self.assertEqual(missing_connector.status, "not_ready")
            self.assertFalse(missing_connector.ready)
            self.assertTrue(any(item.code == "connector_kit_incomplete" for item in missing_connector.issues))

            build_agent_connect(target, name="local-runner", mode="runner")
            connector_report = build_agent_workflow_audit(target, level="runner", connector="local-runner")
            self.assertEqual(connector_report.status, "ready")
            self.assertTrue(connector_report.ready)
            self.assertEqual(connector_report.evidence["connector_name"], "local-runner")
            self.assertEqual(connector_report.evidence["connector_manifest_schema"], "fictionops.agent_connector.v1")
            self.assertEqual(connector_report.evidence["connector_manifest_mode"], "runner")

            cli = self.run_cli("audit-agent-workflow", str(target), "--level", "runner", "--format", "json")
            data = json.loads(cli.stdout)
            self.assertEqual(data["status"], "ready")
            self.assertEqual(data["level"], "runner")

            connector_cli = self.run_cli(
                "audit-agent-workflow",
                str(target),
                "--level",
                "runner",
                "--connector",
                "local-runner",
                "--format",
                "json",
            )
            connector_data = json.loads(connector_cli.stdout)
            self.assertEqual(connector_data["status"], "ready")
            self.assertEqual(connector_data["evidence"]["connector_name"], "local-runner")

            model_report = build_agent_workflow_audit(target, level="model-runner")
            self.assertEqual(model_report.status, "not_ready")
            self.assertFalse(model_report.ready)
            self.assertTrue(any(item.code == "provider_not_configured" for item in model_report.issues))

            build_model_config_report(
                target,
                provider="local",
                planning_model="plan-model",
                drafting_model="draft-model",
                audit_model="audit-model",
                write=True,
            )
            configured_model = build_agent_workflow_audit(target, level="model-runner")
            self.assertEqual(configured_model.status, "ready")
            self.assertTrue(configured_model.ready)

            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/ch_001_review",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "ch_001_review"
            (run_dir / "output.md").write_text("# Staged Draft\n\nNeeds review.\n", encoding="utf-8")

            review_boundary = build_agent_workflow_audit(target, level="controller", chapter="001")
            self.assertEqual(review_boundary.status, "needs_human_review")
            self.assertFalse(review_boundary.ready)
            self.assertTrue(any(item.code == "agent_output_waiting_for_review" for item in review_boundary.issues))

    def test_agent_controller_loop_executes_safe_steps_and_stops_at_boundaries(self) -> None:
        temp, target = self.make_project()
        with temp:
            log_file = target / "00_management" / "agent_runs" / "controller_loop.jsonl"
            controller = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_loop.py"),
                    str(target),
                    "--chapter",
                    "009",
                    "--no-text-scan",
                    "--max-steps",
                    "3",
                    "--log",
                    str(log_file),
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(CLI),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            data = json.loads(controller.stdout)
            self.assertEqual(data["stop_reason"], "repeated_command")
            self.assertEqual(data["steps_executed"], 2)
            self.assertEqual(data["steps"][0]["action"], "execute")
            self.assertIn("new-chapter", data["steps"][0]["selected_command"])
            self.assertIn("review-gate", data["steps"][1]["selected_command"])
            self.assertTrue((target / "06_drafts" / "book_01" / "chapters" / "ch_009.md").exists())
            self.assertTrue(log_file.exists())
            log_lines = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(log_lines), data["steps_seen"])
            self.assertEqual(log_lines[-1]["stop_reason"], "repeated_command")

            build_agent_run(
                target,
                role="draft-writer",
                chapter="001",
                out_dir="00_management/agent_runs/ch_001_boundary",
                include_context_content=False,
            )
            run_dir = target / "00_management" / "agent_runs" / "ch_001_boundary"
            (run_dir / "output.md").write_text("# Staged Draft\n\nNeeds review.\n", encoding="utf-8")
            boundary = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_loop.py"),
                    str(target),
                    "--chapter",
                    "001",
                    "--no-text-scan",
                    "--max-steps",
                    "2",
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(CLI),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            boundary_data = json.loads(boundary.stdout)
            self.assertEqual(boundary_data["stop_reason"], "human_review_boundary")
            self.assertEqual(boundary_data["steps_executed"], 0)
            self.assertEqual(boundary_data["steps"][0]["candidate_stage"], "agent-inbox")

    def test_agent_controller_loop_handles_placeholder_and_migration_states(self) -> None:
        package_boundary = subprocess.run(
            [
                sys.executable,
                str(ROOT / "examples" / "agent_controller_loop.py"),
                str(ROOT),
                "--max-steps",
                "2",
                "--format",
                "json",
                "--cli",
                sys.executable,
                str(CLI),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        package_data = json.loads(package_boundary.stdout)
        self.assertEqual(package_data["stop_reason"], "human_review_boundary")
        self.assertEqual(package_data["steps_executed"], 0)
        self.assertEqual(package_data["steps"][0]["candidate_stage"], "stable-core")
        self.assertIn(str(ROOT), package_data["steps"][0]["selected_command"])

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "future-project"
            missing_result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_loop.py"),
                    str(missing),
                    "--max-steps",
                    "2",
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(CLI),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            missing_data = json.loads(missing_result.stdout)
            self.assertEqual(missing_data["stop_reason"], "placeholder_command")
            self.assertEqual(missing_data["steps_executed"], 0)
            self.assertIn("<title>", missing_data["steps"][0]["selected_command"])
            self.assertFalse(missing.exists())

            legacy = Path(tmp) / "legacy"
            legacy.mkdir()
            (legacy / "outline.md").write_text("# Old Outline\n\nLegacy material.\n", encoding="utf-8")
            legacy_result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_loop.py"),
                    str(legacy),
                    "--max-steps",
                    "2",
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(CLI),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            legacy_data = json.loads(legacy_result.stdout)
            self.assertEqual(legacy_data["stop_reason"], "repeated_command")
            self.assertEqual(legacy_data["steps_executed"], 1)
            self.assertIn("adopt", legacy_data["steps"][0]["selected_command"])
            self.assertFalse((legacy / "project.yml").exists())

        temp, target = self.make_project()
        with temp:
            queue = target / "06_drafts" / "import_queue"
            queue.mkdir(parents=True, exist_ok=True)
            queued = queue / "ch_099.md"
            queued.write_text("# Imported Draft\n\nNeeds sorting.\n", encoding="utf-8")
            queue_result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_loop.py"),
                    str(target),
                    "--no-text-scan",
                    "--max-steps",
                    "2",
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(CLI),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            queue_data = json.loads(queue_result.stdout)
            self.assertEqual(queue_data["stop_reason"], "repeated_command")
            self.assertEqual(queue_data["steps_executed"], 1)
            self.assertIn("import-plan", queue_data["steps"][0]["selected_command"])
            self.assertTrue(queued.exists())

        with tempfile.TemporaryDirectory() as tmp:
            fake_cli = Path(tmp) / "fake_fictionops.py"
            fake_cli.write_text(
                textwrap.dedent(
                    """\
                    from __future__ import annotations

                    import json
                    import sys

                    command = sys.argv[1] if len(sys.argv) > 1 else ""
                    if command == "agent-next":
                        project = sys.argv[2]
                        print(json.dumps({
                            "status": "ready_for_agent_step",
                            "selected_command": f"fictionops release-gate {project} --book book_01 --format json",
                            "selected_reason": "Release gate status needs inspection.",
                            "candidates": [{
                                "priority": "P4",
                                "stage": "publish",
                                "command": f"fictionops release-gate {project} --book book_01 --format json",
                                "reason": "Release gate status needs inspection.",
                                "safe_to_auto_run": True,
                                "requires_human_review": False
                            }]
                        }))
                    elif command == "release-gate":
                        print(json.dumps({"status": "needs_release_artifacts", "ready": False}))
                    else:
                        print(f"unexpected command: {command}", file=sys.stderr)
                        raise SystemExit(2)
                    """
                ),
                encoding="utf-8",
            )
            release_result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "examples" / "agent_controller_loop.py"),
                    "publish-project",
                    "--max-steps",
                    "2",
                    "--format",
                    "json",
                    "--cli",
                    sys.executable,
                    str(fake_cli),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )
            release_data = json.loads(release_result.stdout)
            self.assertEqual(release_data["stop_reason"], "repeated_command")
            self.assertEqual(release_data["steps_executed"], 1)
            self.assertEqual(release_data["steps"][0]["candidate_stage"], "publish")
            self.assertIn("release-gate", release_data["steps"][0]["selected_command"])

    def test_model_config_builds_safe_provider_config(self) -> None:
        temp, target = self.make_project()
        with temp:
            os.environ["FICTIONOPS_TEST_API_KEY"] = "secret-value"
            try:
                report = build_model_config_report(
                    target,
                    provider="openai",
                    planning_model="planner-model",
                    drafting_model="draft-model",
                    audit_model="audit-model",
                    api_key_env="FICTIONOPS_TEST_API_KEY",
                    write=False,
                )
            finally:
                os.environ.pop("FICTIONOPS_TEST_API_KEY", None)

            self.assertEqual(report.provider, "openai")
            self.assertEqual(report.planning_model, "planner-model")
            self.assertEqual(report.api_key_env, "FICTIONOPS_TEST_API_KEY")
            self.assertEqual(report.env_present, True)
            self.assertEqual(report.written, False)
            self.assertNotIn("secret-value", json.dumps(report.config))
            self.assertEqual([issue.code for issue in report.issues], [])

    def test_model_config_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli(
                "model-config",
                str(target),
                "--provider",
                "local",
                "--planning-model",
                "planner",
                "--drafting-model",
                "writer",
                "--audit-model",
                "auditor",
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["provider"], "local")
            self.assertEqual(data["write"], False)
            self.assertEqual(data["written"], False)

            written = self.run_cli(
                "model-config",
                str(target),
                "--provider",
                "local",
                "--planning-model",
                "planner",
                "--drafting-model",
                "writer",
                "--audit-model",
                "auditor",
                "--write",
            )
            self.assertIn("Wrote FictionOps model config", written.stdout)
            config_path = target / "00_management" / "model_config.json"
            self.assertTrue(config_path.exists())
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["provider"], "local")
            self.assertEqual(config["policy"]["store_api_keys"], False)

            failed = self.run_cli("model-config", str(target), "--provider", "local", "--write", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_setup_ai_writes_provider_config_and_env_example_without_keys(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = build_ai_setup(
                target,
                provider="deepseek",
                model="deepseek-chat",
                force=False,
            )
            self.assertTrue(report.written)
            self.assertEqual(report.provider, "deepseek")
            self.assertEqual(report.api_key_env, "DEEPSEEK_API_KEY")
            self.assertIn("write-chapter", report.dry_run_command)
            self.assertIn("--dry-run", report.dry_run_command)

            config_path = target / "00_management" / "model_config.json"
            env_path = target / "00_management" / "ai_runner.env.example"
            self.assertTrue(config_path.exists())
            self.assertTrue(env_path.exists())
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["provider"], "deepseek")
            self.assertEqual(config["api_key_env"], "DEEPSEEK_API_KEY")
            env_text = env_path.read_text(encoding="utf-8")
            self.assertIn("FICTIONOPS_CHAT_PROVIDER=deepseek", env_text)
            self.assertIn("DEEPSEEK_API_KEY=", env_text)
            self.assertNotIn("sk-", env_text)
            self.assertNotIn("secret", env_text.lower())

            failed = self.run_cli("setup-ai", str(target), "--provider", "deepseek", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

            dry = self.run_cli(
                "setup-ai",
                str(target),
                "--provider",
                "qwen",
                "--dry-run",
                "--format",
                "json",
            )
            data = json.loads(dry.stdout)
            self.assertEqual(data["schema"], "fictionops.ai_setup.v1")
            self.assertEqual(data["provider"], "dashscope")
            self.assertEqual(data["written"], False)
            self.assertEqual(data["safety"]["stores_api_keys"], False)

    def test_setup_ai_supports_local_openai_without_api_key_env(self) -> None:
        temp, target = self.make_project()
        with temp:
            cli = self.run_cli(
                "setup-ai",
                str(target),
                "--provider",
                "local-openai",
                "--model",
                "local-writer",
                "--format",
                "json",
            )
            data = json.loads(cli.stdout)
            self.assertEqual(data["provider"], "local-openai")
            self.assertEqual(data["api_key_env"], "")
            self.assertIn("local OpenAI-compatible server", data["next_actions"][0])
            env_text = (target / "00_management" / "ai_runner.env.example").read_text(encoding="utf-8")
            self.assertIn("FICTIONOPS_CHAT_API_KEY_ENV=", env_text)
            self.assertNotIn("API_KEY=", env_text)

    def test_doctor_includes_model_config_summary(self) -> None:
        temp, target = self.make_project()
        with temp:
            default_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
            )
            self.assertEqual(default_report.model_config["enabled"], True)
            self.assertEqual(default_report.model_config["provider"], "configurable")
            self.assertGreater(default_report.model_config["issues"], 0)

            build_model_config_report(
                target,
                provider="local",
                planning_model="planner",
                drafting_model="writer",
                audit_model="auditor",
                write=True,
            )
            configured_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
            )
            self.assertEqual(configured_report.model_config["enabled"], True)
            self.assertEqual(configured_report.model_config["config_file_exists"], True)
            self.assertEqual(configured_report.model_config["provider"], "local")
            self.assertEqual(configured_report.model_config["planning_model"], "planner")
            self.assertEqual(configured_report.model_config["issues"], 0)

    def test_context_pack_builds_draft_scope(self) -> None:
        temp, target = self.make_project()
        with temp:
            create_chapter(
                target,
                book="book_01",
                chapter="002",
                title="Second Chapter",
                viewpoint="Tester",
                kind="核心情节",
                target_chars=8000,
                force=False,
                dry_run=False,
            )

            report = build_context_pack(
                target,
                task="draft",
                book="book_01",
                chapter="002",
                include_content=False,
            )
            files = {item.path.replace("\\", "/"): item for item in report.files}

            self.assertEqual(report.task, "draft")
            self.assertEqual(report.chapter, "002")
            self.assertEqual(report.issues, [])
            self.assertIn("本章视角人物现在想要什么？", report.checklist)
            self.assertTrue(files["04_structure/book_outlines/book_01_outline.md"].required)
            self.assertTrue(files["06_drafts/book_01/chapter_engines/ch_002_engine.md"].required)
            self.assertTrue(files["06_drafts/book_01/chapters/ch_001.md"].required)
            self.assertFalse(files["05_canon/foreshadowing_echo_table.md"].required)

    def test_context_pack_builds_handoff_scope_with_milestone_artifacts(self) -> None:
        temp, target = self.make_project()
        with temp:
            (target / "07_audits" / "doctor_report.md").write_text("# Doctor\n", encoding="utf-8")
            (target / "07_audits" / "revision_plan.md").write_text("# Revision\n", encoding="utf-8")
            (target / "07_audits" / "book_gate").mkdir(parents=True, exist_ok=True)
            (target / "07_audits" / "book_gate" / "book_01_gate.md").write_text("# Book Gate\n", encoding="utf-8")
            (target / "07_audits" / "release_gate").mkdir(parents=True, exist_ok=True)
            (target / "07_audits" / "release_gate" / "book_01_release_gate.md").write_text("# Release Gate\n", encoding="utf-8")

            report = build_context_pack(
                target,
                task="handoff",
                book="book_01",
                include_content=False,
            )
            files = {item.path.replace("\\", "/"): item for item in report.files}

            self.assertEqual(report.task, "handoff")
            self.assertEqual(report.issues, [])
            self.assertTrue(files["00_management/handoff_log.md"].required)
            self.assertTrue(files["00_management/decision_log.md"].required)
            self.assertTrue(files["04_structure/book_outlines/book_01_outline.md"].required)
            self.assertIn("03_characters/character_index.md", files)
            self.assertIn("03_characters/intelligence_profiles.md", files)
            self.assertIn("03_characters/voice_profiles.md", files)
            self.assertIn("05_canon/object_locations.md", files)
            self.assertIn("05_canon/open_questions.md", files)
            self.assertTrue(files["07_audits/doctor_report.md"].exists)
            self.assertTrue(files["07_audits/revision_plan.md"].exists)
            self.assertTrue(files["07_audits/book_gate/book_01_gate.md"].exists)
            self.assertTrue(files["07_audits/release_gate/book_01_release_gate.md"].exists)

    def test_context_pack_respects_total_content_budget(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = build_context_pack(
                target,
                task="draft",
                book="book_01",
                chapter="001",
                include_content=True,
                max_chars_per_file=1000,
                max_total_chars=10,
            )

            self.assertEqual(report.max_total_chars, 10)
            self.assertEqual(report.included_total_chars, 10)
            self.assertLessEqual(sum(item.included_chars for item in report.files), 10)
            self.assertTrue(any(item.truncated for item in report.files if item.exists))

    def test_context_pack_cli_writes_markdown_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            json_result = self.run_cli(
                "context-pack",
                str(target),
                "--task",
                "draft",
                "--chapter",
                "001",
                "--max-total-chars",
                "10",
                "--no-content",
                "--format",
                "json",
            )
            data = json.loads(json_result.stdout)
            self.assertEqual(data["task"], "draft")
            self.assertEqual(data["chapter"], "001")
            self.assertEqual(data["max_total_chars"], 10)
            self.assertEqual(data["included_total_chars"], 0)
            self.assertTrue(data["files"])
            self.assertEqual(data["files"][0]["content"], "")

            result = self.run_cli(
                "context-pack",
                str(target),
                "--task",
                "draft",
                "--chapter",
                "001",
                "--out",
                "00_management/context_pack.md",
            )
            output = target / "00_management" / "context_pack.md"
            self.assertIn("Wrote FictionOps context pack", result.stdout)
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Context Pack", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "context-pack",
                str(target),
                "--task",
                "draft",
                "--chapter",
                "001",
                "--out",
                "00_management/context_pack.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_workflow_plan_builds_stage_and_all_checklists(self) -> None:
        temp, target = self.make_project()
        with temp:
            report = build_workflow_plan(target, stage="review", book="book_01", chapter="001")
            self.assertEqual(report.stage, "review")
            self.assertEqual(report.chapter, "001")
            self.assertEqual(report.step_count, 10)
            self.assertTrue(any("review-gate" in command for command in report.commands))
            self.assertTrue(any("scan-words" in command for command in report.commands))
            self.assertTrue(any("check-tables" in command for command in report.commands))
            self.assertTrue(any("revision-plan" in command for command in report.commands))
            self.assertFalse(any("&&" in command for command in report.commands))
            self.assertTrue(any(step.stage == "review" for step in report.steps))

            all_report = build_workflow_plan(target, stage="all", book="book_01")
            stages = {step.stage for step in all_report.steps}
            self.assertIn("init", stages)
            self.assertIn("publish", stages)
            self.assertIn("handoff", stages)
            self.assertGreater(all_report.step_count, report.step_count)

            draft_report = build_workflow_plan(target, stage="draft", book="book_01", chapter="001")
            self.assertEqual(draft_report.step_count, 4)
            self.assertTrue(any("post-draft" in command for command in draft_report.commands))

            future = target.parent / "future novel"
            init_report = build_workflow_plan(future, stage="init")
            self.assertEqual(init_report.stage, "init")
            self.assertIn('"', init_report.commands[0])

            with self.assertRaises(ValueError):
                build_workflow_plan(target, stage="draft", book="book_01")

    def test_workflow_plan_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli(
                "workflow-plan",
                str(target),
                "--stage",
                "prep",
                "--chapter",
                "001",
                "--format",
                "json",
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["stage"], "chapter-prep")
            self.assertEqual(data["chapter"], "001")
            self.assertTrue(any("draft-brief" in command for command in data["commands"]))

            written = self.run_cli("workflow-plan", str(target), "--out", "00_management/workflow_plan.md")
            self.assertIn("Wrote FictionOps workflow plan", written.stdout)
            output = target / "00_management" / "workflow_plan.md"
            self.assertTrue(output.exists())
            self.assertIn("# FictionOps Workflow Plan", output.read_text(encoding="utf-8"))

            failed = self.run_cli(
                "workflow-plan",
                str(target),
                "--out",
                "00_management/workflow_plan.md",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_revision_plan_prioritizes_audit_findings(self) -> None:
        temp, target = self.make_project()
        with temp:
            (target / "05_canon" / "information_release_table.md").unlink()
            self.write_long_chapter_with_echo(target)
            (target / "05_canon" / "broken_table.md").write_text(
                "| A | A |\n| --- | --- |\n| filled |\n",
                encoding="utf-8",
            )

            report = build_revision_plan(target, book="book_01")
            self.assertGreater(report.task_count, 0)
            self.assertEqual(report.priority_counts["P1"], 2)
            self.assertEqual(report.tasks[0].priority, "P1")
            self.assertIn(report.tasks[0].code, {"missing_standard_file", "missing_information_table"})
            self.assertTrue(any(task.source_command == "audit-info" for task in report.tasks))
            self.assertTrue(any(task.source_command == "audit-continuity" for task in report.tasks))
            self.assertTrue(any(task.source_command == "check-tables" for task in report.tasks))
            self.assertTrue(any(task.source_command == "scan-words" for task in report.tasks))

    def test_revision_plan_cli_outputs_json_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("revision-plan", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["book"], "book_01")
            self.assertGreaterEqual(data["task_count"], 1)
            self.assertIn("priority_counts", data)

            output = "07_audits/revision_plan.md"
            written = self.run_cli("revision-plan", str(target), "--out", output)
            self.assertIn("Wrote FictionOps revision plan", written.stdout)
            output_path = target / output
            self.assertTrue(output_path.exists())
            self.assertIn("# FictionOps Revision Plan", output_path.read_text(encoding="utf-8"))

            failed = self.run_cli("revision-plan", str(target), "--out", output, check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("Use --force to overwrite", failed.stderr)

    def test_doctor_summarizes_project_health(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_echo_table(target)
            self.write_filled_information_table(target)
            self.write_long_chapter_with_echo(target)

            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=False,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=True,
                stale_after=8,
            )
            self.assertEqual(report.echoes["threads"], 1)
            self.assertEqual(report.echoes["issues"], 0)
            self.assertEqual(report.info["items"], 1)
            self.assertEqual(report.info["issues"], 0)
            self.assertEqual(report.wave["files"], 1)
            self.assertEqual(report.wave["issues"], 0)
            self.assertEqual(report.word_scan["files"], 1)
            self.assertIn("top_terms", report.word_scan)
            self.assertGreaterEqual(report.tables["files"], 1)
            self.assertIn("no_table_files", report.tables)
            self.assertEqual(report.continuity["missing_engines"], 0)
            self.assertEqual(report.continuity["missing_retrospectives"], 1)
            self.assertEqual(report.characters["enabled"], True)
            self.assertGreater(report.characters["issues"], 0)
            self.assertEqual(report.plan["enabled"], True)
            self.assertEqual(report.retrospective["enabled"], True)
            self.assertEqual(report.retrospective["missing_retrospectives"], 1)
            self.assertEqual(report.book_gate["enabled"], True)
            self.assertIn(report.book_gate["status"], {"needs_book_material", "needs_book_closure", "book_notes", "ready_for_clean_export"})
            self.assertEqual(report.model_config["enabled"], True)
            self.assertGreater(report.model_config["issues"], 0)
            self.assertEqual(report.publish["enabled"], False)
            self.assertEqual(report.publish["skipped_reason"], "clean_markdown_not_found")
            self.assertEqual(report.metadata["enabled"], False)
            self.assertEqual(report.metadata["skipped_reason"], "publish_stage_not_started")
            self.assertEqual(report.manifest["enabled"], False)
            self.assertEqual(report.manifest["skipped_reason"], "publish_stage_not_started")
            self.assertEqual(report.epub["enabled"], False)
            self.assertEqual(report.epub["skipped_reason"], "publish_stage_not_started")
            self.assertEqual(report.release_gate["enabled"], False)
            self.assertEqual(report.release_gate["skipped_reason"], "publish_stage_not_started")
            self.assertEqual(report.status, "maintenance_needed")

    def test_doctor_skips_character_audit_for_plain_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "plain"
            target.mkdir()
            (target / "ch_001.md").write_text("只是普通书稿目录。\n" * 20, encoding="utf-8")

            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=False,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=[],
                top=5,
                min_repeat=3,
                scan_text=True,
                stale_after=8,
            )

            self.assertEqual(report.characters["enabled"], False)
            self.assertEqual(report.characters["issues"], 0)
            self.assertEqual(report.characters["skipped_reason"], "target_is_not_standard_project")
            self.assertEqual(report.book_gate["enabled"], False)
            self.assertEqual(report.release_gate["enabled"], False)

    def test_doctor_includes_plan_audit_issues(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_book_outline_plan(
                target,
                "\n".join(
                    [
                        "| 01 | Existing | A | p1 | d1 | o1 | c1 | r1 | 8200 |",
                        "| 02 | Missing Engine | B | p2 | d2 | o2 | c2 | r2 | 7800 |",
                    ]
                ),
            )
            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(report.plan["enabled"], True)
            self.assertEqual(report.plan["planned_chapters"], 2)
            self.assertGreater(report.plan["issues"], 0)
            self.assertEqual(report.status, "needs_attention")

    def test_doctor_includes_retrospective_summary(self) -> None:
        temp, target = self.make_project()
        with temp:
            create_chapter(
                target,
                book="book_01",
                chapter="2",
                title="Retrospective Ready",
                viewpoint=None,
                kind=None,
                target_chars=None,
                force=False,
                dry_run=False,
            )
            self.write_filled_chapter_retrospective(target, "002")

            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=200,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(report.retrospective["enabled"], True)
            self.assertEqual(report.retrospective["chapters"], 2)
            self.assertEqual(report.retrospective["sync_items"], 1)
            self.assertGreater(report.retrospective["issues"], 0)
            self.assertTrue(any("retrospective sync" in item for item in report.recommendations))

    def test_doctor_includes_publish_summary(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_echo_table(target)
            clean = target / "08_publish" / "clean_markdown" / "book_01.md"
            clean.parent.mkdir(parents=True, exist_ok=True)
            clean.write_text("# 第001章\n\n> Draft starts here.\n\n短。", encoding="utf-8")

            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(report.publish["enabled"], True)
            self.assertEqual(report.publish["clean_file_exists"], True)
            self.assertEqual(report.publish["clean_chapters"], 1)
            self.assertGreater(report.publish["issues"], 0)
            self.assertEqual(report.status, "needs_attention")
            self.assertTrue(any("publish clean Markdown" in item for item in report.recommendations))

    def test_doctor_includes_publish_metadata_summary(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_echo_table(target)
            clean = target / "08_publish" / "clean_markdown" / "book_01.md"
            clean.parent.mkdir(parents=True, exist_ok=True)
            clean.write_text("# 第001章\n\n" + "正文内容。" * 40, encoding="utf-8")

            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(report.metadata["enabled"], True)
            self.assertEqual(report.metadata["checklist_file_exists"], True)
            self.assertGreater(report.metadata["issues"], 0)
            self.assertEqual(report.status, "needs_attention")
            self.assertTrue(any("publish metadata" in item for item in report.recommendations))

            self.write_publish_checklist_metadata(target)
            clean_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(clean_report.metadata["enabled"], True)
            self.assertEqual(clean_report.metadata["issues"], 0)
            self.assertGreater(clean_report.metadata["fields_filled"], 0)

    def test_doctor_includes_publish_manifest_summary(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_echo_table(target)
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# 第001章\n\n" + "正文内容。" * 40, encoding="utf-8")
            export_clean_markdown(
                target,
                book="book_01",
                out=None,
                title=None,
                force=False,
                dry_run=False,
            )
            self.write_publish_checklist_metadata(target)
            export_publish_metadata(
                target,
                book="book_01",
                file_path=None,
                out=None,
                force=False,
                dry_run=False,
            )

            report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(report.manifest["enabled"], True)
            self.assertEqual(report.manifest["manifest_file_exists"], False)
            self.assertGreater(report.manifest["issues"], 0)
            self.assertTrue(any("publish manifest" in item for item in report.recommendations))

            export_publish_manifest(
                target,
                book="book_01",
                clean_file=None,
                metadata_file=None,
                out=None,
                force=False,
                dry_run=False,
            )
            clean_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(clean_report.manifest["manifest_file_exists"], True)
            self.assertEqual(clean_report.manifest["hashes_match"], True)
            self.assertEqual(clean_report.manifest["issues"], 0)

            clean_file = target / "08_publish" / "clean_markdown" / "book_01.md"
            clean_file.write_text(clean_file.read_text(encoding="utf-8") + "\n\n追加修订。", encoding="utf-8")
            stale_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(stale_report.manifest["hashes_match"], False)
            self.assertGreater(stale_report.manifest["issues"], 0)

    def test_doctor_includes_publish_epub_summary(self) -> None:
        temp, target = self.make_project()
        with temp:
            self.write_filled_echo_table(target)
            chapter = target / "06_drafts" / "book_01" / "chapters" / "ch_001.md"
            chapter.write_text("# Chapter 001\n\n" + "正文内容。" * 40, encoding="utf-8")
            export_clean_markdown(
                target,
                book="book_01",
                out=None,
                title=None,
                force=False,
                dry_run=False,
            )
            self.write_publish_checklist_metadata(target)
            export_publish_metadata(
                target,
                book="book_01",
                file_path=None,
                out=None,
                force=False,
                dry_run=False,
            )
            export_publish_manifest(
                target,
                book="book_01",
                clean_file=None,
                metadata_file=None,
                out=None,
                force=False,
                dry_run=False,
            )

            missing_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(missing_report.epub["enabled"], True)
            self.assertEqual(missing_report.epub["epub_file_exists"], False)
            self.assertGreater(missing_report.epub["issues"], 0)
            self.assertEqual(missing_report.release_gate["enabled"], True)
            self.assertIn(missing_report.release_gate["status"], {"needs_release_artifacts", "needs_release_fixes", "release_notes", "ready_for_release"})
            self.assertTrue(any("EPUB export" in item for item in missing_report.recommendations))

            export_epub(
                target,
                book="book_01",
                manifest_file=None,
                clean_file=None,
                metadata_file=None,
                cover_file=None,
                out=None,
                force=False,
                dry_run=False,
            )
            clean_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(clean_report.epub["epub_file_exists"], True)
            self.assertEqual(clean_report.epub["epub_valid"], True)
            self.assertEqual(clean_report.epub["issues"], 0)
            self.assertEqual(clean_report.release_gate["enabled"], True)

            clean_file = target / "08_publish" / "clean_markdown" / "book_01.md"
            epub_file = target / "08_publish" / "epub" / "book_01.epub"
            bumped_time = max(clean_file.stat().st_mtime, epub_file.stat().st_mtime) + 10
            os.utime(clean_file, (bumped_time, bumped_time))
            stale_report = build_doctor_report(
                target,
                all_markdown=False,
                pattern="**/*.md",
                metric="nonspace",
                skip_standard=True,
                strict_standard=False,
                min_chapter_chars=20,
                watch_terms=["没有"],
                top=5,
                min_repeat=3,
                scan_text=False,
                stale_after=8,
                book="book_01",
                outline=None,
            )
            self.assertEqual(stale_report.epub["epub_valid"], True)
            self.assertGreater(stale_report.epub["issues"], 0)

    def test_doctor_cli_outputs_json(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("doctor", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["stats"]["files"], 1)
            self.assertIn("wave", data)
            self.assertEqual(data["wave"]["files"], 1)
            self.assertIn("word_scan", data)
            self.assertIn("tables", data)
            self.assertIn("info", data)
            self.assertIn("characters", data)
            self.assertEqual(data["characters"]["enabled"], True)
            self.assertIn("plan", data)
            self.assertEqual(data["plan"]["book"], "book_01")
            self.assertIn("retrospective", data)
            self.assertEqual(data["retrospective"]["book"], "book_01")
            self.assertIn("book_gate", data)
            self.assertEqual(data["book_gate"]["book"], "book_01")
            self.assertIn("publish", data)
            self.assertEqual(data["publish"]["book"], "book_01")
            self.assertIn("model_config", data)
            self.assertEqual(data["model_config"]["enabled"], True)
            self.assertIn("metadata", data)
            self.assertEqual(data["metadata"]["book"], "book_01")
            self.assertIn("manifest", data)
            self.assertEqual(data["manifest"]["book"], "book_01")
            self.assertIn("epub", data)
            self.assertEqual(data["epub"]["book"], "book_01")
            self.assertIn("release_gate", data)
            self.assertEqual(data["release_gate"]["book"], "book_01")
            self.assertIn(data["status"], {"critical", "needs_attention", "maintenance_needed", "review", "pass"})

    def test_report_cli_writes_markdown_and_refuses_overwrite(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("report", str(target), "--out", "07_audits/doctor_report.md")
            output = target / "07_audits" / "doctor_report.md"
            self.assertIn("Wrote FictionOps report", result.stdout)
            self.assertTrue(output.exists())
            report_text = output.read_text(encoding="utf-8")
            self.assertIn("# FictionOps Doctor", report_text)
            self.assertIn("| Wave |", report_text)
            self.assertIn("| Word Scan |", report_text)
            self.assertIn("| Tables |", report_text)
            self.assertIn("| Characters |", report_text)
            self.assertIn("| Information |", report_text)
            self.assertIn("| Plan |", report_text)
            self.assertIn("| Retrospective |", report_text)
            self.assertIn("| Book Gate |", report_text)
            self.assertIn("| Model Config |", report_text)
            self.assertIn("| Publish |", report_text)
            self.assertIn("| Metadata |", report_text)
            self.assertIn("| Manifest |", report_text)
            self.assertIn("| EPUB |", report_text)
            self.assertIn("| Release Gate |", report_text)

            refused = self.run_cli(
                "report",
                str(target),
                "--out",
                "07_audits/doctor_report.md",
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("Use --force to overwrite", refused.stderr)

    def test_report_cli_outputs_json_stdout(self) -> None:
        temp, target = self.make_project()
        with temp:
            result = self.run_cli("report", str(target), "--format", "json")
            data = json.loads(result.stdout)
            self.assertEqual(data["stats"]["files"], 1)
            self.assertIn("wave", data)
            self.assertEqual(data["wave"]["files"], 1)
            self.assertIn("word_scan", data)
            self.assertIn("tables", data)
            self.assertIn("info", data)
            self.assertIn("book_gate", data)
            self.assertIn("release_gate", data)
            self.assertIn("model_config", data)
            self.assertIn("recommendations", data)


if __name__ == "__main__":
    unittest.main()
