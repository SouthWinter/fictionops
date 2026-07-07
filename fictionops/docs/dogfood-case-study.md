# Dogfood Case Study: Maintaining a Million-Character Novel With FictionOps

This case study summarizes a private real-project dogfood run. The manuscript text, story-specific canon, character details, and local paths are intentionally redacted. The public value of the run is the workflow evidence: FictionOps was used on a large, messy, long-horizon fiction project and had to survive migration, repair planning, prose review, clean export, EPUB packaging, and release gates.

The active sustained dogfood cycle is still deferred until the seven-calendar-day window closes. This document is a case study, not a 1.0 acceptance claim.

## Problem

Long-form fiction is a useful stress test for agent workflows because the hard parts are not one-shot generation.

A large novel project has:

- very long context that cannot fit in a single model call;
- evolving canon, outlines, character memory, and information boundaries;
- hidden knowledge states: different characters and reader segments know different things at different times;
- local prose quality questions that cannot be solved by global string replacement;
- multi-stage release artifacts such as clean Markdown, metadata, manifests, and EPUB files;
- human aesthetic judgment that must remain in the loop.

Before the dogfood run, the private project had the typical shape of a long-lived writing workspace: useful material existed, but it was distributed across outlines, drafts, imported notes, retrospectives, stale templates, and publish files. The goal was not to let an agent rewrite the book. The goal was to turn the project into a maintainable state machine.

## What FictionOps Provided

FictionOps acted as an AgentOps-style workflow harness.

It provided:

- a file layout for project memory: structure, canon, characters, drafts, audits, and publishing;
- static audits for information release, character arcs, table hygiene, chapter plans, echo threads, continuity, style patterns, and chapter-length wave;
- revision planning that sorts audit findings into prioritized repair work;
- scoped context packs and agent harness commands that keep model-facing context bounded;
- inbox and gate semantics so external agent output is staged rather than applied directly;
- publishing commands for clean Markdown, metadata JSON, manifest JSON, EPUB generation, and release readiness.

The important design choice was separation of authority:

- FictionOps can surface signals and enforce workflow gates.
- External model/API runners can propose or generate bounded outputs.
- Human review decides whether a prose signal is real craft work or just a static-count artifact.
- Generated outputs do not overwrite the source manuscript without a deliberate review step.

## Workflow

The dogfood run used a migrated private sandbox rather than the original manuscript workspace. This let FictionOps repair, export, and package the project without risking source overwrite.

The maintenance sequence was:

1. Run migration and health checks: `adopt-review`, `doctor`, `audit-info`, `audit-characters`, `context-pack`, `revision-plan`, and `eval-agent`.
2. Repair project memory before prose: information release table, character memory tables, active table hygiene, book outline synchronization, and echo/continuity tracking.
3. Convert style and wave findings into a reader-experience memo rather than immediate rewrites.
4. Apply bounded prose edits only after human classification of high-priority chapters.
5. Re-run style, word, and wave audits after each prose pass.
6. Export clean Markdown and run publish gates.
7. Generate metadata, manifest, EPUB, and final release-gate evidence.

This order matters. It avoids a common agent failure mode: polishing local text while the underlying project memory is still inconsistent.

## Results

The dogfood run produced measurable state transitions.

Project-memory repairs:

- `adopt-review` reached `ready=true` with `blocking_issue_count=0` in the private sandbox checkpoint.
- `audit-info` moved to `item_count=8` and `issues=0` after the active information-release table repair.
- `audit-characters` moved to 8 parsed characters, 8 arcs, 8 index rows, 8 intelligence profiles, 8 voice profiles, and `issues=0`.
- Active table issues moved to `0`.
- The active Book 01 outline synchronized with the draft inventory: 33 planned chapters, 33 draft files, 33 engine files, 33 synced engines, and `issues=0`.
- Active echo tracking moved to one maintained echo table with 3 threads and `issues=0`; continuity template issues moved to `0`.
- The private `revision-plan` dropped from 616 initial tasks to a small set of non-blocking style/wave/word-scan notes after structural repair.

Reader-experience repairs:

- The first reader-experience pass identified high-priority chapters without doing bulk replacements.
- A bounded prose sequence addressed targeted clusters: nameless-title repetition, court-density explanation, first-blood causality, and a final bone-knife light read.
- Style watch totals moved from 3843 at reader-experience baseline to 3770 after the targeted prose pass.
- The chapter wave audit kept the same known pacing prompts; no new pacing category was introduced.
- The key principle was preserved: style counts were treated as prompts for reading, not commands for mechanical editing.

Publish-chain smoke:

- Clean Markdown exported 33 chapters.
- `audit-publish` reported 33 clean chapters matching 33 draft chapters and `issues=[]`.
- Metadata JSON, manifest JSON, and EPUB artifacts were generated.
- `audit-epub` reported `epub_valid=true`, 33 chapters, and `issues=[]`.
- `book-gate` reported `Ready: yes` with `Blocking issues: 0`.
- `release-gate` reported `Ready: yes` with `Blocking issues: 0`.

The generated publish metadata used a sandbox placeholder author value to exercise the pipeline. It is not real publication metadata.

## What This Shows

This run supports a narrower and more useful claim than "AI can write a novel."

It shows that a long-horizon creative project can be managed as an auditable workflow:

- messy legacy material can be staged into a structured project;
- project-memory problems can be repaired before prose editing starts;
- agent-facing context can be scoped instead of dumping the whole project into a model;
- style and pacing signals can be turned into human review decisions;
- publish artifacts can be generated and gated reproducibly;
- the system can leave evidence after each pass.

This is why FictionOps is best described as a workflow harness, not an autonomous author.

## Agent Research Framing

For agent research, this case study maps naturally to several problems:

- long-context task decomposition;
- external memory maintenance;
- human-in-the-loop revision;
- scoped context selection;
- safe output staging;
- workflow recovery and refusal to overwrite;
- evaluation beyond single-turn answer quality;
- domain-specific gates for creative work.

The project is not tied to one model provider. FictionOps itself does not call a model. It prepares bounded task bundles and lets an external runner or controller call OpenAI, local model servers, or other APIs.

## Failure Modes Avoided

The dogfood run deliberately avoided several tempting shortcuts:

- global replacement of repeated words;
- padding chapters to hit a uniform target length;
- marking static audit warnings as literary truth;
- letting an agent overwrite source drafts;
- claiming the sustained dogfood cycle accepted before the seven-day window ends;
- exposing private story text in public evidence.

## Current Limits

The case study is still one private long-form project. It does not prove generality across all genres, languages, or teams.

Remaining limits:

- literary quality still requires human judgment;
- some audits are heuristic and intentionally conservative;
- the public repository contains redacted evidence, not the private manuscript;
- the sustained dogfood cycle remains deferred until the maintenance window closes;
- richer agent-runner comparisons would require repeated experiments across multiple models and controllers.

## Reproducible Evidence Trail

Related public evidence:

- [Sustained dogfood cycle evidence](dogfood-cycle-evidence.md)
- [Real-project adopt dogfood report, Chinese](dogfood-legacy-adopt.zh-CN.md)
- [Agent evaluation protocol](agent-evaluation.md)
- [Agent workflow positioning](agent-workflow.md)
- [End-to-end migration and publishing case](end-to-end-migration-publish.md)

The public record is intentionally evidence-oriented. It documents what commands were exercised, what gates changed, and what remains deferred, while keeping private creative content out of the repository.
