# Codex Skill Cross-Chapter Generalization

This forward test evaluates the FictionOps Codex skill on three frozen, full-length chapters with different functions:

- high-pressure action and a first irreversible killing;
- translation, captivity, pricing, and information boundaries;
- relationship-bearing quiet pressure before a concealed reversal.

Each run received only the frozen chapter, a task contract, a minimal authority context pack, and a source manifest. Fresh Codex agents loaded the skill and wrote a typed teacher decision plus trajectory. Separate blind evaluators then judged the selected finding without loading the skill or seeing other cases.

## Results

| Case | Initial blind verdict | Initial score | Revised blind verdict | Revised score |
|---|---|---:|---|---:|
| Action | withdraw | 9.5/15 | uphold | 14/15 |
| Translation | uphold | 12.5/15 | uphold | 14/15 |
| Relationship | withdraw | 11/15 | uphold | 15/15 |
| **Mean** | 1/3 upheld | **11.0/15** | 3/3 upheld | **14.33/15** |

The first pass exposed two failures. The skill treated a coerced, non-instrumental action as if the character needed to predict its utility, and it selected a local prose-restraint concern while missing a stronger viewpoint-contract violation. Decision JSON also drifted between flat and nested shapes.

The revision added:

- chapter-affordance counterevidence for action, translation, and relationship-bearing chapters;
- a mandatory P0-P2 scan before finalizing P3-P5 findings;
- withdrawal when counterevidence defeats a claim's necessary premise;
- one canonical top-level teacher-decision contract;
- deterministic verification for exact manuscript evidence, typed authority evidence, boundary flags, numeric confidence, and P0-P5 severity.

The revised action finding no longer demanded a mature rescue calculation. The relationship case elevated the explicit viewpoint-contract violation above local style concerns. The translation case retained only a low-severity, locally grounded legibility problem. All revised runs passed deterministic evidence verification and preserved the frozen source hashes.

## Claim Boundary

This is a three-case, one-sample-per-condition forward test scored by independent model reviewers. It supports the mechanism claim that the skill can improve candidate ranking, counterevidence use, and output stability across unlike chapter functions. It does not establish literary ground truth, human acceptance rate, cross-model transfer, or broad statistical generalization.
