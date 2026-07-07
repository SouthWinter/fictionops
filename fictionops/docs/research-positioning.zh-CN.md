# FictionOps 研究定位

FictionOps 是一个面向长周期创作项目的 workflow harness。它使用小说作为领域，但研究问题并不只属于小说：当一个 AI-assisted 或 agentic 系统进入一个庞大、持续变化、由人类负责最终质量的项目时，如何避免上下文遗忘、源文件污染、权限失控和决策不可追踪？

本文用于研究讨论、实习面试、论文构思和系统展示。工程细节见 [Agent workflow 定位](agent-workflow.zh-CN.md)、[Agent 集成说明](agent-integration.zh-CN.md) 和 [Agent 评估协议](agent-evaluation.zh-CN.md)。

## 核心判断

FictionOps 不是模型，也不是自主小说家。它是持久创作工作区的操作层：

- 把长篇项目整理成稳定文件；
- 为具体任务编排有限上下文；
- 把模型/API 工作包装成显式任务包；
- 把模型或 runner 输出保存为暂存产物；
- 在源文件变更前运行审计和门禁。

研究贡献不是“模型会写小说”，而是边界设计：模型可以参与长期项目，但不能同时无声地变成项目记忆、编辑、发布者和最终权威。

## 问题场景

长篇小说是长周期 agent 的高压测试场，因为它同时具有：

- 庞大且持续变化的上下文；
- 复杂的信息边界；
- 人物记忆与口吻一致性；
- 长线伏笔与回声；
- 难以自动打分的主观质量；
- 人工复核、修订和发布约束；
- 需要跨月维护和恢复的大量文件。

这些特性也存在于法律文本、设计文档、科研项目、产品规格、游戏叙事、课程开发等领域。核心问题是：模型如何在持久工作区中行动，而人类仍然对最终状态负责。

## 它不是什么

FictionOps 不应该被描述成：

- 一键生成小说工具；
- 作者替代品；
- LangGraph、CrewAI、AutoGPT 那样的通用 agent 编排框架；
- 单独的 RAG 系统；
- 自动文学质量评分器。

这些系统可以接入 FictionOps，但 FictionOps 的核心是围绕持久状态、上下文编排、暂存输出、审计和门禁的工作流框架。

## 系统抽象

FictionOps 可以抽象成六层：

| 层 | 作用 | 研究功能 |
| --- | --- | --- |
| 持久工作区 | Markdown、YAML、JSON、草稿、审计、发布产物 | 给 agent 稳定外部状态，而不是依赖聊天记忆。 |
| 上下文编译器 | `context-pack`、`draft-brief`、`agent-prompt` | 把巨大项目压成任务相关上下文。 |
| 任务信封 | `agent-run` request、role、task、chapter、constraints | 让模型工作显式、可复现。 |
| Runner 边界 | `agent-exec` 接外部 API、模型或脚本 | 允许替换模型而不改变核心契约。 |
| 暂存输出 | `agent-inbox`、run receipt、output files | 阻止模型直接写入正文或正史。 |
| 审计与门禁 | 连续性、信息、人物、风格、成书、发布 | 让复核和停止条件显性化。 |

这套设计有意区分能力和权威。模型可以起草、规划或审计，但 FictionOps 要求输出先暂存，再经过复核边界，才能影响持久项目状态。

## 研究问题

FictionOps 可以支持以下研究问题：

1. **上下文治理：** 有边界的任务包是否比 raw chat 或全项目 dump 更能减少上下文漂移？
2. **权限边界：** 暂存输出和门禁是否能减少不安全直接编辑，同时保留模型协作价值？
3. **持久记忆：** 普通文件能否成为长周期 agent workflow 的可恢复记忆底座？
4. **人工复核成本：** 结构化任务轨迹和审计输出是否能降低人类判断模型贡献的成本？
5. **Controller 行为：** 外部 controller 能否选择安全下一步，并在人工复核边界停下？
6. **不依赖文学自动评分的评估：** 能否评估工作流可靠性，而不是假装自动指标等于文学判断？

## 假设

这些是研究假设，不是已经完全证明的结论：

- H1：FictionOps runner 条件比 direct-write agent 条件有更少的直接写入违规。
- H2：有边界的任务包比 raw chat 更能提高轨迹完整性、减少无关上下文。
- H3：FictionOps controller 比通用自主循环更可靠地停在复核边界。
- H4：审计和门禁产物能降低坏输出之后的恢复成本。
- H5：人类更容易接受、拒绝或隔离暂存输出，而不是自由聊天输出。

## 当前证据

公共仓库目前能证明：

- 文件优先的项目结构；
- 面向混乱旧材料的迁移工具；
- 有边界的上下文包和任务包；
- 外部 runner 执行；
- 暂存 agent inbox；
- 无模型 controller 示例；
- 连续性、信息、人物、风格、表格、波形、成书、发布和 EPUB 审计；
- 多 Python 版本 CI；
- TestPyPI release trial 证据；
- 公开 demo fixture 和私有 dogfood 总结。

但 1.0 stable core 还没有关闭。项目仍需要持续 dogfood cycle 和 stability window 的 accepted 证据。

## 评估定位

FictionOps 应该被评估为工作流系统，而不是散文模型。更有意义的指标包括：

- 暂存输出率；
- 直接写入违规；
- 复核边界召回；
- 任务轨迹完整性；
- 上下文覆盖；
- 审计问题变化；
- 恢复成本；
- 人工复核时间；
- 暂存输出接受/拒绝比例。

这些指标衡量可靠性、治理和可维护性，不声称衡量文学质量。

## 与 Agent 研究的关系

FictionOps 更接近长周期创意工作的 AgentOps / harness 层：

- 像 agent 框架一样定义工具边界和 controller-facing 命令；
- 像评估 harness 一样提供可复现任务、轨迹和指标；
- 像项目管理系统一样保存持久工作产物；
- 但它不是通用编排框架，而是对复核、源文件权威和发布门禁有强约束的领域框架。

最合适的表述是：FictionOps 是一个环境与工作流契约，外部 agents、模型 API 和 controllers 可以接入其中。

## 研究限制

当前限制：

- 私有 dogfood 不能暴露正文；
- 公开 fixture 规模较小；
- 没有公开 leaderboard；
- 模型对比实验尚未完成；
- 人工复核 rubric 仍早期；
- 自动审计是启发式的，不能替代编辑判断；
- 稳定性证据仍在等待关闭。

这些限制要主动说清楚。清楚地划边界，反而会让项目更可信。

## 一句话研究 pitch

FictionOps 是一个 local-first 的长周期写作 agent workflow harness。它把大型小说项目变成持久工作区，提供有边界的上下文包、显式任务信封、暂存模型输出、审计门禁和发布产物。核心研究问题是：agent 如何协助复杂创意项目，同时保留人类权威、可恢复性和长期状态一致性。

## 可以安全说的结论

可以说：

- FictionOps 展示了 AI-assisted 写作 workflow 的暂存输出安全边界。
- 它为评估长周期 agent 在持久项目状态中的行为提供了具体环境。
- 它区分了模型能力和源文件权威。
- 它可以接外部 runner、API、本地模型或 controller。
- 它在私有百万字级长篇项目上做过 dogfood，公开的是 workflow 证据，不泄露正文。

不要说：

- FictionOps 证明 AI 可以自主写小说。
- FictionOps 可以自动评价文学质量。
- 当前公开 fixture 足以证明泛化。
- 在持续 dogfood 和 stability window 接受前，1.0 stable core 已经完成。
