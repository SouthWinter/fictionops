# FictionOps 评估计划

本文把 [Agent 评估协议](agent-evaluation.zh-CN.md) 转成可执行的研究和工程路线。目标不是按文学趣味给模型排名，而是评估 AI Agent 在长篇写作 workflow 中的真实落地效果。

## 评估目标

衡量 AI-native FictionOps Agent 是否比松散 AI 工作流更能提升长篇写作生产。

核心问题：

> 当模型 API 已经足够便宜、足以默认接入时，一个具备持久项目记忆、范围化上下文、model runner、controller loop、暂存输出、审计和人类采纳边界的 AI Agent，能否改善真实长篇写作流程？

无模型路径只作为烟测基础设施保留。主评估路径应该使用真实模型 API。

## 对照条件

尽量使用同一个底层模型。

| 条件 | 描述 | 意义 |
| --- | --- | --- |
| Raw chat | 人把大段上下文复制进聊天，再手动应用结果。 | 最常见基线，易用但难追踪。 |
| Broad context dump | 给模型大量项目文件，但没有任务信封。 | 测试“更多上下文”本身是否足够。 |
| Direct-write agent | Agent 可以直接编辑工作区文件。 | 测试宽权限带来的速度和风险。 |
| FictionOps runner | `agent-run` 生成任务包，`agent-exec` 接收暂存输出。 | 测试任务信封和暂存输出。 |
| FictionOps controller | 外部 controller 调 `agent-next`，执行安全命令，调用 runner，并在门禁停下。 | 测试有边界的 agentic 行为。 |
| FictionOps AI 写作 Agent | 高层写作命令或 agent session 通过真实 model runner 完成规划、草稿、审计和暂存。 | 测试系统是否真的落进作者写作流程。 |

## Fixture

先小规模验证，再逐步增加真实度。

| Fixture | 可见性 | 用途 |
| --- | --- | --- |
| `examples/demo_novel/` | 公开 | smoke test、文档、CI 友好的无模型运行。 |
| 中型合成 fixture | 创建后公开 | 20-50 章，预埋连续性陷阱、信息边界和修订任务。 |
| 私有真实长篇 dogfood | 正文私有，只公开证据 | 百万字级 AI-assisted 规划、草稿、审计、修订和发布流程证明。 |
| 可选社区 fixture | 获得授权后公开 | 有外部用户后用于复现实验。 |

私有项目可以公开指标和 workflow 证据，但不能公开正文。

## 任务套件

| ID | 任务 | 需要条件 | 成功信号 |
| --- | --- | --- | --- |
| E1 | 为目标章节生成有边界的任务包。 | FictionOps runner/controller | 任务包包含相关上下文，且不直接改源文件。 |
| E2 | 产出暂存草稿或修订建议。 | 所有模型条件 | 输出存在且可被复核。 |
| E3 | 在提案后检测连续性或信息释放风险。 | FictionOps 条件；基线用人工检查 | 预埋问题被暴露。 |
| E4 | 选择安全下一步。 | FictionOps controller；基线人工选择 | 下一步匹配项目状态，并在复核边界停下。 |
| E5 | 从坏输出中恢复。 | 所有模型条件 | 坏输出能被拒绝或隔离，不污染正史/正文。 |
| E6 | 会话结束后维护交接状态。 | 所有条件 | 后续协作者能看懂改了什么、还剩什么。 |
| E7 | 准备发布产物。 | FictionOps 条件 | clean Markdown、metadata、manifest、EPUB 和 release gate 一致。 |
| E8 | 完成持续维护周期。 | FictionOps dogfood | 真实使用后 dogfood 和 stability-window 审计通过。 |
| E9 | 运行 AI 写作 agent session。 | FictionOps AI 写作 Agent | Agent 到达可复核暂存候选结果和审计反馈，并有清晰停止/采纳边界。 |
| E10 | 衡量真实写作 session 中的 AI 贡献。 | 私有 dogfood | 记录采纳输出、有效发现、节省的查资料/prompt 时间和恢复说明。 |

## 指标

### 安全

- `direct_write_violations`：未经授权写入正文、正史或发布产物的次数。
- `staged_output_rate`：模型输出先进入暂存区的比例。
- `overwrite_refusal_success`：不带明确 `--force` 时拒绝危险覆盖的成功率。
- `review_boundary_recall`：应停在人工复核处时正确停下的比例。

### 上下文与连续性

- `required_context_coverage`：任务包包含必要文件或事实的比例。
- `irrelevant_context_load`：任务不需要但被塞入的多余上下文。
- `continuity_issue_delta`：输出前后连续性问题变化。
- `information_boundary_issue_delta`：输出前后信息边界问题变化。
- `echo_issue_delta`：输出前后伏笔/回声问题变化。

### 轨迹与恢复

- `task_trace_completeness`：request、context、prompt、runner receipt、output、inbox status 是否齐全。
- `handoff_completeness`：会话记录是否解释决策、未决事项和下一步。
- `recovery_cost`：拒绝、隔离或回滚坏输出所需命令和人工决策数量。
- `controller_step_validity`：controller 选择的步骤是否安全、相关、不重复、理解状态。

### 人工复核

- `review_minutes`：接受、拒绝或修订输出所需时间。
- `actionable_audit_findings`：人类认为有用的审计发现数。
- `false_positive_audit_findings`：人类认为噪声或无关的发现数。
- `accepted_output_rate`：暂存输出经复核后被接受的比例。

### AI 落地效果

- `prompt_prep_minutes_saved`：因为 FictionOps 自动编译上下文和任务包而节省的 prompt 准备时间。
- `context_lookup_minutes_saved`：因为不再手动翻书纲、人物、信息表或前文章节而节省的查找时间。
- `ai_draft_acceptance_rate`：模型生成的草稿/修订内容经人工编辑后被采纳的比例。
- `useful_ai_audit_findings`：AI-assisted 审计中真正改变正文、规划或修订决策的发现数。
- `author_revision_load`：作者采纳 AI-assisted 输出后仍需重写的负担。
- `agent_session_completion_rate`：AI 写作 agent session 在不越权的情况下到达有用暂存输出的比例。

指标必须配合证据和 reviewer notes。只有数字、没有轨迹，证据很弱。

## 流程

### Phase 0：无模型 Harness 验证

目的：在没有 API 波动的情况下证明评估机器能跑。这一阶段是基础设施验证，不是主要产品主张。

运行：

```bash
fictionops eval-agent fictionops/examples/demo_novel --chapter 002 --out fictionops/docs/agent-evaluation-smoke.md
```

预期证据：

- 任务包生成；
- echo runner 输出进入暂存；
- inbox 看到 ready output；
- controller 安全停下；
- doctor/report 输出被记录。

### Phase 1：单模型 Runner 评估

目的：用同一个真实模型比较 raw chat、broad context 和 FictionOps runner。

步骤：

1. 选择一个 fixture 和一个目标任务。
2. 准备 raw-chat prompt 和 broad-context prompt。
3. 准备 FictionOps `agent-run` 任务包。
4. 在每个条件下运行同一模型。
5. 记录输出、复核决定、审计变化和恢复说明。

预期证据：

- 可比的任务 prompt；
- 保存的模型输出；
- 复核 notes；
- 审计/门禁结果；
- 指标表。

### Phase 2：Controller 评估

目的：测试外部 controller 是否能推进安全 AI-assisted 工作，同时不跨越权限边界。

步骤：

1. 在 fixture 上运行 `agent-next`。
2. 只允许 controller 执行 safe commands。
3. 遇到暂存输出、人工复核、缺失外部证据或危险写入时停下。
4. 保存 JSONL controller logs。
5. 评估 step validity 和 boundary behavior。

预期证据：

- JSONL logs；
- 被选择的命令和理由；
- 停止理由；
- inbox/gate 状态；
- 无未经授权的源文件编辑。

### Phase 3：真实 Dogfood 周期

目的：在真实长项目写作和维护中评估 AI Agent 参与。

步骤：

1. 使用私有或授权的长项目。
2. 记录 AI-assisted 规划、草稿、审计、修订和发布 session。
3. 记录模型/供应商、命令、暂存输出、作者修改、接受/拒绝决定和修复动作。
4. 在有边界改动前后运行相关审计。
5. 记录 prompt 准备时间节省、上下文查找时间节省、有效 AI 发现、复核分钟数和恢复成本。
6. 条件成熟后用 `audit-dogfood-cycle`、`audit-stability-window`、`audit-stable-core` 收口。

预期证据：

- 不泄露正文的公开总结；
- 模型/供应商和 runner/controller 版本；
- 接受/拒绝的 AI 输出；
- 有效/噪声 AI 发现；
- 时间节省估计和复核成本 notes；
- dogfood cycle record；
- stability-window record；
- accepted 或明确 deferred 的决定。

## 报告产物

每次评估运行都应产出：

- 日期、commit、model/provider、runner/controller 版本；
- fixture 描述和 task IDs；
- 实际命令；
- task bundle 路径；
- output 路径；
- inbox/gate 结果；
- 指标表；
- reviewer notes；
- 失败案例和恢复说明。

推荐输出路径：

```text
docs/evaluation-runs/<date>-<fixture>-<condition>.md
```

大型私有运行可以把详细证据留在私有位置，只提交脱敏总结。

## 有效证据标准

一次评估要算有效证据，至少要满足：

- fixture 和任务明确；
- 模型或 runner 明确；
- prompt 或任务包可保存/可复现；
- 源文件变更要么没有发生，要么被明确复核；
- 暂存输出可检查；
- 指标能对应文件路径或命令输出；
- reviewer notes 解释模糊情况；
- 失败被记录，而不是被藏起来。

对于 1.0 stable claim，单次评估不够。持续 dogfood cycle 和 stability-window 证据也必须 accepted。

## 有效性威胁

- 文学质量主观，不能压成自动分数。
- 私有 dogfood 限制外部复现。
- 小型公开 fixture 可能低估长周期难度。
- 不同 reviewer 严格程度不同。
- 不同模型对同一任务信封反应不同。
- harness 本身会塑造行为，让某些动作更容易。

缓解方式：

- 报告轨迹，不只报告分数；
- 保留基线；
- 在公开 fixture 中预埋问题；
- 保存 reviewer notes；
- 把安全/可靠性指标和艺术判断分开。

## 近期最有价值的实现工作

1. 增加 `setup-ai`，或等价的 OpenAI-compatible API 供应商引导配置路径。
2. 增加 AI-first 写作命令，例如 `write-chapter`、`revise-chapter`、`audit-chapter` 和 `agent-session`。
3. 在 `docs/evaluation-runs/` 下增加报告模板，记录 AI 贡献，而不仅是 harness 健康状态。
4. 扩展 `eval-agent`，为 model-runner 和 controller-loop 输出紧凑 JSON metrics。
5. 用同一个真实模型跑 raw chat、broad-context、FictionOps runner 和 FictionOps controller 条件。
6. 在私有小说上记录一次真实 AI-assisted dogfood session，包括接受/拒绝输出和时间节省 notes。
7. AI-first 路径稳定后，再新增一个中型公开合成 fixture，预埋连续性和信息边界陷阱。

这些动作最好在当前公开文档和稳定性证据保持干净后推进，因为评估可信度依赖稳定命令。
