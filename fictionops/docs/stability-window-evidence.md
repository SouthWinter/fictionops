# Stability Window Evidence

This file records the compatibility/stability window required before FictionOps can claim a 1.0 stable core. It is not a substitute for tests, release evidence, or dogfood evidence; it records that those surfaces stayed stable over a real maintenance window.

## Instructions

- Fill this record after a real compatibility window, not at the start of one.
- Use `YYYY-MM-DD` for start/end dates; the end date must not be earlier than the start date, and the window must cover at least 7 calendar days.
- Release and dogfood references must point to concrete evidence files, run URLs, or recorded artifacts; vague notes cannot close the window. Local Markdown evidence-file references are checked for existence and must themselves pass `audit-release-evidence` or `audit-dogfood-cycle`.
- Local Markdown evidence-file references must stay inside the audited target checkout; do not close a stability window by pointing at accepted files from another local sandbox or temporary directory.
- URL references must be complete `https://...` URLs with a host and should point to a concrete run, artifact, release, dogfood, or evidence record; bare `http`, non-HTTPS URLs, and generic home-page links are not accepted.
- Run `fictionops audit-stability-window . --file docs/stability-window-evidence.md`, then `fictionops audit-stable-core . --stability-file docs/stability-window-evidence.md`, before using the record as 1.0 evidence.
- Use `Decision: accepted` only when compatibility notes, breaking-change notes, and recovery notes have been reviewed by a named human reviewer.

## Record

- Window ID:
- Start date:
- End date:
- Version range:
- Release evidence reference:
- Dogfood cycle reference:
- Compatibility notes:
- Breaking changes:
- Recovery notes:
- Decision: deferred
- Reviewer:

## Decision Meanings

- `accepted`: stable surfaces remained compatible or every breaking change had a documented migration path.
- `deferred`: the window is not complete or has not been reviewed.
- `failed`: a compatibility or recovery regression was found and must be fixed before 1.0.
