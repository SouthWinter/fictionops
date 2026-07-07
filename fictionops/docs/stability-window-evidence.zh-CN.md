# 稳定窗口证据

这份文件记录 FictionOps 宣称 1.0 stable core 前需要的兼容性/稳定窗口证据。它不能替代测试、发布证据或 dogfood 证据；它记录的是这些稳定表面在一段真实维护窗口内没有静默漂移。

## 填写说明

- 在真实兼容性窗口结束后填写，不要在窗口开始前预填。
- 起止日期使用 `YYYY-MM-DD`，结束日期不能早于开始日期，且窗口至少覆盖 7 个自然日。
- 发布证据和 dogfood 证据引用必须指向具体证据文件、运行 URL 或已记录 artifact；含糊备注不能关闭稳定窗口。本地 Markdown 证据文件引用会检查文件是否存在，并且必须分别通过 `audit-release-evidence` 或 `audit-dogfood-cycle`。
- 本地 Markdown 证据文件引用必须留在被审计的目标 checkout 内；不要用另一个本地沙盒或临时目录里的 accepted 文件关闭稳定窗口。
- URL 引用必须是带有 host 的完整 `https://...` URL，并应指向具体 run、artifact、release、dogfood 或 evidence 记录；裸 `http`、非 HTTPS URL 和泛泛首页链接不能作为外部证据引用。
- 作为 1.0 证据前，先运行 `fictionops audit-stability-window . --file docs/stability-window-evidence.md`，再运行 `fictionops audit-stable-core . --stability-file docs/stability-window-evidence.md`。
- 只有兼容性说明、破坏性变更说明和恢复说明都由具名复核人复核后，才使用 `Decision: accepted`。

## 记录

- Window ID:
- Start date:
- End date:
- Version range:
- Release evidence reference:
- Dogfood cycle reference:
- Compatibility notes:
- Breaking changes:
- Recovery notes:
- Decision: deferred
- Reviewer:

## 结论含义

- `accepted`：稳定表面保持兼容，或每个破坏性变更都有明确迁移路径。
- `deferred`：窗口尚未完成或尚未复核。
- `failed`：发现兼容性或恢复路径回归，修复前不能进入 1.0。
