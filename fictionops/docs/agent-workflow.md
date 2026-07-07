# Agent Workflow Positioning

This document answers a narrow but important question: once FictionOps is connected to AI or a model API, does FictionOps itself count as an agent workflow?

Short answer: **FictionOps core is not an agent. Connected to a model API through a runner, it is an API-backed AI workflow. Connected to a controller that can choose safe next steps and call runners in a loop, the whole setup becomes an agentic workflow.**

## The Boundary

FictionOps core does four things:

- prepares scoped context;
- packages bounded tasks;
- records staged outputs;
- runs gates and audits before manuscript or canon changes are accepted.

External runners and controllers sit outside FictionOps core:

- reads a task bundle;
- calls a model API, local model server, script, or other tool;
- writes a staged response;
- optionally asks FictionOps for the next safe command.

The useful distinction is:

| Setup | What It Is | Why |
| --- | --- | --- |
| FictionOps with no AI call | workflow toolkit | It structures and audits a project, but no model acts. |
| Human copies `context-pack` into a chat | AI-assisted workflow | The human chooses the task and applies results. |
| `agent-run` + external API/model runner + `agent-inbox` | API-backed AI workflow | A runner calls a model or service for a scoped task, and FictionOps captures the result for review. |
| `audit-agent-workflow` before connecting a runner/controller | preflight gate | FictionOps checks project shape, staged-output state, model configuration, and controller boundaries before automation starts. |
| `agent-next` + external controller | agentic workflow | A controller can select safe next steps from project evidence; when pointed at the FictionOps package checkout, it selects from stable-core governance action items instead of treating the repository as a novel to adopt. |
| Controller loops through multiple steps but keeps staged outputs and gates | bounded agentic workflow | Automation can advance work, but authority remains outside model output. |
| Model directly overwrites manuscript/canon | outside FictionOps safety contract | It bypasses staging, review, and gates. |

## Why This Matters

Many writing tools become fragile when they connect to AI because the model sees too much, forgets too much, or acts with too much authority. FictionOps tries to split that problem into visible layers:

- **Context scope:** the runner receives only the files needed for the task.
- **Role boundary:** the prompt says whether the model or tool is drafting, auditing, planning, or publishing.
- **Staging boundary:** output lands beside the task bundle, not inside the manuscript.
- **Gate boundary:** review commands decide whether the project is ready for the next step.
- **Human authority:** a person decides what becomes canon or published text.

That means FictionOps is not competing to be a "better novelist agent." It is the operating layer that lets model APIs, local tools, human collaborators, and controllers participate without silently breaking a long project.

## Practical Answer

If you connect an AI model only as a helper for one command, call the setup **AI-assisted FictionOps**.

If you connect an external runner that receives task bundles, calls an API or local model, and returns staged outputs, call it an **API-backed FictionOps workflow**.

If you connect a controller that reads `agent-next` JSON, chooses commands, invokes runners, and chains multiple steps, call it a **FictionOps agentic workflow**. For a normal writing project, `agent-next` chooses from migration, inbox, chapter, revision, and publishing steps. For the FictionOps package itself, it chooses from stable-core evidence action items and stops on external release, dogfood, or stability-window work that cannot be fabricated locally.

Before connecting either one, run `fictionops audit-agent-workflow <project> --level runner`, `--level controller`, or `--level model-runner` to check whether the project is ready for that integration level. When the target is the FictionOps package checkout itself, `audit-agent-workflow --level controller` uses the same package-governance boundary as `agent-next`: it reports stable-core evidence action items and stops at human-review boundaries instead of recommending `adopt`.

If you let a model edit canon or manuscript directly without staging and gates, do not call that FictionOps-compatible automation. It may still be useful experimentation, but it is outside the core safety model.

For setup commands and runner/controller patterns, see [Agent integration guide](agent-integration.md).
