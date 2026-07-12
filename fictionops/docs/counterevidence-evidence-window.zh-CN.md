# Counterevidence 补证窗口

`agent counterevidence reverify` 不再默认把 packet 正文、项目上下文、author guards 和 escalation evidence 原样拼接。每个去重 finding 会先被编译为一个可审计的模型可见证据窗口。

## 三种策略

- `bounded_claim_windows`：finding 有精确引文、active author guard 或 preserve constraint，并明确只处理指定位置。窗口包含命中段、相邻段、相关权威上下文和 active guards。
- `scoped_evidence_windows`：人物、知识来源、相邻段或作者意图问题。窗口保留 escalation 已按 scope 检索到的材料，并增加引文邻域。
- `full_scope_deduplicated`：真正依赖全章节奏、结构、回声或功能的判断。完整章节仍会进入模型，但 packet 与 escalation 中的重复副本只保留一份。

## 验证边界

模型返回的 `uphold/withdraw` 必须至少有一条逐字引文落在该次 prompt 可见窗口。后处理阶段即使仍能访问 packet，也不会用模型未见过的材料替它补证。窗口 manifest 记录来源、权威级别、哈希、截断、压缩前后字符和选择策略。

`--max-evidence-chars` 默认16000。该预算限制模型可见证据，不改变 `--max-model-calls` 的调用次数硬上限，也不授予模型采纳正文的权限。真正的全章依赖若无法在预算内完整放入，会在任何 API 调用前停止并要求提高预算，不会截断后冒充完整章级判断。
