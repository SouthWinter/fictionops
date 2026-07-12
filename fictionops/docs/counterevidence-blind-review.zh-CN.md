# Counterevidence 匿名人工复核

Preservation verifier 不会把证据不足的问题直接交给 reviser，也不会把它伪装成已经解决。`needs_counterevidence` 队列需要独立复核，判断原 finding 应当进入修订、撤回，还是仍需更多上下文。

## 导出盲包

从 benchmark dogfood 证据导出：

```powershell
fictionops agent counterevidence export `
  docs/evidence/deepseek-preservation-verifier-v1.json `
  --benchmark docs/evidence/deepseek-benchmark-v2.json `
  --fixtures tests/fixtures/agent_benchmark_v2_cases.json `
  --out docs/evidence/deepseek-counterevidence-v1.blind.json `
  --key-out "$HOME/.fictionops/evidence/deepseek-counterevidence-v1.key.json"
```

也可以直接导出某次 `agent revise` 的运行目录：

```powershell
fictionops agent counterevidence export <run-dir> `
  --out counterevidence.blind.json `
  --key-out "$HOME/.fictionops/evidence/counterevidence.key.json"
```

盲包包含章节材料、权威上下文、作者约束、reviewer finding、verifier 的证据与理由，以及空白标注栏。它不包含 prompt id、case id、condition、正负标签或预期答案。私钥单独保存这些映射，不应交给标注者，也不应提交到公开仓库。

## 标注协议

每条样例填写：

- `decision`：`uphold` 表示 finding 可以进入 reviser；`withdraw` 表示应保留原文；`insufficient` 表示人也需要更多反证或上下文；
- `evidence_grounded`：finding 是否被当前材料直接支持；
- `repair_harm_risk`：执行该建议破坏人物、留白、声音或节奏的风险，取 `low`、`medium` 或 `high`；
- `effort_minutes`：人工阅读与判断耗时；
- `notes`：简短理由，可为空。

标注者应先完成整个盲包，再接触 key。不能由产生 finding 或 verifier 结论的同一次模型调用冒充人工标注。

## 评分

```powershell
fictionops agent counterevidence score counterevidence.annotated.json `
  --key "$HOME/.fictionops/evidence/counterevidence.key.json" `
  --out counterevidence-evaluation.json `
  --format json
```

评分器拒绝空标注、非法枚举、重复 sample id 和 packet/key 不匹配。报告包括人工裁决分布、解决率、证据落地率、修订伤害风险、总耗时/中位耗时，以及人工裁决与原 benchmark case control 的一致和冲突。

正例章节中 reviewer 额外生成的问题没有自动真值，因此标为 `unevaluable`。负例的“整例应保留”也只是 case-level control，不能自动变成每条动态 finding 的 issue-level 真值；人工 uphold 记为 `label challenge`，不冒充 false positive。这个边界避免把 fixture 的章节标签错误扩张到模型生成的每一条问题。

## 当前证据边界

[`deepseek-counterevidence-v1.blind.json`](evidence/deepseek-counterevidence-v1.blind.json) 是未填写盲包。第一轮作者盲评已经完成，聚合结果见 [`deepseek-counterevidence-v1.zh-CN.md`](evidence/deepseek-counterevidence-v1.zh-CN.md)；原始盲包仍保持空白，可继续交给第二名独立编辑者，避免受到第一轮答案影响。
