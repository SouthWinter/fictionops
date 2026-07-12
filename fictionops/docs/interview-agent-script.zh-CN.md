# FictionOps Agent 科研实习面试讲稿

## 三分钟版

### 0:00–0:30：问题

我用自己的百万字级长篇项目研究长程 Agent。真实问题不是模型能不能写出一章，而是它能否跨很多次会话维护人物知识、信息释放、物件状态、修改历史和作者偏好。普通聊天或 RAG 只能回答“这次给模型看什么”，不能保证中断恢复、错误不重复、输出不污染正文，也不能决定什么时候必须停下来交给作者。

### 0:30–1:10：核心洞察

我最初以为“精炼上下文 + 模型自评”就够了。真实 DeepSeek dogfood 中，模型生成了长度和结构都合格的候选，也逐项声称约束通过，但实际进入了禁止视角、凭空增加记忆，并保留了要求降低的文字问题。第二个模型 verifier 仍然给出假阳性。

所以我把可靠性从模型内部外置：模型负责生成和语义判断；确定性 controller 管理持久状态、预算、证据合并、恢复和作者权限。

### 1:10–2:05：系统

系统先从项目记忆编译有来源、权威级别和 token 预算的上下文；再做因果模拟和场景状态规划；writer 生成暂存候选；独立 reviewer 与确定性 gate 分别检查语义问题和可执行约束。两类证据合并后，失败只路由到受影响场景。即使全部通过，也只到 `ready_for_approval`，必须由作者显式 accept。

每个 session 都有 checkpoint、问题账本、模型调用预算和统一 `trajectory.jsonl`。轨迹记录 observation、context attribution、decision、action、model receipt、state transition 和 authority，所以可以判断失败来自检索、推理、验证还是 controller。

### 2:05–2:40：证据

一次逐场景实验调用 DeepSeek 21 次，状态和体量最终稳定，但文学问题仍未解决，系统正确停在 `needs_revision_attention`，没有覆盖正文。这个失败驱动了证据 grounding、metric progress、选择性复修和预算控制。

当前工程有 158 条回归测试；failure lab 对源文件漂移、产物篡改、取消后恢复、预算耗尽、畸形 receipt、悬空证据和禁提前结论实现了 7/7 检测，受保护正史哈希保持不变。另有 raw/RAG/full/ablation 的一键实验 harness。

### 2:40–3:00：边界

我不 claim 它已经提高文学质量。当前证明的是：可以构造一个 artifact-grounded、author-governed 的长程创作 Agent，使状态、失败、成本和权限可追踪、可恢复、可实验。下一步是固定模型做多次对照和人工盲评。

## 十分钟版

### 1. 场景与研究问题（1 分钟）

- 项目规模：百万字级正文、人物、书纲、卷纲、信息边界和长期修订历史。
- 研究问题：上下文重置后，Agent 如何继续工作而不是重新猜测项目状态？
- 成功定义：不只看输出质量，还看状态一致性、证据落地、恢复成本和人类权限。

### 2. 失败的初版假设（1 分钟）

- 初版：RAG + 写作模型 + 第二次模型检查。
- 失败：verifier 会重复生成模型的盲点，并把结构完整误判成约束满足。
- 结论：self-reflection 不能作为唯一验收器。

### 3. 分层架构（2 分钟）

1. **Memory/Context Compiler**：检索正史、人物、连续性、作者偏好；记录来源、authority、reason、hash 和字符预算。
2. **Story State**：因果图、场景 entry/exit state、数量/时间/物件账本、知识边界。
3. **Model Worker**：planner、writer、reviewer、targeted reviser，通过统一 runner 接口调用不同模型。
4. **Deterministic Controller**：状态转移、预算、schema repair、证据 grounding、hash/checkpoint、停止条件。
5. **Human Authority**：候选暂存；`ready_for_approval` 与 `accepted` 分离。

### 4. 为什么需要统一轨迹（1 分钟）

之前日志分散在 session、events、budget 和 verification 中，不适合研究归因。现在 `trajectory.jsonl` 将一次 Agent 行为统一成：

```text
observation -> retrieved context -> decision -> action/model call
            -> verification -> state transition -> authority
```

这使我们能区分 retrieval failure、reasoning failure、verification failure 和 control failure，并比较每一步的 token/费用。

### 5. 三次真实模型失败（2 分钟）

- 旧章修订：目标问题未下降、模型新增记忆，verifier 假阳性。
- 最小上下文盲写：8304 字符且非复制，但违反人物成长和视角约束。
- 逐场景生成：21 次调用后状态稳定，文学门禁仍拒绝；说明 workflow 完成不等于作品合格。

每次失败都对应可定位的系统改动，不是继续加 prompt。

### 6. 评估设计（1 分钟）

- `agent benchmark`：raw、RAG、full、no-memory、no-guard、no-contract；支持重复运行。
- 指标：类别命中、证据落地、额外问题、token、费用。
- `agent failure-lab`：故障发现点、恢复成功率、正史污染。
- 后续：固定模型多次采样、人工盲评、作者复核时间、采纳率和编辑距离。

### 7. 工程与研究权衡（1 分钟）

- 文件式状态比纯向量库慢，但可审计、可版本控制、能表达权威层级。
- 多 reviewer 增加成本，所以做证据路由和选择性复修。
- 确定性规则不能判断文学好坏，只负责可明确验证的底线。
- 不做无人值守全书改稿，因为扩大自动修改半径会破坏作者权限和实验可解释性。

### 8. 结论（1 分钟）

FictionOps 的核心不是小说领域的 prompt 集，而是一个面向真实长程创作的 Agent harness：把隐含在聊天上下文里的状态、证据、恢复和权限变成可执行、可观察、可对照的系统对象。小说是压力测试域，这套模式可以迁移到研究、法务文档、复杂报告等长期知识工作。

## 高频追问

### 这不就是 RAG 吗？

RAG 解决一次调用检索什么。FictionOps 还管理检索材料的权威与新鲜度、跨 session 状态、候选隔离、验证、预算、失败恢复和作者采纳。RAG 是 Context Compiler 的一个组件。

### 为什么算 Agent，不只是 workflow？

模型根据动态状态生成计划和动作，controller 根据模型输出、工具证据、预算和权限选择下一状态；失败会触发定向重试或恢复，过程跨会话持久化。它不是固定流水线，但也不是让模型任意决定权限的全自治 Agent。

### 为什么不用 LangGraph/CrewAI？

它们适合通用编排；本项目研究的是领域状态、证据和验收语义。runtime 可以以后挂在通用编排器下，但核心贡献不是重新实现图执行器，而是定义长期创作任务的状态与失败边界。

### 多 Agent/多 reviewer 真的有用吗？

角色数量本身不是贡献。关键是 reviewer 与 writer 的证据和权限分离，并且 reviewer 结论必须通过 candidate grounding；否则多个模型只会放大共同偏差。

### 21 次调用是不是太贵？

是，所以这次 dogfood 的价值正是暴露成本问题。后来增加调用/token/费用预算、场景级证据路由和选择性复修。面试时不把 21 次当成绩，而把“从成本失败推导 controller 设计”作为研究过程。

### 怎么处理记忆冲突？

记忆记录来源、hash、authority 和类型。作者显式偏好与当前正史高于回顾和旧稿；冲突不能由相似度自动覆盖，必须暴露给 controller 或作者。后续还可以专门评估 conflict resolution。

### 如何避免 evaluator 和生成模型同源偏差？

三层处理：独立 prompt/角色；证据必须落在候选原文；可确定的约束由静态 gate 判断，模型 verdict 不能覆盖静态失败。更正式实验还应跨模型 reviewer 和人工盲评。

### 当前最大的研究不足是什么？

真实证据主要来自一个中文长篇和少量 DeepSeek dogfood。三个公开 fixture 只能验证协议，不能证明泛化。下一步应扩任务集、固定模型重复采样，并加入独立人工标注。

### 如果部署到大厂场景，最先改什么？

把文件事件接入对象存储/数据库与统一 trace backend；增加并发控制、租户隔离、PII 策略和异步队列；保留同一 trajectory、checkpoint、evidence 和 authority schema。不会先增加更多 Agent 角色。

### 你个人最重要的技术判断是什么？

不要把“模型能解释自己为什么正确”当成可靠验证。长程 Agent 需要把状态、证据和权限外置，让失败能被另一个机制观察和阻断。

## 简历 Bullet

Built and dogfooded FictionOps, an artifact-grounded long-horizon writing agent harness with attributed project memory, causal/scene state, independent evidence-grounded review, deterministic gates, checkpoint recovery, token/cost budgets, unified trajectories, and explicit human authority; added reproducible raw/RAG/ablation evaluation and a 7-scenario failure-injection lab over a million-character Chinese fiction project.
