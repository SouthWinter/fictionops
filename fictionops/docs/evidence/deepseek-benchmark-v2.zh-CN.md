# DeepSeek Benchmark v2

日期：2026-07-11

## 目标

第一轮 pilot 的三个显性正例让所有条件都达到 100% 检出率，无法判断项目记忆和 preservation guard 是否有用。Benchmark v2 加入：

- 4 个 memory-only 正例：身体状态、能力发现边界、关系阶段、身份揭晓时点；
- 2 个局部正例：解释性旁白、同构修辞重复；
- 4 个 preservation 负例：仪式重复、少女的具体聪明、视角化神话版本、地域口语。

## 实验设置

- 条件：`raw`、`rag`、`full`
- 样例：10 个，每个条件运行 1 次，共 30 次真实 API 调用
- 请求配置：provider `deepseek`，model alias `deepseek-chat`，temperature `0.2`
- 回执实际模型：`deepseek-v4-flash`
- 总耗时：113.6 秒
- 总用量：8,811 input tokens，7,350 output tokens，合计 16,161 tokens
- 成本：未配置显式单价，不使用可能过期的内置价格

逐次输出见 [`deepseek-benchmark-v2.json`](deepseek-benchmark-v2.json)，匿名人工评审包见 [`deepseek-benchmark-v2.blind.json`](deepseek-benchmark-v2.blind.json)。condition key 只保存在本机 `~/.fictionops/evidence/deepseek-benchmark-v2.blind-key.json`。

## 自动结果

| Condition | TP | FN | FP | TN | Precision | Recall | Accuracy | FPR | Grounded | Extra issues | Tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw` | 1 | 5 | 4 | 0 | 20.0% | 16.7% | 10.0% | 100.0% | 16.7% | 14 | 4,640 |
| `rag` | 6 | 0 | 4 | 0 | 60.0% | 100.0% | 60.0% | 100.0% | 83.3% | 4 | 4,652 |
| `full` | 6 | 0 | 3 | 1 | 66.7% | 100.0% | 70.0% | 75.0% | 100.0% | 13 | 6,869 |

## 解释

1. 项目记忆决定召回。raw 只命中剑能力的信息异常，其余 memory-only 正例均漏掉；RAG 命中全部 6 个正例。
2. workflow contract 改善引证。full 的 grounded evidence 为 100%，高于 RAG 的 83.3%。
3. preservation guard 有效但不充分。full 正确保留仪式性重复，却仍误伤少女聪明、神话多版本和寒泽口语，FPR 仍为 75%。
4. full 有过度审阅倾向。它在正例上输出大量跨维度附加问题，extra issues 为 13，明显高于 RAG 的 4。
5. 有些“误报”明确写着 `No change needed`，但仍被放进 `issues` 数组。评测继续将其计为 FP，因为输出契约要求无问题时返回空数组。

## 污染实验

第一次 v2 运行把描述性内部 case id（例如 `memory_continuity_missing_hand`）放进提示词，raw 可以从名字猜测目标，构成 label leakage。该批 30 次调用已判定无效，移至本机 `~/.fictionops/evidence/deepseek-benchmark-v2.invalid-leaky-id.*`，未进入公开证据。

正式运行改用 `B01` 至 `B10` 不透明 prompt id。报告保留内部 case id 供机器评分；公开 blind packet 不包含 condition、内部 case id 或预期标签。

## 评测器处理

模型会使用 `叙事一致性`、`canon_consistency`、`stylistic_repetition` 等语义等价标签。accepted taxonomy 在模型调用后、重评分前由人工按问题含义登记，且从不进入提示词。原始模型输出通过 replay runner 重评分，没有追加 API 调用。

没有把下列偏题发现登记为正确命中：

- 将弟子礼问题解释为“公开场合不够正式”；
- 将半张纸问题解释为父亲行为逻辑矛盾；
- 将重复问题解释为转场不清或明喻难懂。

## 下一步结论

Preservation-aware verifier 已实现并完成真实 dogfood，结果见 [`deepseek-preservation-verifier-v1.zh-CN.md`](deepseek-preservation-verifier-v1.zh-CN.md)。它将自动修订集合的 FPR 从 75% 降到 0%，但 actionable recall 从 100% 降到 83.3%；被挡下的真实问题进入 counterevidence 人工队列后，总保留 recall 仍为 100%。下一步应为作者保留约束建立稳定 guard id，并盲评 counterevidence 队列。
