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

## 当前占位记录

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
- Decision: deferred
- Reviewer:

## 验收结论

- `accepted`：持续周期已完成，导入队列和阻塞项清零，兼容性/恢复说明已更新，且通过 `audit-dogfood-cycle`。
- `deferred`：仓库已有迁移证据，但持续维护周期还没有完成。
- `failed`：周期暴露真实回归或契约漂移，需要修复、补测试并重新记录。
