# Dogfood Metrics Reference

Track metrics that show whether the AI workflow improves real long-form writing work.

## Useful Metrics

- Context setup time saved.
- Draft or revision acceptance rate.
- Number of useful audit findings.
- False-positive audit findings.
- Human review time per staged output.
- Continuity issues caught before publication.
- Canon or outline updates required after a chapter.
- Regression count introduced by accepted AI output.

## Evidence Shape

Record:

- Project or sandbox.
- Date and commit.
- Book or project slice.
- Chapter range and focused chapter list.
- Provider and model, without secrets.
- Task type.
- Inputs used.
- Outputs staged.
- Runner or controller path used.
- Human review boundary.
- Human decision.
- Follow-up audits.

Use these notes to evaluate the agent workflow, not to claim that the model autonomously wrote the book.

## Sustained Cycle Evidence

A seven-day dogfood cycle is useful only when it proves cross-day recovery, continuation, and review discipline. Do not stretch a one-day maintenance pass into seven days.

For each cycle, record:

- Day-one baseline commands and issue counts.
- The exact book and chapters touched.
- The AI/API path used, such as `eval-agent`, `agent-run`, `agent-exec`, `agent-inbox`, a real OpenAI-compatible runner, or a controller.
- The staged-output boundary that prevented direct source overwrite.
- Human decisions: accepted, revised, rejected, or deferred.
- Close-day rerun commands and before/after comparison.

Accepted cycle evidence should be able to answer: what book was processed, which chapters changed or were reviewed, what the model/agent did, what the human decided, and whether the same project state remained recoverable after time elapsed.
