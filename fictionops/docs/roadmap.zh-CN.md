# FictionOps Roadmap / 后续完成路线

这份路线图定义 0.1.0 pre-alpha MVP 之后，“更完整”到底是什么意思。它刻意采用证据导向：一个里程碑不是因为想法存在就算完成，而是仓库里有命令、文档、测试、示例、dogfood 记录或发布记录能证明它完成。

## 当前基线

0.1.0 已证明一条本地、文件优先的工作流：

- 项目脚手架；
- 旧项目诊断和安全复制到迁移沙盒；
- 导入队列规划和安全应用；
- 章节规划、场景计划和写前任务单；
- 写后、审稿、书级和发布门禁；
- 信息、人物、伏笔、风格、表格、体量波形和连续性审计；
- 范围化上下文包和 prepare-only Agent 任务包；
- 外部 runner 桥、暂存输出收件箱、下一步 controller 基础件和 agent 接入指南；
- clean Markdown、元数据、manifest、EPUB 导出和 EPUB 审计；
- CI、发布文档、兼容性与已知限制文档、包构建和安装烟测。

0.1.0 的证据记录见 [completion-audit-0.1.0.zh-CN.md](completion-audit-0.1.0.zh-CN.md)。逐里程碑当前状态见 [milestone-status.zh-CN.md](milestone-status.zh-CN.md)，更严格的 1.0 证据矩阵见 [stable-core-audit.zh-CN.md](stable-core-audit.zh-CN.md)。

## 里程碑矩阵

| 里程碑 | 目标 | 必要证据 | 暂不要求 |
| --- | --- | --- | --- |
| 0.2.0 迁移 dogfood | 证明真实长篇可以从旧材料复制状态推进到常规 FictionOps 项目工作。 | 一份 dogfood 记录显示 `adopt-review` 进入 `ready_for_project_work`，或所有剩余阻塞都被明确记录在 `07_audits/adopt_review/waivers.json`；迁移修复组已关闭或延期；导入队列清空；根据经验更新迁移文档。 | 云同步、Web UI、自动文学改写。 |
| 0.3.0 Agent Controller | 证明 controller 可以连续推进多步，同时保留暂存输出和门禁。 | `examples/agent_controller_loop.py` 能调用 `agent-next`、执行安全命令、在人类复核边界、占位命令、重复建议和迁移诊断状态停下，并记录 JSONL run log；`docs/agent-integration.md` 记录 runner/controller 接线方式；测试覆盖非破坏性停止行为。 | 让模型直接改正文或正史。 |
| 0.4.0 发布演练 | 证明本地 checkout 之外的安装和发布流程。 | GitHub Actions release flow 跑通；若决定发布则有 TestPyPI 记录；从构建包安装到干净虚拟环境；release notes 记录外部结果。 | 如果仍是 pre-alpha，不要求正式 PyPI 发布。 |
| 0.5.0 英文文档补齐 | 让外部贡献者可以不依赖中文深文档完成接手。 | 英文文档覆盖 CLI 契约、迁移、Agent workflow、发布、测试、demo、贡献，以及至少一个端到端迁移/发布案例。 | 每一条中文设计笔记都完整翻译。 |
| 1.0.0 稳定核心 | 固定可供真实作者和贡献者依赖的命令契约。 | 持续维护的兼容性策略；兼容性说明；完整本地测试；包发布；持续维护的已知限制文档；至少一轮通过 `audit-dogfood-cycle` 的持续真实项目 dogfood；accepted 稳定窗口证据并通过 `audit-stability-window`；`audit-stable-core` 返回 ready。 | 自动文学质量评分或自主小说作者。 |

## 0.2.0 验收清单

0.2.0 应该优先打通真实项目迁移路径，而不是急着堆新命令。

- 在一个足够复杂的真实项目沙盒上跑完 legacy-to-FictionOps 链路。
- 清空 `import_queue` 条目；其他可延期阻塞写入 `07_audits/adopt_review/waivers.json`，但未归位的导入正文仍然会让沙盒停在 `needs_import_sorting`。
- 补足足够的信息边界、人物记忆、章节发动机和逐章复盘，使 `adopt-review` 不再报告迁移专属阻塞。
- 记录每个无法安全自动化的人工判断。
- 把 dogfood 暴露的粗糙点写回迁移文档。
- 若 dogfood 导致命令行为变化，补回归测试。

退出条件：

```text
fictionops adopt-review <sandbox> --book <book_id> --format json
```

返回的状态要么已经可以进入常规项目工作，要么只剩有文档记录、被有意识延期的问题。

## 0.3.0 验收清单

0.3.0 应该证明 Agent workflow 可以编排，但不会把权力直接交给模型。

- 增加一个能连续运行多步的 controller 示例。
- controller log 必须记录所选命令、证据、执行结果和停止理由。
- 遇到 Agent 输出等待人类复核时自动停止。
- 遇到正文/正史覆盖风险前自动停止。
- `agent-exec` 输出仍然只进入暂存区。
- 测试覆盖缺失项目、导入队列、已有可复核 Agent 输出、发布门禁等状态。

退出条件：贡献者可以跑一个本地 no-model controller demo，看见完整、可审计、不会静默改正文或正史的循环。

## 1.0.0 稳定门槛

FictionOps 不应该过早宣称 1.0。进入 1.0 前，核心作者工作流应该“无聊地可靠”：

- 命令名和核心 JSON key 稳定；
- 命令、schema 或 controller-facing JSON 变化时，同步维护兼容性策略；
- 危险覆盖行为被一致拒绝；
- 发布门禁能发现过期或缺失的发布物；
- Agent workflow 始终保持暂存和可审计；
- 混乱旧项目迁移至少有一轮通过 `audit-dogfood-cycle` 的持续真实项目证明；
- 稳定窗口记录已 accepted，通过 `audit-stability-window`，且 `audit-stable-core` 返回 ready；
- 文档同时解释顺路流程、已知限制和常见错误恢复。

逐项 1.0 审计见 [stable-core-audit.zh-CN.md](stable-core-audit.zh-CN.md)。修改 1.0 里程碑状态前，应先以该文件和 `fictionops audit-stable-core .` 作为最终清单。

## 明确非目标

这些可以成为插件或未来实验，但不属于核心路线图的必需项：

- 云端数据库后端；
- 多人 Web 应用；
- 自动文学质量评分；
- 一键自主生成整部小说；
- 绕过审稿门禁，让模型直接写入正史或正文。
