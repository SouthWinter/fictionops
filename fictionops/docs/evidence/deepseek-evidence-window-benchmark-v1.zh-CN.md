# DeepSeek Evidence-window 成对实验

## 设计

固定 `deepseek-v4-flash`、temperature 0，对5个匿名 case 分别运行 `full_context` 与 `window`。两种条件共享 finding、裁决规则和输出 schema；expected verdict 与 control notes 不进入 prompt。五类 scope 为局部行文、相邻段节奏、知识来源、人物记忆和全章功能。

## 首轮失败

v1 共10次调用。full-context 与 window 的期望裁决准确率均为0.8，窗口 grounding 和必要证据召回均为1.0，但成对裁决一致率只有0.6。

- 局部行文：full-context 误把“只限制修订范围”的 guard 当作保留原句的理由，窗口条件正确 uphold。
- 知识来源：窗口条件的模型理由明确说缺失来源已由人物记忆补足，却把应当 withdraw 的原 finding 标为 uphold。

第二项不是检索失败，而是 verdict orientation 失败。系统因此补入通用规则：裁决对象始终是原 finding；补证关闭了原缺口就应 withdraw；限制 scope 的 guard 不自动证明原句正确。没有加入 case id、期望标签或答案措辞。

## v2 结果

相同 fixture 重跑10次：

| 指标 | Full context | Window |
| --- | ---: | ---: |
| 期望裁决准确率 | 1.0 | 1.0 |
| Grounded resolution | 1.0 | 1.0 |
| 必要证据召回 | 1.0 | 1.0 |
| 输入 token | 8789 | 7257 |
| Total token | 12049 | 10742 |
| 模型可见证据字符 | 2436 | 1476 |

成对裁决一致率为1.0；输入 token 下降17.43%，total token 下降10.85%，证据字符下降39.41%。各类输入降幅为9.76%至26.23%。短 fixture 中固定裁决契约占比较高，因此总体 token 降幅明显小于真实万字章节的单例结果。

## 限制

这不是统计显著性结论：只有一个模型、每个 case-condition 一次调用、5个受控样本；v2 还受到开发者已观察 v1 失败的影响。下一阶段需要冻结契约，在 held-out case 上重复多次并报告置信区间。原始完整输出保存在本机 `~/.fictionops/evidence`，公开 JSON 只保留聚合、失败轨迹和限制。
