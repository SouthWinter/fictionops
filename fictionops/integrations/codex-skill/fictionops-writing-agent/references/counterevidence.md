# Counterevidence Reference

Use this workflow when a reviewer finding is plausible but not sufficiently grounded, or when the proposed repair may violate author intent.

## Resolve The Finding

1. Export disputed findings into an anonymous packet and keep control identity separate.
2. Record the human annotation: `uphold`, `withdraw`, or `insufficient`, plus grounding and repair-harm risk.
3. Escalate `insufficient` findings at the claim's real scope:
   - Local wording: exact quote and neighboring paragraph.
   - Adjacent rhythm: neighboring paragraph window.
   - Knowledge source: character memory, canon boundary, and relevant adjacent state.
   - Character behavior: stable profile, relationship state, and active guards.
   - Chapter function: one complete deduplicated chapter.
4. Reverify independently. Interpret verdicts against the original finding:
   - `uphold`: the defect remains after new evidence.
   - `withdraw`: new evidence disproves or closes the alleged gap, or the repair violates an active guard.
   - `still_insufficient`: the requested evidence remains missing or indirect.
5. Require at least one exact quotation from the model-visible evidence window for a resolved verdict.
6. Apply only machine state to the ledger. Do not edit prose during escalation or re-verification.

## Revise A Grounded Uphold

1. Prepare a minimal reviser bundle containing only grounded open upholds, exact evidence, active guards, and the unchanged chapter.
2. Verify the staged candidate with deterministic preflight first.
3. Send only the issue contract and complete diff to the model verifier after preflight passes.
4. Use local `old_quote -> new_quote` repair for a narrow introduced regression.
5. Stop at `ready_for_approval`; require the author's explicit accept action.

## Refuse False Closure

- Do not let model confidence replace an exact quote.
- Do not treat a scope-limiting guard as proof that the quoted prose is correct.
- Do not call evidence that supplies a missing source an `uphold`; it closes that original gap and therefore supports `withdraw`.
- Do not reuse hidden benchmark labels as issue-level truth.
