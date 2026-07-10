# Dogfood Cycle Evidence（持续 dogfood 周期证据）

这份文档记录 1.0 stable core 前必须补上的“持续真实项目 dogfood 周期”。它不是 0.2 迁移收口记录本身，而是迁移收口之后，真实项目继续使用 FictionOps 维护一轮后留下的证据。

## 证据规则

- 周期必须发生在 0.2 迁移收口之后。
- 需要记录项目/沙盒、起止日期、版本或 commit 范围、覆盖命令、前后 adopt-review 状态、兼容性说明、恢复说明和最终结论。
- 必须写清楚实际处理的是哪本书/哪个项目切片、哪些章节、哪些重点任务、AI/agent runner 路径以及人工复核边界。只写“维护”或“smoke”不够。
- 起止日期使用 `YYYY-MM-DD`，结束日期不能早于开始日期，且周期至少覆盖 7 个自然日。
- 至少覆盖三条命令路径；只跑一两个命令的 smoke 不能作为 1.0 accepted dogfood 证据。
- 命令覆盖必须写出至少三条可识别的 FictionOps CLI 命令，例如 `adopt-review`、`adopt-plan`、`import-plan`、`doctor`、`report` 或 `context-pack`；含糊标签不能作为覆盖证明。
- accepted 的持续证据必须包含 day-by-day ledger，至少要有开始 checkpoint 和关闭 checkpoint。七天窗口证明的是跨日恢复和接续，不是把一天能做完的任务硬拖成七天。
- 只有 `import_queue_files` 与 `blocking_issue_count` 都为 `0`，最终状态 ready/complete，且兼容性敏感变化有说明时，才可以写 `accepted`。
- 缺少具名复核人时，不能把周期写成 `accepted`。
- 真实关闭日期到来时，按 [Dogfood 周期关闭 Runbook](dogfood-cycle-close-runbook.zh-CN.md) 复跑 checkpoint 并关闭证据。
- 关闭 1.0 前运行 `fictionops audit-dogfood-cycle . --file <filled-cycle.md>`。

## 证据模板

```markdown
## Dogfood Cycle Evidence

- Cycle ID:
- Project / sandbox:
- Start date:
- End date:
- Version / commit range:
- Scope:
- Book / chapter scope:
- Focused tasks:
- Commands exercised:
- AI workflow evidence:
- Human review boundary:
- Day-by-day ledger:
- Initial adopt-review status:
- Final adopt-review status:
- import_queue_files:
- blocking_issue_count:
- Waiver count:
- Compatibility notes:
- Recovery notes:
- Decision: accepted / deferred / failed
- Reviewer:

### Summary

- What stayed stable:
- What changed:
- Regression tests added:
- Docs updated:
- Follow-up:
```

## 当前活跃周期

- Cycle ID: dogfood-2026-07-private-maintenance
- Project / sandbox: 私有长篇小说维护沙盒；公开仓库不暴露本地路径和正文内容
- Start date: 2026-07-07
- End date: 2026-07-14
- Version / commit range: 3e0703f..cycle-close
- Scope: 0.2 迁移收口后的持续维护周期，覆盖项目健康检查、上下文包、审稿门禁和 agent/runner 证据
- Book / chapter scope: Book 01（`book_01`），结构层覆盖 `ch_001` 到 `ch_033`；重点复盘/修订 `ch_007`、`ch_010`、`ch_012`、`ch_013`、`ch_014`、`ch_026`、`ch_027`、`ch_028`；`eval-agent` 使用 `ch_002`，真实 DeepSeek runner 覆盖 `ch_002` 小审读和高风险承重章节 `ch_010` 综合审读
- Focused tasks: 修复 active 项目记忆表、同步第一本书纲/正文/chapter engine、分离 active 伏笔表与导入旧材料、整理 reader-experience 信号、对重点章节做有边界的维护修订、运行第一本发布链路 smoke、验证真实 API runner 暂存边界
- Commands exercised: adopt-review, doctor, context-pack, report, audit-info, audit-characters, revision-plan, eval-agent, audit-chapter, agent-inbox
- AI workflow evidence: `eval-agent` 在 `ch_002` 上运行并停在人类复核边界；2026-07-10 私有沙盒新增真实 DeepSeek OpenAI-compatible runner checkpoints，使用 `audit-chapter --role info-boundary-auditor` 审读 `book_01/ch_002`：第一次验证 API runner 边界，第二次完成一条有边界的信息释放小审读。随后同一真实 runner 对高风险承重章节 `book_01/ch_010` 运行五角色综合审读：`architect`、`character-auditor`、`info-boundary-auditor`、`style-auditor`、`foreshadowing-auditor`。所有输出都只进入 agent run 暂存目录，`agent-inbox` 返回 `ready_for_review`，没有覆盖正文或正史，并在私有证据目录生成综合审读记录
- Human review boundary: style/wave/word 信号先转成 reader-experience memo 和 targeted review，再决定是否修订；真实 runner 输出保持 staged，需要人工判断后才可采纳
- Day-by-day ledger: 2026-07-07 day-one checkpoint：基线审计、项目记忆修复、第一本大纲同步、伏笔/连续性清理、阅读体验分诊、重点 prose pass、发布链路 smoke；2026-07-10 AI runner checkpoints：真实 DeepSeek `audit-chapter` 审读 `book_01/ch_002`，包括一条完整的信息释放小审读，随后对高风险承重章节 `book_01/ch_010` 做五角色综合审读；输出进入 staged inbox，不覆盖源文件；2026-07-14 close checkpoint：待复跑同一命令族并由人类复核后再决定是否 accepted
- Initial adopt-review status: baseline_pending_on_private_sandbox
- Final adopt-review status: deferred_until_cycle_close
- import_queue_files: 0
- blocking_issue_count: 0
- Waiver count: 0
- Compatibility notes: 周期仍在进行中；真实关闭日期到来并复核前，不声明兼容性已最终通过。
- Recovery notes: 已验证诊断不覆盖源文件、agent 输出停在暂存目录、DeepSeek runner 不由 FictionOps 保存 API key；关闭日仍需复跑。
- Decision: deferred
- Reviewer: maintainer pending final review

## 验收结论

- `accepted`：持续周期已完成，导入队列和阻塞项清零，兼容性/恢复说明已更新，且通过 `audit-dogfood-cycle`。
- `deferred`：仓库已有迁移证据，但持续维护周期还没有完成。
- `failed`：周期暴露真实回归或契约漂移，需要修复、补测试并重新记录。
