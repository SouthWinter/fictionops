# DeepSeek Agent Baseline Pilot

日期：2026-07-11

## 实验设置

- 实现基线：`112fd95`，标签 `agent-research-harness-v1`
- 条件：`raw`、`rag`、`full`
- 样例：3 个合成长篇高风险审阅样例
- 重复：每个条件、每个样例 2 次，共 18 次真实 API 调用
- 请求配置：provider `deepseek`，model alias `deepseek-chat`，temperature `0.2`
- 回执实际模型：`deepseek-v4-flash`
- 总耗时：52.6 秒
- 总用量：5,468 input tokens，3,626 output tokens，合计 9,094 tokens
- 价格：未配置显式单价，因此不报告成本，避免使用可能过期的内置价格

完整逐次输出见 [`deepseek-baseline-pilot.json`](deepseek-baseline-pilot.json)。

## 结果

| Condition | Samples | Detection | Grounded evidence | Extra issues | Input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw` | 6 | 100.0% | 83.3% | 0 | 1,508 | 1,205 |
| `rag` | 6 | 100.0% | 66.7% | 0 | 1,732 | 1,011 |
| `full` | 6 | 100.0% | 100.0% | 1 | 2,228 | 1,410 |

这里的 grounded evidence 要求至少一条命中目标类别的发现，能够逐字指向本次提供的章节摘录或检索上下文。`full` 的 workflow contract 明确要求分类与引证，在这批样例上改善了引证可核验性，但也增加了 token 和额外发现。

## 不能声称什么

- 三个条件的检出率都饱和，不能据此声称 FictionOps 提高了缺陷召回率。
- 只有 3 个样例、每项 2 次重复，不能作统计显著性结论。
- 样例是短小的合成片段，不代表章节级长上下文性能。
- `extra_issue_count` 只表示超出目标标签的发现，不等同于人工确认的误报。
- 没有盲评修订质量，也没有测量最终接受率或人工修改成本。

## 评测器事故

初次自动评分采用类别字符串完全匹配，把模型返回的 `information_boundary`、`narrative intrusion`、`prose_repetition_and_breath` 等语义正确标签判成漏检，原始检出率被错误计为 `raw=0%`、`rag=0%`、`full=33.3%`。

修复包括：

1. 在夹具中维护不暴露给提示词的 accepted category taxonomy。
2. 统一类别标点、空格与单复数表示。
3. 正确处理字符串或数组形式的 `evidence`。
4. 从带解释的证据中抽取直接引文，并按条件限定可用来源。
5. 增加 replay runner，用同一批模型输出重评分，不重复调用 API。

原始错误评分保存在本机 `~/.fictionops/evidence/deepseek-baseline-pilot.raw-evaluator.json`，不进入公开仓库；公开 JSON 保留全部 18 份原始模型审阅、回执、提示词哈希和修正后评分。

## 下一轮

下一轮应优先提高评测区分度，而不是继续增加相同调用：加入无问题负例、需要项目记忆才能识别的章节级样例、会被错误规则误伤的功能性重复，以及匿名化人工盲评。核心指标改为 precision/recall、证据可核验率、修订接受率和单位 accepted fix 的 token 成本。
