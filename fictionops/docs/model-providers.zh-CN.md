# 模型供应商接入

FictionOps 核心不直接调用模型。它用 `setup-ai` 或 `model-config` 记录供应商元数据，用 `agent-run` / `write-chapter` 准备任务包，再通过 `agent-exec` 保存外部 runner 的暂存输出。真正的 API 调用放在外部 runner 里。

这样可以同时支持 OpenAI、国内主流模型供应商、本地模型服务和未来新供应商，而不把核心包变成一堆厂商 SDK。

## 推荐 runner

- `examples/agent_runner_openai_chat.py`：用于 OpenAI-compatible Chat Completions 接口。DeepSeek、通义千问/DashScope、Kimi/Moonshot、GLM/智谱、豆包/火山方舟、硅基流动、很多网关和本地服务都适合先走这条。这个 runner 支持 provider preset、显式 `.env`、dry-run 报告、timeout、输出长度保护，以及针对传输错误、HTTP 429 和 HTTP 5xx 的有限重试。
- `examples/agent_runner_openai_responses.py`：用于 OpenAI Responses API。
- 如果供应商不是 OpenAI-compatible chat 接口，或鉴权方式特殊，就写自定义 runner。

OpenAI-compatible runner 会在每次真实调用成功后，通过 stderr 输出带版本的 telemetry receipt。provider 响应 id 与 token usage 会自动进入 `execution.json` 和 `model_budget.json`。只有显式传入 `--input-cost-per-million` 和/或 `--output-cost-per-million` 时才计算费用；FictionOps 不内置容易过期的供应商价格表。

```powershell
fictionops agent write chapter.md --engine engine.md --max-total-tokens 200000 --max-cost 2.00 --cost-currency USD --runner python examples/agent_runner_openai_chat.py --provider deepseek --model deepseek-chat --input-cost-per-million 0.27 --output-cost-per-million 1.10
```

token/费用阈值依据 provider 已回传的消耗，并在下一次模型调用前检查。因此单次正在进行的响应可能越过阈值；controller 会记录超额，并拒绝后续调用。

## DeepSeek 示例

```bash
fictionops setup-ai my-novel --provider deepseek --model deepseek-chat
```

`setup-ai` 会写出 `00_management/model_config.json` 和 `00_management/ai_runner.env.example`。env 示例只包含变量名，不包含真实 key。

底层命令链也可以手动写：

```bash
fictionops model-config my-novel \
  --provider deepseek \
  --planning-model deepseek-chat \
  --drafting-model deepseek-chat \
  --audit-model deepseek-chat \
  --api-key-env DEEPSEEK_API_KEY \
  --base-url https://api.deepseek.com \
  --write

fictionops agent-run my-novel \
  --role draft-writer \
  --book book_01 \
  --chapter 001 \
  --out-dir my-novel/00_management/agent_runs/ch_001

set DEEPSEEK_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --model deepseek-chat \
  --api-key-env DEEPSEEK_API_KEY \
  --base-url https://api.deepseek.com
```

第一次接新供应商时，先加 `--dry-run` 检查暂存边界。

v1 chat runner 也可以直接使用 DeepSeek preset：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --dry-run \
  --provider deepseek \
  --model deepseek-chat
```

真实调用时，key 仍然放在项目外：

```bash
set DEEPSEEK_API_KEY=...
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --provider deepseek \
  --model deepseek-chat \
  --max-output-chars 12000
```

如果想用 `.env`，必须显式传路径：

```bash
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --provider deepseek \
  --env-file my-runner.env
```

runner 会先读取这个文件，再解析 provider、model 和 key 环境变量。真实 API key 不要提交进仓库。

## 常见供应商起点

下面是 OpenAI-compatible Chat Completions 接口的实用起点。供应商 base URL 和模型 ID 可能变化，正式使用前请核对当前官方文档。

| 供应商 | `--provider` | 密钥环境变量 | Base URL | 模型示例 |
| --- | --- | --- | --- | --- |
| OpenAI Chat Completions | `openai-chat` | `OPENAI_API_KEY` | `https://api.openai.com/v1` | `gpt-4.1-mini` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | `https://api.deepseek.com` | `deepseek-chat` |
| 通义千问 / DashScope 兼容模式 | `dashscope` | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Kimi / Moonshot | `moonshot` | `MOONSHOT_API_KEY` | `https://api.moonshot.cn/v1` | 当前 Kimi 模型 |
| GLM / 智谱 | `zhipu` | `ZHIPUAI_API_KEY` | `https://open.bigmodel.cn/api/paas/v4` | 当前 GLM 模型 |
| 豆包 / 火山方舟 | `volcengine-ark` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3` | Ark endpoint 或模型 ID |
| 硅基流动 | `siliconflow` | `SILICONFLOW_API_KEY` | `https://api.siliconflow.cn/v1` | 当前供应商模型 |
| 本地 OpenAI-compatible 服务 | `local-openai` | 可选本地变量 | `http://127.0.0.1:8000/v1` | 本地模型名 |

chat runner 会在 base URL 后拼接 `/chat/completions`。

runner 支持的 provider alias：

- `openai`、`openai-chat`
- `deepseek`
- `dashscope`、`qwen`
- `moonshot`、`kimi`
- `zhipu`、`glm`
- `volcengine-ark`、`doubao`
- `siliconflow`
- `local-openai`、`local`

本地无鉴权服务可用 `--provider local-openai`；除非额外指定 API key env，runner 不会发送 Authorization header。

## 安全规则

- 项目里只记录环境变量名，不记录真实 key。
- 供应商日志和诊断写 stderr。
- stdout 只写候选暂存输出，由 `agent-exec` 保存。
- 第一次真实调用前先跑 `--dry-run`。
- 初次连接建议加 `--max-output-chars`，避免异常长输出直接进入暂存。
- 先跑 `agent-inbox`，再跑 FictionOps 的正常门禁，最后才决定是否进入正文或正史。
- 模型名属于运行配置，不属于 FictionOps 正史。

## 什么时候算 agentic workflow

单纯通过 runner 调模型，是 API-backed AI workflow。只有外部 controller 进一步读取 FictionOps 状态、选择下一条安全命令、调用 runner，并在复核门禁前停下，整套系统才算 agentic workflow。参见 [Agent workflow 定位](agent-workflow.zh-CN.md)。
