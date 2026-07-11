# FictionOps Testing Guide

FictionOps uses Python standard-library `unittest`. The goal is to protect workflow contracts, CLI behavior, package contents, and migration safety. The test suite is not a literary-quality judge.

## Run The Tests

From the repository root:

```bash
python -m unittest discover -s fictionops/tests -v
```

Run only `test_cli.py`:

```bash
python -m unittest discover -s fictionops/tests -p test_cli.py -v
```

Run tests whose names contain a substring:

```bash
python -m unittest discover -s fictionops/tests -p test_cli.py -k release_smoke -v
```

## Current Coverage

The current suite covers 62 CLI commands and 164 regression tests. It checks:

- every CLI help entry;
- CLI contracts and documentation coverage;
- project initialization;
- book and chapter scaffolding;
- chapter planning, scene planning, and draft briefs;
- post-draft, review, book, and release gates;
- stats, word scans, table checks, style, wave, continuity, echo, information, and character audits;
- migration diagnostics with `adopt`;
- sandbox copy with `adopt --copy-to`;
- post-copy review with `adopt-review`;
- explicit migration waivers for deferred adopt-review blockers;
- grouped migration cleanup with `adopt-plan`;
- import queue sorting with `import-plan`;
- unified `agent write|revise|accept|continue`, agent prompt, connector kit generation, reproducible agent harness evaluation, connector smoke tests, run, exec, inbox, closed-loop revision verification, hash-guarded revision acceptance, session-aware safe continuation, guided AI setup, agent workflow preflight audit, no-model controller loop workflows, OpenAI-compatible Chat runner v1 presets/env-file wiring, and OpenAI Responses runner dry-run wiring;
- persistent issue identity, cross-session merge/reopen, explicit waive/reject decisions, stable author guard create/update/retire history, preservation-aware reviewer withdrawal/counterevidence, anonymous counterevidence packet/key isolation and scoring, deterministic evidence escalation/deduplication, grounded model-backed escalated re-verification, hash-guarded counterevidence ledger application with machine-only states, minimal `agent-exec` reviser bundles containing only grounded open upholds, independently grounded candidate verification, bounded-change and hash-drift refusal, explicit atomic acceptance, controller routing across open/blocked/withdrawn counterevidence, and anonymous information-boundary/character/prose high-risk reviewer fixtures;
- phase checkpoints with artifact hashes, explicit session cancellation, duplicate-cancel refusal, and cancelled-session controller boundaries;
- runner receipt parsing, token/cost aggregation across resume segments, and observed token-budget stops before the next model call;
- unified trajectory steps for attributed context, paired model calls, state transitions, and author authority;
- table-driven deterministic controller policy, repeated raw/RAG/full/ablation benchmarking, positive/negative controls, blind-review packet isolation, prompt-answer isolation, and seven bounded failure-injection scenarios;
- model config and context packs;
- structured quantity/time/object fact ledgers, state-aware scene-by-scene chapter assembly, evidence-routed selective scene rewriting, and hard model-call budget stops;
- clean Markdown, metadata, manifest, EPUB export, and EPUB audit;
- release, dogfood-cycle, stability-window, and stable-core evidence auditing;
- demo project workflow;
- legacy migration example workflow;
- packaging, source install smoke, built-wheel install smoke, sdist contents, English CLI contracts, CI governance, and release documentation.
- package release evidence auditing, including unfinished templates and filled external records.
- sustained dogfood-cycle evidence auditing, including unfinished placeholders and filled accepted cycles.
- stable-core evidence aggregation, including current external gaps and a complete accepted evidence set.

## Testing Principles

- Use temporary directories. Tests must not write into a real writing project.
- Test contracts before formatting. For example, engine files must not be counted as chapter prose.
- Cover both core functions and CLI subprocess behavior when adding a command.
- Do not encode aesthetic judgment as a test.
- Preserve safety boundaries: migration source folders are read-only unless copied, and agent outputs stay staged.

## Adding A Command

When adding a CLI command, include at least:

- a direct core-function test;
- a CLI subprocess test;
- JSON output validation with `json.loads` if the command supports JSON;
- an empty, invalid, or failure case;
- a no-overwrite case, unless the command is read-only;
- a path or text case that exercises Unicode project material where relevant.

If the command changes package contents, update:

- `MANIFEST.in`;
- sdist content tests;
- CI and publish workflow package checks;
- release notes, completion audit, and roadmap when the change affects release evidence or next-stage acceptance criteria.

## Local Release Validation

Before cutting a release candidate locally:

```bash
python -m compileall -q fictionops/src fictionops/examples
python -m unittest discover -s fictionops/tests -v
python -m pip wheel ./fictionops -w fictionops/dist --no-deps --no-build-isolation
python -c "import os, pathlib, setuptools.build_meta as b; os.chdir('fictionops'); pathlib.Path('dist').mkdir(exist_ok=True); print(b.build_sdist('dist'))"
```

Then install the wheel in a clean virtual environment and check:

```bash
fictionops --version
python -m fictionops --version
fictionops init smoke-novel --title "Smoke Novel"
fictionops doctor smoke-novel
```
