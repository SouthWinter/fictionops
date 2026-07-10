# 快速开始

FictionOps 不要求使用者一上来学完所有命令。先选一条入口，把故事跑起来；等项目变长、变乱、需要交接或接模型时，再逐步加结构。

## 入口 A：新项目

```bash
fictionops init my-novel --title "我的长篇"
fictionops new-book my-novel --book book_01 --title "第一本"
fictionops new-chapter my-novel --book book_01 --chapter 001 --title "第一章"
fictionops plan-chapter my-novel --book book_01 --chapter 001
fictionops draft-brief my-novel --book book_01 --chapter 001
```

日常循环可以很简单：

1. 更新书纲或章节发动机。
2. 生成写前任务单。
3. 自己写，或让外部助手生成暂存文本。
4. 跑 `post-draft` 和 `review-gate`。
5. 记录重要决定，再进入下一章。

## 入口 B：已有长篇迁移

```bash
fictionops adopt old-novel --out adopt_report.md
fictionops init migrated-novel --title "迁移后的长篇"
fictionops adopt old-novel --copy-to migrated-novel --format json
fictionops adopt-review migrated-novel
fictionops adopt-plan migrated-novel --write-groups 07_audits/adopt_review/repair_groups
```

适合已经有正文、设定、旧大纲、角色笔记、散落正史的项目。`adopt` 和 `adopt-review` 会先在沙盒里整理，不改原目录。

## 入口 C：接模型/API

FictionOps 核心不直接调用模型。它只准备任务包，接收外部 runner 的暂存输出。比如接 DeepSeek：

```bash
fictionops setup-ai my-novel --provider deepseek --model deepseek-chat

fictionops write-chapter my-novel \
  --book book_01 \
  --chapter 001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --provider deepseek \
  --model deepseek-chat \
  --dry-run

fictionops agent-inbox my-novel
```

先在项目外设置 `DEEPSEEK_API_KEY`，确认暂存边界没问题后，再去掉 `--dry-run`。DeepSeek、通义千问、Kimi、GLM、豆包 Ark、硅基流动、本地 OpenAI-compatible 服务和 OpenAI 的接法见 [模型供应商接入](model-providers.zh-CN.md)。

## 下一步读什么

- [CLI 使用说明](cli.zh-CN.md)：查命令细节。
- [Agent 接入指南](agent-integration.zh-CN.md)：看 runner 和 controller 怎么接。
- [模型供应商接入](model-providers.zh-CN.md)：看国内外模型 API 怎么配。
- [迁移指南](migration.md)：整理已有项目。
- [测试说明](testing.zh-CN.md)：验证本地 checkout。
