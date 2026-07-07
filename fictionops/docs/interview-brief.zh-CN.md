# 面试备忘：FictionOps

这份文档用于在 agent 研究或应用 AI 工程面试中介绍 FictionOps。它刻意短、证据导向，方便快速组织回答。

## 60 秒介绍

FictionOps 是一个面向长篇小说项目的 AgentOps 风格 workflow harness。它不是一键小说生成器，也不是自主写作 agent。它解决的核心问题是长程项目维护：一部长篇会不断积累大纲、正史、人物记忆、信息边界、修订历史、模型交接和发布产物。

FictionOps 把这些东西组织成文件化 workflow：CLI 审计、范围化上下文包、暂存式 agent 输出、修订计划、门禁和发布产物。模型或 API runner 可以在限定任务里提出输出，但 FictionOps 把最终权力留给人：输出进入 inbox，审计暴露风险，门禁决定项目是否能进入下一阶段。

我用一个私有百万字级长篇项目做了 dogfood。这个项目完成了项目记忆修复、33 个计划章节和正文/章节发动机同步、把风格警告转成人工读者体验判断、有边界的 prose pass，以及 clean Markdown、metadata、manifest、EPUB 和 release-gate 证据生成。

## 要强调什么

- 它是 workflow harness，不是写作模型。
- 研究问题是长程 agent 如何在持久外部状态中可控工作。
- 领域是小说，但技术模式可以迁移到其他复杂项目：外部记忆、范围化上下文、人类复核、门禁。
- 核心贡献不是自动写正文，而是 scoped context、staged output、auditability、recovery 和 gates。
- 公开仓库不暴露私有正文，只保留流程证据。

## 具体证据

私有 dogfood 关键结果：

- `adopt-review`: `ready=true`, `blocking_issue_count=0`。
- `audit-info`: 8 条信息释放行，`issues=0`。
- `audit-characters`: 8 条人物弧线、8 个智慧模式、8 个口吻资料，`issues=0`。
- `audit-plan`: 33 个计划章节、33 个正文、33 个章节发动机、33 个同步发动机，`issues=0`。
- `audit-echoes`: 3 条活动长线，`issues=0`。
- bounded prose pass 后，style watch total 从 3843 降到 3770。
- `audit-publish`: 33 个 clean 章节对应 33 个草稿章节，`issues=[]`。
- `audit-epub`: `epub_valid=true`，33 章，`issues=[]`。
- `book-gate`: `Ready: yes`，阻塞 0。
- `release-gate`: `Ready: yes`，阻塞 0。

公开证据：

- [Dogfood 案例研究](dogfood-case-study.zh-CN.md)
- [持续 dogfood 周期证据](dogfood-cycle-evidence.md)
- [Agent evaluation protocol](agent-evaluation.md)
- [Agent workflow positioning](agent-workflow.md)

## 架构讲法

FictionOps 可以讲成四层：

1. **项目记忆层：** 用 Markdown、YAML、JSON 管理结构、正史、人物、正文、审计和发布。
2. **审计和门禁层：** `audit-info`、`audit-characters`、`audit-plan`、`audit-wave`、`revision-plan`、`book-gate`、`release-gate`。
3. **Agent 边界层：** `context-pack`、`agent-run`、`agent-exec`、`agent-inbox`、`agent-next`、`eval-agent`。
4. **发布层：** `export-clean`、`export-metadata`、`export-manifest`、`export-epub`、`audit-epub`。

最重要的安全契约是：模型输出先暂存，不直接写入正史或正文。

## 常见追问

### FictionOps 算 agent 吗？

FictionOps 本体不是 agent，而是 workflow harness。接上外部 runner 调用模型 API 后，它是 API-backed AI workflow。再接上 controller，由 controller 读取项目状态、选择安全下一步、调用 runner，并在门禁处停止，整体才构成 agentic workflow。

### 为什么用小说做领域？

长篇小说是很强的长程 benchmark。它有巨大上下文、隐藏知识状态、连续性约束、主观质量、修订历史和发布产物。它会暴露短任务不容易暴露的问题：遗忘承诺、信息提前泄露、风格变平、直接改坏 source-of-truth 文件。

### 和 RAG 有什么区别？

RAG 主要解决一次模型调用要取哪些上下文。FictionOps 解决的是上下文之外的整个工作流：哪些文件是长期记忆、哪些进入当前任务包、输出暂存在哪里、任务后跑哪些审计、哪些门禁阻止发布。RAG 可以是其中一部分，但不是整个系统。

### 和 LangGraph / AutoGPT / CrewAI 有什么区别？

那些更像通用 agent 编排框架。FictionOps 是面向长篇项目维护的领域 harness 和评估表面。它可以接外部 runner 或 controller，但核心价值是持久项目状态、审计、门禁和发布链路。

### 技术难点是什么？

难点是把混乱的人类写作工作转成稳定、可机器检查的边界，同时不假装静态检查就是文学判断。比如某个词频很高，不等于一定要全局替换；FictionOps 要把它转成阅读提示，再保留人类判断。

### 怎么评估？

不自动评价文学质量，而评价 workflow 可靠性：阻塞问题数量、章节同步覆盖、审计问题变化、staged output rate、gate readiness、发布产物有效性，以及系统是否在 human-review boundary 停下。私有 dogfood 是一条证据链；更正式的研究可以比较 raw chat、direct-write agent、FictionOps runner 和 FictionOps controller。

### 局限是什么？

当前证据主要来自一个私有大型项目和公开 demo fixture。审计是启发式且偏保守的。FictionOps 不替代审美判断。持续 dogfood cycle 还没到七天窗口结束。更强结论需要跨项目、跨模型、跨 controller 重复实验。

## 简历 bullet

Built FictionOps, an open-source AgentOps-style workflow harness for long-form fiction projects, with structured project memory, scoped context packs, staged agent outputs, audit gates, revision planning, and publish/export pipelines. Dogfooded it on a million-character-scale novel project to study long-horizon consistency, controllable agent handoff, and human-in-the-loop revision workflows.

## 不要这样说

- 不要说 FictionOps 是完全自主小说家。
- 不要说文学质量可以自动打分。
- 七天窗口结束前，不要说私有 dogfood cycle 已 accepted。
- 不要暴露私有正文或未公开故事细节。
- 不要把它讲成通用 Python 发布工具。
