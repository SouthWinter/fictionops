# DeepSeek Counterevidence Blind Review v1

Preservation verifier dogfood 留下的 `needs_counterevidence` 已导出为独立盲审包：[`deepseek-counterevidence-v1.blind.json`](deepseek-counterevidence-v1.blind.json)。

- 样例数：16 条 issue-level finding；
- 来源：初次 preservation verifier 的正/负 control，以及作者 guard registry dogfood；
- 隐藏字段：prompt id、case id、condition、control class、预期标签与来源分组；
- 私钥位置：本机 `~/.fictionops/evidence/deepseek-counterevidence-v1.key.json`，不进入仓库；
- 当前状态：等待独立人工标注，不能报告为已完成人评。

该包的目的不是再调用一个模型替 verifier 投票，而是测量人工边界本身：哪些争议可安全撤回、哪些应回到 reviser、哪些确实缺上下文，以及每条判断需要多少人工时间。

协议和评分命令见 [`counterevidence-blind-review.zh-CN.md`](../counterevidence-blind-review.zh-CN.md)。
