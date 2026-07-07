# FictionOps

[English](README.md) | 简体中文

> 一个面向长篇小说的创作操作系统，用于规划、写作、复盘、审计和发布。它服务于人的审美，也允许外部模型 API、runner 或 controller 参与协作。

FictionOps 是一套拟开源的长篇小说工作流底座。它不是“一键生成小说”的工具，也不是把小说写成表格的管理软件，更不是自主写作 agent。更准确地说，它是一套 API-backed workflow harness：用文件、命令、上下文包、任务包、外部 runner、收件箱和门禁，把人类作者与模型 API/外部工具之间的协作边界固定下来。接上外部模型 API runner 后，它是 AI-assisted 或 API-backed workflow；再接上能够读取状态、选择下一步、调用 runner 并在复核边界停下的 controller 后，整套系统才构成 agentic workflow。FictionOps 本体仍然是编排、暂存和门禁层，不是直接掌权的自主小说家。它的目标是帮助作者、编辑、模型工具和 controller 一起维护那些可能跨越数百章、数百万字、多视角、多时间线、多卷设定和长期伏笔的故事。

核心判断很简单：

**一部长篇不只是正文。它也是一套不断生长的承诺、压力、记忆、规则、沉默、回声和修订。**

FictionOps 要做的，就是把这套系统变成一个可维护的项目。

## 0. 当前仓库内容

当前目录已经包含一组中文优先的 MVP 文档与模板：

```text
fictionops/
  pyproject.toml
  LICENSE
  CHANGELOG.md
  CONTRIBUTING.md
  CONTRIBUTING.zh-CN.md
  README.md
  README.zh-CN.md
  src/
    fictionops/
      __init__.py
      adopt.py
      adopt_review.py
      agent_prompt.py
      character_audit.py
      cli.py
      core.py
      constants.py
      models.py
      markdown.py
      model_config.py
      audit_plan.py
      init_project.py
      new_book.py
      new_chapter.py
      plan_chapter.py
      scene_plan.py
      draft_brief.py
      post_draft.py
      review_gate.py
      book_gate.py
      release_gate.py
      retrospective.py
      stats.py
      word_scan.py
      table_check.py
      chapter_wave.py
      style_audit.py
      continuity_audit.py
      echo_audit.py
      information_audit.py
      context_pack.py
      workflow_plan.py
      doctor.py
      epub_audit.py
      report.py
      revision_plan.py
      export_clean.py
      publish_audit.py
      publish_copy.py
      publish_epub.py
      publish_metadata.py
      publish_manifest.py
      templates/
  docs/
    cli.md
    cli-contracts.md
    cli.zh-CN.md
    agent-protocol.md
    cli-contracts.zh-CN.md
    migration.md
    testing.md
    release.md
    release-trial-evidence.md
    release-trial-evidence.zh-CN.md
    dogfood-cycle-evidence.md
    dogfood-cycle-evidence.zh-CN.md
    stability-window-evidence.md
    stability-window-evidence.zh-CN.md
    compatibility.md
    compatibility.zh-CN.md
    known-limits.md
    known-limits.zh-CN.md
    recovery.md
    recovery.zh-CN.md
    completion-audit-0.1.0.zh-CN.md
    roadmap.md
    roadmap.zh-CN.md
    milestone-status.md
    milestone-status.zh-CN.md
    stable-core-remaining-checklist.md
    stable-core-remaining-checklist.zh-CN.md
    stable-core-audit.md
    stable-core-audit.zh-CN.md
    end-to-end-migration-publish.md
    dogfood-legacy-adopt.zh-CN.md
    pypi-release.zh-CN.md
    testing.zh-CN.md
    project-structure.zh-CN.md
    audit-priority.zh-CN.md
    agent-protocol.zh-CN.md
    agent-connector-contract.md
    agent-connector-contract.zh-CN.md
    agent-workflow.md
    agent-workflow.zh-CN.md
    agent-integration.md
    agent-integration.zh-CN.md
    tutorial-demo.md
    release-checklist.zh-CN.md
    release-notes-0.1.0.zh-CN.md
    tutorial-demo.zh-CN.md
  tests/
    test_cli.py
  examples/
    agent_controller_next.py
    agent_controller_loop.py
    agent_runner_echo.py
    agent_runner_openai_responses.py
    demo_novel/
  workflows/
    from-seed-to-publication.zh-CN.md
  templates/
    project.yml
    story_seed.zh-CN.md
    character_arc.zh-CN.md
    book_outline.zh-CN.md
    book_retrospective.zh-CN.md
    chapter_engine.zh-CN.md
    information_release_table.zh-CN.md
    foreshadowing_echo_table.zh-CN.md
    chapter_retrospective.zh-CN.md
    style_audit.zh-CN.md
    publish_checklist.zh-CN.md
    handoff_log.zh-CN.md
  examples/
    demo_novel/
    legacy_novel_source/
    long_novel_outline_migration_case_zh.md
```

建议阅读顺序：

1. 先读 [项目结构说明](docs/project-structure.zh-CN.md)，理解每类文件放在哪里。
2. 再读 [从故事种子到发布](workflows/from-seed-to-publication.zh-CN.md)，理解完整流程。
3. 读 [审计优先级](docs/audit-priority.zh-CN.md)，理解哪些问题必须先修。
4. 读 [Agent 协作协议](docs/agent-protocol.zh-CN.md)，理解 AI 协作的输入输出边界。
5. 读 [Agent workflow 定位说明](docs/agent-workflow.zh-CN.md)，理解“接上模型 API 后算不算 agent workflow”以及 FictionOps 本体和外部 runner/controller 的边界。
6. 读 [CLI 使用说明](docs/cli.zh-CN.md)，了解所有 CLI 命令。
7. 读 [CLI 契约](docs/cli-contracts.zh-CN.md)，理解命令输入、输出、失败语义和稳定承诺。
8. 读 [测试说明](docs/testing.zh-CN.md)，了解如何验证 CLI。
9. 读 [发布检查清单](docs/release-checklist.zh-CN.md)，理解发布前要证明哪些事情。
10. 跑一遍 [最小示例教程](docs/tutorial-demo.zh-CN.md)，确认命令链路怎么落到真实文件。
11. 读 [0.1.0 完成审计](docs/completion-audit-0.1.0.zh-CN.md)，确认当前版本已经证明了什么、没有证明什么。
12. 读 [后续完成路线](docs/roadmap.zh-CN.md)，理解 0.2、0.3、0.5 和 1.0 分别需要什么证据。
13. 读 [真实长篇 adopt 迁移报告](docs/dogfood-legacy-adopt.zh-CN.md)，看 `adopt` 在百万字级旧项目上的分层结果和暴露的问题。
14. 读 [Dogfood 案例研究](docs/dogfood-case-study.zh-CN.md)，看一个私有百万字级项目如何经过结构修复、读者体验修订和发布链路烟测。
15. 读 [0.1.0 发布说明](docs/release-notes-0.1.0.zh-CN.md)，了解发布边界和已知限制。
16. 读 [兼容性策略](docs/compatibility.zh-CN.md)，理解哪些 CLI 和 JSON 行为可以被脚本或 controller 依赖。
17. 读 [已知限制](docs/known-limits.zh-CN.md)，理解哪些事情 FictionOps 当前不保证。
18. 读 [PyPI 发布说明](docs/pypi-release.zh-CN.md)，了解 trusted publishing、凭据隔离和回滚记录。
19. 读 [发布演练证据模板](docs/release-trial-evidence.zh-CN.md)，了解如何记录 GitHub Actions run、artifact、TestPyPI URL、安装烟测和最终结论；publish workflow 也会生成独立的 release trial evidence draft artifact，避免证据草稿混入 wheel/sdist 发布包。
20. 读 [持续 dogfood 周期证据模板](docs/dogfood-cycle-evidence.zh-CN.md)，了解 1.0 前如何记录收口后的真实项目维护周期。
21. 读 [稳定窗口证据模板](docs/stability-window-evidence.zh-CN.md)，了解 1.0 前如何记录兼容性窗口。
22. 读 [1.0 剩余执行清单](docs/stable-core-remaining-checklist.zh-CN.md)，明确哪些工作已经只是维护，哪些必须等真实外部发布、dogfood 和稳定窗口证据。
23. 然后复制 `templates/` 里的模板，建立自己的长篇项目，或读 [长篇大纲迁移案例](examples/long_novel_outline_migration_case_zh.md)，看一部复杂长篇如何从混乱材料变成可维护结构。

英文外部接手入口包括 [CLI guide](docs/cli.md)、[CLI contracts](docs/cli-contracts.md)、[Agent protocol](docs/agent-protocol.md)、[Agent connector contract](docs/agent-connector-contract.md)、[Agent integration guide](docs/agent-integration.md)、[Migration guide](docs/migration.md)、[Dogfood case study](docs/dogfood-case-study.md)、[Testing guide](docs/testing.md)、[Release guide](docs/release.md)、[Compatibility policy](docs/compatibility.md)、[Known limits](docs/known-limits.md)、[Milestone status](docs/milestone-status.md)、[Stable core remaining checklist](docs/stable-core-remaining-checklist.md)、[Stable core audit](docs/stable-core-audit.md)、[Demo tutorial](docs/tutorial-demo.md)、[Legacy migration example](examples/legacy_novel_source/README.md) 和 [Contributing](CONTRIBUTING.md)。

参与开发前请读 [贡献指南](CONTRIBUTING.zh-CN.md) 或 [Contributing](CONTRIBUTING.md)，版本变化记录在 [CHANGELOG](CHANGELOG.md)，项目使用 [MIT License](LICENSE)。

仓库根目录包含 GitHub issue/PR 模板、`.github/workflows/fictionops-ci.yml` 和 `.github/workflows/fictionops-publish.yml`；CI 会针对 `fictionops/` 包运行编译检查、完整 unittest、wheel/sdist 构建和 wheel/sdist 内容检查，发布 workflow 可手动触发 TestPyPI/PyPI trusted publishing，并会单独上传 `fictionops-release-trial-evidence-<version>` 证据草稿 artifact。

发布证据见 [0.1.0 完成审计](docs/completion-audit-0.1.0.zh-CN.md) 和 [0.1.0 发布说明](docs/release-notes-0.1.0.zh-CN.md)，外部发布演练记录见 [release-trial-evidence](docs/release-trial-evidence.zh-CN.md)，1.0 剩余执行顺序见 [stable-core-remaining-checklist](docs/stable-core-remaining-checklist.zh-CN.md)，1.0 稳定核心判断见 [stable-core-audit](docs/stable-core-audit.zh-CN.md)，后续验收标准见 [Roadmap](docs/roadmap.zh-CN.md)。

### CLI 快速开始

当前 CLI 实现了五十一个最小 MVP 命令：`adopt`、`adopt-review`、`adopt-plan`、`import-plan`、`init`、`new-book`、`new-chapter`、`plan-chapter`、`scene-plan`、`draft-brief`、`post-draft`、`review-gate`、`book-gate`、`audit-plan`、`retrospective`、`stats`、`scan-words`、`check-tables`、`audit-wave`、`audit-style`、`audit-continuity`、`audit-echoes`、`audit-info`、`audit-characters`、`agent-prompt`、`agent-connect`、`eval-agent`、`agent-smoke`、`agent-run`、`agent-exec`、`agent-inbox`、`agent-next`、`audit-agent-workflow`、`model-config`、`context-pack`、`workflow-plan`、`revision-plan`、`doctor`、`report`、`export-clean`、`audit-publish`、`publish-copy`、`export-metadata`、`export-manifest`、`export-epub`、`audit-epub`、`release-gate`、`audit-release-evidence`、`audit-dogfood-cycle`、`audit-stability-window` 和 `audit-stable-core`。

在仓库根目录运行：

```bash
python fictionops/src/fictionops/cli.py adopt existing-novel --out adopt_report.md
python fictionops/src/fictionops/cli.py adopt-review migrated-novel
python fictionops/src/fictionops/cli.py init my-novel --title "My Novel"
python fictionops/src/fictionops/cli.py new-book my-novel --book book_02 --title "第二本"
python fictionops/src/fictionops/cli.py new-chapter my-novel --chapter 002 --title "第二章"
python fictionops/src/fictionops/cli.py plan-chapter my-novel --chapter 002
python fictionops/src/fictionops/cli.py scene-plan my-novel --chapter 002
python fictionops/src/fictionops/cli.py draft-brief my-novel --chapter 002
python fictionops/src/fictionops/cli.py post-draft my-novel --chapter 002
python fictionops/src/fictionops/cli.py review-gate my-novel --chapter 002
python fictionops/src/fictionops/cli.py book-gate my-novel --book book_01
python fictionops/src/fictionops/cli.py audit-plan my-novel --book book_01
python fictionops/src/fictionops/cli.py retrospective my-novel --book book_01
python fictionops/src/fictionops/cli.py stats my-novel
python fictionops/src/fictionops/cli.py scan-words my-novel --watch "不是,没有"
python fictionops/src/fictionops/cli.py check-tables my-novel --all
python fictionops/src/fictionops/cli.py audit-wave my-novel
python fictionops/src/fictionops/cli.py audit-style my-novel
python fictionops/src/fictionops/cli.py audit-continuity my-novel
python fictionops/src/fictionops/cli.py audit-echoes my-novel
python fictionops/src/fictionops/cli.py audit-info my-novel
python fictionops/src/fictionops/cli.py audit-characters my-novel
python fictionops/src/fictionops/cli.py agent-prompt my-novel --role draft-writer --chapter 001
python fictionops/src/fictionops/cli.py agent-connect my-novel --name local-runner --mode runner
python fictionops/src/fictionops/cli.py eval-agent examples/demo_novel --chapter 002 --out docs/agent-evaluation-smoke.md
python fictionops/src/fictionops/cli.py agent-smoke my-novel --connector local-runner
python fictionops/src/fictionops/cli.py agent-run my-novel --role draft-writer --chapter 001 --out-dir 00_management/agent_runs/ch_001
python fictionops/src/fictionops/cli.py agent-exec my-novel/00_management/agent_runs/ch_001 --runner python run_model.py
python fictionops/src/fictionops/cli.py agent-inbox my-novel
python fictionops/src/fictionops/cli.py agent-next my-novel --book book_01 --chapter 001 --format json
python fictionops/src/fictionops/cli.py audit-agent-workflow my-novel --level runner
python fictionops/src/fictionops/cli.py model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor
python fictionops/src/fictionops/cli.py context-pack my-novel --task draft --chapter 001
python fictionops/src/fictionops/cli.py workflow-plan my-novel --stage review --chapter 001
python fictionops/src/fictionops/cli.py revision-plan my-novel --book book_01
python fictionops/src/fictionops/cli.py doctor my-novel --book book_01
python fictionops/src/fictionops/cli.py report my-novel --book book_01 --out 07_audits/doctor_report.md
python fictionops/src/fictionops/cli.py export-clean my-novel --book book_01
python fictionops/src/fictionops/cli.py audit-publish my-novel --book book_01
python fictionops/src/fictionops/cli.py publish-copy my-novel --book book_01
python fictionops/src/fictionops/cli.py export-metadata my-novel --book book_01
python fictionops/src/fictionops/cli.py export-manifest my-novel --book book_01
python fictionops/src/fictionops/cli.py export-epub my-novel --book book_01
python fictionops/src/fictionops/cli.py audit-epub my-novel --book book_01
python fictionops/src/fictionops/cli.py release-gate my-novel --book book_01
python fictionops/src/fictionops/cli.py audit-release-evidence . --file docs/release-trial-evidence.md
python fictionops/src/fictionops/cli.py audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md
python fictionops/src/fictionops/cli.py audit-stability-window . --file docs/stability-window-evidence.md
python fictionops/src/fictionops/cli.py audit-stable-core .
```

或在仓库根目录做本地安装后运行：

```bash
python -m pip install ./fictionops
fictionops --version
```

开发时也可以做可编辑安装：

```bash
python -m pip install -e ./fictionops
fictionops adopt existing-novel --out adopt_report.md
fictionops adopt-review migrated-novel
fictionops init my-novel --title "My Novel"
fictionops new-book my-novel --book book_02 --title "第二本"
fictionops new-chapter my-novel --chapter 002 --title "第二章"
fictionops plan-chapter my-novel --chapter 002
fictionops scene-plan my-novel --chapter 002
fictionops draft-brief my-novel --chapter 002
fictionops post-draft my-novel --chapter 002
fictionops review-gate my-novel --chapter 002
fictionops book-gate my-novel --book book_01
fictionops audit-plan my-novel --book book_01
fictionops retrospective my-novel --book book_01
fictionops stats my-novel
fictionops scan-words my-novel --watch "不是,没有"
fictionops check-tables my-novel --all
fictionops audit-wave my-novel
fictionops audit-style my-novel
fictionops audit-continuity my-novel
fictionops audit-echoes my-novel
fictionops audit-info my-novel
fictionops audit-characters my-novel
fictionops agent-prompt my-novel --role draft-writer --chapter 001
fictionops agent-connect my-novel --name local-runner --mode runner
fictionops eval-agent examples/demo_novel --chapter 002 --out docs/agent-evaluation-smoke.md
fictionops agent-smoke my-novel --connector local-runner
fictionops agent-run my-novel --role draft-writer --chapter 001 --out-dir 00_management/agent_runs/ch_001
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python run_model.py
fictionops agent-inbox my-novel
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
fictionops model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor
fictionops context-pack my-novel --task draft --chapter 001
fictionops workflow-plan my-novel --stage review --chapter 001
fictionops revision-plan my-novel --book book_01
fictionops doctor my-novel --book book_01
fictionops report my-novel --book book_01 --out 07_audits/doctor_report.md
fictionops export-clean my-novel --book book_01
fictionops audit-publish my-novel --book book_01
fictionops publish-copy my-novel --book book_01
fictionops export-metadata my-novel --book book_01
fictionops export-manifest my-novel --book book_01
fictionops export-epub my-novel --book book_01
fictionops audit-epub my-novel --book book_01
fictionops release-gate my-novel --book book_01
```

可用参数：

```bash
fictionops adopt existing-novel --format json
fictionops adopt existing-novel --max-files 120 --out adopt_report.md
fictionops init migrated-novel --title "迁移沙盒"
fictionops adopt existing-novel --copy-to migrated-novel --format json
fictionops adopt-review migrated-novel --format json
fictionops init my-novel --dry-run
fictionops init my-novel --language zh-CN
fictionops init my-novel --force
fictionops new-book my-novel --book book_02 --title "第二本"
fictionops new-book my-novel --book 2 --dry-run
fictionops new-chapter my-novel --book book_01 --chapter 002 --title "第二章"
fictionops new-chapter my-novel --chapter 002 --viewpoint "某人物" --kind "转场" --target-chars 8200
fictionops new-chapter my-novel --chapter 002 --dry-run
fictionops plan-chapter my-novel --book book_01 --chapter 002
fictionops plan-chapter my-novel --chapter 002 --dry-run
fictionops plan-chapter my-novel --chapter 002 --force
fictionops scene-plan my-novel --book book_01 --chapter 002
fictionops scene-plan my-novel --chapter 002 --out 06_drafts/book_01/scene_plans/ch_002_scene_plan.md
fictionops scene-plan my-novel --chapter 002 --format json
fictionops draft-brief my-novel --book book_01 --chapter 002
fictionops draft-brief my-novel --chapter 002 --include-context-content --max-chars-per-file 4000 --max-total-chars 24000
fictionops draft-brief my-novel --chapter 002 --out 06_drafts/book_01/draft_briefs/ch_002_draft_brief.md
fictionops post-draft my-novel --book book_01 --chapter 002
fictionops post-draft my-novel --chapter 002 --min-chapter-chars 800
fictionops post-draft my-novel --chapter 002 --out 07_audits/post_draft/ch_002_gate.md
fictionops review-gate my-novel --book book_01 --chapter 002
fictionops review-gate my-novel --chapter 002 --out 07_audits/review_gate/ch_002_review_gate.md
fictionops review-gate my-novel --chapter 002 --format json
fictionops book-gate my-novel --book book_01
fictionops book-gate my-novel --book book_01 --out 07_audits/book_gate/book_01_gate.md
fictionops book-gate my-novel --book book_01 --format json
fictionops audit-plan my-novel --book book_01
fictionops audit-plan my-novel --book book_01 --format json
fictionops retrospective my-novel --book book_01
fictionops retrospective my-novel --book book_01 --out 07_audits/book_retrospectives/book_01_report.md
fictionops stats my-novel --all
fictionops stats my-novel --metric cjk
fictionops stats my-novel --format json
fictionops audit-wave my-novel --flat-tolerance 200
fictionops audit-wave my-novel --min-spread-ratio 15
fictionops audit-wave my-novel --format json
fictionops audit-style my-novel --min-repeat 5
fictionops audit-style my-novel --watch "不是,没有,有人,忽然"
fictionops audit-style my-novel --format json
fictionops audit-continuity my-novel --skip-standard
fictionops audit-continuity my-novel --format json
fictionops audit-echoes my-novel --table "05_canon/foreshadowing_echo_table.md"
fictionops audit-echoes my-novel --no-text-scan
fictionops audit-echoes my-novel --format json
fictionops audit-info my-novel --table "05_canon/information_release_table.md"
fictionops audit-info my-novel --no-text-scan
fictionops audit-info my-novel --format json
fictionops audit-characters my-novel
fictionops audit-characters my-novel --format json
fictionops agent-prompt my-novel --role draft-writer --chapter 001
fictionops agent-prompt my-novel --role info-boundary-auditor --task review --chapter 002 --include-context --include-context-content --max-total-chars 24000
fictionops agent-prompt my-novel --role publisher --out 00_management/publisher_prompt.md
fictionops agent-connect my-novel --name local-runner --mode runner
fictionops eval-agent examples/demo_novel --chapter 002 --out docs/agent-evaluation-smoke.md
fictionops agent-smoke my-novel --connector local-runner
fictionops agent-run my-novel --role draft-writer --chapter 001 --out-dir 00_management/agent_runs/ch_001
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python run_model.py
fictionops agent-inbox my-novel
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
fictionops model-config my-novel --provider openai --planning-model gpt-planner --drafting-model gpt-writer --audit-model gpt-auditor --api-key-env OPENAI_API_KEY
fictionops model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor --write
fictionops model-config my-novel --provider local --format json
fictionops context-pack my-novel --task draft --chapter 001
fictionops context-pack my-novel --task review --chapter 002 --no-content
fictionops context-pack my-novel --task handoff --max-total-chars 80000 --out 00_management/context_pack.md
fictionops context-pack my-novel --task canon-sync --chapter 010 --format json
fictionops workflow-plan my-novel --stage all --out 00_management/workflow_plan.md
fictionops workflow-plan my-novel --stage review --chapter 002 --format json
fictionops revision-plan my-novel --book book_01
fictionops revision-plan my-novel --book book_01 --out 07_audits/revision_plan.md
fictionops revision-plan my-novel --book book_01 --format json
fictionops doctor my-novel --book book_01 --skip-standard
fictionops doctor my-novel --book book_01 --format json
fictionops doctor my-novel --book book_01 --outline 04_structure/book_outlines/book_01_outline.md
fictionops doctor my-novel --book book_01 --flat-tolerance 200
fictionops report my-novel --book book_01 --out 07_audits/doctor_report.md
fictionops report my-novel --book book_01 --format json --out 07_audits/doctor_report.json
fictionops export-clean my-novel --book book_01
fictionops export-clean my-novel --book book_01 --title "第一本" --out 08_publish/clean_markdown/book_01.md
fictionops export-clean my-novel --book book_01 --format json
fictionops audit-publish my-novel --book book_01
fictionops audit-publish my-novel --book book_01 --format json
fictionops audit-publish my-novel --book book_01 --min-chapter-chars 1000
fictionops publish-copy my-novel --book book_01
fictionops publish-copy my-novel --book book_01 --format json
fictionops publish-copy my-novel --book book_01 --dry-run
fictionops export-metadata my-novel --book book_01
fictionops export-metadata my-novel --book book_01 --format json
fictionops export-metadata my-novel --book book_01 --dry-run
fictionops export-manifest my-novel --book book_01
fictionops export-manifest my-novel --book book_01 --format json
fictionops export-manifest my-novel --book book_01 --dry-run
fictionops export-epub my-novel --book book_01
fictionops export-epub my-novel --book book_01 --format json
fictionops export-epub my-novel --book book_01 --dry-run
fictionops audit-epub my-novel --book book_01
fictionops audit-epub my-novel --book book_01 --format json
fictionops release-gate my-novel --book book_01
fictionops release-gate my-novel --book book_01 --out 07_audits/release_gate/book_01_release_gate.md
fictionops release-gate my-novel --book book_01 --format json
```

`init` 默认不会覆盖已有文件；使用 `--force` 才会覆盖生成文件。

`adopt` 会扫描已有写作目录，把旧大纲、正文、设定、人物、正史、复盘和归档材料映射到 FictionOps 层级，给出迁移阶段和建议目标路径，并可用 `--copy-to` 复制到一个已经 `init` 的独立 FictionOps 沙盒，但不会修改源文件；复制后还会写出 `00_management/adopted_handoff/adopt_manifest.json`，保留旧源路径和目标路径映射。`adopt-review` 会在复制后聚合 `doctor`、`audit-info`、`audit-characters` 和 `book-gate`，给出迁移沙盒是否还卡在导入队列、信息边界、人物资料或书级收束上的结论；`adopt-plan` 会继续把这些复查问题转成迁移整改任务清单，并把大量同类问题折叠成阶段化修复组，先判断修复顺序，再进入逐条任务；传入 `--write-groups` 时，它还会写出修复组索引和逐组 Markdown 工作文件，方便交给人或 agent 接手。`import-plan` 会检查 `06_drafts/import_queue/`，优先利用 adopt manifest 推断书/章目标，标出低置信度、目标已存在和重复目标，并且只在传入 `--apply` 时移动无歧义文件，传入 `--apply --create-scaffolds` 时还会为已移动章节补齐缺失的章节发动机和逐章复盘，传入 `--replace-placeholder-targets` 时只会替换生成模板式的占位章节目标。`doctor` 和 `report` 会汇总正文体量、章节体量波形、词频扫描、表格结构、风格模式、连续性、人物弧线与口吻资料、伏笔回声、信息边界、计划层同步、写后复盘收束、书级门禁状态、模型供应商配置、Agent 输出收件箱、已生成发布稿、发布元数据、发布包 manifest、EPUB 成品状态和最终发布门禁状态，适合做阶段性健康检查或交接报告。`scene-plan` 会把已填写的章节发动机转成场景骨架，但不代写正文，`draft-brief` 会把场景任务、范围化上下文和写作禁区合成写前任务单，`post-draft` 会检查单章草稿、发动机、逐章复盘和同步项是否已经关门，`review-gate` 会在细审前聚合单章写后、连续性、信息、人物、伏笔、风格和体量波形信号，`book-gate` 会在清稿导出前聚合书级计划、复盘、修订、表格结构、词频提示和体量波形信号，`scan-words` 会做通用高频词和关注词扫描，`check-tables` 会检查 Markdown 表格结构和占位行，`audit-wave` 会检查章节体量波形是否过平或突跳，`audit-info` 会检查信息释放表是否缺少认知状态或可能提前命中正文，`audit-characters` 会检查人物弧线、智慧模式、口吻资料和人物索引覆盖，`agent-prompt` 会生成角色专属 Agent 提示词，`agent-connect` 会生成外部 runner 或 controller 的接入套件，包括 manifest、环境变量样例、烟测命令和 adapter stub，但不调用模型、不保存密钥，`agent-run` 会把提示词、范围化上下文、模型配置和可选写前任务单打成 prepare-only 任务包但不调用模型、不覆盖正文，`agent-exec` 会把任务包喂给外部 runner，把 stdout 保存成暂存输出并写出执行回执，但不应用到正文或正史，`agent-inbox` 会检查外部 runner 回写到任务包目录里的输出是否存在、唯一且能进入后续门禁，`agent-next` 会为外部 controller 选择下一条安全 FictionOps 命令，但不执行命令、不调用模型、不应用输出，`model-config` 会记录本地模型供应商与模型名配置，但不保存真实密钥、不调用模型，`context-pack` 会按写作、审稿、交接、正史同步等任务生成带单文件和整包预算的范围化上下文包，交接包会携带模型配置、人物记忆、正史状态、修订计划和门禁报告，避免 Agent 每次吞全项目，`workflow-plan` 会把从种子到发布的流程转成分阶段命令清单，`revision-plan` 会把审计问题、表格结构问题和低优先级词频提示转成按优先级排序的修订任务清单。`export-clean` 会把一本书的章节草稿合并到 `08_publish/clean_markdown/`，`audit-publish` 会检查 clean Markdown 的章节顺序、缺章、残留草稿标记和过短章节，`publish-copy` 会从项目证据生成可编辑的简介、标签和关键词草稿，`export-metadata` 会把发布清单里的简介、标签、分类、作者名和可选封面路径导出为 JSON，`export-manifest` 会把 clean Markdown、metadata JSON 和可选封面组合成带 hash 的发布包清单，`export-epub` 会导出带基础样式、可选封面的 EPUB3 文件，`audit-epub` 会验收 EPUB 结构和新鲜度，`release-gate` 会在上传或归档前聚合书级收束、发布稿、元数据、manifest 和 EPUB 准备状态，`audit-release-evidence` 会审计 FictionOps 自身包发布演练证据，避免空模板或未复核草稿误关发布里程碑，`audit-dogfood-cycle` 会审计 1.0 所需的持续真实项目 dogfood 周期证据，`audit-stability-window` 会审计兼容性/稳定窗口证据，`audit-stable-core --format json` 会输出结构化 `action_items`，列出剩余证据线的文件、验收命令和完成标准，但这些行动项本身不能当作完成证据。

安装包会携带 `src/fictionops/templates/` 下的模板文件；根目录 `templates/` 是工作区副本，测试会检查两者保持一致。

### 测试

```bash
python -m unittest discover -s fictionops/tests -v
```

## 1. 为什么需要 FictionOps

长篇小说常常不是死在句子不够漂亮，而是死在系统失忆：

- 人物逐渐失去各自的智慧模式、声音、弱点和犯错方式。
- 大纲变成机械清单，章节像按格子填内容。
- 伏笔要么几百页没人想起，要么每次出现都被解释一遍。
- 作者知道得太多，角色也开始说出作者级别的信息。
- 重要秘密过早变成公共知识。
- 章节体量太整齐，阅读压力变平。
- 旧大纲、新大纲、设定、正文、发布稿混在一起。
- AI 辅助写作会放大解释、排比、模板句和前后遗忘。

FictionOps 把长篇当作一个结构化创作项目来维护。它给每个阶段一个位置：

- 故事种子
- 世界规则
- 人物弧线
- 卷、书、章节结构
- 章节发动机
- 正文写作
- 连续性审计
- 风格与读者体验审计
- 正史同步
- 发布包管理

目标不是让写作机械化，而是保护那些应该保持鲜活的部分。

## 2. 设计理念

### 2.1 大纲是承重结构，不是笼子

大纲应该防止故事走丢，但不应该把每个场景都压成预写清单。

FictionOps 区分两类东西：

- **梁**：不可逆选择、关系转折、信息边界、人物终点、系统压力、主题问题。
- **砖**：谁打断对话、哪个物件临时变重要、章节在哪里收束、哪个小角色误读现场。

梁要稳，砖可以在写作中改变。

### 2.2 角色不能共享作者的大脑

每个角色都应该有自己的知识边界、思考方式、情绪习惯、盲点和失败模式。

作者可以知道全图，角色只能知道：

- 自己看见了什么
- 自己听见了什么
- 自己误读了什么
- 自己愿意承认什么
- 阶层、地域、职业、宗教或创伤教会他注意什么

因此 FictionOps 强调信息释放表、人物智慧模式表和人物口吻表。

### 2.3 伏笔需要回声，不需要讲解

长线伏笔至少有十个状态：

- 埋下
- 轻轻回声
- 转化或兑现

回声最好通过这些方式出现：

- 物件转手
- 同一动作在不同语境下重复
- 谣言跨地区变形
- 一句话被改掉一个字
- 身体反应
- 禁忌话题周围的沉默
- 角色误用旧信息

读者应该被唤起记忆，而不是被旁白提醒。

### 2.4 章节需要发动机

章节不能只定义为“这一章要写哪些点”。它需要内部发动机。

FictionOps 使用五列表：

| 列 | 问题 |
| --- | --- |
| Pressure 压力 | 这一章有什么外部力量进入？ |
| Desire 欲望 | 视角人物此刻想要什么？ |
| Obstacle 阻碍 | 什么阻止、扭曲或提高了代价？ |
| Change 变化 | 章末有什么不可回退的改变？ |
| Remainder 余留 | 什么仍未说完、未解决、被误解或情绪上没有落地？ |

这样可以让章节既活着，又不丢长线连续性。

### 2.5 风格审计不是风格警察

FictionOps 不会简单禁止某些词或句式。它关心的是：这个模式正在承担什么功能？

例如：

- 太多“不是/没有”可能说明叙述一直在用缺席定义世界。
- 太多排比可能让读者感觉被句子推着走。
- 太多“其实/真正/事实上”可能说明作者在替读者纠偏。
- 太多“忽然/突然”可能把情绪变成按钮。
- 太完整的解释会挤掉读者思考空间。

目标不是清空模式，而是让文字保持新鲜、具身和有呼吸。

## 3. FictionOps 九层流程

### 第 1 层：故事种子

项目从一组简短但强约束的创作承诺开始：

- 前提
- 类型与子类型
- 情绪承诺
- 核心冲突
- 主题问题
- 目标读者体验
- 色调
- 故事拒绝变成什么

### 第 2 层：世界与规则系统

世界设定不等于一次性讲给读者听。常见文件包括：

- 地理
- 历史
- 势力
- 宗教与神话版本
- 阶层结构
- 经济与物流
- 法律与治理
- 命名规则
- 地域口吻

关键区分：

**作者真相不等于世界内部信仰。**

同一个神话、法律、事件或历史记忆，应该允许不同势力拥有不同版本。

### 第 3 层：人物弧线系统

主要人物至少需要维护：

- 起点创伤
- 公开身份
- 私人欲望
- 恐惧
- 智慧模式
- 盲点
- 典型错误
- 关系锚点
- 道德压力点
- 成长路径
- 失败路径
- 终点或转化方向

不是所有聪明人都是谋士。有人擅长读人但不懂系统，有人懂物流但情绪迟钝，有人行动果断但抽象能力弱，有人政治敏锐却身体粗心。角色应该有符合自己的犯错方式。

### 第 4 层：长结构

这一层维护：

- 系列总纲
- 卷纲
- 书纲
- 幕结构
- 不可逆事件
- 视角分配
- 节奏波形
- 升级逻辑
- 每本书的进入状态与离开状态

它要回答：

- 这本书改变了什么不能复原的东西？
- 哪些角色带着一种信念进入，又带着另一种信念离开？
- 哪个系统被揭开、损坏、建立或误解？
- 哪些秘密仍然局部，哪些扩散，哪些变形？

### 第 5 层：章节发动机

每章写作前维护一张表：

```markdown
| Chapter | Pressure | Desire | Obstacle | Change | Remainder | Required Echo | Info Boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | ... | ... | ... | ... | ... | ... | ... |
```

写作前还应检查：

- 上一章留下了什么压力？
- 视角人物从上次出场带来了什么情绪残留？
- 哪条伏笔上一次在哪里回声？
- 此时谁知道什么？
- 哪些信息应该保持错误、局部或沉默？

### 第 6 层：正文写作

写作应优先依赖场景、身体、动作、对话、物件和误读。

应避免：

- 旁白解释每个动机
- 角色在不安全场合公开讨论秘密
- 所有聪明人都像同一个谋士
- 每章结尾都变成揭晓
- 情绪后果过快消解
- 把世界观写成讲义

推荐方法：

- 规则先被感到，再被命名。
- 物件以新含义回归。
- 角色误解了一个正确事实。
- 沉默承担政治重量。
- 场景在解释完成前结束。

### 第 7 层：连续性审计

连续性审计检查：

- 上章压力
- 人物残留
- 时间线
- 物件位置
- 伤病和身体代价
- 关系状态
- 信息边界
- 公共谣言与私人真相
- 正史冲突
- 伏笔回声状态

连续性不是只问“事实对不对”，还要问：

- 这一章有没有记得角色刚刚经历过什么？
- 读者有没有得到足够的轻回声？
- 有没有人知道得太早？
- 谣言扩散速度是否符合世界物流？
- 秘密是否在耳朵太多的房间被公开讨论？

### 第 8 层：风格与读者体验审计

检查对象包括：

- 高频词
- 重复句式动作
- 解释过满
- 对话口吻变平
- 对称过度
- 开头和结尾太同款
- 章节体量波形
- 情绪节奏
- AI 模板感

这一层不抽象评价“美不美”，而是判断文字是否服务当前章节压力。

### 第 9 层：发布层

发布层管理：

- 清稿正文
- 校对版
- EPUB
- 纸书排版
- 标签
- 简介
- 必要的内容提示
- 字数统计
- 发布说明
- 旧大纲归档

规划文件、正文文件和发布文件不应该混在一起。

## 4. 推荐项目结构

```text
my-novel/
  README.md
  project.yml

  00_management/
    handoff_log.md
    current_context.md
    workflow.md
    decision_log.md
    glossary.md

  01_story_seed/
    premise.md
    themes.md
    reader_promise.md
    tonal_palette.md
    anti_goals.md

  02_world/
    geography.md
    history.md
    factions.md
    religion_and_myth.md
    economy.md
    law_and_governance.md
    naming_rules.md
    regional_voices.md

  03_characters/
    character_index.md
    protagonist_arc.md
    antagonist_arc.md
    relationship_map.md
    intelligence_profiles.md
    voice_profiles.md

  04_structure/
    series_outline.md
    volume_01_outline.md
    book_01_outline.md
    act_pressure_chain.md
    timeline.md

  05_canon/
    information_release_table.md
    foreshadowing_echo_table.md
    object_locations.md
    open_questions.md
    resolved_questions.md

  06_drafts/
    book_01/
      chapters/
      chapter_engines/
      revision_notes/

  07_audits/
    continuity/
    character_arc/
    style/
    pacing/
    book_retrospectives/

  08_publish/
    clean_markdown/
    epub/
    print/
    synopsis/
    metadata/
    manifest/

  99_archive/
    old_outlines/
    deprecated_canon/
    abandoned_scenes/
```

核心原则是：每类文件只承担一种责任。修改一个设定时，要知道它应该同步到哪里，也知道它不该污染哪里。

## 5. Agent 角色

FictionOps 可以实现为一个带模式的 Agent，也可以拆成多个专职 Agent。

### Architect 架构师

维护系列、卷、书、幕、不可逆事件和节奏波形。它保护“梁”，不微操“砖”。

### Canon Keeper 正史管理员

维护时间线、世界规则、物件位置、信息已知/未知、命名一致性和废弃设定。它必须区分作者真相、角色信念、公共谣言、官方记录和后世解释。

### Character Arc Auditor 人物弧线审计

检查角色是否在变化中仍然是自己。关注动机、创伤、智慧模式、说话方式、典型错误、关系记忆和情绪残留。

### Information Boundary Auditor 信息边界审计

追踪谁知道什么、以什么形式知道。特别适合政治小说、悬疑、宫廷、神话奇幻和战争叙事。

### Foreshadowing Auditor 伏笔审计

追踪长线伏笔的第一次埋下、上次回声、当前读者记忆、下一次轻回声、禁止提前解释和兑现方向。

### Chapter Planner 章节规划

生成五列章节发动机，并给出场景顺序、必要正史检查和可弹性处理的空间。

### Draft Writer 正文写手

根据章节发动机写场景，必须尊重视角知识、人物口吻、地域语言、身体连续性、情绪残留和当前信息边界。

### Style Auditor 风格审计

检查重复词、句式动作、解释过满、对话节奏趋同、过度整齐、AI 模板感。它应该提出选择，而不是把文字磨平。

### Publisher 发布员

处理清稿、校对、字数统计、标签、简介、EPUB 和发布元数据。它不应覆盖草稿或规划文件。

## 6. 核心表格

### 6.1 信息释放表

```markdown
| Event / Secret | Author Truth | Reader Knows | Character A Knows | Character B Knows | Public Version | Official Version | Next Release |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

用于回答：**谁知道什么？以什么版本知道？**

### 6.2 伏笔回声表

```markdown
| Thread | First Plant | Last Echo | Current State | Next Light Echo | Do Not Reveal Yet | Payoff Direction |
| --- | --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | ... | ... |
```

用于回答：**读者如何记住这条线，而不是被讲解？**

### 6.3 人物智慧模式表

```markdown
| Character | Sees Quickly | Misses | Solves By | Fails By | Speech Mode | Growth Pressure |
| --- | --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | ... | ... |
```

用于防止所有角色都变成同一种聪明。

### 6.4 章节发动机

```markdown
| Chapter | Pressure | Desire | Obstacle | Change | Remainder | Required Echo | Info Boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | ... | ... | ... | ... | ... | ... | ... |
```

用于正文写作前。

### 6.5 复盘表

```markdown
| Chapter | Function | Pressure Carried | Character Residue | Echoes Created | Echoes Paid | Risk | Revision Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

用于一本书写完后。

## 7. 当前 CLI 范围

当前第一版已经覆盖旧项目接入诊断、管理 Markdown 文件、静态审计、词频扫描、表格检查、Agent 提示词、任务包、输出收件箱与模型供应商配置、范围化上下文包、健康报告、clean Markdown 导出、发布稿审计、发布文案草稿、发布元数据导出、发布包 manifest、带样式 EPUB 导出、EPUB 包审计和最终发布门禁：

```bash
fictionops adopt existing-novel --out adopt_report.md
fictionops init my-novel
fictionops new-book my-novel --book book_01
fictionops new-chapter my-novel --book book_01 --chapter 001
fictionops plan-chapter my-novel --book book_01 --chapter 001
fictionops scene-plan my-novel --book book_01 --chapter 001
fictionops draft-brief my-novel --book book_01 --chapter 001
fictionops post-draft my-novel --book book_01 --chapter 001
fictionops review-gate my-novel --book book_01 --chapter 001
fictionops book-gate my-novel --book book_01
fictionops audit-plan my-novel --book book_01
fictionops audit-continuity my-novel --skip-standard
fictionops audit-style my-novel/06_drafts/book_01
fictionops audit-echoes my-novel
fictionops audit-info my-novel
fictionops audit-characters my-novel
fictionops agent-prompt my-novel --role draft-writer --chapter 001
fictionops agent-run my-novel --role draft-writer --chapter 001 --out-dir 00_management/agent_runs/ch_001
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python run_model.py
fictionops agent-inbox my-novel
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
fictionops model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor
fictionops context-pack my-novel --task draft --chapter 001
fictionops workflow-plan my-novel --stage review --chapter 001
fictionops revision-plan my-novel --book book_01
fictionops stats my-novel/06_drafts/book_01
fictionops audit-wave my-novel/06_drafts/book_01
fictionops retrospective my-novel --book book_01
fictionops export-clean my-novel --book book_01
fictionops audit-publish my-novel --book book_01
fictionops publish-copy my-novel --book book_01
fictionops export-metadata my-novel --book book_01
fictionops export-manifest my-novel --book book_01
fictionops export-epub my-novel --book book_01
fictionops audit-epub my-novel --book book_01
fictionops release-gate my-novel --book book_01
```

可能输出：

- 人物情绪残留缺失
- 可疑信息泄露
- 物件位置未解决
- 章节结尾类型重复
- 高频词簇
- 某伏笔太久没有回声
- 角色专属 Agent 提示词
- 写作或审稿任务的范围化上下文包
- 从章节发动机生成的场景骨架
- 带场景护栏和缺失上下文提示的写前任务单
- 检查草稿、发动机、复盘和同步项的写后关门报告
- 聚合写后和审计信号的单章审稿门禁报告
- 清稿导出前的书级收束门禁报告
- 按优先级排序的修订任务清单
- 本地模型供应商配置缺失或存在不安全项
- 人物弧线、智慧模式或口吻资料缺口
- 章节体量波形报告
- 上传或归档前的最终发布门禁报告
- 公共谣言扩散过快

## 8. MVP 范围

### MVP 1：项目模板

- 文件夹结构
- Markdown 模板
- 通用示例项目
- README 文档
- 工作流指南

不需要模型集成。

### MVP 2：静态审计 CLI

- 分章字数
- 章节体量波形
- 高频词扫描
- 重复短语扫描
- 表格完整度检查
- 章节与正史文件的简单链接检查

仍不需要模型集成。

### MVP 3：Agent 辅助报告

- 连续性报告
- 人物弧线报告
- 伏笔报告
- 信息边界报告
- 章节规划助手

模型供应商应可配置。

### MVP 4：正文辅助

- 从章节发动机生成场景骨架（`scene-plan`）
- 写前任务单（`draft-brief`）
- 写后关门检查（`post-draft`）
- 单章审稿门禁（`review-gate`）
- 书级收束门禁（`book-gate`）
- 严格视角和正史约束下的正文写手提示词（`agent-prompt --role draft-writer`）
- 从审计问题生成优先级修订建议（`revision-plan`）
- 风格审计（`audit-style`）

这一层应该保持可选。系统也应服务于只想规划和审计、不想生成正文的作者。

## 9. 数据格式

FictionOps 应优先使用普通文件：

- Markdown：给人读的文档
- YAML 或 JSON：结构化元数据
- CSV：可选，用于表格软件

示例 `project.yml`：

```yaml
project:
  title: "Untitled Novel"
  language: "zh-CN"
  genre: "fantasy"
  status: "planning"

workflow:
  chapter_engine: true
  continuity_audit: true
  style_audit: true
  update_handoff_log: true

models:
  provider: "openai"
  config_file: "00_management/model_config.json"
  api_key_env: "OPENAI_API_KEY"
  base_url: ""
  planning_model: "configurable"
  drafting_model: "configurable"
  audit_model: "configurable"

paths:
  canon: "05_canon"
  drafts: "06_drafts"
  audits: "07_audits"
  publish: "08_publish"
```

普通文件的好处是：

- 可版本管理
- 可审阅
- 容易备份
- 模型无关
- 编辑器友好

## 10. 开源定位

FictionOps 应该被定位为：

**长篇小说连续性、规划和修订的工作流与工具箱。**

它不应该被宣传成：

- 自动小说家
- 作者替代品
- 可保证出版质量的机器
- 单纯设定数据库
- 单纯提示词集合

它最强的价值在于把这些能力组合起来：

- 叙事架构
- 正史追踪
- 信息边界
- 伏笔回声管理
- 角色专属智慧模式
- 文风模式审计
- 发布工作流

## 11. 它和普通写作软件有什么不同

大多数写作软件保存文本。FictionOps 保存文本与长期叙事压力之间的关系。

它追踪：

- 读者记得什么
- 角色记得什么
- 世界认为发生了什么
- 官方记录写成了什么
- 事实真相是什么
- 哪些东西暂时不能解释
- 上一次承载回声的是哪个物件、句子或伤口

适用场景包括：

- 史诗奇幻
- 历史小说
- 政治阴谋
- 悬疑
- 多卷文学小说
- 网文
- 连载小说
- RPG 叙事圣经
- 协作写作工作室

## 12. 风险与边界

### 过度工程化

如果每章都变成填表，小说会死。

缓解方式：

- 章节发动机保持短小
- 区分梁和砖
- 允许草稿反过来修改大纲
- 决策可以事后记录

### AI 口吻压平

Agent 可能让所有聪明角色说话都一样。

缓解方式：

- 维护人物智慧模式
- 维护地域与阶层口吻
- 单独审计对话
- 保留错误和盲点

### 虚假的连续性自信

表格完整不代表故事好读。

缓解方式：

- 加入读者体验审计
- 追踪情绪残留
- 审查章节开头和结尾
- 保留人工 override

### 剧透泄露

如果每次任务都加载全量正史，Agent 可能把未来真相泄进早期章节。

缓解方式：

- 使用范围化上下文
- 分离作者真相和当前章节真相
- 写作前强制做信息边界检查

## 13. 路线图

### Phase 0：白皮书与模板

- README / 中文 README / 贡献与发布治理文件
- 通用文件结构和可打包模板
- 故事种子、章节发动机、信息释放、伏笔回声、人物弧线、复盘、风格审计和发布清单模板
- 通过 `fictionops init` 生成示例项目骨架

### Phase 1：CLI 原型

- 旧项目接入诊断：`adopt`
- 项目、书、章节脚手架：`init`、`new-book`、`new-chapter`
- 章节规划与写前准备：`plan-chapter`、`scene-plan`、`draft-brief`
- 基础静态扫描：`stats`、`scan-words`、`check-tables`

### Phase 2：审计报告

- 连续性和项目记忆审计：`audit-continuity`
- 伏笔回声审计：`audit-echoes`
- 信息边界审计：`audit-info`
- 人物弧线、智慧模式和口吻审计：`audit-characters`
- 书纲计划审计和复盘聚合：`audit-plan`、`retrospective`
- 章节波形和风格审计：`audit-wave`、`audit-style`
- 项目健康报告和里程碑摘要：`doctor`、`report`

### Phase 3：Agent 集成

- 可配置模型供应商边界，不保存真实密钥：`model-config`
- 架构、正史、人物、信息、伏笔、规划、写作、风格和发布角色提示词：`agent-prompt`
- 外部 runner/controller 接入套件：`agent-connect`
- prepare-only 模型/API 任务包：`agent-run`
- 外部 runner 执行桥，保存暂存输出但不自动应用：`agent-exec`
- Agent 输出暂存收件箱审计：`agent-inbox`
- Level 2 controller 下一步安全命令选择：`agent-next`
- 写作、审稿、交接、正史同步任务的范围化上下文，支持内容预算，交接任务会带上里程碑产物：`context-pack`
- 分阶段工作流清单：`workflow-plan`
- 审计到修订的优先级工作流：`revision-plan`
- 单章、书级和发布门禁：`review-gate`、`book-gate`、`release-gate`

### Phase 4：发布管线

- 清稿正文生成与审计：`export-clean`、`audit-publish`
- 发布文案草稿：`publish-copy`
- 元数据导出：`export-metadata`
- 可复现发布包 manifest：`export-manifest`
- 带样式 EPUB 导出和包审计：`export-epub`、`audit-epub`
- 纳入书级收束和发布物状态的最终发布门禁：`release-gate`

## 14. 指导原则

FictionOps 的存在，是为了帮一部长篇记住自己，而不是逼它变得机械。

它应该保护：

- 不确定
- 沉默
- 误读
- 情绪残留
- 角色专属智慧
- 延迟理解
- 活的文字

如果工作流让小说过于整齐，应该弯曲的是工作流。

故事优先。

## 新手与模型接入

- [快速开始](docs/getting-started.zh-CN.md)：按新项目、旧项目迁移、接模型/API 三条入口上手。
- [模型供应商接入](docs/model-providers.zh-CN.md)：DeepSeek、通义千问、Kimi、GLM、豆包 Ark、硅基流动、本地 OpenAI-compatible 服务和 OpenAI Chat Completions 的 runner 配置起点。
- [Getting started](docs/getting-started.md) and [Model providers](docs/model-providers.md) are also available in English.

## 15. 示例

- [可运行 demo 项目](examples/demo_novel/README.md)：一个微型 FictionOps 项目，可跑书纲同步、场景计划、写前 brief、上下文包和 doctor 报告。
- [最小示例教程](docs/tutorial-demo.zh-CN.md)：按步骤演示如何运行 `examples/demo_novel/`。
- [长篇大纲迁移案例（中文）](examples/long_novel_outline_migration_case_zh.md)：展示一部多卷长篇如何从混乱大纲、修订意见和设定碎片，迁移为可维护的 FictionOps 结构。
