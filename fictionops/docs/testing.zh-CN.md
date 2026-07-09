# FictionOps 测试说明

> 当前测试体系使用 Python 标准库 `unittest`，不引入第三方依赖。目标是保护 CLI 的核心契约，而不是追求复杂覆盖率报表。

## 1. 运行全部测试

在仓库根目录运行：

```bash
python -m unittest discover -s fictionops/tests -v
```

如果本机没有 `python` 命令，可以使用任何 Python 3.10+ 解释器替代。

## 2. 运行单个测试文件

```bash
python -m unittest discover -s fictionops/tests -p test_cli.py -v
```

只跑某个测试名：

```bash
python -m unittest discover -s fictionops/tests -p test_cli.py -k release_smoke -v
```

## 3. 当前覆盖范围

当前测试文件：

```text
fictionops/tests/test_cli.py
```

覆盖的核心行为：

| 命令/模块 | 覆盖点 |
| --- | --- |
| `init` | 创建标准目录和文件；默认不覆盖；`force=True` 覆盖 |
| CLI 入口 | `--version`、`init` 子进程调用 |
| CLI help/contracts | 根命令和全部子命令 `--help`；CLI 契约文档覆盖 54 个命令 |
| `adopt` | 只读扫描既有写作目录；分层映射旧文件；输出迁移阶段和建议目标路径；JSON/Markdown 输出；写报告默认不覆盖；忽略工具目录 |
| `new-book` | 创建书纲、书稿目录和书级复盘；书号标准化；默认不覆盖 |
| `new-chapter` | 创建正文、章节发动机和逐章复盘；章节号标准化；默认不覆盖 |
| `plan-chapter` | 从书纲逐章规划表同步章节发动机；保留非空字段；支持 `--force` |
| `scene-plan` | 从章节发动机生成场景骨架；尊重已填场景顺序；JSON 输出；写出 Markdown 且默认不覆盖 |
| `draft-brief` | 从场景骨架和范围化上下文生成写前任务单；可选嵌入上下文并受总预算限制；JSON 输出；写出 Markdown 且默认不覆盖 |
| `post-draft` | 检查单章草稿、发动机、逐章复盘和同步项是否关门；JSON 输出；写出 Markdown 且默认不覆盖 |
| `review-gate` | 聚合单章写后、连续性、信息、人物、伏笔、风格和体量波形信号；JSON 输出；写出 Markdown 且默认不覆盖 |
| `book-gate` | 聚合书级计划、复盘、修订、表格、词频和体量波形信号；JSON 输出；写出 Markdown 且默认不覆盖 |
| `audit-plan` | 检查书纲逐章规划、正文文件和章节发动机同步情况 |
| `retrospective` | 汇总逐章复盘、书级复盘、缺失复盘和待同步项；支持写报告 |
| `stats` | 统计章节文件；不把 `ch_001_engine.md` 算作正文 |
| `scan-words` | 扫描高频词、短语和指定关注词；JSON 输出 |
| `check-tables` | 检查 Markdown 表格结构、占位行和行宽问题；JSON 输出 |
| `audit-wave` | 检查章节体量波形；识别过平、连续同档和相邻突跳 |
| `audit-style` | 关注词命中；重复句首识别 |
| `audit-continuity` | 标准项目文件检查；章节发动机覆盖；复盘缺口 |
| `audit-echoes` | 伏笔表解析；章节文本粗略命中 |
| `audit-info` | 信息释放表解析；缺认知状态；正文提前命中粗扫 |
| `audit-characters` | 人物索引、人物弧线、智慧模式和口吻资料覆盖；JSON 输出 |
| `agent-prompt` | 生成角色提示词；可附带受预算限制的 context-pack；JSON 输出；写出 Markdown 且默认不覆盖 |
| `agent-connect` | 生成外部 Agent 接入套件；写出 manifest、环境变量样例、烟测命令和 adapter stub；不调用模型、不保存密钥 |
| `eval-agent` | 在临时 fixture 副本上跑无网络 Agent harness 评估；验证暂存输出、收件箱复核边界和 controller 停止行为 |
| `agent-smoke` | 串联 workflow audit、agent-run、agent-exec 和 agent-inbox；用 no-network adapter 证明接入边界；不应用暂存输出 |
| `agent-run` | 准备 prepare-only Agent 任务包；写出 request/prompt/context/brief；JSON 输出；默认不覆盖；不调用模型 |
| `agent-exec` | 执行外部 runner；把 stdout 写成暂存输出；写出执行回执；JSON 输出；默认不覆盖；不自动应用 |
| OpenAI runner examples | 验证 OpenAI-compatible Chat runner v1 的 provider preset / `.env` dry-run 路径，以及 `examples/agent_runner_openai_responses.py --dry-run` 可通过 `agent-exec` 接收任务包并写入 staging，不联网也不需要真实 API key |
| `agent-inbox` | 检查 Agent run 目录里的暂存输出；识别缺输出、唯一输出和多候选输出；JSON 输出；只读不应用 |
| `agent-next` | 读取项目健康状态、导入队列和 Agent 收件箱，选择下一条安全命令；JSON 输出；只读不执行 |
| `audit-agent-workflow` | 检查 manual、runner、controller、model-runner 接入层级是否 ready；识别暂存输出复核边界、模型配置缺口和非标准项目 |
| controller loop example | 验证 `examples/agent_controller_loop.py` 只执行安全命令、写出 JSONL log，并在人工复核边界停止 |
| `model-config` | 生成本地模型供应商配置；不保存真实密钥；JSON 输出；写出配置且默认不覆盖 |
| `context-pack` | 范围化上下文收集；缺必读文件提示；每文件和整包预算截断；写出 Markdown 且默认不覆盖 |
| `workflow-plan` | 生成分阶段工作流清单；章节型阶段需要章节号；JSON 输出；写出 Markdown 且默认不覆盖 |
| `revision-plan` | 汇总审计问题为 P1-P5 修订任务；纳入词频提示和表格结构问题；JSON 输出；写出 Markdown 且默认不覆盖 |
| `doctor` | 汇总健康状态；JSON 输出；纳入章节波形、词频、表格、信息边界、人物弧线、计划层、写后复盘、书级门禁、Agent 输出收件箱、模型配置、发布稿、发布元数据、manifest、EPUB 和发布门禁摘要 |
| `report` | 输出 Markdown/JSON 健康报告；默认不覆盖 |
| `export-clean` | 合并章节草稿为发布用 clean Markdown；JSON 输出；默认不覆盖 |
| `audit-publish` | 检查 clean Markdown 的章节顺序、缺章、草稿标记和短章 |
| `publish-copy` | 从发布清单、故事种子、书纲和 clean Markdown 生成简介、标签、关键词草稿；JSON 输出；默认不覆盖 |
| `export-metadata` | 从发布清单导出简介、标签、分类、作者名和可选封面路径；JSON 输出；默认不覆盖 |
| `export-manifest` | 组合 clean Markdown、metadata JSON 和可选封面，导出带 hash 的发布包 manifest |
| `export-epub` | 从 manifest、clean Markdown 和 metadata JSON 导出带 CSS、可选封面的 EPUB；默认不覆盖 |
| `audit-epub` | 检查 EPUB 结构、CSS、章节、封面声明和相对输入文件的新鲜度 |
| `release-gate` | 聚合书级收束、发布稿、元数据、manifest 和 EPUB 的最终发布门禁；JSON 输出；写出 Markdown 且默认不覆盖 |
| `audit-release-evidence` | 检查 FictionOps 包发布演练证据；空模板、未复核草稿和已填实外部记录分别给出不同状态 |
| `audit-dogfood-cycle` | 检查 1.0 持续 dogfood 周期证据；空模板、延期记录和已填实周期分别给出不同状态 |
| `audit-stability-window` | 检查 1.0 稳定窗口证据；空模板、非 accepted 结论和已填实窗口分别给出不同状态 |
| `audit-stable-core` | 聚合 1.0 稳定核心证据；检查发布证据、持续 dogfood、稳定窗口和里程碑声明是否一致 |
| release smoke | 从 `init` 到 `release-gate` 跑完整快速开始链路 |
| demo example | 复制 `examples/demo_novel/` 到临时目录，验证书纲同步、场景计划、写前 brief、handoff、信息表、人物表和 doctor 汇总 |
| legacy migration example | 复制 `examples/legacy_novel_source/` 到临时目录，验证 adopt、copy-to、adopt-review、import-plan apply 和再次复查 |
| release governance | 检查 `LICENSE`、`CHANGELOG`、贡献指南和发布清单入口 |
| release evidence | 检查 release notes、completion audit、roadmap、CI、英文 CLI 契约和开源维护入口存在且被 README/CHANGELOG 引用 |
| packaging smoke | 本地安装包后调用真正的 `fictionops` 入口，确认安装态能找到随包模板 |
| template sync | 检查根目录 `templates/` 与 `src/fictionops/templates/` 内容一致 |

## 4. 测试原则

1. **只用临时目录。** 测试不写入真实小说项目。
2. **先测契约。** 例如“发动机文件不应被当作正文”比具体输出排版更重要。
3. **CLI 与函数都测。** 函数测试定位问题快，CLI 子进程测试防止入口坏掉。
4. **不测试审美判断。** `audit-style` 只保证能统计模式，不断言某种写法一定好坏。
5. **不假装理解剧情。** `audit-continuity`、`audit-echoes`、`audit-info` 和 `audit-characters` 测的是维护结构，不是文学质量。

## 5. 新增命令时的测试清单

新增 CLI 命令时，至少补：

- 一个直接调用核心函数的测试；
- 一个 CLI 子进程 JSON 输出测试；
- 一个失败或空输入场景；
- 一个能覆盖中文路径或中文章节名的场景；
- 一个防止误识别的回归测试。

## 追加测试：`agent-run`

`test_agent_run_prepares_bundle_without_calling_model` 覆盖 Agent 任务包路径：

- `build_agent_run` 会读取 `model-config`，选择与任务匹配的规划、正文或审计模型名。
- 写作任务会组合 `agent-prompt`、`context-pack` 和 `draft-brief`。
- `--out-dir` 会写出 `README.md`、`request.json`、`prompt.md`、`context_pack.md` 和写作任务的 `draft_brief.md`。
- `request.json` 必须声明不调用模型、不覆盖正文、不保存密钥。
- CLI 的 `--format json` 输出必须是纯 JSON。
- 第二次写同一目录默认失败，必须传入 `--force` 才能覆盖。

## 追加测试：`agent-exec`

`test_agent_exec_runs_external_runner_into_staging_output` 覆盖外部 runner 桥接路径：

- `--dry-run` 不执行外部命令，也不写暂存输出。
- 正常执行会把任务包组合为 stdin 传给外部 runner。
- runner stdout 会写入 `output.md`，并生成 `execution.json`。
- 写入后 `agent-inbox` 能识别 run 状态为 `ready_for_review`。
- 已有暂存输出时默认拒绝覆盖，必须显式传入 `--force`。
- CLI 的 `--runner` 后续参数会原样传给外部命令。

`test_agent_exec_example_runner_is_usable` 覆盖仓库自带的 `examples/agent_runner_echo.py`：

- 示例 runner 读取 FictionOps stdin 并输出暂存 Markdown。
- `agent-exec` 能用该 runner 写出 `output.md`。
- `agent-inbox` 能把示例输出识别为 `ready_for_review`。

`test_openai_responses_runner_dry_run_is_usable` 覆盖仓库自带的 `examples/agent_runner_openai_responses.py`：

- 通过 `agent-exec` 调用 runner 的 `--dry-run` 模式，不读取真实 API key，不联网。
- dry-run 输出会写成 `output.md`，声明模型名、角色、任务和“未发起网络请求”。
- `agent-inbox` 能把该 staging 输出识别为 `ready_for_review`。

## 追加测试：`agent-inbox`

`test_agent_inbox_tracks_staged_agent_outputs` 覆盖 Agent 输出回收路径：

- 没有输出文件时，收件箱状态为 `awaiting_output`，run 状态也是 `awaiting_output`。
- 写入 `output.md` 后，收件箱状态变成 `ready_for_review`，并给出 `post-draft` / `review-gate` 后续动作。
- 直接把 `path` 指向单个 run 目录时，CLI JSON 输出的 `mode` 应为 `run_dir`。
- 同时出现 `output.md` 和 `response.md` 时，状态变成 `needs_attention`，并输出 `ambiguous_output`。
- 使用 `--output-name output.md` 时，可以明确选择一个输出候选。

## 追加测试：`agent-next`

`test_agent_next_selects_safe_controller_step` 覆盖 Level 2 controller 入口：

- 非标准旧目录会优先建议 `adopt`。
- 标准项目指定未来章节时会建议 `new-chapter`。
- 如果 Agent run 已有暂存输出，会优先建议 `agent-inbox`，并标记需要人工复核。
- 仓库自带的 `examples/agent_controller_next.py` 能调用源码 CLI，读取 `agent-next` JSON，并返回同一条 `selected_command`。

## 追加测试：controller loop

`test_agent_controller_loop_executes_safe_steps_and_stops_at_boundaries` 覆盖多步 no-model controller：

- 能通过源码 CLI 执行 `agent-next` 推荐的安全命令。
- 会写出 JSONL controller log。
- 遇到重复命令会停止，避免无状态命令循环。
- 遇到已有暂存 Agent 输出会停在 `human_review_boundary`，不继续执行新命令。
- 遇到缺失项目的 `<title>` 占位初始化命令会停止，不会盲目创建项目。
- 遇到旧项目和导入队列时只运行只读诊断命令，并在重复建议时停止。
- 通过 fake CLI 覆盖发布门禁候选，确认 controller 仍按安全标记执行并在重复建议时停止。

## 追加测试：`adopt --copy-to`

`test_adopt_can_copy_into_initialized_sandbox` 覆盖迁移沙盒路径：

- `dry_run=True` 时只产生 `planned_copies`，不写目标文件。
- 实际运行时把 `handoff.md`、`book_outline.md` 和 `ch_001.md` 复制到对应的 `00_management/`、`04_structure/` 和 `06_drafts/import_queue/` 目标路径。
- 实际运行时会写出 `00_management/adopted_handoff/adopt_manifest.json`，保留源路径和目标路径映射。
- 第二次运行默认跳过已有目标文件。
- CLI 的 `--format json --copy-to` 输出仍可直接 `json.loads`，不会混入状态提示文本。
- `test_adopt_copy_disambiguates_same_target_paths` 覆盖同名建议目标路径：多个旧文件映射到同一目标时，`adopt --copy-to` 必须生成唯一目标路径，而不是跳过候选材料。

## 追加测试：`adopt-review`

`test_adopt_review_reports_migration_sandbox_gaps` 覆盖迁移后复查路径：

- 先用 `adopt --copy-to` 把旧材料复制到标准 FictionOps 沙盒。
- `build_adopt_review` 会识别 `06_drafts/import_queue/` 中尚未归入书/章结构的导入正文。
- 状态应为 `needs_import_sorting`，`ready` 为 `false`。
- CLI 的 `--format json` 输出可被 `json.loads` 解析，并包含 `doctor` 与 `book_gate` 聚合结果。
- Markdown 报告默认不覆盖，必须传入 `--force` 才能覆盖已有报告。
- `test_adopt_review_waivers_defer_explicit_blockers` 覆盖 `07_audits/adopt_review/waivers.json`：被明确写入理由、负责人和期限的阻塞会从活跃阻塞中移出，但仍保留在总问题数和 waiver 记录里。

## 追加测试：`adopt-plan`

`test_adopt_plan_turns_review_findings_into_tasks` 覆盖迁移整改计划路径：

- 先用 `adopt --copy-to` 构造包含 `06_drafts/import_queue/` 的迁移沙盒。
- `build_adopt_plan` 会复用 `adopt-review` 的结论，并把 `import_queue_unsorted` 转成迁移任务。
- 报告应保留 `review_status`、`review_ready`、`priority_counts`、`task_groups`、`tasks`、`next_actions` 和原始 `adopt_review` 证据。
- `task_groups` 应把同类任务折叠成阶段化修复组，至少包含 `phase`、`code`、`count`、`blocking_count`、`source_commands`、`sample_paths` 和 `suggested_action`。
- CLI 的 `--format json` 输出必须是纯 JSON。
- `adopt-plan` 会使用同一份 waiver 文件，不把已延期的 `adopt-review` 阻塞重新生成当前修复任务。
- `--write-groups` 应写出 `index.md` 和每个修复组的 Markdown 工作文件，JSON 中应回填 `group_output_dir`、`group_files_written` 和 `group_files`。
- Markdown 计划和修复组文件默认不覆盖，必须传入 `--force` 才能覆盖已有计划，并应在逐条任务前输出 `Repair Groups`。

## 追加测试：`import-plan`

`test_import_plan_suggests_and_applies_safe_import_moves` 覆盖导入队列整理路径：

- `build_import_plan` 会读取 `06_drafts/import_queue/`，按文件名、标题和 adopt manifest 中的旧源路径推断目标章节与书号。
- 目标已存在、章号缺失或目标重复的文件会进入人工复查，不会被 `--apply` 自动移动。
- CLI 的 `--format json` 输出必须是纯 JSON，并包含 `import_queue_files`、`ready_count` 和逐文件 `items`。
- Markdown 计划默认不覆盖，必须传入 `--force` 才能覆盖已有计划。
- `apply=True` 只移动无歧义、目标不存在的文件，并保留需要人工判断的导入文件。
- `create_scaffolds=True` 会为已移动章节生成缺失的章节发动机和逐章复盘，但不会覆盖已移动的正文。
- `replace_placeholder_targets=True` 只替换初始化生成的占位章节目标；非占位已有正文仍保留在导入队列中等待人工判断。
