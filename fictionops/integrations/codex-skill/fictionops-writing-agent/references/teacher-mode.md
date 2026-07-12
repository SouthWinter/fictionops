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

For a review decision, keep evidence types separate:

```json
{
  "schema": "fictionops.teacher_decision.v1",
  "task_id": "stable-task-id",
  "decision": "uphold",
  "category": "prose_reader_experience",
  "severity": "P4",
  "scope": "one bounded location and claim",
  "problem": "the surviving defect",
  "manuscript_evidence": ["verbatim target text without added quote marks"],
  "authority_evidence": [
    {"source": "path/to/authority.md", "support": "rule or state used in judgment"}
  ],
  "strongest_counterevidence": "the strongest reason the finding may be wrong",
  "countercheck_effect": "how that reason changed the verdict, scope, or confidence",
  "resolution_reason": "why the residual claim survives or is withdrawn",
  "preserve_constraints": ["material that a later repair must not damage"],
  "suggested_action": "a bounded future action or no action for withdraw",
  "confidence": 0.8,
  "manuscript_edited": false,
  "teacher_ground_truth": false
}
```

Use this exact top-level shape for the required fields. Use `P0` through `P5` for `severity`. Do not nest the decision under `finding`, rename `suggested_action`, or duplicate evidence at multiple levels. Do not emit legacy `evidence`. `authority_evidence` may paraphrase its support, but every item must identify its source; `manuscript_evidence` must remain verbatim.

Before finalizing the decision:

1. Run `scripts/verify_teacher_evidence.py <frozen-source> <decision.json>`.
2. Require every `manuscript_evidence` item to match after whitespace normalization only, require typed `authority_evidence`, and reject a legacy `evidence` field.
3. Record the verifier artifact or result in `trajectory.jsonl` under the verification layer.
4. If verification fails, stop and correct the evidence source or downgrade the claim. Never strip punctuation automatically to make a quote pass.

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
