# Getting Started

FictionOps does not require a user to learn every command before it becomes useful. Start with one of these paths, then grow the workflow only when the project needs more structure.

## Path A: New Project

```bash
fictionops init my-novel --title "My Novel"
fictionops new-book my-novel --book book_01 --title "Book One"
fictionops new-chapter my-novel --book book_01 --chapter 001 --title "Chapter One"
fictionops plan-chapter my-novel --book book_01 --chapter 001
fictionops draft-brief my-novel --book book_01 --chapter 001
```

Use this when the story is still being built. The useful daily loop is:

1. Update outline or chapter engine.
2. Generate a draft brief.
3. Write or ask an external assistant to produce staged text.
4. Run `post-draft` and `review-gate`.
5. Record decisions before moving on.

## Path B: Existing Novel

```bash
fictionops adopt old-novel --out adopt_report.md
fictionops init migrated-novel --title "Migrated Novel"
fictionops adopt old-novel --copy-to migrated-novel --format json
fictionops adopt-review migrated-novel
fictionops adopt-plan migrated-novel --write-groups 07_audits/adopt_review/repair_groups
```

Use this when a long project already has drafts, outlines, notes, or scattered canon files. `adopt` and `adopt-review` help sort the mess without modifying the source directory.

## Path C: Model/API Integration

The unified FictionOps agent delegates model calls to an external runner and keeps outputs staged. The lower-level core can still prepare task bundles without calling a model:

```bash
fictionops setup-ai my-novel --provider deepseek --model deepseek-chat

fictionops write-chapter my-novel \
  --book book_01 \
  --chapter 001 \
  --runner python fictionops/examples/agent_runner_openai_chat.py \
  --provider deepseek \
  --model deepseek-chat \
  --dry-run

fictionops agent-inbox my-novel
```

Set `DEEPSEEK_API_KEY` outside the project and remove `--dry-run` only after the staged-output boundary looks right. See [Model providers](model-providers.md) for DeepSeek, Qwen, Kimi, GLM, Doubao/Ark, SiliconFlow, local OpenAI-compatible servers, and OpenAI.

## What To Read Next

- [CLI guide](cli.md) for command details.
- [Agent integration guide](agent-integration.md) for runner and controller patterns.
- [Model providers](model-providers.md) for API wiring.
- [Migration guide](migration.md) for existing projects.
- [Testing guide](testing.md) for validating a checkout.
