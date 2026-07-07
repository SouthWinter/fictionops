# FictionOps 恢复手册

这份手册处理常见误操作和损坏状态。原则很简单：先保留证据，再读报告，最后只运行最小的安全恢复命令。

FictionOps 是文件系统工作流。恢复时优先使用备份、版本控制、显式报告和重新生成的发布产物，不做静默修复。

## 恢复原则

动手前先做五件事：

1. 保留当前项目目录，或先提交到版本控制。
2. 先跑只读命令：`doctor`、`report`、`adopt-review`、`book-gate`、`release-gate`、`agent-inbox`。
3. 不确定要替换哪个生成文件前，不要用 `--force`。
4. 不让外部模型直接编辑 `03_characters/`、`04_structure/`、`05_canon/` 或 `06_drafts/`。
5. 人类有意做出的决定，写入 `00_management/decision_log.md`、相关复盘或 waiver 文件。

## 快速诊断

```bash
fictionops doctor my-novel --book book_01 --format json
fictionops report my-novel --book book_01 --format json
fictionops workflow-plan my-novel --stage all --book book_01
```

根据输出判断下面哪一节适用。

## 生成报告被覆盖

症状：

- Markdown 报告、context pack、draft brief 或 gate report 被坏内容覆盖。

先跑：

```bash
fictionops doctor my-novel --format json
```

如果这是纯生成文件，里面没有人类手写笔记，可以用同一命令加 `--force` 重新生成：

```bash
fictionops context-pack my-novel --task handoff --out 00_management/context/handoff.md --force
fictionops review-gate my-novel --chapter 001 --out 07_audits/review_gate/ch_001.md --force
fictionops release-gate my-novel --book book_01 --out 07_audits/release_gate/book_01.md --force
```

如果文件里有人类笔记，先从版本控制或备份恢复，不要再次覆盖。

## 正文或正史被误改

症状：

- 章节、人物文件、信息表或结构文件出现意外变化。

先跑：

```bash
fictionops audit-continuity my-novel --book book_01 --format json
fictionops audit-info my-novel --book book_01 --format json
fictionops audit-characters my-novel --format json
```

然后和版本控制或备份对比。FictionOps 不会静默重建正文或正史。恢复最后可信版本后，再跑：

```bash
fictionops review-gate my-novel --chapter 001 --format json
fictionops book-gate my-novel --book book_01 --format json
```

如果恢复后的状态和后续章节冲突，停下交给人判断。

## Agent 输出错误或不安全

症状：

- `agent-exec` 写出了不可用的 `output.md`；
- `agent-inbox` 报告多输出、空输出或损坏请求；
- 模型输出包含未来秘密或直接改文件指令。

先跑：

```bash
fictionops agent-inbox my-novel --format json
```

然后：

- 归档或删除坏的暂存输出；
- 如果需要审计轨迹，保留 `request.json`、`prompt.md` 和 `execution.json`；
- 重新跑 `agent-inbox`；
- 修正 runner 或提示词边界后再跑 `agent-exec`。

不要把不安全输出直接粘进正文或正史。若人类决定采纳其中一部分，需要记录决定并重新跑对应门禁。

## 导入队列卡住

症状：

- `adopt-review` 报告 `needs_import_sorting`；
- `06_drafts/import_queue/` 下还有文件。

先跑：

```bash
fictionops import-plan my-novel --format json
fictionops import-plan my-novel --out 07_audits/adopt_review/import_plan.md
```

确认计划后，只应用安全移动：

```bash
fictionops import-plan my-novel --apply --create-scaffolds --format json
```

只有目标是初始化生成的占位章节时，才使用 `--replace-placeholder-targets`。真实已有章节目标应留给人工复核。

应用后：

```bash
fictionops adopt-review my-novel --format json
```

如果仍有歧义文件，先决定书/章目标，再手工处理。

## 迁移 Waiver 过宽

症状：

- `adopt-review` 看起来异常干净；
- 添加 `07_audits/adopt_review/waivers.json` 后，重要问题消失。

处理方式：

1. 打开 waiver 文件。
2. 用 `source`、`code`、`subject` 或 `path` 收窄每条 waiver。
3. 保留明确理由。
4. 重新运行：

```bash
fictionops adopt-review my-novel --format json
fictionops adopt-plan my-novel --format json
```

waiver 是延期已知工作，不是掩盖未知工作；它也不能清理物理存在的 `import_queue` 文件。

## 发布产物缺失或过期

症状：

- `audit-publish`、`audit-epub`、`doctor` 或 `release-gate` 报告缺失、过期或 hash 不匹配。

重新生成发布产物：

```bash
fictionops export-clean my-novel --book book_01 --force --format json
fictionops audit-publish my-novel --book book_01 --format json
fictionops export-metadata my-novel --book book_01 --force --format json
fictionops export-manifest my-novel --book book_01 --force --format json
fictionops export-epub my-novel --book book_01 --force --format json
fictionops audit-epub my-novel --book book_01 --format json
fictionops release-gate my-novel --book book_01 --format json
```

这里使用 `--force` 是因为这些是生成型发布产物。`release-gate` 通过也不等于平台一定接收。

## Controller 反复选择同一步

症状：

- 外部 controller 一直选择同一命令；
- 多轮之间项目证据没有变化。

先跑：

```bash
fictionops agent-next my-novel --book book_01 --format json
```

再检查 controller log。安全 controller 应在重复建议时停止。如果没有停止，禁用 controller，手动运行被选中的命令，不要盲目循环。

## 什么时候必须停下

以下情况停止自动恢复，交给人类复核：

- 下一步会修改正文、正史、凭据或真实发布上传；
- 两个故事状态都有效，并且都会影响后文；
- 一个迁移文件有多个合理章节目标；
- waiver 会消除你还没理解的问题；
- 模型输出改变事实、时间线或信息边界。

恢复的目标不是让所有门禁快速变绿，而是在作者做出真实决定前保住证据链。
