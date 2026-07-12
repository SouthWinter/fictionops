# Audit Reference

## Order Findings By Risk

1. Canon, continuity, quantity, time, object, or physical-state contradiction.
2. Character knowledge leak, premature reveal, or viewpoint violation.
3. Causal gap hidden by explanatory narration.
4. Character voice, age, region, relationship, or intelligence-mode drift.
5. Chapter function, pacing, and long-line echo failure.
6. Repeated prose templates, over-regularity, and reader-experience friction.
7. Packaging and release issues.

Before finalizing a P3-P5 finding, explicitly check whether any P0-P2 candidate is better grounded and more consequential. A local prose issue cannot be the requested single strongest finding while a verified viewpoint, knowledge, causality, or character-contract violation remains open.

## Match Evidence Scale

- Use an exact line for a local wording claim.
- Use neighboring paragraphs for rhythm or repeated syntax.
- Use character memory and canon for knowledge or voice claims.
- Use the whole chapter for chapter function or distributed repetition.
- Use adjacent chapters, outline, or echo records for long-line continuity.
- Use an active author guard for author intent; reviewer-created preserve text is not author authority.

Do not uphold a broad claim from a narrow excerpt. Do not request a whole chapter for a uniquely anchored local defect.

## Separate Observation From Judgment

Record:

- Observable text or state.
- The inferred defect.
- Evidence that could disprove it.
- Repair scope and preserve constraints.
- Confidence and remaining gap.

Use `needs_counterevidence` when the disproof evidence is absent. Do not rewrite large sections merely because an audit found a pattern.

## Common Gates

- `review-gate`, `book-gate`, and `doctor` for broad readiness.
- `audit-continuity`, `audit-info`, and `audit-characters` for semantic boundaries.
- `audit-style` and `audit-wave` for deterministic prose/length signals.
- Counterevidence verification for disputed model findings.

Treat deterministic counts as evidence, not literary verdicts.

## Respect Chapter Affordances

- In a high-pressure first action, a character may make a wrong, non-instrumental, irreversible move when perceived options collapse. Do not require the character to know the move will rescue someone, open an exit, or solve the trap. Verify perceived option collapse, not mature utility calculation.
- In translation or captivity, procedural precision still needs a visible source. Distinguish rough inference from unexplained knowledge of a complete cross-station workflow.
- In a relationship-bearing misdirection chapter, repeated objects or interpretations may be doing necessary credibility work. Check viewpoint and knowledge contracts before selecting a local restraint complaint, then preserve the repetitions that make the alternative outcome believable.
- Treat a chapter affordance as counterevidence, not automatic immunity. Uphold only the residual claim that remains independently grounded after the affordance is applied.

## Keep Evidence Typed

- Put verbatim target-text excerpts in `manuscript_evidence`.
- Put rules, canon, outline, character memory, and later echoes in `authority_evidence`, with their source paths.
- Do not add decorative quotation marks to excerpts. Preserve source characters exactly; only Markdown whitespace may be normalized during verification.
- Run `scripts/verify_teacher_evidence.py <source> <decision>` for structured teacher or comparison findings. A failed quotation check blocks promotion of the finding; it does not authorize silently repairing the quote.
- Keep `problem`, `counterevidence`, and `resolution_reason` outside both evidence arrays. Evidence is observed material, not the reviewer conclusion.
