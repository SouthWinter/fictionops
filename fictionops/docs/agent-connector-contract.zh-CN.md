# Agent 接入契约

这份契约给任何想把模型 runner、IDE agent、本地自动化或外部 controller 接到 FictionOps 的人使用。

FictionOps 核心保持不直接调用模型。外部接入层可以调用模型、选择安全命令、生成草稿或审稿意见，但必须保留“暂存输出”的边界。

## 稳定接入形状

```text
FictionOps 项目
  -> fictionops agent-connect connector kit
  -> fictionops agent-run / context-pack / agent-prompt / draft-brief
  -> agent run 目录
  -> 外部 connector
  -> 暂存 output.md 与 execution.json
  -> fictionops agent-inbox / gates / 人类决策
```

connector 在核心包之外。项目文件仍然是事实来源。

## Connector Kit 契约

`fictionops agent-connect` 会生成外部 agent 的接入套件。它不调用模型、不保存真实 key、不执行 controller，也不应用暂存输出。

套件包含 `connector_manifest.json`、`.env.example`、`smoke_commands.md`、`README.md` 和 `runner_adapter.py`。外部 connector 应先通过这些文件跑无网络烟测，再替换成真实模型调用。

## Runner 契约

runner 指任何传给 `fictionops agent-exec --runner ...` 的命令。

它必须：

- 从 stdin 读取完整任务包；
- 只向 stdout 写一个可审阅的暂存结果；
- 把诊断、进度、供应商日志写到 stderr；
- 当没有可用暂存结果时以非零状态退出；
- 让 API key 留在项目外，通常通过环境变量传入；
- 不直接编辑 `03_characters/`、`04_structure/`、`05_canon/`、`06_drafts/`、`08_publish/` 或其他项目文件。

它可以：

- 调用云端模型、本地模型、IDE assistant 或自定义 agent 框架；
- 从 stdin 中读取 `request.json`、`prompt.md`、`context_pack.md` 和可选的 `draft_brief.md`；
- 在角色提示词要求时，把简短自检说明放进 stdout；
- 利用 `model-config` 元数据选择供应商或模型。

它不能：

- 自己把输出应用到正文或正史；
- 把真实凭据写进 `request.json`、`execution.json` 或项目 Markdown；
- 把上下文缺失当成发明正史的许可；
- 绕过 `agent-inbox`、`post-draft`、`review-gate`、`book-gate` 或 `release-gate`。

## Controller 契约

controller 指调用 `fictionops agent-next --format json` 的外部循环。

只有在以下条件同时成立时，它才可以执行被选中的命令：

- FictionOps 将候选命令标记为安全；
- 命令不会应用暂存模型输出；
- 命令不会覆盖正文、正史、凭据或发布产物；
- 同一命令没有在项目证据不变化的情况下反复出现；
- 当前没有人类复核边界。

它必须在以下情况停下：

- `agent-next` 报告复核边界；
- `agent-inbox` 中已有待审暂存输出；
- 迁移被含混导入或未豁免修复组卡住；
- 发布步骤需要外部凭据、服务状态或人类确认；
- 下一步是占位命令、未知命令或 FictionOps 安全列表之外的命令。

## 必要文件

一个 `agent-run` 目录应包含：

| 文件 | 归属 | 用途 |
| --- | --- | --- |
| `request.json` | FictionOps | 机器可读的角色、任务、项目范围、模型元数据和安全契约。 |
| `prompt.md` | FictionOps | 人类可读的角色提示词和输出规则。 |
| `context_pack.md` | FictionOps | 为任务裁剪过的项目上下文。 |
| `draft_brief.md` | FictionOps | 章节写作任务中存在。 |
| `output.md` | connector 经由 `agent-exec` | 等待复核的暂存结果。 |
| `execution.json` | FictionOps | runner 命令、退出码、输出路径和安全元数据。 |

外部 connector 应忽略未知 JSON 字段，并优先依赖命名字段，而不是字段顺序。

## 最小烟测

接真实模型之前，先跑：

```bash
fictionops agent-connect my-novel --name local-runner --mode runner
fictionops agent-smoke my-novel --connector local-runner
```

`agent-smoke` 会把 no-network adapter 串过 `audit-agent-workflow`、`agent-run`、`agent-exec` 和 `agent-inbox`。如果需要手动展开，可以按下面四步执行：

```bash
fictionops agent-connect my-novel --name local-runner --mode runner

fictionops agent-run my-novel \
  --role draft-writer \
  --book book_01 \
  --chapter 001 \
  --out-dir my-novel/00_management/agent_runs/ch_001

fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_echo.py

fictionops agent-inbox my-novel/00_management/agent_runs/ch_001 --format json
```

当 `agent-inbox` 报告只有一个可审阅暂存输出，且没有损坏请求、空输出或多输出问题时，烟测通过。

## OpenAI Responses 示例

仓库中的 `examples/agent_runner_openai_responses.py` 是一个带供应商调用的 runner 示例。它仍然是 connector，不是 FictionOps 核心。

先 dry-run：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
```

再只从环境变量读取真实 key：

```bash
set OPENAI_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --model your-model
```

## 验收证据

一个 agent 接入方案只有留下这些证据，才算值得信任：

- 任务包存在；
- connector 能跑无网络烟测；
- 项目文件中没有真实凭据；
- `agent-inbox` 能看见暂存输出；
- 后续 FictionOps 门禁仍然决定输出能否进入正文、正史或发布产物；
- 当里程碑依赖外部服务状态时，记录外部 run ID 或 URL。

这条线区分了普通 AI 写作聊天和可审计的 FictionOps agent workflow。
