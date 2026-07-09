# FictionOps Research Positioning

FictionOps is an AI-native long-horizon writing agent workflow. It uses the author's real long-form fiction work as the landing domain, but the research problem is broader: how can an AI agent operate over a large, evolving human project, do useful work by default, and still avoid context drift, source-of-truth corruption, and hidden decisions?

This document frames FictionOps for research discussions, internships, papers, and system demos. For implementation details, see [Agent workflow positioning](agent-workflow.md), [Agent integration guide](agent-integration.md), and [Agent evaluation protocol](agent-evaluation.md).

## Core Claim

FictionOps is not merely a writing organizer that can optionally call AI. Its next direction is an AI agent system for long-form writing, where model APIs are assumed to be available and the no-model path is only a smoke/debug/fallback mode. It is an operating layer for persistent creative workspaces:

- it turns a long project into durable files;
- it compiles scoped context for bounded tasks;
- it packages model/API work as explicit task bundles;
- it captures model or runner output as staged artifacts;
- it runs audits and gates before source-of-truth changes are accepted.

The research contribution is agent landing under real workflow constraints: an AI agent can participate in planning, drafting, auditing, revision, and publishing preparation, while the system preserves project memory, traceability, recovery, and human-governed acceptance.

## Problem Setting

Long fiction is a useful stress test for long-horizon agents because it combines several hard properties:

- large and changing context;
- hidden information boundaries;
- character memory and voice consistency;
- long-range foreshadowing and payoff;
- subjective quality that cannot be reduced to one automatic score;
- human review, revision, and publishing constraints;
- many files that must remain recoverable over months of work.

These properties also appear in other domains: legal drafting, design documents, research projects, product specs, game writing, curriculum development, and any project where a model must act inside a persistent workspace while a human remains accountable for the final state.

## What FictionOps Is Not

FictionOps should not be described as:

- a one-click novel generator;
- a replacement for an author;
- a general agent orchestration framework like LangGraph, CrewAI, or AutoGPT;
- a RAG system by itself;
- an automatic literary quality scorer.

Those systems may be connected to FictionOps, but the core artifact is the workflow harness around durable state, scoped context, staged outputs, audits, and gates.

## System Abstraction

FictionOps can be described as six layers.

| Layer | Role | Research Function |
| --- | --- | --- |
| Persistent workspace | Markdown, YAML, JSON, drafts, audits, release artifacts | Gives the agent stable external state instead of relying on chat memory. |
| Context compiler | `context-pack`, `draft-brief`, `agent-prompt` | Turns a huge project into bounded, task-specific context. |
| Task envelope | `agent-run` request, role, task, chapter, constraints | Makes model work explicit and reproducible. |
| Runner boundary | `agent-exec` with external API/model/script | Lets different models participate without changing the core contract. |
| Staged output | `agent-inbox`, run receipts, output files | Prevents direct model writes to manuscript or canon. |
| Audits and gates | continuity, information, character, style, book, release | Makes review and stopping conditions visible. |

The design deliberately separates ability from authority. A model may be able to draft, plan, or audit; FictionOps still requires staged output and review boundaries before durable project state changes.

In the AI-native product path, the normal loop is:

```text
agent observes project state
  -> compiles scoped context
  -> calls an OpenAI-compatible runner
  -> stages candidate output
  -> reads audits/gates
  -> continues or stops for author acceptance
```

No-model runners remain useful for tests and reproducibility, but they are not the primary product narrative.

## Research Questions

FictionOps supports several concrete research questions.

1. **Context governance:** Can scoped task bundles reduce context drift compared with raw chat or broad project dumps?
2. **Authority boundaries:** Can staged output and gates reduce unsafe direct edits while still allowing useful model assistance?
3. **Persistent memory:** Can ordinary files serve as a recoverable memory substrate for long-running agent workflows?
4. **Human review cost:** Does structured task trace and audit output reduce the time needed to review model contributions?
5. **Controller behavior:** Can an external controller choose safe next steps and stop at human-review boundaries?
6. **Evaluation without literary scoring:** Can workflow reliability be evaluated without pretending that automatic metrics equal artistic judgment?
7. **AI landing impact:** Does the agent reduce real author labor in context lookup, prompt preparation, drafting, auditing, revision, and publishing preparation?

## Hypotheses

These are research hypotheses, not yet fully proven claims.

- H1: A FictionOps runner condition will have fewer direct-write violations than a direct-write agent condition.
- H2: Scoped task bundles will improve trace completeness and reduce irrelevant context compared with raw chat.
- H3: A FictionOps controller will stop more reliably at review boundaries than a generic autonomous loop.
- H4: Audit and gate artifacts will reduce recovery cost after bad model output.
- H5: Human reviewers will find staged outputs easier to accept, reject, or quarantine than free-form chat outputs.
- H6: An AI-first FictionOps agent will reduce repeated context-preparation and project-lookup work compared with raw chat while preserving author authority.

## Current Evidence

The public repository currently demonstrates:

- a file-first project structure;
- migration tooling for messy legacy folders;
- scoped context and task bundles;
- external runner execution;
- staged agent inbox;
- no-model controller examples for smoke testing;
- OpenAI-compatible real runner v1 for provider-backed AI work;
- continuity, information, character, style, table, wave, book, release, and EPUB audits;
- CI across Python versions;
- TestPyPI release-trial evidence;
- public demo fixtures and private dogfood summaries.

The stronger 1.0 claim is not yet closed. The project still needs accepted sustained dogfood-cycle evidence and stability-window evidence before it should be called a stable core.

## Evaluation Position

FictionOps should be evaluated as a workflow system, not as a prose model. Useful measurements include:

- staged output rate;
- direct-write violations;
- review-boundary recall;
- task trace completeness;
- context coverage;
- audit issue deltas;
- recovery cost;
- human review minutes;
- accepted/rejected staged output ratio.

These metrics are about reliability, governance, and maintainability. They do not claim to measure literary quality.

## Relationship To Agent Research

FictionOps is closest to an AgentOps or harness layer for long-horizon creative work:

- Like an agent framework, it defines tool boundaries and controller-facing commands.
- Like an evaluation harness, it provides reproducible tasks, traces, and metrics.
- Like a project management system, it stores durable work artifacts.
- Unlike a general agent framework, it is domain-specific and opinionated about review, source authority, and publishing gates.

The project is strongest when framed as an environment and workflow contract that other agents, model APIs, and controllers can plug into.

## Research Limitations

Current limitations:

- private dogfood evidence cannot expose manuscript text;
- public fixtures are small;
- no public leaderboard exists;
- model comparisons and real AI-assisted writing-session reports are not yet complete;
- human-review rubrics are early;
- automatic audits are heuristic and cannot replace editorial judgment;
- sustained stability evidence is still pending.

These limitations should be stated plainly. They make the project more credible, not weaker.

## Short Research Pitch

FictionOps is an AI-native workflow harness for long-horizon writing agents. It turns a real long-form fiction project into a persistent workspace where an agent can observe state, construct scoped context, call model runners, produce candidate drafts or audit findings, read workflow feedback, and stop for author acceptance. The key research question is how agents can land in real creative production while improving context use, tool use, reviewability, recoverability, and long-term state consistency.

## Safe Claims

Good claims:

- FictionOps demonstrates a staged-output safety boundary for AI-assisted writing workflows.
- It provides a concrete environment for evaluating long-horizon agent behavior over persistent project state.
- It separates model ability from source-of-truth authority.
- It assumes external model/API runners in the primary product path, while retaining no-model runners for smoke tests and fallback.
- It has been dogfooded on a private million-character-scale novel project, with public workflow evidence but no private manuscript leakage.

Claims to avoid:

- FictionOps proves AI can write novels autonomously.
- FictionOps automatically evaluates literary quality.
- The current public fixture is enough to prove generalization.
- The 1.0 stable core is complete before the sustained dogfood and stability-window evidence are accepted.
