# Interview Brief: FictionOps

Use this brief when explaining FictionOps in an agent research or applied AI engineering interview. It is intentionally short and evidence-oriented.

## 60-Second Pitch

FictionOps is an AgentOps-style workflow harness for long-form fiction projects. It is not a one-click novel generator and it is not an autonomous author. The core problem is long-horizon project maintenance: a large story has evolving outlines, canon, character memory, information boundaries, revision history, model handoffs, and publish artifacts.

FictionOps turns that into a file-based workflow with CLI audits, scoped context packs, staged agent outputs, revision plans, gates, and release artifacts. The model or API runner can propose bounded outputs, but FictionOps keeps source authority with the human: outputs go to an inbox, audits surface risks, and gates decide whether the project is ready for the next step.

I dogfooded it on a private million-character-scale novel project. The run repaired project memory, synchronized 33 planned chapters with drafts and engines, converted style warnings into human reader-review decisions, completed bounded prose passes, and generated clean Markdown, metadata, manifest, EPUB, and release-gate evidence with no blocking issues.

## What To Emphasize

- This is a workflow harness, not a writing model.
- The research problem is long-horizon agent control under persistent external state.
- The domain is fiction, but the technical pattern generalizes to complex projects with evolving memory and human review.
- The main contribution is not automatic prose generation; it is scoped context, staged output, auditability, recovery, and gates.
- The public repository redacts private manuscript content and keeps only workflow evidence.

## Concrete Evidence

Private dogfood run highlights:

- `adopt-review`: `ready=true`, `blocking_issue_count=0`.
- `audit-info`: 8 information-release rows, `issues=0`.
- `audit-characters`: 8 character arcs, 8 intelligence profiles, 8 voice profiles, `issues=0`.
- `audit-plan`: 33 planned chapters, 33 drafts, 33 engines, 33 synced engines, `issues=0`.
- `audit-echoes`: 3 active longline threads, `issues=0`.
- Style watch total moved from 3843 to 3770 after bounded reader-experience prose passes.
- `audit-publish`: 33 clean chapters matched 33 drafts, `issues=[]`.
- `audit-epub`: `epub_valid=true`, 33 chapters, `issues=[]`.
- `book-gate`: `Ready: yes`, blocking issues 0.
- `release-gate`: `Ready: yes`, blocking issues 0.

Public evidence:

- [Dogfood case study](dogfood-case-study.md)
- [Sustained dogfood cycle evidence](dogfood-cycle-evidence.md)
- [Agent evaluation protocol](agent-evaluation.md)
- [Research positioning](research-positioning.md)
- [Evaluation plan](evaluation-plan.md)
- [Agent workflow positioning](agent-workflow.md)

## Architecture Talking Points

FictionOps has four layers:

1. **Project memory:** Markdown, YAML, and JSON files for structure, canon, characters, drafts, audits, and publishing.
2. **Audits and gates:** commands such as `audit-info`, `audit-characters`, `audit-plan`, `audit-wave`, `revision-plan`, `book-gate`, and `release-gate`.
3. **Agent boundary:** `context-pack`, `agent-run`, `agent-exec`, `agent-inbox`, `agent-next`, and `eval-agent`.
4. **Publishing:** `export-clean`, `export-metadata`, `export-manifest`, `export-epub`, `audit-epub`.

The important safety contract is that model output is staged, not directly applied to canon or manuscript.

## Likely Interview Questions

### Is FictionOps an agent?

FictionOps core is not an agent. It is a workflow harness. Connected to an external runner that calls a model API, it becomes an API-backed AI workflow. Connected to a controller that reads project state, chooses safe next steps, invokes runners, and stops at gates, the whole setup becomes an agentic workflow.

### Why use fiction as the domain?

Long fiction is a strong long-horizon benchmark. It has huge context, hidden knowledge states, continuity constraints, subjective quality, revision history, and publish artifacts. It exposes failure modes that short coding or QA tasks often hide: forgotten promises, premature reveals, flattened style, and unsafe edits to source-of-truth files.

### How is this different from RAG?

RAG retrieves context for a model call. FictionOps manages the whole workflow around context: what files are durable memory, what belongs in the current task pack, where output is staged, which audits run after the task, and which gates block release. Retrieval could be one component, but it is not the whole system.

### How is this different from LangGraph, AutoGPT, or CrewAI?

Those are general agent orchestration frameworks. FictionOps is a domain-specific harness and evaluation surface for long-form fiction maintenance. It can be connected to external runners or controllers, but its core value is the durable project state, audits, gates, and publish pipeline.

### What was technically hard?

The hardest part was turning messy human writing work into stable machine-checkable boundaries without pretending that static checks equal literary judgment. For example, a high count of a word is not automatically a bug. FictionOps must surface it as a reading prompt, then preserve the human decision about whether it matters.

### How do you evaluate it?

I use workflow reliability metrics rather than automatic literary scoring: blocking issue count, synchronized chapter coverage, audit issue deltas, staged-output rate, gate readiness, publish artifact validity, and whether the system stops at human-review boundaries. The private dogfood run is one evidence trail; a broader research version would compare raw chat, direct-write agents, FictionOps runners, and FictionOps controllers.

### What are the limits?

The current evidence is from one private large project plus public demo fixtures. The audits are heuristic and conservative. FictionOps does not solve artistic judgment. The sustained dogfood cycle is still deferred until the full maintenance window closes. Richer claims require repeated runs across more projects and model/controller configurations.

## Resume Bullet

Built FictionOps, an open-source AgentOps-style workflow harness for long-form fiction projects, with structured project memory, scoped context packs, staged agent outputs, audit gates, revision planning, and publish/export pipelines. Dogfooded it on a million-character-scale novel project to study long-horizon consistency, controllable agent handoff, and human-in-the-loop revision workflows.

## What Not To Claim

- Do not claim FictionOps is a fully autonomous novelist.
- Do not claim literary quality can be automatically scored.
- Do not claim the private dogfood cycle is accepted before the seven-day window closes.
- Do not expose private manuscript text or unreleased story details.
- Do not frame it as a generic Python publishing tool.
