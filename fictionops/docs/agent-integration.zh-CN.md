# Agent 接入指南

这份文档回答一个更落地的问题：怎样把外部模型 API、runner 或 controller 接进 FictionOps，同时不让模型输出悄悄覆盖正文或正史。

FictionOps 本体是 workflow harness。runner 可以只是 API 包装器、本地脚本、IDE 工具或模型服务客户端；controller 才可能把这些调用串成 agentic loop。外部 runner 和 controller 应遵守的最小接口边界见 [Agent 接入契约](agent-connector-contract.zh-CN.md)。

## 接入层级

| 层级 | 适用场景 | FictionOps 命令 | 谁采纳输出 |
| --- | --- | --- | --- |
| 手动聊天助手 | 作者想把范围化上下文交给 ChatGPT、Claude、本地模型或其他助手。 | `context-pack`、`agent-prompt`、`draft-brief` | 人 |
| 外部 runner | 脚本、API 包装器或模型服务客户端能读 stdin、写 stdout。 | `agent-connect`、`agent-run`、`agent-exec`、`agent-inbox` | 人复核后采纳 |
| controller 循环 | 脚本需要根据项目状态选择并运行安全命令。 | `agent-connect`、`agent-next`、`examples/agent_controller_loop.py` | 到复核边界交还给人 |
| 真实模型 runner | runner 调用 OpenAI、本地模型服务或其他供应商。 | `model-config`、`agent-connect`、`agent-exec`、runner 脚本 | 人复核后采纳 |

核心规则是：**外部 runner 和 controller 可以产出暂存结果，但不能直接改正文或正史。**

## 文件流向

```text
项目文件
  -> agent-connect connector kit
  -> context-pack / agent-prompt / draft-brief
  -> agent-run 任务目录
  -> 外部 runner 或 controller
  -> 00_management/agent_runs/ 中的暂存输出
  -> agent-inbox / post-draft / review-gate / book-gate
  -> 作者决定是否采纳
```

任务目录就是 FictionOps 和外部 runner/controller 之间的契约：

- `request.json`：机器可读的任务信封。
- `prompt.md`：角色提示词和输出契约。
- `context_pack.md`：范围化项目上下文。
- `draft_brief.md`：章节写作类任务会带上的写前任务单。
- `output.md`：`agent-exec` 保存的暂存输出。
- `execution.json`：runner 命令、退出码和输出路径记录。

## 模式一：手动接聊天界面或 API

适合还没有 runner 脚本，只想让作者把材料交给某个聊天界面、API 控制台或其他工具的情况。

```bash
fictionops context-pack my-novel --task draft --book book_01 --chapter 001 --out context.md
fictionops agent-prompt my-novel --role draft-writer --book book_01 --chapter 001 --out prompt.md
fictionops draft-brief my-novel --book book_01 --chapter 001 --out brief.md
```

把这些文件交给助手。助手返回的内容应先作为候选文本或暂存文本处理，不要直接当成正史或正文。

## 模式二：接外部 Runner

适合已有一个能读 stdin、写 stdout 的模型 API 调用、本地工具或助手命令。

```bash
fictionops agent-connect my-novel --name local-runner --mode runner
fictionops agent-smoke my-novel --connector local-runner

fictionops agent-run my-novel \
  --role draft-writer \
  --book book_01 \
  --chapter 001 \
  --out-dir my-novel/00_management/agent_runs/ch_001

fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_echo.py

fictionops agent-inbox my-novel/00_management/agent_runs/ch_001 --format json
```

runner 契约：

- 从 stdin 读取完整任务包；
- stdout 只写候选暂存结果；
- 需要诊断信息时写 stderr；
- 不直接改项目文件；
- 无法产出有效候选结果时用非零退出码失败。

这样可以接本地脚本、托管模型包装器、IDE 助手或其他 orchestration 框架。

## 模式三：接 OpenAI-compatible Chat Runner

仓库里有一个通用 Chat Completions runner，适合带 OpenAI-compatible API 的供应商。DeepSeek、通义千问/DashScope 兼容模式、Kimi/Moonshot、GLM/智谱、豆包/火山方舟、硅基流动和本地 OpenAI-compatible 服务，都可以先从这个 runner 开始。

先 dry-run：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --dry-run \
  --model deepseek-chat \
  --api-key-env DEEPSEEK_API_KEY \
  --base-url https://api.deepseek.com
```

确认暂存边界后，再从环境变量读取真实 key：

```bash
set DEEPSEEK_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --model deepseek-chat \
  --api-key-env DEEPSEEK_API_KEY \
  --base-url https://api.deepseek.com
```

`model-config` 可以记录供应商、模型名、base URL 和密钥环境变量名：

```bash
fictionops model-config my-novel \
  --provider deepseek \
  --planning-model deepseek-chat \
  --drafting-model deepseek-chat \
  --audit-model deepseek-chat \
  --api-key-env DEEPSEEK_API_KEY \
  --base-url https://api.deepseek.com \
  --write
```

这个 runner 会在 `--base-url` 后拼接 `/chat/completions`。常见供应商配置起点见 [模型供应商接入](model-providers.zh-CN.md)。

## 模式四：接 OpenAI Responses Runner

仓库里有一个 OpenAI Responses API runner 示例。它故意放在 FictionOps 核心之外。

先 dry-run：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --dry-run --model your-model
```

确认边界没问题后，把 API key 放在环境变量里，再跑真实模型：

```bash
set OPENAI_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_responses.py --model your-model
```

`model-config` 可以记录应该读取哪个环境变量，但不能保存 key 本身。

```bash
fictionops model-config my-novel \
  --provider openai \
  --planning-model planner \
  --drafting-model writer \
  --audit-model auditor \
  --api-key-env OPENAI_API_KEY \
  --write
```

## 模式五：接 Controller Loop

适合外部 controller 要根据项目证据选择下一条安全命令。

```bash
fictionops agent-next my-novel --book book_01 --chapter 001 --format json
fictionops audit-agent-workflow my-novel --level controller --book book_01 --chapter 001 --connector openai-runner
```

无模型循环示例：

```bash
python fictionops/examples/agent_controller_loop.py my-novel \
  --chapter 001 \
  --max-steps 3 \
  --log my-novel/00_management/agent_runs/controller_loop.jsonl \
  --cli fictionops
```

controller 应在这些地方停下：

- `agent-next` 报告需要人类复核；
- 已有 agent 输出等待复核；
- 下一步会覆盖正文或正史；
- 迁移状态需要人工整理或豁免；
- 同一条命令反复出现但没有推进。

## 接入前检查

真正调用模型或 controller 前，先确认：

- `fictionops audit-agent-workflow <project> --level runner`、`--level controller` 或 `--level model-runner` 返回 `ready`。
- 如果使用接入套件，`fictionops audit-agent-workflow <project> --level <level> --connector <name>` 也应返回 `ready`，并验证 connector manifest、安全标记、烟测命令和必需文件。
- 项目已经初始化，并且有 `project.yml`。
- 任务有明确的书/章范围，或有明确的审计范围。
- API key 放在环境变量里，不写进项目文件。
- runner 只写暂存输出。
- `agent-inbox` 能看到唯一、非空的候选输出。
- 采纳前仍会跑 `post-draft`、`review-gate`、`book-gate` 或 `release-gate` 等门禁。
- 人类覆盖审计建议时，重要决定会写进 decision log 或复盘。

## 不建议的接法

不要给模型、API runner 或 controller 直接写 `06_drafts/`、`05_canon/` 或 `04_structure/` 的权限，然后让它自己改文件。这可以作为私人实验，但它绕过了 FictionOps 的暂存、复核和门禁契约，不能算可审计的 FictionOps workflow。
