# DeepSeek Preservation Verifier v1

日期：2026-07-11

## 实验来源

复用 [`deepseek-benchmark-v2.json`](deepseek-benchmark-v2.json) 中 `full` 条件的 10 个 reviewer 输出，不重新调用 reviewer。Preservation verifier 对有 issues 的 9 个样例各运行一次；B06 首次输出 JSON 畸形，再运行一次有界 schema repair，共 10 次真实 API 调用。

- 请求模型：`deepseek-chat`
- 回执实际模型：`deepseek-v4-flash`
- 用量：11,845 input tokens，5,256 output tokens，共 17,101 tokens
- 完整逐条决定：[`deepseek-preservation-verifier-v1.json`](deepseek-preservation-verifier-v1.json)

## 权限规则

Verifier 不能凭模型意见直接删除问题：

1. issue 自己写着 `No change needed`、`无需修改`、`建议保留` 时，确定性规则可直接 withdraw；
2. 模型只有引用明确编号的作者 preservation guard，才可 withdraw；
3. 没有授权 guard id 的模型撤回一律降为 `needs_counterevidence`；
4. `needs_counterevidence` 不进入自动 reviser，但保留在人工队列和原始审计记录中。

## 结果

| Metric | Verifier 前 | 自动修订集合 | 含人工 counterevidence 队列 |
| --- | ---: | ---: | ---: |
| Precision | 66.7% | 100.0% | 待人工标注 |
| Recall | 100.0% | 83.3% | 100.0% |
| Negative-control FPR | 75.0% | 0.0% | 75.0% 进入复核而非自动修改 |
| 正例目标保留 | 6/6 | 5/6 | 6/6 |

负例原有 5 条误报：

- B09、B10 的 issue 自己写明 `No change needed`，由确定性规则撤回；
- B08 的 3 条年龄/信息/语气指控与“少女可以具体地聪明”冲突，但没有编号 author guard，因此不直接撤回，转入 counterevidence 队列；
- 自动 reviser 最终收到 0 条负例问题。

正例中，B01–B05 的目标问题仍可自动处理。B06 的真实同构修辞问题被模型试图撤回；由于没有授权 guard id，系统拒绝直接撤回，将 6 条 finding 转入 counterevidence 队列。因此 actionable recall 为 83.3%，但问题没有被遗忘或伪装成已解决。

## 新发现

B06 verifier 首次返回畸形 JSON。系统新增一次有界 repair：保留原始输出，只修复 JSON/schema，并计入模型预算。repair 成功恢复全部 6 个逐条决定；若 repair 仍失败，系统退回确定性裁决，不让格式错误自动清空 reviewer findings。

## Author Guard ID 复测

在项目级稳定 guard registry 完成后，又对 B08 与 B06 运行 2 次 DeepSeek verifier，共 4,743 tokens：

- B08 注册 `G-B08-CHILD-INTELLIGENCE`。模型认为“少女可以聪明”不足以直接裁定库存信息来源和父女语气，因此没有引用该 ID，三条争议全部保持 `needs_counterevidence`，没有越权撤回。
- B06 注册 `G-B06-RHYTHMIC-ANCHOR`。模型 uphold 两条核心修辞/节奏问题，三条证据不足的问题进入 counterevidence，只对一条会导致机械同义词替换的建议引用 guard 并 withdraw；目标问题仍在自动修订集合。

这说明 guard id 不是“给模型一个撤回理由”，而是限制它只能在 statement 覆盖范围内使用作者权限。

## 结论

v1 证明 verifier 可以显著降低自动误修，但不能被描述成“提升了整体审读准确率”。它把一部分模型不确定性从自动 action 转成了人工 review boundary。稳定 author guard id 已完成；下一步应对 counterevidence 队列做人类盲评，判断哪些可安全自动 withdraw。
