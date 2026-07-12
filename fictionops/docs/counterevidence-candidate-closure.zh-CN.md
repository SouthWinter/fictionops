# Counterevidence 候选验证与采纳闭环

最小 reviser bundle 解决“只让模型改已证实问题”，但模型输出本身仍不能直接落文。候选闭环增加两个独立动作：

```powershell
fictionops agent counterevidence verify-revision <bundle> --runner ...
fictionops agent counterevidence accept-revision <bundle> --dry-run
fictionops agent counterevidence accept-revision <bundle>
```

## 独立验证

verifier 只接收 issue contract、原文、候选与统一 diff，不重新做全章找错。每个 issue 必须返回候选中的逐字证据。最终通过同时要求：

- 每个 contracted issue 已解决且候选证据可逐字定位；
- 没有无关改动；
- active author guards 未被破坏；
- 没有新增正史；
- 标题不变，改动行数和字符比例处于窄修订上限；
- bundle、contract 与原章自准备后均未漂移。

模型的 `overall_pass` 不能覆盖任一确定性失败。

每次 verifier 调用的原始 stdout/stderr 都按编号保存在 `verification_attempts/`，即使 JSON 解析失败也不会丢掉失败证据；成功报告记录对应文件与 SHA-256。

若 contracted issue 已解决，但修法引入新的句界复沓，确定性门禁会覆盖模型的 `overall_pass`。此时 controller 选择 `repair_counterevidence_candidate`，由局部修复器返回唯一的 `old_quote -> new_quote`；它不会再生成整章。旧候选与 execution 会进入编号 attempt 目录，字节不变的重试被视为 no-progress。

## 显式采纳

采纳前再次核对 source/candidate/contract/manifest 哈希，并确认所有 issue 在项目 ledger 中仍是 grounded `open/uphold`。`--dry-run` 不写正文。正式命令原子替换原章，然后留下 `addressed -> verified -> accepted` 三段记录，其中最后一步明确标记为作者调用产生的权限动作。

## 真实 DeepSeek Dogfood

受控章节先写明人物左臂齐肩而断，末段却写“抬起左手”。真实 DeepSeek 补证后 uphold，最小 reviser 只把“左手”改成“右手”，其余文本逐字不动；独立 verifier 给出候选逐字证据并通过。dry-run 保持原哈希，正式采纳后 source SHA-256 与 candidate 完全一致，issue 最终为 `accepted`。

聚合证据见 [`deepseek-counterevidence-candidate-closure-v1.json`](evidence/deepseek-counterevidence-candidate-closure-v1.json)。该实验只作用于 `~/.fictionops/evidence` 下的受控章节，不涉及真实小说正文。
