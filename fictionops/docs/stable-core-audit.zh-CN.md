# 稳定核心审计

这份审计用来判断 FictionOps 是否可以称为 1.0 stable core。它比本地测试更严格：测试能证明当前行为，但 1.0 还需要外部发布证据和经过时间验证的兼容性。

当前结论：**未完成**。

可机器检查的聚合门禁：先运行 `fictionops audit-stability-window . --file docs/stability-window-evidence.md --format json`，再运行 `fictionops audit-stable-core . --format json`。聚合命令返回 `ready=true` 之前，本文档和里程碑账本都不能诚实地标记 1.0 完成。JSON 里还会给出结构化 `action_items`，供外部 runner 或维护者接手；这些条目只是交接计划，不是已经完成的证据。

执行交接清单见 `docs/stable-core-remaining-checklist.zh-CN.md`。那份清单会把本地维护和必须真实发生的外部发布、dogfood、稳定窗口证据分开，避免把本地加固误认为 1.0 完成进度。

## 证据矩阵

| 要求 | 当前证据 | 状态 | 剩余证明 |
| --- | --- | --- | --- |
| 命令名和核心 JSON key 稳定 | `docs/cli-contracts.md`、`docs/compatibility.md`、CLI help 覆盖、JSON 解析测试、controller 指南。 | 本地较强 | 需要一段兼容性窗口，证明行为变化没有静默破坏契约。 |
| 兼容性策略持续维护 | `docs/compatibility.md`、`docs/compatibility.zh-CN.md`、`CHANGELOG.md`、release notes、发布治理测试。 | 本地较强 | 后续行为变化仍必须同步更新这些记录。 |
| 危险覆盖被稳定拒绝 | 回归测试覆盖 CLI 输出、暂存 agent 输出、包产物、项目脚手架等 no-overwrite 行为。 | 本地较强 | 新增写命令时继续补 no-overwrite 测试。 |
| 发布门禁能发现缺失或过期产物 | `release-gate`、`audit-publish`、`export-metadata`、`export-manifest`、`export-epub`、`audit-epub`，以及缺失、过期、损坏产物测试。 | 本地较强 | 每次发布尝试前继续使用这些门禁。 |
| Agent workflow 保持暂存和可审计 | `agent-connect`、`agent-smoke`、`agent-run`、`agent-exec`、`agent-inbox`、`agent-next`、`examples/agent_controller_loop.py`、`docs/agent-connector-contract.md` 和 controller 测试。 | 本地较强 | 真实模型/controller 接入可继续作为外部实验，但必须保留暂存输出和复核门禁。 |
| 混乱旧项目迁移有持续真实项目证据 | `docs/dogfood-legacy-adopt.zh-CN.md` 已记录 0.2 收口，`docs/dogfood-cycle-evidence.md` 和 `audit-dogfood-cycle` 定义持续周期证据门禁。 | 部分证明 | 1.0 仍需要一份填实并通过 `audit-dogfood-cycle` 的收口后维护周期记录。 |
| 恢复路径保持更新 | `docs/recovery.md`、`docs/recovery.zh-CN.md`、已知限制文档、兼容性策略、发布证据测试。 | 本地较强 | 任何会创建、修复、再生成或使持久状态失效的命令变化，都必须同步恢复文档。 |
| 本地 checkout 之外存在包发布证据 | 本地 wheel/sdist 构建、CI/publish workflow、已 accepted 的 `docs/release-trial-evidence.md`、GitHub Actions run `28849146871`、TestPyPI `fictionops==0.1.1`、干净 venv 安装烟测，以及 `audit-release-evidence` 返回 `ready=true`。 | 外部证据已完成 | 后续 release trial 继续记录真实 run URL、包 hash、安装烟测、reviewer 和 decision。 |
| 行为经过时间稳定 | 里程碑账本、兼容性策略、release notes、回归测试、`docs/stability-window-evidence.md`、`audit-stability-window` 和 `audit-stable-core`。 | 目前无法证明 | 需要 accepted 稳定窗口记录，证明经过真实使用时间且没有未记录的破坏性变化。 |

## 当前本地结论

当前仓库可以证明：

- 0.1.0 pre-alpha MVP 本地完成。
- 0.2 迁移 dogfood 本地完成。
- 0.3 no-model controller 编排本地完成。
- 0.4 发布演练已完成，并有 accepted 外部证据。
- 0.5 文档接手本地完成。
- 1.0 稳定核心未完成。

## 1.0 阻塞项

以下全部成立前，不要标记 1.0 完成：

1. 0.2 迁移收口之后，至少记录一轮持续真实项目 dogfood，并通过 `audit-dogfood-cycle`。
2. 兼容性敏感行为在该周期内保持稳定，或每个破坏性变化都有明确迁移路径，并记录在 `docs/stability-window-evidence.md`，且通过 `audit-stability-window`。
3. 对所有会创建、修复、再生成、发布或使持久项目状态失效的命令，恢复文档仍保持同步。
4. `fictionops audit-stable-core .` 返回 `ready=true`。

## 行动项契约

`audit-stable-core --format json` 会为每条 1.0 证据线输出一个行动项：

- `local-foundation`：本地治理文件、workflow、文档和测试存在。
- `release-trial-evidence`：外部包发布演练证据已经填实并 accepted。
- `sustained-dogfood-cycle`：真实迁移后维护周期已经填实并 accepted。
- `stability-window`：经过时间的兼容性窗口已经填实并 accepted。
- `stable-core-ledger`：证据就绪后，stable-core 审计和里程碑账本诚实标记完成。

`external_required` 或 `docs_update_required` 这类状态只是给下一位执行者看的指令，不能当作证据。每个行动项里的 audit command 才是验收命令。

## 审计规则

后续如果改动 CLI 命令名、必填参数、核心 JSON key、覆盖行为、包内容、发布流程、Agent 暂存边界或恢复路径，需要同步更新本审计、兼容性文档、里程碑状态、release notes 和测试。
