# Teacher Mode Reference

Use teacher mode to produce a high-quality reference trajectory for diagnosing or improving an API agent. Do not present the teacher as ground truth.

## Freeze The Comparison

Keep the task, project snapshot, source hashes, model-visible evidence, budgets, and acceptance contract fixed. Separate hidden controls from both teacher and student inputs. Record any tool or context advantage the teacher has.

## Produce The Reference Trajectory

Preserve FictionOps runtime artifacts and summarize each consequential decision with:

- `observation`: directly observed state or quotation.
- `source`: path/artifact, hash when available, authority, and selection reason.
- `hypothesis`: defect, causal explanation, or next-state prediction.
- `action`: command or edit attempted.
- `expected_transition`: state expected after the action.
- `result`: actual state and verification evidence.
- `counterevidence`: strongest reason the action might be wrong.
- `alternatives`: viable actions rejected and why.
- `authority`: model, deterministic gate, canon, or author.
- `stop_reason`: continue, blocked, budget, stale state, or author review.

Use `trajectory.jsonl`, context manifests, runner receipts, diffs, verifier reports, and issue history as the factual backbone. Clearly mark any retrospective explanation added by Codex.

## Teach Decisions, Not Prose

Compare teacher and student on:

- Task classification and next-action choice.
- Evidence source and scope selection.
- Causal or character-state simulation.
- Finding precision and counterevidence handling.
- Repair scope and regression rate.
- Grounding, budget use, recovery, and stop behavior.

Do not train or score only on final chapter similarity. Multiple strong chapters may differ lexically while sharing correct state transitions and authority discipline.

## Generate Useful Feedback

For each student failure, assign the earliest responsible layer:

1. Observation/state reconstruction.
2. Retrieval or authority ranking.
3. Planning/causal simulation.
4. Tool or model execution.
5. Verification/grounding.
6. Controller stop or authority boundary.

Give one minimal corrective rule and one counterfactual example. Avoid replacing the student output with the teacher answer when diagnosis is sufficient.

## Protect Evaluation Integrity

- Require author confirmation or deterministic support before promoting a teacher judgment to a label.
- Freeze the teacher contract before held-out evaluation.
- Keep teacher traces, expected verdicts, and post-hoc critiques out of student prompts.
- Report provider, model, context/tool asymmetry, repetitions, variance, and human review effort.
- Preserve failed teacher trajectories; do not publish only successful demonstrations.
