# Agent Workflow 定位说明

这份文档回答一个很窄但很重要的问题：FictionOps 接上 AI 之后，它自己算不算一个 agent workflow？

简短答案是：**算，但要说准确一点，接上模型 runner 或外部 controller 之后，整套系统构成 agentic workflow；FictionOps 本体仍然是 workflow harness，不是那个 autonomous agent。**

## 边界怎么划

FictionOps 本体负责四件事：

- 准备范围化上下文；
- 打包有边界的任务；
- 记录暂存输出；
- 在正文或正史被接纳前运行门禁与审计。

外部 AI runner 或 controller 才负责 agent 行为：

- 读取任务包；
- 调用模型或本地 agent；
- 写回暂存结果；
- 必要时询问 FictionOps 下一条安全命令。

可以这样区分：

| 接入方式 | 定位 | 原因 |
| --- | --- | --- |
| 只使用 FictionOps，不调用 AI | 工作流工具 | 它组织和审计项目，但没有模型在行动。 |
| 作者把 `context-pack` 复制进聊天框 | AI-assisted workflow | 人决定任务，也决定如何采纳结果。 |
| `agent-run` + 外部模型 runner + `agent-inbox` | 有边界的 agent workflow | 模型执行范围化任务，FictionOps 把结果收进暂存区等待复核。 |
| 接入 runner/controller 前运行 `audit-agent-workflow` | 预检门禁 | FictionOps 检查项目骨架、暂存输出、模型配置和 controller 边界是否 ready。 |
| `agent-next` + 外部 controller | agentic workflow | controller 可以根据项目证据选择下一条安全命令。 |
| controller 连续推进多步，但保留暂存输出和门禁 | 接近自主的 agentic workflow | 自动化能推进流程，但权力不直接交给模型输出。 |
| 模型直接覆盖正文或正史 | 不属于 FictionOps 安全契约 | 它绕过了暂存、复核和门禁。 |

## 为什么这件事重要

很多 AI 写作工具一接模型就会变脆：模型看得太多、忘得太多，或者拿了太多权力。FictionOps 试图把这个风险拆成几个可见层：

- **上下文边界：** Agent 只拿到当前任务需要的材料。
- **角色边界：** 提示词明确它是在写作、审稿、规划还是发布。
- **暂存边界：** 输出先落在任务包旁边，不直接进入正文。
- **门禁边界：** 后续命令判断项目是否真的可以进入下一步。
- **人类权威：** 人决定什么进入正史、正文和发布稿。

所以 FictionOps 不是在争当“更会写小说的 agent”。它更像一层操作系统，让多个 agent 可以参与长篇项目，却不悄悄破坏正史、信息边界和复盘顺序。

## 实际怎么叫

如果只是把 AI 当成单次助手，叫 **AI-assisted FictionOps**。

如果接入外部 runner，让模型读取任务包并写回暂存输出，叫 **FictionOps agent workflow**。

如果接入 controller，让它读取 `agent-next` 的 JSON 并串联多条命令，叫 **FictionOps agentic workflow**。

接入 runner 或 controller 前，可以先运行 `fictionops audit-agent-workflow <project> --level runner`、`--level controller` 或 `--level model-runner`，确认当前项目适合进入对应接入层级。

如果让模型绕过暂存和门禁，直接改正文或正史，就不要说它是 FictionOps-compatible automation。它可以是实验，但不属于 FictionOps 的核心安全模型。

## FictionOps 源码包自身的 controller 边界

当目标路径是 FictionOps 源码包本身时，`fictionops audit-agent-workflow <package-checkout> --level controller` 不应把它误判成待迁移小说项目，也不应建议 `adopt`。它会沿用 `agent-next` 的 package governance 模式，读取 stable-core governance action items，并在外部发行证据、持续 dogfood 证据或稳定窗口证据这类不能由 controller 伪造的事项前返回 `needs_human_review`。
