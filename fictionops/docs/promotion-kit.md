# Promotion Kit

This file prepares FictionOps for public sharing without changing the core product promise. FictionOps is not a Python package publishing helper and not a one-click novel generator. It is a local-first CLI workflow system for long-form fiction maintenance, AI-assisted writing boundaries, audits, and publishable outputs.

## Positioning

Short version:

> FictionOps is a local-first CLI workflow system for maintaining long-form fiction projects: outlines, chapter plans, canon, character memory, information boundaries, AI task bundles, review gates, and EPUB/Markdown outputs.

One-line social version:

> I built a CLI workflow for writers who need a long novel to remember its outlines, secrets, character memory, AI handoffs, audits, and publishing files.

Avoid these descriptions:

- "automatic novel generator";
- "Python package publishing tool";
- "autonomous writing agent";
- "AI that writes your book for you".

## Readiness Checklist

Before wide promotion:

- GitHub root README explains what the project does, why it exists, and how to start.
- `LICENSE` exists at the repository root and inside the package directory.
- `CITATION.cff` exists at the repository root.
- GitHub description and topics are set.
- CI is green on `main`.
- A demo command chain runs from the README.
- Formal PyPI publishing has either happened or the README clearly says to install from GitHub for now.
- GitHub Release notes are ready.
- A short demo asset exists: SVG preview, terminal recording, GIF, or video.

## Demo Script

Use this for a terminal recording or a two-minute video.

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

Narration beats:

1. FictionOps creates a file-based novel project.
2. It separates outlines, chapter engines, drafts, canon, characters, audits, and publish files.
3. It prepares a bounded writing task instead of dumping the whole project into a model.
4. A runner returns staged output.
5. `agent-inbox` and later gates keep human review in control.

## GitHub Release Draft

Title:

```text
FictionOps 0.1.1: local-first workflow for long-form fiction projects
```

Body:

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
- 128 regression tests and GitHub Actions CI.

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

## Show HN Draft

Title:

```text
Show HN: FictionOps - a CLI workflow for maintaining long-form fiction projects
```

Post:

```text
I built FictionOps, a local-first CLI workflow system for long-form fiction projects.

It is not an automatic novel generator. The goal is to help a writer keep a large story maintainable: outlines, chapter plans, canon, character memory, information boundaries, AI-assisted task bundles, review gates, and EPUB/Markdown outputs all live in ordinary files.

One thing I wanted to avoid is giving a model direct write access to manuscript/canon. FictionOps prepares scoped task bundles and stores runner output as staged text, then `agent-inbox` and review gates keep human review in the loop.

It currently includes 50 CLI commands, a demo project, migration helpers for old writing folders, OpenAI-compatible runner examples, EPUB export, and 128 regression tests.

I would especially appreciate feedback on the CLI shape, README, and whether the "staged AI runner" boundary is clear.
```

## Reddit / Community Draft

```text
I made a pre-alpha CLI tool for managing long-form fiction projects and AI-assisted writing boundaries.

The problem: once a novel gets large, the hard part is not just drafting prose. It is keeping outlines, canon, character memory, secrets, information release, revisions, and publishing files from drifting apart.

FictionOps keeps those pieces in ordinary files and provides CLI checks, task bundles, staged AI runner output, and review gates. It is not meant to replace the writer.

I am looking for feedback on whether the quickstart and CLI workflow make sense to people who write or maintain large creative projects.
```

## Chinese Article Outline

Title:

```text
我做了一个给长篇小说用的本地 CLI 工作流：FictionOps
```

Structure:

1. 长篇写作真正难的不是写一章，而是让几百万字记住自己。
2. 普通文件夹、聊天记录和表格为什么会失控。
3. FictionOps 的核心思路：文件结构、章节发动机、正史、人物记忆、信息边界、伏笔回声、门禁。
4. 为什么不让 AI 直接改正文：runner 只能产出暂存文本。
5. 三分钟 demo：init、new-chapter、plan-chapter、draft-brief、agent-run、agent-inbox、doctor。
6. 当前边界：pre-alpha、中文优先、不是自动写书。
7. 项目链接和希望获得的反馈。

## Outreach Order

Recommended order:

1. Keep GitHub README, topics, LICENSE, citation, CI, and demo ready.
2. Run TestPyPI and record release evidence.
3. Publish to formal PyPI only after TestPyPI is accepted.
4. Create GitHub Release.
5. Record a short terminal demo.
6. Publish one Chinese article and one English technical post.
7. Share to targeted communities asking for API/CLI feedback.
8. Submit to relevant awesome lists only after external users can install and run it.
