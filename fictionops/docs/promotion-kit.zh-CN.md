# 推广准备包

这份文档用于准备 FictionOps 的公开介绍。它先纠正一个边界：FictionOps 不是 Python 包发布工具，也不是一键小说生成器。它是一套面向长篇小说项目维护、AI 协作边界、审计和发布产物的本地优先 CLI 工作流。

## 定位

短版：

> FictionOps 是一套面向长篇小说的本地优先 CLI 工作流，用来维护大纲、章节计划、正史、人物记忆、信息边界、AI 任务包、复核门禁和 EPUB/Markdown 发布产物。

社交平台一句话：

> 我做了一个给长篇小说用的 CLI 工作流，帮助作者管理大纲、秘密、人物记忆、AI 接手、审计和发布文件。

不要这样描述：

- 自动小说生成器；
- Python 包发布工具；
- 自主写作 agent；
- 替你写完整本书的 AI。

面试或研究实习交流时，可以先看 [面试备忘](interview-brief.zh-CN.md)。需要展示真实项目证据链时，看 [Dogfood 案例研究](dogfood-case-study.zh-CN.md)。

## 发布前检查

大范围宣传前确认：

- GitHub 根目录 README 已说明项目做什么、为什么有用、怎么开始。
- 根目录和包目录都有 `LICENSE`。
- 根目录有 `CITATION.cff`。
- GitHub description 和 topics 已设置。
- `main` 分支 CI 通过。
- README 里的 demo 命令能跑。
- 如果还没正式 PyPI 发布，README 必须明确当前从 GitHub 安装。
- GitHub Release 文案已准备。
- 至少有一个 demo 素材：SVG 预览、终端录屏、GIF 或视频。

## Demo 脚本

适合录终端或两分钟视频：

```bash
python -m pip install "git+https://github.com/SouthWinter/fictionops.git#subdirectory=fictionops"
fictionops init my-novel --title "My Novel"
fictionops new-book my-novel --book book_01 --title "Book One"
fictionops new-chapter my-novel --book book_01 --chapter 001 --title "Chapter One"
fictionops plan-chapter my-novel --book book_01 --chapter 001
fictionops draft-brief my-novel --book book_01 --chapter 001
fictionops agent-run my-novel --role draft-writer --book book_01 --chapter 001 --out-dir my-novel/00_management/agent_runs/ch_001
fictionops agent-exec my-novel/00_management/agent_runs/ch_001 --runner python fictionops/examples/agent_runner_echo.py
fictionops agent-inbox my-novel --format json
fictionops doctor my-novel --book book_01
```

解说顺序：

1. FictionOps 创建一个文件化小说项目。
2. 它把大纲、章节发动机、正文、正史、人物、审计和发布文件分层。
3. 它不是把整个项目丢给模型，而是准备有边界的写作任务包。
4. runner 只返回暂存输出。
5. `agent-inbox` 和后续门禁保证人类复核权。

## GitHub Release 草稿

标题：

```text
FictionOps 0.1.1: local-first workflow for long-form fiction projects
```

正文：

```markdown
FictionOps 0.1.1 is a pre-alpha CLI workflow system for maintaining long-form fiction projects.

It helps writers keep outlines, chapter plans, canon, character memory, information boundaries, AI-assisted task bundles, review gates, and publishable outputs in ordinary files.

Highlights:

- project scaffolding for books and chapters;
- migration diagnostics for existing writing folders;
- chapter planning, scene planning, and draft briefs;
- audits for continuity, information release, characters, echoes, style, tables, and chapter rhythm;
- staged AI/API runner integration without direct manuscript or canon writes;
- OpenAI-compatible Chat Completions runner example for providers such as DeepSeek, Qwen/DashScope, Kimi/Moonshot, GLM/Zhipu, Doubao/Ark, SiliconFlow, OpenAI-compatible local servers, and OpenAI Chat Completions;
- clean Markdown, metadata, manifest, and EPUB export;
- 129 regression tests and GitHub Actions CI.

Install from GitHub for now:

```bash
python -m pip install "git+https://github.com/SouthWinter/fictionops.git#subdirectory=fictionops"
```

The intended formal install path after PyPI release is:

```bash
python -m pip install fictionops
```

This is not a one-click novel generator. It is a project harness for writers who want a long story to stay maintainable.
```

## Show HN 草稿

标题：

```text
Show HN: FictionOps - a CLI workflow for maintaining long-form fiction projects
```

正文：

```text
I built FictionOps, a local-first CLI workflow system for long-form fiction projects.

It is not an automatic novel generator. The goal is to help a writer keep a large story maintainable: outlines, chapter plans, canon, character memory, information boundaries, AI-assisted task bundles, review gates, and EPUB/Markdown outputs all live in ordinary files.

One thing I wanted to avoid is giving a model direct write access to manuscript/canon. FictionOps prepares scoped task bundles and stores runner output as staged text, then `agent-inbox` and review gates keep human review in the loop.

It currently includes 51 CLI commands, a demo project, migration helpers for old writing folders, OpenAI-compatible runner examples, EPUB export, and 129 regression tests.

I would especially appreciate feedback on the CLI shape, README, and whether the "staged AI runner" boundary is clear.
```

## Reddit / 社区草稿

```text
I made a pre-alpha CLI tool for managing long-form fiction projects and AI-assisted writing boundaries.

The problem: once a novel gets large, the hard part is not just drafting prose. It is keeping outlines, canon, character memory, secrets, information release, revisions, and publishing files from drifting apart.

FictionOps keeps those pieces in ordinary files and provides CLI checks, task bundles, staged AI runner output, and review gates. It is not meant to replace the writer.

I am looking for feedback on whether the quickstart and CLI workflow make sense to people who write or maintain large creative projects.
```

## 中文文章骨架

标题：

```text
我做了一个给长篇小说用的本地 CLI 工作流：FictionOps
```

结构：

1. 长篇写作真正难的不是写一章，而是让几百万字记住自己。
2. 普通文件夹、聊天记录和表格为什么会失控。
3. FictionOps 的核心思路：文件结构、章节发动机、正史、人物记忆、信息边界、伏笔回声、门禁。
4. 为什么不让 AI 直接改正文：runner 只能产出暂存文本。
5. 三分钟 demo：init、new-chapter、plan-chapter、draft-brief、agent-run、agent-inbox、doctor。
6. 当前边界：pre-alpha、中文优先、不是自动写书。
7. 项目链接和希望获得的反馈。

## 对外顺序

建议顺序：

1. 保持 GitHub README、topics、LICENSE、citation、CI 和 demo 可用。
2. 跑 TestPyPI，并记录 release evidence。
3. TestPyPI 通过后再正式发 PyPI。
4. 创建 GitHub Release。
5. 录一个短终端 demo。
6. 发一篇中文文章和一篇英文技术帖。
7. 到精准社区征求 API/CLI 反馈。
8. 等外部用户能安装并跑通后，再给相关 awesome list 提 PR。
