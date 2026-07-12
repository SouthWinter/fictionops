# Counterevidence 补证窗口

`agent counterevidence reverify` 不再默认把 packet 正文、项目上下文、author guards 和 escalation evidence 原样拼接。每个去重 finding 会先被编译为一个可审计的模型可见证据窗口。

## 三种策略

- `bounded_claim_windows`：finding 有精确引文、active author guard 或 preserve constraint，并明确只处理指定位置。窗口包含命中段、相邻段、相关权威上下文和 active guards。
- `scoped_evidence_windows`：人物、知识来源、相邻段或作者意图问题。窗口保留 escalation 已按 scope 检索到的材料，并增加引文邻域。
- `full_scope_deduplicated`：真正依赖全章节奏、结构、回声或功能的判断。完整章节仍会进入模型，但 packet 与 escalation 中的重复副本只保留一份。

## 验证边界

模型返回的 `uphold/withdraw` 必须至少有一条逐字引文落在该次 prompt 可见窗口。后处理阶段即使仍能访问 packet，也不会用模型未见过的材料替它补证。窗口 manifest 记录来源、权威级别、哈希、截断、压缩前后字符和选择策略。

`--max-evidence-chars` 默认16000。该预算限制模型可见证据，不改变 `--max-model-calls` 的调用次数硬上限，也不授予模型采纳正文的权限。真正的全章依赖若无法在预算内完整放入，会在任何 API 调用前停止并要求提高预算，不会截断后冒充完整章级判断。

## 成对评测

```powershell
fictionops agent counterevidence benchmark-windows tests/fixtures/evidence_window_benchmark_cases.json --format json --runner ...
```

命令让同一模型分别读取 `full_context` 和 `window`，两边共享 finding、裁决规则和输出 schema。期望裁决与 control notes 不进入 prompt。报告按 case 和 scope 配对，统计裁决一致率、期望裁决准确率、grounded resolution、必要证据召回、输入 token 和证据字符。

五类 DeepSeek 单次实验的首轮暴露了 verdict 方向错误：模型理由明确说知识来源已补足，却输出 `uphold`。通用契约随后明确“裁决对象是原 finding；补证关闭缺口应 `withdraw`”，而不是针对 case 写答案。相同 fixture 的 v2 得到5/5成对一致、5/5窗口期望裁决正确、5/5 grounded，输入 token 下降17.43%，证据字符下降39.41%。这仍是单模型、每例一次的小样本工程证据，不是统计显著性结论。

公开报告见 [`evidence/deepseek-evidence-window-benchmark-v1.zh-CN.md`](evidence/deepseek-evidence-window-benchmark-v1.zh-CN.md)。
