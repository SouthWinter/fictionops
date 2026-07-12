# DeepSeek Counterevidence Blind Review v1

Preservation verifier dogfood 留下的 `needs_counterevidence` 已导出为独立盲审包：[`deepseek-counterevidence-v1.blind.json`](deepseek-counterevidence-v1.blind.json)。

- 样例数：16 条 issue-level finding；
- 来源：初次 preservation verifier 的正/负 control，以及作者 guard registry dogfood；
- 隐藏字段：prompt id、case id、condition、control class、预期标签与来源分组；
- 私钥位置：本机 `~/.fictionops/evidence/deepseek-counterevidence-v1.key.json`，不进入仓库；
- 当前状态：作者盲评已完成；尚未完成第二名独立编辑者标注。

该包的目的不是再调用一个模型替 verifier 投票，而是测量人工边界本身：哪些争议可安全撤回、哪些应回到 reviser、哪些确实缺上下文，以及每条判断需要多少人工时间。

## 作者盲评结果

作者在不读取私钥的情况下逐条判断 16 个 finding，完成后才由评分器合并 control 映射。公开聚合与逐行结果见 [`deepseek-counterevidence-v1.author-evaluation.json`](deepseek-counterevidence-v1.author-evaluation.json)；带完整作者备注的 annotated packet 仍保存在本机证据目录。

| 指标 | 结果 |
| --- | ---: |
| Uphold | 5 |
| Withdraw | 5 |
| Insufficient | 6 |
| 已裁决率 | 62.5% |
| 证据充分率 | 31.25% |
| 高误修风险 | 4 |
| 人工时间 | 32 分钟 |
| 单条中位时间 | 2 分钟 |
| 与原 case control 一致率 | 71.4% |
| Case-control 标签挑战 | 2 |

71.4% 是与原 case 标签的一致率，不是作者准确率。两条挑战都来自 B08：fixture 把“少女可以聪明”整体作为 preservation 负例，但作者稳定认为“三仓”仍需要具体信息来源。这个结果说明 case-level 的“整例应保留”不能自动扩张成模型动态生成的每一条 finding 都是假阳性。

## 工程结论

1. `needs_counterevidence` 不是一个单一状态。6 条 insufficient 多数缺全章或相邻段原文，controller 应先自动扩大上下文，再请求人工。
2. 聪明程度与信息来源必须分开审计。女孩可以自然推出“缺粮就运粮”，但精确的“三仓”仍需要来源。
3. 4 条高误修风险 finding 全部被撤回，说明 preservation gate 确实挡住了会损伤人物直率与留白的修改。
4. 盲包包含多组近似重复，适合测一致性，但生产工作流应先聚类去重，减少作者负担。
5. 章节功能、推进速度和跨段模板化不能只靠单段摘录裁决；reviewer 的 evidence contract 应要求与指控范围同尺度的文本窗口。

这是一轮作者盲评，测量的是 Agent 与作者意图的对齐。它不能替代独立编辑者评审；后续可让第二名标注者使用同一盲包，测量作者与外部读者之间的一致性。

协议和评分命令见 [`counterevidence-blind-review.zh-CN.md`](../counterevidence-blind-review.zh-CN.md)。
