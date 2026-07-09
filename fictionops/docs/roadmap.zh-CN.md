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

## AI-native 方向

后续产品和研究方向应默认 **AI-native**。FictionOps 应被呈现和发展为一个默认接入模型 API 的长篇写作 Agent 系统。无模型路径仍然有价值，但定位应是 CI、烟测、调试、可复现和离线降级，而不是主要价值主张。

目标用户体验应从“很多可以选接 AI 的 CLI 积木”，转向“一个嵌入真实写作流程的 AI Agent”：

```text
故事/项目状态
  -> agent 观察工作区
  -> 编译范围化上下文
  -> model runner 产出候选工作
  -> 审计/门禁提供反馈
  -> controller 决定继续或停在复核边界
  -> 作者接受、修改或拒绝
```

AI Agent 默认应该承担真实写作工作：

- 根据书纲、人物记忆和信息边界规划章节；
- 通过 OpenAI-compatible runner 生成候选正文或修订建议；
- 审计信息泄露、人物失真、连续性、伏笔回声、行文模式和发布准备；
- 准备简介、标签、元数据、clean Markdown、EPUB 和发布清单；
- 通过 controller loop 判断安全下一步；
- 在审美判断、源文件变更、凭据、发布或外部证据需要人类权威时停下。

Echo/no-model runner 应被文档化为测试基础设施，而不是主叙事。主叙事应是 AI Agent 落地到真实长篇写作流水线。

## 里程碑矩阵

| 里程碑 | 目标 | 必要证据 | 暂不要求 |
| --- | --- | --- | --- |
| 0.2.0 迁移 dogfood | 证明真实长篇可以从旧材料复制状态推进到常规 FictionOps 项目工作。 | 一份 dogfood 记录显示 `adopt-review` 进入 `ready_for_project_work`，或所有剩余阻塞都被明确记录在 `07_audits/adopt_review/waivers.json`；迁移修复组已关闭或延期；导入队列清空；根据经验更新迁移文档。 | 云同步、Web UI、自动文学改写。 |
| 0.3.0 Agent Controller | 证明 controller 可以连续推进多步，同时保留暂存输出和门禁。 | `examples/agent_controller_loop.py` 能调用 `agent-next`、执行安全命令、在人类复核边界、占位命令、重复建议和迁移诊断状态停下，并记录 JSONL run log；`docs/agent-integration.md` 记录 runner/controller 接线方式；测试覆盖非破坏性停止行为。 | 让模型直接改正文或正史。 |
| 0.4.0 发布演练 | 证明本地 checkout 之外的安装和发布流程。 | GitHub Actions release flow 跑通；若决定发布则有 TestPyPI 记录；从构建包安装到干净虚拟环境；release notes 记录外部结果。 | 如果仍是 pre-alpha，不要求正式 PyPI 发布。 |
| 0.5.0 英文文档补齐 | 让外部贡献者可以不依赖中文深文档完成接手。 | 英文文档覆盖 CLI 契约、迁移、Agent workflow、发布、测试、demo、贡献，以及至少一个端到端迁移/发布案例。 | 每一条中文设计笔记都完整翻译。 |
| 0.6.0 AI 供应商接入 | 让真实模型 API 配置成为默认首次使用路径。 | `setup-ai` 或等价引导命令；OpenAI-compatible API provider preset；`.env.example`；dry-run 和真实调用文档；测试证明 API key 不进入项目文件。 | Web UI、托管账号、自动计费管理。 |
| 0.7.0 写作 Agent 命令 | 把多命令写作流程封装成 AI-first 命令。 | `write-chapter`、`revise-chapter`、`audit-chapter` 或等价编排命令，能调用规划、brief、model runner、inbox 和审计；测试覆盖暂存输出和停止行为。 | 自动采纳进入正文/正史。 |
| 0.8.0 Agent runtime dogfood | 证明 AI Agent 改善真实写作流程，而不只是基础设施跑通。 | 真实项目 AI dogfood 报告：模型/供应商、任务、采纳率、有效发现、prompt 准备时间节省、上下文查找时间节省、复核成本、失败案例和恢复记录。 | 公开正文或自动文学评分。 |
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

退出条件：贡献者可以跑一个本地 controller demo，看见完整、可审计、不会静默改正文或正史的循环。no-model demo 可以作为烟测，但后续里程碑必须把真实模型 API 作为默认产品路径。

## 0.6.0 AI 供应商接入验收清单

0.6.0 要让 AI 配置成为正常入口：

- 增加 `setup-ai`，或等价的引导命令链，面向 OpenAI-compatible providers。
- 通过 preset 或文档支持 OpenAI、DeepSeek、通义千问/DashScope、Kimi/Moonshot、GLM/智谱、豆包/火山方舟、硅基流动和本地 OpenAI-compatible 服务。
- 生成只含变量名和占位符的 `.env.example`，不保存真实 secrets。
- 同时提供 `--dry-run` 和真实调用示例。
- README quickstart 改成 AI-first，把 echo/no-model 用法移到 smoke test 区域。
- 补测试证明真实 API key 不会写入项目文件、receipt、任务包、文档或生成报告。

退出条件：新用户能配置供应商，跑 dry-run，跑真实模型调用，查看暂存输出，并理解作者采纳边界在哪里。

## 0.7.0 写作 Agent 命令验收清单

0.7.0 要把常规命令编排藏到 AI-first 写作命令后面：

- `write-chapter`：同步章节规划，生成场景/brief/context，调用 drafting runner，保存暂存输出，运行 inbox 和基础审计。
- `revise-chapter`：读取审稿/审计发现，构造修订任务包，调用模型 runner，保存暂存修订建议。
- `audit-chapter`：调用信息边界、人物失真、连续性、伏笔回声和行文模式等角色审计，汇总 findings。
- `agent-session`：持久记录单章 write/revise/audit 多步台账，读取暂存输出状态，并在复核边界停下。
- 未来的 `agent-loop`：观察项目状态，选择安全下一步，执行工具，调用 model runner，并继续受同一套复核门禁约束。
- 保持采纳由人治理：agent 可以产出候选工作和结构化发现，但源文件变更仍需明确采纳。

退出条件：普通用户故事从“手动拼五条命令”变成“让 FictionOps Agent 处理这一章”。

## 0.8.0 AI Agent Dogfood 验收清单

0.8.0 要衡量 AI Agent 在真实写作流程里改变了什么：

- 记录至少一次真实章节规划/草稿/修订 session，使用 model runner。
- 记录至少一次 AI-assisted 审计 session，覆盖信息、人物、连续性、伏笔或行文新鲜感。
- 记录至少一次发布准备 session，让 agent 帮助 metadata、clean copy 或 release checks。
- 记录模型/供应商、命令链、暂存输出、接受/拒绝、复核时间、有效发现、噪声发现、恢复动作和作者备注。
- 尽可能与 raw chat 或纯人工流程对照。

退出条件：项目不仅能说“AI 已接入”，还要能诚实地说“AI Agent 在真实长篇写作流程中的参与已经被观察、复核和测量”。

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
