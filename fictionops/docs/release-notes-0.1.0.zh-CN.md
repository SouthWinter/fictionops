# FictionOps 0.1.0 Release Notes

发布日期：2026-07-06

## 版本定位

FictionOps 0.1.0 是一个中文优先、文件系统优先的长篇小说工作流 MVP。它不是一键写作工具，也不主动调用模型；它提供的是一套可维护的项目结构、CLI 命令、审计信号、上下文打包和发布前门禁。

这个版本证明三件事：

1. 长篇小说可以被拆成可维护的项目状态，而不是只依赖聊天记录和作者记忆。
2. AI Agent 参与写作时，可以通过范围化上下文、信息边界、人物记忆和门禁降低失忆与提前泄露。
3. 从故事种子、章节规划、写前任务单、写后复盘、审计、清稿到 EPUB 发布，可以形成一条本地可验证链路。

## 已包含能力

- 旧项目接入诊断：`adopt`，包含分层、迁移阶段、建议目标路径和只读 dogfood 报告。
- 迁移沙盒复制：`adopt --copy-to <initialized-project>`，不会修改源目录；同名目标会自动消歧，不跳过候选材料，并写出 adopt manifest 保留源路径映射。
- 迁移后复查：`adopt-review`，聚合 `doctor`、`audit-info`、`audit-characters` 和 `book-gate`，并支持 `07_audits/adopt_review/waivers.json` 记录人工延期阻塞。
- 迁移整改计划：`adopt-plan`，把 `adopt-review` 的复查问题转成优先级任务清单，并用 `task_groups` 把大量同类问题折叠成阶段化修复组；传入 `--write-groups` 时可写出修复组索引和逐组 Markdown 工作文件；已明确豁免的问题不会重新生成当前修复任务。
- 导入队列整理计划：`import-plan`，利用 adopt manifest、文件名和标题推断 `06_drafts/import_queue/` 中正文文件的书/章目标，并可用 `--apply` 移动无歧义文件，用 `--create-scaffolds` 补齐章节发动机和逐章复盘，用 `--replace-placeholder-targets` 替换初始化模板占位章节。
- 项目、书、章节脚手架：`init`、`new-book`、`new-chapter`。
- 章节规划与写前准备：`plan-chapter`、`scene-plan`、`draft-brief`。
- 写后与审稿门禁：`post-draft`、`review-gate`、`book-gate`、`release-gate`。
- 静态审计：`stats`、`scan-words`、`check-tables`、`audit-wave`、`audit-style`、`audit-continuity`、`audit-echoes`、`audit-info`、`audit-characters`。
- Agent 协作辅助：`agent-prompt`、`agent-connect`、`agent-smoke`、`agent-run`、`agent-exec`、`agent-inbox`、`agent-next`、`model-config`、`context-pack`、`workflow-plan`、`revision-plan`，并提供不调用模型的 connector smoke、`examples/agent_runner_echo.py` 外部 runner 示例、OpenAI-compatible Chat Completions 外部 runner dry-run 示例、OpenAI Responses API 外部 runner dry-run 示例、`examples/agent_controller_next.py` 单步 controller 示例、`examples/agent_controller_loop.py` 多步 controller 示例，`docs/agent-connector-contract.md` / `docs/agent-connector-contract.zh-CN.md` 接入契约，以及 `docs/agent-integration.md` / `docs/agent-integration.zh-CN.md` 接入指南。
- 健康报告：`doctor`、`report`，包含 Agent 输出收件箱、模型配置、发布包等摘要。
- 发布管线：`export-clean`、`audit-publish`、`publish-copy`、`export-metadata`、`export-manifest`、`export-epub`、`audit-epub`。
- 包发布证据审计：`audit-release-evidence`，用于检查 0.4 发布演练记录是否仍是空模板、未复核草稿、无效 URL/hash、缺安装烟测或非 `accepted` 结论。
- 持续 dogfood 周期审计：`audit-dogfood-cycle`，用于检查 1.0 所需的真实项目持续维护周期是否填实、收口、兼容性说明齐备。
- 稳定窗口证据审计：`audit-stability-window`，用于检查 1.0 所需的兼容性/稳定窗口记录是否经过真实时间、填实并 accepted。
- 可运行示例：`examples/demo_novel/`、`examples/legacy_novel_source/` 与 `docs/tutorial-demo.zh-CN.md`。
- 开源维护包装：MIT License、CHANGELOG、中英文贡献指南、中英文核心入口文档、英文 CLI 契约入口、Agent 接入契约、Agent 接入指南、英文端到端迁移/发布案例、兼容性策略、已知限制文档、恢复手册、里程碑状态账本、1.0 稳定核心审计、发布清单、PyPI 发布说明、发布演练证据模板 `release-trial-evidence.md`、持续 dogfood 周期证据模板 `dogfood-cycle-evidence.md`、稳定窗口证据模板 `stability-window-evidence.md`、publish workflow 自动生成的 release trial evidence draft artifact、`audit-release-evidence` / `audit-dogfood-cycle` / `audit-stability-window` / `audit-stable-core` 证据审计、GitHub Actions CI/发布 workflow、issue/PR 模板。

## 验证结果

本地验证环境：Windows / bundled Python runtime。

已运行并通过：

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

验证摘要：

- 完整测试：`131 tests OK`。
- wheel 构建成功：`fictionops/dist/fictionops-0.1.0-py3-none-any.whl`。
- sdist 构建成功：`fictionops/dist/fictionops-0.1.0.tar.gz`。
- wheel 内容检查通过：包含模板、入口元数据、迁移模块和 Agent 模块。
- sdist 内容检查通过：包含源码、随包模板、根模板、中英文文档、英文 CLI 契约、Agent 接入契约、Agent 接入指南、英文端到端迁移/发布案例、兼容性、已知限制、恢复文档与稳定核心审计、示例 runner、示例 controller、示例项目、测试和 workflow 文档。
- 安装烟测通过：源码安装和构建后 wheel 干净虚拟环境安装均可用；安装 wheel 后 `fictionops --version` 与 `python -m fictionops --version` 返回 `fictionops 0.1.0`，`fictionops init` 能生成标准项目骨架，`doctor`、`agent-connect --help`、`agent-smoke --help`、`agent-next --help`、`audit-agent-workflow --help`、`audit-release-evidence --help`、`audit-dogfood-cycle --help`、`audit-stability-window --help` 和 `audit-stable-core --help` 可运行；CI 与 publish workflow 也会在上传或发布前执行 built-wheel clean venv smoke，publish workflow 还会上传独立的 `fictionops-release-trial-evidence-<version>` 证据草稿 artifact。
- 示例项目测试通过：`examples/demo_novel/` 能跑通书纲同步、场景计划、写前 brief、handoff context-pack、信息审计、人物审计、doctor 汇总和 controller 下一步选择；`examples/legacy_novel_source/` 能跑通 adopt、copy-to、adopt-review、import-plan apply 和再次复查。

## 已知边界

- 不内置供应商 API 调用，不保存真实 API key；`model-config` 只记录本地供应商配置边界，`agent-exec` 只运行用户显式传入的外部 runner，并把结果保存为暂存输出。
- 不判断文学质量；审计命令检查结构、表格、信息边界、词频和维护状态。
- 英文文档已覆盖核心 CLI、CLI 契约、兼容性策略、Agent 协议、demo 教程、迁移、端到端迁移/发布案例、测试、发布、已知限制和贡献入口；全量细节仍轻于中文文档，当前逐命令深细节以中文文档为主。
- 不是数据库产品；所有状态都落在 Markdown、YAML、JSON 和 EPUB 文件里。
- `examples/demo_novel/` 是微型示例，不代表完整成书质量，也不追求真实章节体量。
- 已完成真实长篇项目的 `adopt` 只读 dogfood，并在后续 0.2 收口复跑中证明导入队列可清空、迁移阻塞可修复或明确延期；正史归一和信息表整理仍属于后续人工维护。

## 发布建议

0.1.0 可以作为 GitHub pre-alpha release 发布，用来收集工作流反馈、命令契约反馈和真实项目 dogfood 反馈。

不建议把 0.1.0 宣传为成熟自动写作 Agent。更准确的说法是：

> FictionOps 0.1.0 是一个面向长篇小说维护和 AI 协作边界的本地 CLI MVP。

## 下一步

完整后续验收矩阵见 [roadmap.zh-CN.md](roadmap.zh-CN.md)。

1. 在真实长篇迁移沙盒中继续处理已延期的信息边界、伏笔首次埋设位置、人物资料和表格卫生问题，把迁移后的普通维护任务逐步关掉。
2. 根据 dogfood 结果收敛 `context-pack`、`draft-brief`、`revision-plan` 的默认策略。
3. 继续补英文深水区 CLI 细节和更多小型示例。
4. 如决定发布到 PyPI，按 `docs/pypi-release.zh-CN.md` 先跑 TestPyPI trusted publishing 演练，下载 publish workflow 生成的 `fictionops-release-trial-evidence-<version>` 草稿，再按 `docs/release-trial-evidence.zh-CN.md` 记录 GitHub Actions run URL、artifact、TestPyPI URL、安装烟测和 `accepted/deferred/failed` 结论，最后触发正式 PyPI 发布。
