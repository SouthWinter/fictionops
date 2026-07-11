# FictionOps 已知限制

FictionOps 的设计是保守的。它已经是有状态写作 Agent，但不承诺自主文学权威、法律判断、平台发布结果，也不把“门禁通过”解释成“小说已经完成”。模型不能自行接受正文、修改正史或绕过作者决策。

## 产品阶段

FictionOps 仍处于 pre-alpha 本地 CLI 阶段。命令行为有测试和契约文档保护，但还没有进入 1.0 稳定 API。

当前稳定预期：

- CLI 命令应尽量保留已有 JSON key。
- 新报告字段优先新增，而不是替换旧字段含义。
- 写文件命令默认拒绝意外覆盖，除非命令暴露并收到 `--force`。
- 1.0 前的破坏性变化必须写入 `CHANGELOG.md` 和 CLI 契约文档。

更细的兼容性策略见 [compatibility.zh-CN.md](compatibility.zh-CN.md)。

## 文学判断

FictionOps 不判断文字是否优美、是否能出版、情绪是否真正成立、是否有商业价值。审计命令只能发现维护风险，例如信息边界缺失、句首重复、章节体量过平、伏笔回声过久未更新、人物资料不完整。

建议缓解：

- 把审计输出当证据，不当判决。
- 把人工编辑判断记录进复盘和决策日志。
- 如果某个审计警告在审美上应该忽略，应记录这次 deliberate override。

## 模型行为

FictionOps 核心不调用模型供应商。外部 runner 可以通过 `agent-exec` 调用 OpenAI、本地模型或其他系统，但输出只进入 staging，必须复核。

已知限制：

- 模型质量、费用、延迟、供应商可用性不由 FictionOps 控制。
- OpenAI runner 只是接入示例，不是托管供应商 SDK。
- 如果用户自己写的外部 runner 不安全，仍可能泄露或误用上下文。

建议缓解：

- 使用 `context-pack` 的预算和任务范围。
- 先用 dry-run 或沙盒运行外部 runner。
- API key 只放环境变量，不写入项目文件。
- 用 `agent-inbox` 检查暂存输出，再决定是否应用。

## 上下文与记忆

FictionOps 把项目记忆存成文件，但不能保证每个人或每个 Agent 都读到了正确文件。表格缺失或过期时，报告可能看起来比真实故事更干净。

已知限制：

- `audit-info` 和 `audit-echoes` 依赖结构化表格和粗略文本扫描，不是完整语义理解。
- 人物、口吻和智慧模式审计只知道已经记录进人物记忆的内容。
- 长篇项目可能含有旧版、重复或废弃笔记，仍需要人工整理。

建议缓解：

- 把废弃材料放入 `99_archive/`。
- 大型手改后运行 `doctor`、`review-gate` 和 `book-gate`。
- `adopt-review` waiver 只用于有意识延期，不用于掩盖未知。

## 迁移

迁移工具负责诊断和暂存旧材料。它们不会自动理解一个混乱写作档案的真正含义。

已知限制：

- `adopt` 的建议目标路径是启发式结果。
- `import-plan --apply` 只移动安全、无歧义的正文文件。
- `adopt-review` 能证明已知阻塞被清掉或被明确延期，但不能证明旧项目在概念上已经完美迁移。

建议缓解：

- 迁移到独立初始化沙盒。
- 源项目保持只读。
- 保留 `00_management/adopted_handoff/adopt_manifest.json`。
- 用 `07_audits/adopt_review/waivers.json` 记录每个延期阻塞的理由。

## 发布

FictionOps 可以导出 clean Markdown、metadata、manifest、EPUB 和 release gate。它不保证平台合规、版权清理、封面授权、ISBN、印刷厂要求或平台审核通过。

建议缓解：

- 把 `release-gate` 当成本地发布包就绪检查。
- 平台特定验证在 FictionOps 外部完成。
- 最终上传凭据、税务/收款资料和平台账户不要放进项目。

## 协作与版本控制

FictionOps 使用普通文件，适合 Git 和备份。但它不提供文件锁、多人实时编辑、冲突合并或云同步。

建议缓解：

- 共享项目使用常规版本控制。
- 避免多人同时编辑同一张正史表。
- 重大结构决定写入 `00_management/decision_log.md`。

## 安全边界

FictionOps 不是安全沙盒。`agent-exec` 可以运行外部命令，这些命令拥有当前用户的执行权限。

建议缓解：

- 只运行可信外部 runner。
- 给敏感上下文前先审阅 runner 脚本。
- 真实模型调用前先 dry-run。
- 不要把 FictionOps 命令指向你不愿意审计的目录。

## 恢复预期

FictionOps 应该让常见错误变得可见，但恢复仍需要人工动作。

例子：

- 如果报告被 `--force` 覆盖，从版本控制恢复或重新生成。
- 如果暂存 Agent 输出错误，删除或归档 staging 文件，再运行 `agent-inbox`。
- 如果迁移 waiver 太宽，收窄匹配字段后重新运行 `adopt-review`。
- 如果发布物过期，重新运行对应导出命令，再运行 `release-gate`。

分步骤处理方式见 [恢复手册](recovery.zh-CN.md)。

稳定原则是：FictionOps 应保留证据链。作者决定什么进入书里。
