# 最小 Counterevidence Reviser Bundle

`fictionops agent counterevidence prepare-revision RUN_DIR` 把已经完成补证、复核并写入 ledger 的 grounded uphold 转成一个窄范围修订任务。它解决的是“证据已经确认后如何进入修订”，不是再做一次全章审读。

## 输入门禁

生成器必须同时确认：

- `counterevidence_application.json` 已应用，且没有修改正文；
- reviser queue 与 application 的 upheld issue ID 完全一致；
- 原章节 SHA-256 与 application 记录一致；
- 每个 queue issue 在当前 ledger 中仍是 `open`；
- 每个 issue 的 effective verdict 仍是 `uphold`，并含 grounded evidence。

任一条件失效即拒绝生成。空 queue 也不会产生一个看似可运行、实际没有合法任务的 bundle。

## 最小上下文

bundle 只携带：

- 完整未改章节；
- queue 中每个 issue 的问题、grounded evidence、建议动作和局部 preserve constraints；
- 当前 active author guards；
- application、queue 与 source 的哈希链。

`model_withdrawn`、`evidence_blocked`、作者 waive/reject、既有 resolved issue 和原始全章 reviewer 输出不会进入修订提示。这样 reviser 不会因重新审读而扩张任务面。

## 执行边界

生成物采用标准 `fictionops.agent_run_request.v1` / `prepare_only` 契约，可直接交给：

```powershell
fictionops agent-exec <bundle-dir> --runner ...
fictionops agent-inbox <bundle-dir>
```

模型输出仍只是 staging candidate。bundle 准备阶段不调用模型、不改正文，也不绕过后续 verification 和作者采纳边界。

候选生成后继续运行独立验证与显式采纳：

```powershell
fictionops agent counterevidence verify-revision <bundle-dir> --runner ...
fictionops agent counterevidence accept-revision <bundle-dir> --dry-run
fictionops agent counterevidence accept-revision <bundle-dir>
```

完整门禁见 [`counterevidence-candidate-closure.zh-CN.md`](counterevidence-candidate-closure.zh-CN.md)。
