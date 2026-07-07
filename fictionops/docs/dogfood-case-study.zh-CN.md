# Dogfood 案例研究：用 FictionOps 维护一部百万字级长篇

这份案例研究总结了一次真实私有项目 dogfood。正文、专有设定、人物细节和本地路径都已从公开仓库中移除。公开价值不在于展示小说内容，而在于展示一套长程复杂创作项目如何被 FictionOps 迁移、审计、修复、导出、打包和门禁。

当前持续 dogfood 周期仍在七个自然日窗口内，结论仍是 deferred。这份文档是案例研究，不是 1.0 accepted 声明。

## 问题

长篇小说是一个很好的 agent workflow 压力测试，因为难点并不是一次性生成正文。

一个大型长篇项目会同时包含：

- 单次模型调用装不下的超长上下文；
- 持续演化的大纲、正史、人物记忆和信息边界；
- 多层知识状态：不同角色、不同读者阶段知道和不知道的东西不同；
- 不能用全局替换解决的局部行文问题；
- clean Markdown、metadata、manifest、EPUB 等发布产物；
- 必须保留在人类手里的审美判断。

dogfood 开始前，私有项目是典型的长期写作工作区：材料很多，也很有价值，但分散在大纲、正文、导入笔记、复盘、旧模板和发布文件里。目标不是让 agent 重写这本书，而是把这个项目整理成一套可维护、可审计、可恢复的状态机。

## FictionOps 做了什么

FictionOps 在这里扮演的是 AgentOps 风格的 workflow harness。

它提供：

- 项目记忆分层：结构、正史、人物、正文、审计、发布；
- 信息释放、人物弧线、表格卫生、章节计划、伏笔回声、连续性、行文模式和章节体量波形等静态审计；
- `revision-plan`，把审计结果转成有优先级的修订任务；
- `context-pack` 和 agent harness 命令，把模型可见上下文限制在任务范围内；
- inbox 和 gate 语义，让外部 agent 输出先暂存，不直接覆盖正文；
- clean Markdown、metadata JSON、manifest JSON、EPUB 和 release gate 等发布链路。

关键设计是权责分离：

- FictionOps 负责暴露信号和执行门禁。
- 外部模型/API runner 负责在限定任务里生成或建议输出。
- 人类判断负责决定某个行文信号是不是真的伤害阅读体验。
- 生成物默认不覆盖源正文，必须经过复核边界。

## 工作流

这次 dogfood 使用的是迁移后的私有沙盒，而不是原始小说目录。这样 FictionOps 可以修复、导出和打包项目，同时不冒险覆盖源文件。

维护顺序是：

1. 跑迁移和健康检查：`adopt-review`、`doctor`、`audit-info`、`audit-characters`、`context-pack`、`revision-plan`、`eval-agent`。
2. 先修项目记忆，再修正文：信息释放表、人物记忆表、活动表格卫生、书级大纲同步、伏笔和连续性追踪。
3. 把风格和波形提示转成读者体验 memo，而不是立刻机械改文。
4. 经过人工分类后，只对高优先级章节做有边界的 prose pass。
5. 每轮 prose pass 后重新跑 style、word、wave 审计。
6. 导出 clean Markdown 并跑发布门禁。
7. 生成 metadata、manifest、EPUB 和 release gate 证据。

这个顺序很重要。它避免了一个常见 agent 失败模式：底层项目记忆还不一致，就开始局部润色正文。

## 结果

这轮 dogfood 产生了一组可量化的状态变化。

项目记忆修复：

- 私有沙盒中 `adopt-review` 达到 `ready=true`，`blocking_issue_count=0`。
- 信息释放表修复后，`audit-info` 达到 `item_count=8`、`issues=0`。
- 人物记忆层修复后，`audit-characters` 达到 8 个角色、8 条人物弧线、8 条索引、8 个智慧模式、8 个口吻资料，`issues=0`。
- 活动表格问题降到 `0`。
- 第一本大纲和正文库存同步：33 个计划章节、33 个正文文件、33 个章节发动机、33 个同步发动机，`issues=0`。
- 伏笔回声表收束为一个活动表、3 条长线，`issues=0`；连续性模板问题降到 `0`。
- 私有 `revision-plan` 从初始 616 个任务，降到结构修复后的少量非阻塞 style/wave/word-scan notes。

读者体验修复：

- 第一轮读者体验 memo 先分类高优先级章节，没有做全局替换。
- prose pass 只处理明确目标：无名称谓重复、宫廷解释密度、第一次见血的因果解释、骨刀章轻读。
- style watch total 从读者体验基线的 3843 降到 targeted prose pass 后的 3770。
- 章节波形仍保留相同的已知节奏提示，没有引入新的 pacing category。
- 核心原则得以保留：词频和风格信号只是阅读提示，不是机械改文命令。

发布链路烟测：

- clean Markdown 成功导出 33 章。
- `audit-publish` 报告 clean 章节 33，对应 draft 章节 33，`issues=[]`。
- metadata JSON、manifest JSON 和 EPUB 均成功生成。
- `audit-epub` 报告 `epub_valid=true`，33 章，`issues=[]`。
- `book-gate` 报告 `Ready: yes`，`Blocking issues: 0`。
- `release-gate` 报告 `Ready: yes`，`Blocking issues: 0`。

发布 metadata 中使用了沙盒占位作者名，只用于跑通发布链路，不是真实发布笔名。

## 这说明了什么

这次 dogfood 支持的不是“AI 能自动写小说”这种笼统说法。

它更准确地说明：一个长程创作项目可以被组织成可审计的 workflow。

具体来说：

- 混乱旧材料可以被阶段化迁移进结构化项目；
- 项目记忆问题可以在 prose edit 前被优先修复；
- agent 可见上下文可以被范围化，而不是把整本书塞给模型；
- 风格和节奏信号可以先进入人工阅读判断；
- 发布产物可以可复现地生成和门禁；
- 每一轮修复都能留下证据。

因此，FictionOps 更适合被描述为 workflow harness，而不是自主写作者。

## Agent 研究视角

从 agent 研究角度，这个案例对应几个问题：

- 长上下文任务分解；
- 外部记忆维护；
- human-in-the-loop revision；
- scoped context selection；
- 安全输出暂存；
- workflow recovery 和拒绝危险覆盖；
- 超越单轮答案质量的评估；
- 面向创作领域的专用门禁。

FictionOps 不绑定某个模型提供商。它本体不直接调用模型，只准备有边界的任务包；外部 runner 或 controller 可以调用 OpenAI、本地模型服务器或其他 API。

## 避免的失败模式

这轮 dogfood 刻意避免了几种捷径：

- 对高频词做全局替换；
- 为了统一字数而填充章节；
- 把静态审计警告当成文学判断；
- 让 agent 直接覆盖源正文；
- 七天窗口未结束就声称 dogfood accepted；
- 在公开证据中暴露私有正文。

## 当前限制

这仍然只是一个私有长篇项目的案例，不证明所有类型、所有语言、所有团队都能直接适用。

当前限制包括：

- 文学质量仍需要人类判断；
- 部分审计是启发式的，而且故意偏保守；
- 公开仓库只有脱敏证据，不包含私有正文；
- 持续 dogfood 周期仍在 deferred 状态，必须等维护窗口结束后复核；
- 若要做更正式的 agent 评估，还需要跨模型、跨 controller、跨项目重复实验。

## 可复现证据

相关公开证据：

- [持续 dogfood 周期证据](dogfood-cycle-evidence.md)
- [真实长篇 adopt dogfood 报告](dogfood-legacy-adopt.zh-CN.md)
- [Agent evaluation protocol](agent-evaluation.md)
- [Agent workflow positioning](agent-workflow.md)
- [End-to-end migration and publishing case](end-to-end-migration-publish.md)

公开记录刻意以证据为中心：记录跑过哪些命令、哪些门禁发生变化、哪些结论仍然 deferred，同时不把私有创作内容放进仓库。
