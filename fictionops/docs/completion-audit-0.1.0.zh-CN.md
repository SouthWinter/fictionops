# FictionOps 0.1.0 完成审计

审计日期：2026-07-06

## 结论

FictionOps 0.1.0 的 MVP 范围已经具备可发布证据：CLI 命令、模板、文档、测试、示例、wheel/sdist 构建、安装烟测、CI 配置和 PyPI 发布自动化均已存在，并通过本地验证。

这不等于 FictionOps 作为长期产品已经完成。当前完成的是 **0.1.0 pre-alpha MVP**：一个可以开源展示、安装试用、用于真实项目 dogfood 的本地工作流工具。

## 审计范围

本审计覆盖：

- 项目结构与模板。
- CLI 命令覆盖。
- 写作、审计、Agent 协作和发布流程。
- 示例项目和教程。
- 测试与构建证据。
- 开源维护文件。
- 已知边界。

## 要求与证据

| 要求 | 当前证据 | 状态 |
| --- | --- | --- |
| 旧项目可诊断迁入 | `adopt` 只读扫描已有写作目录，输出分层映射、迁移阶段、建议目标路径、风险提示和下一步建议 | 已完成 |
| 真实旧项目 adopt dogfood | `docs/dogfood-legacy-adopt.zh-CN.md` 记录一次百万字级目录扫描、误判修正、迁移沙盒复跑和迁移建议 | 已完成 |
| 迁移沙盒可复制 | `adopt --copy-to` 可把候选文件复制到已初始化 FictionOps 项目，不修改源目录；同名目标会自动消歧，并写出 adopt manifest | 已完成 |
| 迁移后可复查 | `adopt-review` 聚合 `doctor`、`audit-info`、`audit-characters` 和 `book-gate`，并能识别 `import_queue` 未整理；`07_audits/adopt_review/waivers.json` 可记录人工延期阻塞，并区分总问题、活跃问题和已豁免问题 | 已完成 |
| 迁移整改可计划 | `adopt-plan` 把 `adopt-review` 的复查问题转成按优先级排序的迁移整改任务，并用 `task_groups` 把大量同类问题折叠成阶段化修复组；真实示例长篇沙盒 530 条任务可折成 16 组，并可用 `--write-groups` 写出 17 个修复组工作文件；已延期阻塞不会重新生成当前任务 | 已完成 |
| 导入队列可整理 | `import-plan` 可利用 adopt manifest、文件名和标题推断 `06_drafts/import_queue/` 中文件的书/章目标，标出歧义，只在 `--apply` 时移动安全文件，可用 `--create-scaffolds` 补齐章节维护入口，并可显式替换初始化占位目标；真实示例长篇沙盒已从 102 个导入正文清到 0 | 已完成 |
| 项目可初始化 | `init` 命令、模板目录、安装烟测生成标准项目骨架 | 已完成 |
| 书/章可维护 | `new-book`、`new-chapter`、`plan-chapter`、章节发动机模板和书纲模板 | 已完成 |
| 写前可拆场景 | `scene-plan`、`draft-brief`、demo 工作流测试 | 已完成 |
| 写后可关门 | `post-draft`、逐章复盘模板、`review-gate` 测试 | 已完成 |
| 信息边界可维护 | `information_release_table` 模板、`audit-info`、demo 信息审计测试 | 已完成 |
| 伏笔回声可维护 | `foreshadowing_echo_table` 模板、`audit-echoes` 测试 | 已完成 |
| 人物记忆可维护 | 人物弧线、智慧模式、口吻资料、`audit-characters`、demo 人物审计测试 | 已完成 |
| 文风/词频/章节波形可审计 | `audit-style`、`scan-words`、`audit-wave` 和对应测试 | 已完成 |
| Agent 接手可范围化 | `context-pack`、`agent-prompt`、`agent-connect`、`agent-smoke`、`agent-run`、`agent-exec`、`agent-inbox`、`agent-next`、`model-config`、`workflow-plan`、`revision-plan`；`agent-connect` 可生成外部 runner/controller 接入套件，`agent-smoke` 可用 no-network adapter 跑通 workflow audit、任务包、外部执行和 inbox 暂存闭环，`agent-run` 可生成 prepare-only 任务包，`agent-exec` 可把任务包交给外部 runner 并保存暂存输出，`agent-inbox` 可检查回传暂存输出，`agent-next` 可为外部 controller 选择下一条安全命令；`examples/agent_runner_echo.py` 提供不调用模型的外部 runner 示例，`examples/agent_runner_openai_chat.py` 提供 OpenAI-compatible Chat Completions 外部 runner dry-run 示例，`examples/agent_runner_openai_responses.py` 提供 OpenAI Responses API 外部 runner dry-run 示例，`examples/agent_controller_next.py` 提供不执行命令的单步 controller 示例，`examples/agent_controller_loop.py` 提供只执行安全命令并在复核边界停止的多步 controller 示例；`docs/agent-connector-contract.md` / `docs/agent-connector-contract.zh-CN.md` 记录外部 runner/controller 的接入契约和烟测证据；`docs/agent-integration.md` / `docs/agent-integration.zh-CN.md` 说明手动聊天、外部 runner、真实模型 runner 和 controller loop 的接入方式；FictionOps 不保存密钥、不自动应用输出、不覆盖正文 | 已完成 |
| 单章、书级、发布门禁可用 | `review-gate`、`book-gate`、`release-gate` 和对应测试 | 已完成 |
| 包发布证据可审计 | `audit-release-evidence` 能检查发布演练证据是否仍为空模板、未复核草稿、无效 run URL/hash、缺安装烟测或非 `accepted` 结论，避免 0.4 被弱证据误关 | 已完成 |
| 持续 dogfood 周期证据可审计 | `audit-dogfood-cycle` 能检查 1.0 所需持续维护周期是否仍为空模板、非 ready 最终状态、非零导入队列或阻塞项、缺兼容性/恢复说明或非 `accepted` 结论 | 已完成 |
| 稳定窗口证据可审计 | `audit-stability-window` 能检查 1.0 所需兼容性/稳定窗口是否仍为空模板、缺证据引用、缺兼容性/破坏性变化/恢复说明或非 `accepted` 结论 | 已完成 |
| 稳定核心聚合证据可审计 | `audit-stable-core` 能聚合发布证据、持续 dogfood、稳定窗口证据、稳定核心文档和里程碑状态，避免 1.0 被局部证据误关 | 已完成 |
| 清稿和发布包可生成 | `export-clean`、`publish-copy`、`export-metadata`、`export-manifest`、`export-epub` | 已完成 |
| EPUB 可审计 | `audit-epub`，有效、损坏、过期 EPUB 测试 | 已完成 |
| 项目健康可汇总 | `doctor`、`report` 覆盖计划、复盘、人物、信息、Agent 输出收件箱、模型配置、发布等摘要 | 已完成 |
| 开源文档入口存在 | README、README.zh-CN、docs、workflow、examples；`docs/agent-connector-contract.md` / `docs/agent-connector-contract.zh-CN.md` 记录外部 agent 接入契约，`docs/compatibility.md` / `docs/compatibility.zh-CN.md` 记录版本化兼容策略，`docs/known-limits.md` / `docs/known-limits.zh-CN.md` 记录当前不保证的边界，`docs/recovery.md` / `docs/recovery.zh-CN.md` 记录常见恢复路径，`docs/milestone-status.md` / `docs/milestone-status.zh-CN.md` 记录路线图逐项证据状态，`docs/stable-core-audit.md` / `docs/stable-core-audit.zh-CN.md` 记录 1.0 稳定核心证据矩阵 | 已完成 |
| 英文外部接手入口存在 | `docs/cli.md`、`docs/cli-contracts.md`、`docs/compatibility.md`、`docs/agent-protocol.md`、`docs/agent-connector-contract.md`、`docs/agent-workflow.md`、`docs/agent-integration.md`、`docs/tutorial-demo.md`、`docs/migration.md`、`docs/end-to-end-migration-publish.md`、`docs/testing.md`、`docs/release.md`、`docs/known-limits.md` 和 `CONTRIBUTING.md` 覆盖核心 CLI、命令契约、兼容性策略、Agent 协议、接入契约、接入方式、demo、迁移、端到端迁移/发布案例、测试、发布、已知限制和贡献路径；全量细节仍以中文文档为准 | 已完成 |
| 可运行示例存在 | `examples/demo_novel/`、`examples/legacy_novel_source/`、`docs/tutorial-demo.zh-CN.md`、demo 测试和 legacy migration example 测试 | 已完成 |
| 维护治理存在 | LICENSE、CHANGELOG、中英文 CONTRIBUTING、release checklist、PyPI/release guide、release-trial-evidence 外部发布演练证据模板、issue/PR 模板 | 已完成 |
| CI 与发布自动化存在 | `.github/workflows/fictionops-ci.yml`、`.github/workflows/fictionops-publish.yml`；publish workflow 使用手动触发、environment 隔离和 Trusted Publishing；CI/publish 分发包内容检查覆盖当前 Agent 接入、兼容性、已知限制、OpenAI runner 和 controller loop 产物；两条 workflow 都会从构建好的 wheel 安装到干净 venv 并运行 CLI 烟测；publish workflow 会生成独立的 `fictionops-release-trial-evidence-<version>` 证据草稿 artifact，且不混入 `fictionops-dist-<version>` 发布包 artifact | 已完成 |
| 包可构建并安装 | wheel 构建、wheel 内容检查、sdist 构建、sdist 内容检查、源码安装烟测、构建后 wheel 干净虚拟环境安装烟测 | 已完成 |

## 验证命令

最近一次本地验证目标：

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

验证摘要：

- `152 tests OK`
- `fictionops-0.1.0-py3-none-any.whl` 构建成功
- `fictionops-0.1.0.tar.gz` 构建成功
- wheel 内容检查通过
- sdist 内容检查通过
- 安装烟测通过，包括源码安装和构建后 wheel 干净虚拟环境安装；`fictionops --version`、`python -m fictionops --version`、`agent-connect --help`、`agent-smoke --help`、`agent-exec --help`、`agent-next --help`、`audit-agent-workflow --help`、`audit-release-evidence --help`、`audit-dogfood-cycle --help`、`audit-stability-window --help`、`audit-stable-core --help`、`init` 和 `doctor` 可用
- publish workflow 会自动生成 release trial evidence draft artifact；这增强了 0.4 的外部证据采集，但仍不替代真实 GitHub Actions run、TestPyPI/PyPI 记录和安装烟测后的最终验收。

## 不纳入 0.1.0 完成定义

以下事项重要，但不属于当前 MVP 完成定义：

- 自动调用大模型生成正文。
- 云端数据库、Web UI 或多人协作服务器。
- 文学质量自动评分。
- 真实长篇项目基于 `adopt` 报告的全量分层迁移完成。
- PyPI 正式发布。
- 英文全量细节完全对齐中文文档。

## 下一阶段完成标准

完整路线图见 [roadmap.zh-CN.md](roadmap.zh-CN.md)。0.2.0 或下一阶段应重点证明：

1. 真实长篇项目已经通过 0.2 收口复跑证明导入队列可清空、迁移阻塞可修复或明确延期；后续继续补全信息边界、人物资料、章节发动机和逐章复盘内容，属于常规项目维护。
2. 从迁移 dogfood 中发现的命令体验问题被修复或记录为已知限制。
3. 英文文档继续覆盖深水区 CLI 细节和更多迁移/发布案例。
4. 发布流程在 GitHub Actions 中跑通。
5. 如决定发布 PyPI，先跑 TestPyPI trusted publishing 演练，下载 `fictionops-release-trial-evidence-<version>` 草稿，按 `docs/release-trial-evidence.zh-CN.md` 记录外部 run、artifact、安装烟测和必要回滚记录，并把正式发布结果同步回 release notes。
