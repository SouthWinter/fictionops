# Dogfood 周期关闭 Runbook

这份 runbook 用来关闭 FictionOps 的持续 dogfood 周期。它的原则很简单：不要把一天内完成的维护 pass 包装成七天证据。只有真实结束日期到了，并且重新跑过关闭 checkpoint，才能 accepted。

当前进行中的周期是 `dogfood-2026-07-private-maintenance`，时间为 `2026-07-07` 到 `2026-07-14`。在 `2026-07-14` 关闭 checkpoint 完成前，不要把它标成 accepted。

## 目标

关闭 checkpoint 需要证明四件事：

- 同一个真实项目/沙盒经过时间后仍能被 FictionOps 接住。
- 处理的是哪本书、哪些章节，必须写清楚。
- AI/API runner 或 agent workflow 路径必须可追踪。
- 模型或工具输出仍然停在人类复核边界，不能直接污染正文或正史。

## 关闭前准备

收集这些信息：

- 私有沙盒路径；
- 当前 FictionOps commit；
- 开始 checkpoint 文件夹；
- 关闭 checkpoint 文件夹；
- 书号和章节范围；
- 周期内完成的重点任务；
- AI runner/controller 证据；
- 人类复核人姓名或 handle。

## 关闭日命令

在 release 仓库运行下列命令，把 `<sandbox>` 换成私有项目路径，把 `<date>` 换成关闭日期。

```bash
fictionops adopt-review <sandbox> --format json
fictionops doctor <sandbox> --book book_01 --format json
fictionops audit-info <sandbox> --format json
fictionops audit-characters <sandbox> --format json
fictionops audit-plan <sandbox> --book book_01 --format json
fictionops audit-echoes <sandbox> --format json
fictionops audit-continuity <sandbox> --format json
fictionops context-pack <sandbox> --task handoff --book book_01 --format json
fictionops revision-plan <sandbox> --book book_01 --format json
fictionops eval-agent <sandbox> --chapter 002 --format json
fictionops agent-inbox <sandbox> --format json
fictionops report <sandbox> --book book_01 --format json
```

如果这个周期包含真实模型/API 调用，还要记录暂存 run 路径：

```bash
fictionops agent-run <sandbox> --role draft-writer --book book_01 --chapter <chapter> --out-dir <run-dir>
fictionops agent-exec <run-dir> --runner <runner-command>
fictionops agent-inbox <run-dir> --format json
```

不要把 staged output 直接应用到源文件。模型输出是否采纳，应该写进项目工作日志或人工修订记录，而不是由 runner 命令直接决定。

## 必须比较的指标

对比开始 checkpoint 和关闭 checkpoint：

| 信号 | 必须记录 |
| --- | --- |
| `adopt-review` | `ready`、`blocking_issue_count`、`import_queue_files` |
| `doctor` | 优先级计数和新增 blocker |
| `revision-plan` | 任务数量和剩余类别 |
| `audit-plan` | 计划章节、正文章节、chapter engine 同步 |
| `audit-info` | 信息项数量和问题数量 |
| `audit-characters` | 人物、弧线、索引、智慧、口吻覆盖 |
| `audit-echoes` / `audit-continuity` | 问题数量 |
| `eval-agent` / runner | pass/fail、暂存输出路径、停止原因 |
| 发布门禁，如有 | blocking issue 数量 |

## 更新证据文件

编辑 `docs/dogfood-cycle-evidence.md`：

- 只有关闭 checkpoint 支持时，才把 `Final adopt-review status` 写成 `ready`、`ready_for_project_work`、`complete` 或 `completed`；
- 只有关闭 checkpoint 支持时，才保留 `import_queue_files: 0` 和 `blocking_issue_count: 0`；
- 在 `Day-by-day ledger` 里补入真实关闭 checkpoint；
- 在 `Compatibility notes` 里写清命令、JSON key、默认行为、runner 契约或恢复路径是否变化；
- 在 `Recovery notes` 里写清 no-overwrite、inbox quarantine、失败 runner 恢复等观察；
- 只有人类复核后，才能写 `Decision: accepted`。

然后运行：

```bash
fictionops audit-dogfood-cycle . --file docs/dogfood-cycle-evidence.md --format json
fictionops audit-stable-core . --format json
```

## 这些情况不能 accepted

- 关闭日期还没到；
- 没有重新跑关闭 checkpoint；
- 书/章节范围含糊；
- AI workflow evidence 只写了 “no AI used”；
- staged output 没有停在人类复核边界；
- 命令输出出现新的 P1/P2 blocker 且没有解释；
- `audit-dogfood-cycle` 没有返回 `ready=true`。

## accepted 之后

提交证据更新，例如：

```bash
git commit -m "Accept sustained dogfood cycle evidence"
```

然后再启动 stability-window 这条线。稳定窗口应该引用 accepted release evidence 和 accepted dogfood evidence，不能建立在 deferred dogfood 周期上。
