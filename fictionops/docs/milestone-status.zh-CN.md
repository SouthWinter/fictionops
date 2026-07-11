# FictionOps 里程碑状态账本

这份文档记录当前仓库对路线图的证明程度。它比功能清单更严格：一个里程碑只有在当前文件、测试、workflow 或发布记录能证明所需行为时，才算完成。

状态含义：

- **本地已完成**：仓库证据已经能证明，不依赖外部服务状态。
- **已由外部证据完成**：仓库证据加真实外部 run 或服务记录已经能证明。
- **部分证明**：已有关键证据，但仍缺至少一个验收项。
- **等待外部证据**：仓库内准备已经存在，但完成依赖 GitHub Actions、TestPyPI、PyPI 或真实项目状态。
- **未完成**：实现或证据仍然明显不足。

## 总览

| 里程碑 | 状态 | 当前证据 | 剩余证据 |
| --- | --- | --- | --- |
| 0.1.0 Pre-Alpha MVP | 本地已完成 | `docs/completion-audit-0.1.0.zh-CN.md`、`docs/release-notes-0.1.0.zh-CN.md`、当前回归套件共 162 个测试、wheel/sdist 构建、源码安装和 built-wheel 安装烟测。 | 如果决定发布，还需要外部发布记录。 |
| 0.2.0 Migration Dogfood | 本地已完成 | 真实项目 dogfood 记录、`adopt --copy-to`、`adopt-review`、`adopt-plan`、`import-plan`、迁移豁免、导入队列清理路径、分组修复文件，以及 0.2 收口复跑中的 `ready: true`、`import_queue_files: 0`、`blocking_issue_count: 0`、无 blocking repair groups。 | 后续正史归一属于常规项目维护，不再是迁移里程碑阻塞。 |
| 0.3.0 Agent Controller | 本地已完成 | `examples/agent_controller_loop.py`、`agent-next`、`agent-exec`、`agent-inbox`、`docs/agent-connector-contract.zh-CN.md`、JSONL controller log，以及覆盖安全执行、复核边界、占位命令、迁移状态、重复建议和发布阶段命令的测试。 | 对 0.3 来说真实模型不是阻塞，但 0.6+ 已把真实模型 API 设为默认产品路径。 |
| 0.4.0 Release Trial | 已由外部证据完成 | GitHub Actions publish run `28849146871`、TestPyPI 包 `fictionops==0.1.1`、`docs/release-trial-evidence.md`、分发包哈希、干净环境 TestPyPI 安装烟测，以及 `audit-release-evidence` 返回 `ready=true`。 | 发布演练里程碑无剩余项。 |
| 0.5.0 Documentation Parity Pass | 本地已完成 | 英文 CLI、契约、迁移、Agent 协议、Agent workflow、Agent 接入、测试、发布、兼容性、已知限制、贡献、demo、legacy migration example，以及 `docs/end-to-end-migration-publish.md`。 | 每一条中文设计笔记的完整翻译仍然明确不纳入这个里程碑。 |
| 0.6.0 AI Provider Onboarding | 本地已完成 | OpenAI-compatible Chat runner v1、主要国内外 provider preset、`setup-ai`、无密钥 env、AI-first README quickstart、真实 DeepSeek API 运行，以及密钥不落盘测试/扫描。 | 后续供应商原生 Responses/token usage adapter 属于增强，不阻塞 0.6。 |
| 0.7.0 Writing Agent Commands | 本地已完成 | 统一 Agent 入口、写章/修订闭环、持久 session、上下文归因 trajectory、显式 controller policy、因果模拟、独立审读、预算、选择性复修、哈希采纳和 checkpoint-aware resume/cancel。 | 重试循环内部恢复与批次调度作为可选 P4 增强。 |
| 0.8.0 Agent Runtime Dogfood | 部分证明 | 真实 DeepSeek 报告、可重复 raw/RAG/full/ablation harness、统一 trajectory、7 场景 failure lab 和面试强案例已经形成证据链。 | 仍缺固定模型多次真实基线、AI-assisted 发布准备、作者复核时间和最终采纳编辑距离。 |
| 1.0.0 Stable Core | 未完成 | `docs/stable-core-audit.zh-CN.md`、兼容性策略、已知限制、恢复手册、命令契约、大范围测试、拒绝危险覆盖、暂存式 Agent workflow、发布门禁、已接受的 TestPyPI 发布演练证据、真实项目 dogfood 证据、`docs/dogfood-cycle-evidence.zh-CN.md`、`docs/stability-window-evidence.zh-CN.md`、`audit-dogfood-cycle`、`audit-stability-window` 和 `audit-stable-core`。 | 填实的持续真实项目 dogfood、已接受的稳定窗口证据、核心契约经过时间稳定，以及恢复路径随行为变化持续更新的证据。 |

## 0.2 迁移 Dogfood 细节

当前仓库证明了迁移链路可以扫描百万字级旧项目，把候选文件复制到初始化沙盒，处理目标路径碰撞，整理导入队列，只在显式要求时替换生成占位目标，并把迁移复查问题转成分组修复工作。

`docs/dogfood-legacy-adopt.zh-CN.md` 已追加 0.2 收口复跑记录。真实沙盒 `C:\Users\z\Documents\story\legacy_fictionops_02_closure_sandbox` 在清空导入队列、替换生成占位章节、并对作者判断型正史归一问题写入 `waivers.json` 后，`adopt-review` 返回 `ready: true`、`import_queue_files: 0`、`blocking_issue_count: 0`、`waived_issue_count: 31`；`adopt-plan` 返回 501 条普通维护任务、14 个修复组、无 blocking repair groups。

这不表示迁移后的小说已经完成清稿或正史归一。它证明的是迁移里程碑本身：旧材料可以离开导入队列，已知迁移阻塞可以被修复或有意识延期，项目可以进入常规 FictionOps 工作。

## 0.3 Agent Controller 细节

按路线图里的 controller 安全边界范围，0.3 已经本地满足。no-model loop 证明的是 controller 边界；后续 AI-native 里程碑必须把真实模型 API 变成默认产品路径。controller 可以：

- 调用 `agent-next`；
- 遵守外部 runner/controller 的接入契约；
- 只执行标记为安全的命令；
- 写出 JSONL log；
- 在暂存 Agent 输出处停下；
- 在占位命令处停下；
- 在重复建议处停下；
- 不直接改正文或正史；
- 处理迁移状态和发布阶段命令检查。

这不是宣称 FictionOps 已经是自主小说家。它证明的是：controller 可以编排流程，同时保留暂存输出和复核门禁。它也不代表 AI-native 路线已经完成；0.6-0.8 会继续跟踪供应商接入、写作 Agent 命令和真实 AI dogfood。

## 0.4 发布演练细节

仓库内已经有较强的发布前证据：

- 本地完整测试；
- 本地源码安装烟测；
- 本地 built-wheel 干净 venv 烟测；
- CI 构建和内容检查；
- publish workflow 构建和内容检查；
- CI 和 publish workflow 在上传或发布前执行 built-wheel smoke；
- Trusted Publishing 路径；
- publish workflow 会生成单独的 `fictionops-release-trial-evidence-<version>` artifact，记录 run URL、artifact 名称、wheel hash 和 sdist hash，并与 `fictionops-dist-<version>` 分开，避免证据草稿混入 PyPI/TestPyPI 发布目录。
- workflow-generated release trial evidence draft artifact 是发布审计轨迹的一部分；
- `audit-release-evidence` 会检查外部证据是否仍是空模板、未复核草稿、无效 run URL、无效 hash、缺安装烟测字段或非 `accepted` 结论。

`docs/release-trial-evidence.zh-CN.md` 现在提供固定记录位置，用于填写 GitHub Actions run URL、artifact 名称与 hash、可选 TestPyPI URL、安装烟测、回滚说明和 `accepted/deferred/failed` 结论。

外部发布演练证据现在已经存在：GitHub Actions run `28849146871` 完成分发包构建，通过 trusted publishing 发布 `fictionops==0.1.1` 到 TestPyPI，`docs/release-trial-evidence.md` 中的 accepted 记录也写入了 artifact hash 和干净安装烟测结果。未来发布演练仍不能用本地测试、空模板或未复核的自动草稿替代真实外部记录。

剩余 1.0 工作的执行清单见 `docs/stable-core-remaining-checklist.zh-CN.md`。它列出具体证据线、验收命令、停止条件，以及哪些事项需要维护者或外部服务状态，不能靠继续本地实现来替代。

## 使用方式

标记某个路线图里程碑完成前：

1. 先读本文件里的对应行。
2. 检查该行列出的文件、测试、workflow 或外部记录。
3. 同步更新本账本、roadmap、release notes 和 completion audit。
4. 如果命令、包产物或安全边界成为证据，补回归测试。
