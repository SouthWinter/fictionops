# FictionOps Agent Runtime 完成度审计

审计日期：2026-07-11

本文件按 `docs/agent-system-design.zh-CN.md` 的 P0-P5 退出条件核对当前实现。测试通过只能证明被覆盖的契约，不能自动证明文学质量、真实采纳价值或整个 Agent 已完成。

## 结论

当前 Agent 已能独立完成单章写作或旧章修订的规划、模型调用、验证、有限重试、暂存和安全停止，也有真实 DeepSeek 失败/拒绝证据。统一产品入口、调用预算和 session-aware `continue` 已落地。

单章 Agent 1.0 的工程目标已完成；面向科研实习展示的统一轨迹、显式 policy、对照/消融 harness、failure lab 和案例讲稿也已落地。0.8 的真实效果证据仍未完全闭合，不能把工程完成改写成文学质量或跨项目泛化已经证明。

## 逐项证据

| 设计项 | 状态 | 当前权威证据 | 尚缺 |
| --- | --- | --- | --- |
| P0 闭环章节修订 | 已证明 | `agent-revise-workflow`、`agent-accept-revision`、session/events、before/after issue/audit、diff、语义不变量、定向重试、真实 DeepSeek 旧章 dogfood | 继续积累采纳率，不再作为实现阻塞 |
| P1 结构化语义审读 | 已证明 | 六维综合 reviewer、三 profile 对抗审读、候选原文 grounding、`.fictionops/issues.json` 稳定 ID、跨 session 合并/自动 reopen、显式 waive/reject、候选 verified/accepted 回写，以及信息边界/人物声音/行文三类匿名回归 fixture | 后续继续扩充真实案例，不再作为实现阻塞 |
| P2 上下文编译器 v2 | 已证明当前范围 | 类型化 memory、显式 preference、实体/相邻章检索、权威级别、路径/哈希/理由/截断、source manifest，以及写入 `trajectory.jsonl` 的实际 context attribution | 更强设定冲突检测与 embedding 是否必要，继续由遗漏实验决定 |
| P3 写章与写后闭环 | 已证明 | 因果模拟、planner、故事事实账本、逐场景写作、选择性复修、独立 reviewer/evaluator、复盘草稿、正史建议、缺失目标安全采纳、真实 DeepSeek 盲写 dogfood | 正史建议仍需 controller 消费，但写章退出条件已满足 |
| P4 项目级 controller | 已满足单章 1.0 范围 | `fictionops agent write|revise|accept|continue|resume|cancel|status`、纯函数 controller policy、session/checkpoint、写章安全阶段与修订 `verification_ready` 恢复、runner telemetry、跨分段 token/费用门禁、统一 trajectory、项目级作者工作台、R0-R4 权限边界 | 逐重试任意指令点恢复与批次/书级自动执行列为 1.x 扩展，不扩大 1.0 自动修改半径 |
| P5 Skill、开放 API、研究证据 | 工程面已证明，效果证据继续积累 | 官方 validator 通过的 Codex skill、`fictionops.api` v1、OpenAPI/JSON Schema v1、HTTP adapter、三类高风险 fixture、可重复 raw/RAG/full/ablation harness、7 场景 failure lab、真实 DeepSeek dogfood、面试案例和讲稿 | 尚缺固定模型多次真实基线结果、置信区间、作者时间、采纳率和 edit distance；这些限制研究结论，不阻塞 runtime 工程完成 |

## 当前安全不变量

- 模型输出只进入 run 目录；
- 写章/修订调用受本地调用数和总时限预算约束；
- reviewer 阻断证据必须落在候选原文，或绑定失败 `scene_id`；
- 逐场景重试优先只修改被证据命中的场景；
- 预算耗尽在下一次 runner 调用前停止；
- 正文采纳必须显式执行，且源稿/候选 SHA-256 均匹配；
- 正史建议、失败候选、预算扩大和待采纳候选不会被 `agent continue --execute` 自动处理；
- API key 不进入任务包、报告、session 或公开文档。

## 下一轮固定顺序

1. 用固定模型与采样参数真实运行 raw/RAG/workflow 基线，多次采样并做人工盲评。
2. 完成 AI-assisted 发布准备 dogfood 和作者复核时间/采纳编辑距离记录，再审计 0.8。
3. 在真实使用证明必要后，再增加逐重试任意指令点恢复或批次/书级调度。

## 完成判定

按单章写作 Agent 1.0 工程范围，P0-P5 必需 runtime 已有代码、测试、文档，核心闭环也有真实 DeepSeek 成功拒绝弱候选的 dogfood 证据；工程开发可以进入完成验收。尚未完成的是研究效果证据与 1.x 扩展，不能据此宣称文学质量提升、全书无人值守自动执行或跨供应商效果一致。
