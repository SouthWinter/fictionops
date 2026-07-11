# Codex Skill Adapter

This directory contains the installable Codex Skill adapter for running FictionOps inside Codex.

It is not a fork of FictionOps. The skill should call the FictionOps CLI and use the same project files, staged agent runs, inbox reviews, and audit gates as the generic workflow.

## Intended Use

- Work on a long-form writing project that already uses FictionOps structure.
- Create chapter briefs, call model/API runners, receive staged drafts, and run review gates.
- Audit continuity, information release, character memory, prose patterns, and release readiness.
- Record dogfood metrics for real AI-assisted writing work.

## Install Shape

The reusable skill lives in:

```text
fictionops-writing-agent/
  SKILL.md
  references/
    workflow.md
    chapter-writing.md
    audit.md
    dogfood-metrics.md
```

To use it in a local Codex setup, copy `fictionops-writing-agent/` into `$CODEX_HOME/skills/`, restart Codex, then invoke `$fictionops-writing-agent` in a FictionOps project checkout. The skill delegates to the installed FictionOps CLI and does not fork the runtime.

## Design Notes

- The skill assumes an AI-native workflow by default when a real provider is configured.
- The skill should never require an API key to be stored in the repository.
- The skill should stage outputs first and let the user accept, reject, or revise them.
- The skill may use echo runners only for CI, smoke tests, or debugging.
