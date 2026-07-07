# FictionOps 最小示例教程

这份教程使用 `examples/demo_novel/`，演示一个小型长篇项目如何从书纲走到写前任务单和项目健康检查。

## 1. 准备

在源码仓库中进入示例目录：

```bash
cd fictionops/examples/demo_novel
```

如果已经安装 FictionOps，可以直接使用：

```bash
fictionops doctor . --book book_01
```

如果还没有安装，可以从仓库源码调用：

```bash
python ../../src/fictionops/cli.py doctor . --book book_01
```

## 2. 让书纲同步章节发动机

第二章发动机保留了可被书纲同步的空间。先运行：

```bash
fictionops plan-chapter . --chapter 002 --force
```

这一步会从 `04_structure/book_outlines/book_01_outline.md` 的逐章规划表读取第 2 章的压力、欲望、阻碍、变化、余味，并写入 `06_drafts/book_01/chapter_engines/ch_002_engine.md`。

## 3. 生成场景计划

```bash
fictionops scene-plan . --chapter 002
```

`scene-plan` 不写正文，只把章节发动机拆成场景目标，帮助检查本章是否有压力链。

## 4. 生成写前任务单

```bash
fictionops draft-brief . --chapter 002 --include-context-content --max-total-chars 4000
```

`draft-brief` 会合并场景计划、信息边界、伏笔表、人物口吻和上下文文件。`--max-total-chars` 用来限制内嵌上下文总量，适合几百万字长篇项目。

## 5. 生成交接包

```bash
fictionops context-pack . --task handoff --no-content
```

交接包会列出下一位协作者需要读的文件：交接日志、决策记录、书纲、信息表、伏笔表、人物资料，以及可选的 doctor/report、revision-plan、book/release gate 报告。

## 6. 跑一遍无模型 Agent 管线

先生成 prepare-only 任务包：

```bash
fictionops agent-run . --role draft-writer --chapter 002 --out-dir 00_management/agent_runs/ch_002_demo --force
```

再用仓库自带的 echo runner 模拟外部模型或 agent：

```bash
fictionops agent-exec 00_management/agent_runs/ch_002_demo --runner python ../../examples/agent_runner_echo.py
```

如果要测试 OpenAI Responses runner 的边界，但暂时不联网：

```bash
fictionops agent-exec 00_management/agent_runs/ch_002_demo --force --runner python ../../examples/agent_runner_openai_responses.py --dry-run --model your-model
```

检查暂存输出是否被接住：

```bash
fictionops agent-inbox . --format json
```

这一步只验证管线，也不会把输出应用到正文或正史。OpenAI 示例去掉 `--dry-run` 后才会由外部 runner 调用模型，结果仍然只是 staging 输出。

## 7. 让示例 controller 选择下一步

`examples/agent_controller_next.py` 会调用 `agent-next`，输出下一条建议命令，但不会执行它：

```bash
python ../../examples/agent_controller_next.py . --chapter 002 --no-text-scan --cli fictionops
```

如果从源码调用 CLI：

```bash
python ../../examples/agent_controller_next.py . --chapter 002 --no-text-scan --cli python ../../src/fictionops/cli.py
```

如果要演示会执行安全命令、但会在复核边界停下的 no-model loop：

```bash
python ../../examples/agent_controller_loop.py . --chapter 002 --no-text-scan --max-steps 3 --log 00_management/agent_runs/controller_loop.jsonl --cli fictionops
```

这展示的是 Level 2 controller 的边界：自动化可以选择下一条安全命令，但暂存输出仍然要经过收件箱、门禁和人工确认。

## 8. 做健康检查

```bash
fictionops doctor . --book book_01 --format json
```

`doctor` 会汇总章节体量、连续性、信息边界、人物资料、词频、表格、发布物等状态。这个示例项目故意保持很小，所以它不是“零问题成书”，而是展示每层维护信号如何被工具读到。
