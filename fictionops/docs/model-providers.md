# Model Providers

FictionOps core is model-free. It records provider metadata with `model-config`, prepares task bundles with `agent-run`, and saves staged output through `agent-exec`. The actual API call belongs to an external runner.

This keeps FictionOps usable with OpenAI, Chinese mainstream model providers, local model servers, and future providers without adding every vendor SDK to the core package.

## Recommended Runner Choice

- Use `examples/agent_runner_openai_chat.py` for OpenAI-compatible Chat Completions APIs. This is the easiest path for DeepSeek, Qwen/DashScope, Kimi/Moonshot, GLM/Zhipu, Doubao/Volcengine Ark, SiliconFlow, many gateways, and local servers.
- Use `examples/agent_runner_openai_responses.py` for OpenAI's Responses API.
- Write a custom runner when the provider does not expose an OpenAI-compatible chat endpoint or needs special authentication.

## DeepSeek Example

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

Run the same command with `--dry-run` first when setting up a new provider.

## Provider Presets

These are practical starting points for OpenAI-compatible Chat Completions integrations. Provider base URLs and model IDs can change, so verify the current provider docs before production use.

| Provider | `--provider` | API key env | Base URL | Model example |
| --- | --- | --- | --- | --- |
| OpenAI Chat Completions | `openai-chat` | `OPENAI_API_KEY` | `https://api.openai.com/v1` | `gpt-4.1-mini` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | `https://api.deepseek.com` | `deepseek-chat` |
| Qwen / DashScope compatible mode | `dashscope` | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Kimi / Moonshot | `moonshot` | `MOONSHOT_API_KEY` | `https://api.moonshot.cn/v1` | provider-selected Kimi model |
| GLM / Zhipu AI | `zhipu` | `ZHIPUAI_API_KEY` | `https://open.bigmodel.cn/api/paas/v4` | provider-selected GLM model |
| Doubao / Volcengine Ark | `volcengine-ark` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3` | Ark endpoint or model ID |
| SiliconFlow | `siliconflow` | `SILICONFLOW_API_KEY` | `https://api.siliconflow.cn/v1` | provider-selected model |
| Local OpenAI-compatible server | `local-openai` | optional local env | `http://127.0.0.1:8000/v1` | local model name |

The chat runner appends `/chat/completions` to the base URL.

## Safety Rules

- Store only the environment variable name in the project, never the key value.
- Keep provider logs and diagnostics on stderr.
- Let `agent-exec` save stdout as staged output.
- Run `agent-inbox`, then the normal FictionOps gates before accepting text into manuscript or canon.
- Treat provider-specific model names as configuration, not FictionOps canon.

## When This Becomes Agentic

Calling a model through this runner is an API-backed AI workflow. It becomes an agentic workflow only when an external controller also reads FictionOps state, chooses the next safe command, runs the runner, and stops at review gates. See [Agent workflow positioning](agent-workflow.md).
