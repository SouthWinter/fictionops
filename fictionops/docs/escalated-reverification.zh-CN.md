# Escalated Re-verifier

Evidence escalation 取得匹配尺度的材料后，`agent counterevidence reverify` 会让独立模型重新判断原 finding，而不是沿用第一次 verifier 的结论。

```powershell
fictionops agent counterevidence reverify evidence-escalation.json `
  --packet counterevidence.annotated.json `
  --out escalated-reverification.json `
  --format json `
  --runner python examples/agent_runner_openai_chat.py ...
```

## 判定契约

每个去重后的 evidence request 独立返回：

- `uphold`：新增证据支持原 finding，应进入 reviser；
- `withdraw`：新增证据或 author guard 反证原 finding，应保留原文；
- `still_insufficient`：补证仍缺失、间接或尺度不足，继续停在人工边界。

模型必须给出新增材料中的精确引文和 `remaining_gap`。Controller 会确定性检查引文是否逐字存在于章节、权威上下文、author guard 或 retrieved evidence 中。模型若给出 resolved verdict 却没有任何落地引文，effective verdict 自动降为 `still_insufficient`，原 `model_verdict` 与未落地引文仍保留在审计记录中。

## 执行边界

- 只执行状态为 `ready_for_reverification` 的请求；
- 请求数超过 `--max-model-calls` 时在调用前整体拒绝；
- 每个请求最多允许一次有界 schema repair，且仍受总调用预算约束；
- 解析 runner receipt，累计 input/output/total/cached tokens；
- 不修改正文，不把模型结论升级为作者决定。

## DeepSeek Controlled Dogfood

受控 fixture 先只提供一个静止、无事件的氛围段，reviewer 因而怀疑它是填充；初次 verifier 判断缺少全章，状态为 `insufficient`。Escalation controller 取回完整章节后，可见该段紧邻钟声、门下红水和死亡名单揭示之前，承担蓄压与反差功能。

真实 DeepSeek re-verifier 结果：

- 1 个 ready request，1 次模型调用；
- verdict：`withdraw`；
- resolution rate：100%；
- 1104 input、179 output、1283 total tokens，其中 1024 cached input；
- 精确引文 grounding 通过；
- 无 schema repair；
- 未修改任何正文。

逐次结果见 [`deepseek-escalated-reverification-v1.json`](evidence/deepseek-escalated-reverification-v1.json)，可复现 fixture 见 [`escalated_reverification_control_packet.json`](../tests/fixtures/escalated_reverification_control_packet.json) 与 [`escalated_reverification_control_chapter.md`](../tests/fixtures/escalated_reverification_control_chapter.md)。

这是 controlled evidence，证明补证、重判与 grounding 链路可运行。Grounded verdict 到持久 issue ledger 的状态闭环见 [`counterevidence-ledger-application.zh-CN.md`](counterevidence-ledger-application.zh-CN.md)。它不代表《江山》作者盲评留下的 6 条 `insufficient` 已被解决；匿名 benchmark 没有对应原章，仍应停在 `needs_source`。
