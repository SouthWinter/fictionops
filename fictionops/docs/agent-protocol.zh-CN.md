# FictionOps Agent 协作协议

> 目标：让 AI Agent 参与长篇创作时有边界、有输入输出、有审计顺序，而不是把所有任务都变成“帮我写一章”。

## 0. FictionOps 自己算什么

FictionOps 不是一个单体自动小说家，而是一套 **agentic workflow harness**：它用文件结构、CLI、上下文包、任务包、外部 runner 桥、收件箱和门禁，把人类作者与一个或多个 Agent 放进同一个长篇项目里协作，同时尽量不丢正史、不吞全量上下文、不跳过复盘顺序。

描述接入程度时，建议分三层：

- Level 1，AI-assisted workflow：人类作者决定下一步，然后用 `context-pack`、`agent-prompt` 或 `agent-run` 把一个有边界的任务交给模型或协作者。
- Level 2，agentic workflow：外部脚本或 controller 读取 FictionOps 的 JSON 输出，判断下一条安全命令，运行审计，把结果放回暂存区等待复核。
- Level 3，autonomous writing agent：外部 controller 可以连续推进多个任务，但正文和正史仍必须经过暂存输出、项目门禁和人类确认。

当前包直接支持 Level 1，并提供 Level 2 所需的基础件。Level 3 不应变成“自动覆盖正文”的核心功能；如果要做，也应该作为外部 controller，继续遵守 FictionOps 的安全契约。关于“接上 AI 后算不算 agent workflow”的短答案，见 [Agent workflow 定位说明](agent-workflow.zh-CN.md)。

## 1. 总原则

Agent 是协作者，不是自动作者。

它应该帮助作者：

- 维护正史；
- 追踪信息边界；
- 发现人物失真；
- 规划章节压力；
- 审计读者体验；
- 生成可修改的草稿；
- 打包发布文件。

它不应该：

- 私自覆盖作者决定；
- 把旧案当正史；
- 为了完整解释而泄露秘密；
- 把所有角色写成同一种聪明；
- 把风格磨成安全但无味；
- 用表格取代场景生命。

## 2. 推荐 Agent 角色

| 角色 | 输入 | 输出 | 禁止 |
| --- | --- | --- | --- |
| Architect 架构师 | 总纲、卷纲、书纲、人物终点 | 长结构建议、幕结构、不可逆事件 | 微操每个句子 |
| Canon Keeper 正史管理员 | 世界规则、正文、正史表 | 冲突报告、同步建议 | 私自删旧案 |
| Character Auditor 人物审计 | 人物弧线、正文段落 | 人物失真报告、修订方向 | 把角色磨成标准答案 |
| Info Boundary Auditor 信息边界审计 | 信息释放表、正文 | 泄露报告、改写建议 | 让角色提前知道作者真相 |
| Foreshadowing Auditor 伏笔审计 | 伏笔表、章节 | 回声间隔报告、轻触建议 | 每次都解释伏笔 |
| Chapter Planner 章节规划 | 书纲、上一章、正史 | 章节发动机、场景顺序 | 只列内容清单 |
| Draft Writer 正文写手 | 章节发动机、人物口吻、信息边界 | 草稿章节 | 忽视视角限制 |
| Style Auditor 风格审计 | 正文 | 高频词、句式、解释密度报告 | 统一抹平个人风格 |
| Publisher 发布员 | 清稿、发布清单、书纲、故事种子 | EPUB、简介/标签草稿、元数据、统计 | 覆盖草稿和规划层 |

### 2.1 用 `model-config` 记录模型配置

如果项目需要接入模型，先用本地配置记录供应商、模型名和密钥环境变量名：

```bash
fictionops model-config my-novel --provider openai --planning-model gpt-planner --drafting-model gpt-writer --audit-model gpt-auditor --api-key-env OPENAI_API_KEY --write
fictionops model-config my-novel --provider local --planning-model planner --drafting-model writer --audit-model auditor --format json
```

`model-config` 不保存真实 API key，也不调用模型。它只建立“后续 Agent 应该读取哪份配置”的边界，避免把密钥、角色提示词和任务上下文混在同一个文件里。

### 2.2 用 `agent-prompt` 生成角色边界

推荐角色可以通过 CLI 生成稳定提示词：

```bash
fictionops agent-prompt my-novel --role draft-writer --chapter 001
fictionops agent-prompt my-novel --role info-boundary-auditor --task review --chapter 002 --include-context
fictionops agent-prompt my-novel --role publisher --out 00_management/publisher_prompt.md
```

`agent-prompt` 不调用模型，只生成角色边界、输入偏好、必须做、禁止做、工作顺序和输出契约。

### 2.3 用 `agent-run` 准备任务包

当提示词、上下文和模型配置都需要一起交给人或外部 runner 时，使用 `agent-run`：

```bash
fictionops agent-run my-novel --role draft-writer --chapter 001 --out-dir 00_management/agent_runs/ch_001
fictionops agent-run my-novel --role info-boundary-auditor --task review --chapter 002 --out-dir 00_management/agent_runs/review_ch_002 --no-context-content
```

`agent-run` 当前是 `prepare_only` 模式。它会生成 `README.md`、`request.json`、`prompt.md`、`context_pack.md`，写作任务还会生成 `draft_brief.md`。它不调用模型、不保存 API key、不覆盖正文；外部模型 runner 或人类协作者应把输出写入 staging 文件，再由 FictionOps 门禁验收。

### 2.4 用 `agent-exec` 接外部 runner

如果已经有本地模型 CLI、OpenAI 包装脚本、自动化 agent 或其他外部 runner，可以让 FictionOps 把任务包作为 stdin 喂给它，并把 stdout 保存为暂存输出：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python run_model.py
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --output-name draft.staging.md --runner local-agent --model writer
```

`agent-exec` 会读取 `request.json`、`prompt.md`、`context_pack.md` 和可选 `draft_brief.md`，组合成 runner 输入；runner 的 stdout 会写入 `output.md` 或指定暂存文件，执行信息会写入 `execution.json`。它可能启动会调用模型的外部命令，但 FictionOps 本体不读取真实 API key、不保存 API key、不覆盖正文、不把输出自动应用到正史或章节草稿。

仓库提供一个不调用模型的最小 runner 示例：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python fictionops/examples/agent_runner_echo.py
```

这个示例只解析 FictionOps 输入并生成暂存输出，适合用来确认管线。真实接入时，把示例脚本里生成 echo 文本的部分替换成你的模型调用或本地 agent 调用即可；stdin 仍然读取 FictionOps 任务包，stdout 仍然只输出暂存结果。

仓库也提供一个通用 OpenAI-compatible Chat Completions runner，适合 DeepSeek、通义千问/DashScope 兼容模式、Kimi/Moonshot、GLM/智谱、豆包/火山方舟、硅基流动和本地 OpenAI-compatible 服务。v1 runner 支持 provider preset、显式 `.env`、dry-run 报告和输出长度保护。

先用不联网 dry run 检查边界：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --dry-run \
  --provider deepseek \
  --model deepseek-chat
```

确认边界后，再把真实 key 放在项目外的环境变量里运行：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --provider deepseek \
  --model deepseek-chat \
  --max-output-chars 12000
```

这个示例调用 Chat Completions 的 `/chat/completions` 端点，并会把它拼接到解析出的 base URL 后。没有 preset 的供应商可以显式传 `--api-key-env` 和 `--base-url`。常见供应商配置起点见 [模型供应商接入](model-providers.zh-CN.md)。

仓库也提供一个 OpenAI Responses API 外部 runner 示例。它仍然不属于 FictionOps 核心：API key 只从环境变量读取，任务包从 stdin 进入，模型输出只写到 stdout，再由 `agent-exec` 保存为 staging 文件。

先用不联网 dry run 检查边界：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
```

确认边界后，再设置 `OPENAI_API_KEY` 并运行真实模型：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --model your-model
```

也可以用 `FICTIONOPS_OPENAI_MODEL` 提供模型名。这个示例调用 OpenAI Responses API 的 `/v1/responses` 端点；如果供应商行为变化，应更新外部 runner，而不是削弱 FictionOps 的暂存输出契约。

### 2.5 用 `agent-inbox` 检查回传输出

外部 runner 或人类协作者完成任务后，应把输出保存到对应 run 目录，例如 `output.md`、`response.md`、`result.md` 或 `*.staging.md`，再运行：

```bash
fictionops agent-inbox my-novel
fictionops agent-inbox my-novel/00_management/agent_runs/ch_001
fictionops agent-inbox my-novel --output-name output.md --format json
```

`agent-inbox` 只读检查。它会确认 `request.json`、安全策略、任务包文件和输出文件是否可用；如果输出缺失，状态为 `awaiting_output`；如果输出唯一且非空，状态为 `ready_for_review`；如果多个输出候选或 request 损坏，状态为 `needs_attention`。它不会调用模型，也不会把输出应用到正文或正史。

### 2.6 用闭环命令完成旧章修订或新章写作

普通 runner 接线确认后，真实章节优先使用闭环命令：

```bash
fictionops agent-revise-workflow path/to/old_chapter.md --runner python /absolute/path/to/agent_runner_openai_chat.py --provider deepseek --model deepseek-chat
fictionops agent-write-workflow path/to/new_chapter.md --engine path/to/chapter_engine.md --outline path/to/book_outline.md --runner python /absolute/path/to/agent_runner_openai_chat.py --provider deepseek --model deepseek-chat
fictionops agent-accept-revision path/to/run_dir --dry-run
```

旧章命令默认先读取项目上下文做六维审读，再修订、复检和定向重修。新章命令先把大纲/发动机编译为场景执行计划，再生成正文并做八维验收。两者只有在 `ready_for_approval` 时才能显式采纳；正史同步建议仍需作者逐项确认。

### 2.7 用 `agent-next` 选择下一条安全命令

外部 controller 如果需要机器可读的下一步，可以运行：

```bash
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
```

`agent-next` 会读取项目健康状态、导入队列、Agent 收件箱、可选章节状态和发布门禁，输出 `selected_command`、`selected_reason`、候选命令和证据。它不执行命令，不调用模型，不应用暂存输出。它是 Level 2 controller 的边界：自动化可以选择下一条安全的 FictionOps 命令，但正文和正史变化仍然要经过暂存、门禁和人类确认。如果目标是 FictionOps 包目录本身，它会改为读取 stable-core governance action items，避免把工具仓库误判成待迁移小说项目。

仓库提供了一个不调用模型的 controller 示例：

```bash
python fictionops/examples/agent_controller_next.py my-novel --chapter 001 --cli fictionops
```

如果从源码调用 CLI，可以把源码 CLI 作为命令前缀传入：

```bash
python fictionops/examples/agent_controller_next.py my-novel --chapter 001 --cli python fictionops/src/fictionops/cli.py
```

如果要演示多步 no-model controller，可以使用 `agent_controller_loop.py`。它会反复调用 `agent-next`，只执行标记为安全且不需要人工复核的候选命令，可选写出 JSONL log，并在暂存输出、人类复核或正文/正史权力边界前停止：

```bash
python fictionops/examples/agent_controller_loop.py my-novel --chapter 001 --max-steps 3 --log 00_management/agent_runs/controller_loop.jsonl --cli fictionops
```

## 3. Agent 接手流程

### 3.1 写正文前

推荐先把书纲计划同步到章节发动机，再把发动机压成场景骨架：

```bash
fictionops plan-chapter my-novel --book book_01 --chapter 002
fictionops scene-plan my-novel --book book_01 --chapter 002
fictionops draft-brief my-novel --book book_01 --chapter 002
fictionops context-pack my-novel --task draft --book book_01 --chapter 002
```

`scene-plan` 不调用模型、不写正文。它只把章节发动机中的压力链、信息边界、伏笔回声和场景顺序整理成写前可执行的场景计划。`draft-brief` 会在此基础上合并范围化上下文、缺失文件、必须做和禁止做，形成真正交给作者或写作 Agent 的任务单。

必读：

1. 当前本书大纲；
2. 当前章节发动机；
3. 视角人物弧线；
4. 信息释放表；
5. 相关伏笔表；
6. 上一章正文或复盘。

必须回答：

- 本章视角人物现在想要什么？
- 本章压力从哪里来？
- 本章有什么不能说？
- 本章结尾改变什么？
- 本章应留下什么余味？

### 3.2 审正文前

先确认写后记忆已经关门：

```bash
fictionops post-draft my-novel --book book_01 --chapter 002
fictionops review-gate my-novel --book book_01 --chapter 002
```

如果 `post-draft` 状态是 `needs_draft`、`needs_engine` 或 `needs_retrospective`，先补草稿、章节发动机或逐章复盘。若状态是 `sync_needed`，先把已记录的同步项纳入正史/人物/信息/伏笔维护或 `revision-plan`，再进入广义审稿。若 `review-gate` 状态是 `needs_post_draft` 或 `needs_review_fixes`，先处理阻塞项；若是 `review_notes`，可以带着提示进入定向修订；若是 `review_passed`，再做风格润色。

必读：

1. 被审章节；
2. 章节发动机；
3. 上一章/下一章摘要；
4. 信息释放表；
5. 人物弧线。

审计顺序：

1. 正史；
2. 信息边界；
3. 人物弧线；
4. 章节发动机；
5. 风格与读者体验；
6. 润色。

### 3.3 同步正史时

必须判断：

- 是正文改出了新正史，还是正文误写？
- 哪些文件需要同步？
- 哪些旧设定要归档？
- 这次改动会影响后续哪些章节？

### 3.4 用 `context-pack` 执行范围化接手

`context-pack` 是 Agent 接手流程的本地入口。它不调用模型，只负责按任务类型收集上下文，并用 `--max-chars-per-file` 与 `--max-total-chars` 控制内嵌内容体量，避免每次把全项目塞给 Agent。

```bash
fictionops context-pack my-novel --task draft --chapter 001
fictionops context-pack my-novel --task review --chapter 002 --no-content
fictionops context-pack my-novel --task handoff --max-total-chars 80000 --out 00_management/context_pack.md
fictionops context-pack my-novel --task canon-sync --chapter 010 --format json
```

任务边界：

- `draft`：写正文前，读取书纲、章节发动机、信息释放表、上一章和相关人物/口吻材料。
- `review`：审正文前，读取被审章节、发动机、前后章节、信息边界和人物材料。
- `handoff`：交接时，读取当前上下文、交接日志、决策记录、模型配置、书纲、正史表、人物索引/智慧/口吻资料、书级复盘、doctor/report、revision-plan、book/release gate 报告。
- `canon-sync`：同步正史时，读取决策记录、正史表、物件/问题表，以及可选源章节。

### 3.5 用 `workflow-plan` 和 `revision-plan` 收束工作

在进入新阶段前，可以先用 `workflow-plan` 生成阶段清单：

```bash
fictionops workflow-plan my-novel --stage review --chapter 002
fictionops workflow-plan my-novel --stage publish --book book_01
fictionops workflow-plan my-novel --stage all --out 00_management/workflow_plan.md
```

`workflow-plan` 不执行命令，只输出阶段、目的、命令、产物和出口标准。它适合回答“现在该进入哪一层工作”，避免 Agent 在还没完成正史/信息/人物审计时直接跳到润色或发布。

审计命令发现的是问题，`revision-plan` 负责把这些问题转成按 P1-P5 排序的修订任务。

```bash
fictionops revision-plan my-novel --book book_01 --out 07_audits/revision_plan.md
fictionops book-gate my-novel --book book_01 --out 07_audits/book_gate/book_01_gate.md
fictionops release-gate my-novel --book book_01 --out 07_audits/release_gate/book_01_release_gate.md
```

Agent 在进入改稿前，应先确认高优先级任务是否已经处理。不要越过 P1/P2 去修漂亮句子。整本书进入清稿导出前，应确认 `book-gate` 不再处于 `needs_book_material` 或 `needs_book_closure`；上传或归档发布包前，应确认 `release-gate` 不再处于 `needs_release_artifacts` 或 `needs_release_fixes`。

## 4. 输出格式

### 4.1 章节规划输出

```markdown
## 章节发动机

| Pressure | Desire | Obstacle | Change | Remainder |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 信息边界
- 能说：
- 不能说：
- 只能误读：

## 场景顺序
1.
2.
3.
```

### 4.2 审计输出

```markdown
## Findings

### P0 正史崩坏
- 无 / 有：

### P1 信息边界
- 

### P2 人物弧线
- 

### P3 章节发动机
- 

### P4 风格
- 

## 建议修订
- 
```

### 4.3 接手输出

```markdown
## 当前状态

## 已完成

## 下一步

## 风险

## 必读文件
```

## 5. 人类 override

作者可以随时覆盖 Agent 建议。

但建议记录三类 override：

1. **审美 override**：作者明确选择某种风格，即使审计认为可疑。
2. **剧情 override**：作者选择一个更有张力但风险更高的走法。
3. **系统 override**：为了后续大结构，暂时保留一个当前看似不自然的安排。

override 不代表 Agent 错，只代表长篇创作不能完全由规则裁决。

## FictionOps 源码包治理模式

当外部 controller 的目标不是小说项目，而是 FictionOps 源码包 checkout 本身时，`agent-next` 和 `audit-agent-workflow --level controller` 会进入 package governance 模式：它们从 stable-core governance action items 中选择下一步，并在需要真实外部发行、持续 dogfood 或稳定窗口证据时停在 `needs_human_review`。controller 可以读取这些证据和建议命令，但不能替人类维护者编造证据，也不能把源码包当成 legacy novel 运行 `adopt`。
