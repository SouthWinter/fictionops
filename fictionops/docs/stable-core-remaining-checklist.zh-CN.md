# FictionOps 1.0 Stable Core 剩余执行清单

当前结论：本地基础已经具备，但 1.0 不能关闭。`fictionops audit-stable-core . --format json` 仍应返回 `not_ready`，直到发布演练、持续 dogfood、稳定窗口三条证据链都被真实填实并通过审计。

这份清单回答一个执行问题：从现在到 1.0，还差哪些真事。它不是证据本身，也不能替代 `docs/stable-core-audit.zh-CN.md` 和机器审计命令。

当前执行状态记录见 `docs/stable-core-remaining-execution.zh-CN.md`。如果执行环境、GitHub Actions run、TestPyPI 状态或真实 dogfood 周期发生变化，先更新那份状态记录，再回到本清单逐项关闭。

## 0. 当前状态

| 项目 | 状态 | 说明 |
| --- | --- | --- |
| 本地治理文件、测试、CLI、文档、workflow | 已具备 | `local-foundation` 应为 complete；后续只在发现真实回归时继续加固。 |
| 发布演练证据 | 未完成 | 需要外部 GitHub Actions、artifact 或 TestPyPI、干净环境安装烟测证据。 |
| 持续 dogfood 周期 | 未完成 | 需要至少 7 个自然日的真实项目维护记录。 |
| 稳定窗口 | 未完成 | 需要 release + dogfood 证据之后的兼容性窗口记录。 |
| 里程碑账本关闭 | 未完成 | 只能在 `audit-stable-core` 返回 `ready=true` 后更新为完成。 |

## 1. 不再继续本地打磨的事项

除非发现真实回归，不要把 1.0 时间继续花在这些事项上：

- 继续扩大 CLI 命令面；
- 继续增加空模板字段；
- 继续重复证明本地 wheel/sdist 能构建；
- 继续把 `audit-stability-window` 当成主要工作；
- 继续用本地 smoke、生成草稿、空证据模板替代外部证据。

本地加固可以维护，但它现在不是 1.0 的主要阻塞。

## 2. Phase A：完成外部发布演练

目标：关闭 0.4 release trial 的外部证据缺口。

执行事项：

1. 在 GitHub Actions 手动触发 `FictionOps Publish` workflow，优先选择 TestPyPI 或明确记录跳过 TestPyPI 的原因。
2. 下载并保存 workflow 生成的 `fictionops-release-trial-evidence-<version>` 证据草稿 artifact。
3. 记录真实 GitHub Actions run URL，格式必须类似 `https://github.com/<owner>/<repo>/actions/runs/<run-id>`。
4. 记录 wheel 和 sdist artifact 名称、hash、大小。
5. 如果使用 TestPyPI，记录 TestPyPI project URL、version URL、发布结果和干净环境安装命令；如果跳过，记录跳过原因和接受人。
6. 在干净虚拟环境里从外部 artifact 或 TestPyPI 安装，记录 `fictionops --version`、`python -m fictionops --version`、`fictionops init`、`fictionops doctor` 的结果。
7. 填写 `docs/release-trial-evidence.md` 和必要的中文说明。

验收命令：

```bash
fictionops audit-release-evidence . --file docs/release-trial-evidence.md --format json
```

完成定义：

- `ready=true`；
- `decision=accepted`；
- `blocking_issue_count=0`；
- 证据不是空模板，也不是未经复核的 workflow 草稿；
- release notes 写入真实 run id 或 URL。

## 3. Phase B：完成持续 dogfood 周期

目标：证明 0.2 迁移收口之后，一个真实长篇项目能继续用 FictionOps 做维护，而不是只完成一次迁移展示。

执行事项：

1. 选择一个真实迁移后的项目或等价维护沙箱。
2. 记录周期开始和结束时间，跨度至少 7 个自然日。
3. 周期内至少使用 3 个可识别的 FictionOps CLI 命令，建议覆盖 `adopt-review`、`adopt-plan`、`import-plan`、`doctor`、`report`、`context-pack`、`revision-plan` 里的多个类别。
4. 记录开始和结束时的项目状态，包括 `ready`、`import_queue_files`、`blocking_issue_count`、waiver、延期项和恢复动作。
5. 记录周期内发现的兼容性问题、恢复路径问题和人工决策。
6. 填写 `docs/dogfood-cycle-evidence.md` 和必要的中文说明。

验收命令：

```bash
fictionops audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md --format json
```

完成定义：

- `ready=true`；
- 周期至少覆盖 7 个自然日；
- 命令覆盖被识别为真实 FictionOps 命令；
- 最终状态没有未解释的迁移阻塞；
- 决策为 accepted。

## 4. Phase C：完成稳定窗口

目标：证明稳定面经过真实时间后没有静默漂移；如果发生破坏性变化，每一项都有明确迁移路径。

执行事项：

1. 在发布演练证据和 dogfood 周期证据都通过之后，记录至少 7 个自然日的稳定窗口。
2. 明确窗口内监控的稳定面：命令名、必填参数、核心 JSON key、默认不覆盖行为、包内容、发布流程、Agent 暂存边界、恢复路径。
3. 如果引用本地 Markdown 证据，引用必须在被审计 checkout 内，且对应 release/dogfood 证据本身能通过审计。
4. 如果引用 URL，必须是完整 `https://...`，并指向具体 run、artifact、release、dogfood 或 stability 证据，不要使用泛泛首页链接。
5. 填写 `docs/stability-window-evidence.md` 和必要的中文说明。

验收命令：

```bash
fictionops audit-stability-window . --file docs/stability-window-evidence.md --format json
```

完成定义：

- `ready=true`；
- 周期至少覆盖 7 个自然日；
- release 和 dogfood 引用都真实可审计；
- 没有未记录的破坏性变化；
- 决策为 accepted。

## 5. Phase D：关闭 1.0 账本

目标：在三条外部证据链都通过后，诚实更新 1.0 状态。

执行事项：

1. 运行聚合审计：

```bash
fictionops audit-stable-core . --format json
```

2. 如果聚合结果是 `ready_needs_docs_update`，同步更新：

- `docs/stable-core-audit.md`
- `docs/stable-core-audit.zh-CN.md`
- `docs/milestone-status.md`
- `docs/milestone-status.zh-CN.md`
- `docs/roadmap.md`
- `docs/roadmap.zh-CN.md`
- release notes 和 changelog 中的相关条目

3. 重新运行完整本地验证和包构建。
4. 再次运行 `fictionops audit-stable-core . --format json`。

最终完成定义：

- `ready=true`；
- `status=ready`；
- `blocking_issue_count=0`；
- `action_items` 全部 complete；
- 文档没有把外部证据、模板和计划混写。

## 6. 执行责任表

| 事项 | 主要执行者 | 本地验收命令 | 证据文件 | Codex 能否独自完成 |
| --- | --- | --- | --- | --- |
| 本地基础维护 | Codex | `python -m unittest discover -s fictionops/tests -v` | 测试、workflow、文档 | 可以，但只需修真实回归。 |
| 发布演练证据 | 维护者 + Codex 辅助 | `audit-release-evidence` | `docs/release-trial-evidence.md` | 不能。需要外部 GitHub Actions/TestPyPI 或 artifact 记录。 |
| 持续 dogfood 周期 | 维护者 + Codex 辅助 | `audit-dogfood-cycle` | `docs/dogfood-cycle-evidence.md` | 不能完全独自完成。需要真实项目和经过时间。 |
| 稳定窗口 | 维护者 + Codex 审计 | `audit-stability-window` | `docs/stability-window-evidence.md` | 不能完全独自完成。需要真实经过时间。 |
| 1.0 账本关闭 | Codex + 维护者复核 | `audit-stable-core` | stable-core、milestone、roadmap、release notes | 证据齐全后可以协助完成。 |

## 7. 停止条件

遇到以下情况，不要标记 accepted，也不要关闭 1.0：

- 证据文件仍是模板；
- 证据来自 workflow 生成草稿，但没有人工复核填写；
- 只有本地 smoke，没有外部 run、artifact 或 TestPyPI 记录；
- URL 是泛泛首页，不是具体 run、artifact、release 或证据页；
- 本地引用指向被审计 checkout 外部；
- dogfood 或稳定窗口少于 7 个自然日；
- release、dogfood、stability 三者有任一项没有通过对应 audit 命令。

## 8. 下一件事

下一件真正推进 1.0 的事是：触发一次外部 release trial，填实 `docs/release-trial-evidence.md`，并让 `audit-release-evidence` 返回 `ready=true`。

如果暂时不准备发布，就明确把 release trial 标记为 deferred，并保持 1.0 open。不要再把本地加固误认为 1.0 完成进度。
