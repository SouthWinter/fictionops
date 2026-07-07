# FictionOps 两分钟 Demo 台本

这是一份短录屏或现场演示台本。完整教程见 [最小示例教程](tutorial-demo.zh-CN.md)。

你不一定要亲自录视频。它有三种用法：

- 现场演示：一边敲命令，一边解释边界。
- 录屏素材：按同一组命令录成 GIF、MP4 或 asciinema。
- 面试讲解：不运行命令，只按台本说明项目怎么闭环。

## 准备

从源码仓库进入示例项目：

```bash
cd fictionops/examples/demo_novel
```

如果已经安装 FictionOps，直接使用 `fictionops`。如果还没有安装，把下面命令里的 `fictionops` 替换成：

```bash
python ../../src/fictionops/cli.py
```

下面为了易读，统一写成 `fictionops`。

## 0:00 - 先说清楚项目定位

可以这样说：

> FictionOps 不是自主写小说的 agent。它是一套面向长篇小说的文件化 workflow harness：管理正史、书纲、信息边界、任务包、模型暂存输出、审计和发布门禁。

运行：

```bash
fictionops doctor . --book book_01
```

要点：示例项目故意很小，`doctor` 的价值不是假装一切完美，而是把维护信号暴露出来。

## 0:20 - 把书纲同步成章节工作面

可以这样说：

> 第一步把书纲同步进章节发动机。章节会获得局部压力、欲望、阻碍、变化、余味、视角、章节性质和目标字数。

运行：

```bash
fictionops plan-chapter . --chapter 002 --force
```

要点：FictionOps 从普通 Markdown 文件里整理出可执行的写作工作面。

## 0:40 - 生成有边界的写前任务单

可以这样说：

> 几百万字项目不能把整本书都塞给模型。它需要的是有边界的 brief：场景需求、正史、信息边界、伏笔回声、人物口吻，并且受上下文预算约束。

运行：

```bash
fictionops draft-brief . --chapter 002 --include-context-content --max-total-chars 4000
```

要点：这一步展示的是“上下文编排”，不是无差别堆资料。

## 1:00 - 准备 Agent 任务包

可以这样说：

> 现在准备一个 agent 任务包。注意，这仍然不是让模型直接改正文，而是把任务、上下文和约束打包成可复核文件。

运行：

```bash
fictionops agent-run . --role draft-writer --chapter 002 --out-dir 00_management/agent_runs/ch_002_two_minute_demo --force
```

要点：任务包是可检查的文件产物，不是藏在聊天窗口里的隐形状态。

## 1:20 - 用无模型 Runner 跑通管线

可以这样说：

> 这里的 echo runner 用来模拟外部 API 或 agent wrapper。真实 runner 可以接 OpenAI、DeepSeek、Qwen、本地模型服务或外部 controller，但 FictionOps 只接收暂存输出。

运行：

```bash
fictionops agent-exec 00_management/agent_runs/ch_002_two_minute_demo --force --runner python ../../examples/agent_runner_echo.py
```

要点：runner 的结果会被保存为 staged artifact 和执行回执。

## 1:40 - 查看收件箱

可以这样说：

> 输出进入 inbox。人工复核、门禁和是否应用正文，仍然留在 runner 边界之外。

运行：

```bash
fictionops agent-inbox . --format json
```

要点：接上 controller 后整套流程可以变成 agentic workflow，但 FictionOps 本体负责把复核边界显性化。

## 1:55 - 收束到核心价值

可以这样说：

> 重点不是工具替你写正文，而是让长篇项目变得可维护：有边界的上下文、可见交接、暂存 AI 输出、审计、发布产物和可复现的项目状态。

可选收尾命令：

```bash
fictionops doctor . --book book_01
```

## 录屏方式

PowerShell 里可以先录文本日志：

```powershell
Start-Transcript .\fictionops-two-minute-demo.txt
# 运行 demo 命令
Stop-Transcript
```

如果要录 asciinema：

```bash
asciinema rec fictionops-two-minute-demo.cast
# 运行 demo 命令
exit
```

演示时不用把 `doctor` 的提示藏起来。示例项目本来就是小项目，有维护缺口是正常的；它们正好说明审计层在工作。
