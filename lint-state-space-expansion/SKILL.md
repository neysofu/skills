---
name: lint-state-space-expansion
description: Lint modeled states that no reachable boundary or demonstrated current requirement can produce, then remove or collapse their supporting artifacts.
disable-model-invocation: true
---

# State-Space Expansion Linter

Lint the user-named scope. Read producers, consumers, contracts, tests, and adjacent documentation deeply enough to establish reachability; edit only within the scope.

## Reachability test

For every meaningful state distinction represented by a guard, branch, variant or type member, fallback or recovery path, fixture, test, or explanation, ask:

> What reachable boundary produces this state?

A state is reachable when it can arise from a current public contract or accepted input, persisted or external data, a peer or protocol, concurrency or lifecycle behavior, or demonstrated current compatibility. Rejected input is reachable when a boundary can receive it. Reachability does not require a current internal caller, and rarity does not make a contractually or operationally reachable state expendable.

A merely conceivable state, representable type combination, future consumer, or fabricated fixture is not reachability evidence. A test can demonstrate a state's behavior but cannot establish that production can produce it; trace the whole path to a boundary or current requirement.

Remove an unreachable distinction and the guards, branches, fallbacks, variants, fixtures, tests, or documentation that exist only to support it. Collapse distinctions that can become one without changing behavior for reachable states. Preserve validation and recovery for inputs or failures their boundaries can receive. Fix generated or vendored artifacts through their authoritative source or update mechanism.

Limit findings to excess modeled states; leave missing-case coverage, reachable fallback design, and style unchanged.

## Modes

- **Audit:** Report each finding as `path:line — Remove|Collapse|Report`, identify the unsupported state and the evidence examined for a producing boundary, and state the intended reachable model. Omit ordinary retained states.
- **Fix:** When the user explicitly asks to fix, remove, collapse, or clean the state space, apply high-confidence removals and collapses and align their in-scope tests and documentation. Preserve behavior for reachable states. Leave ambiguous public contracts, intentional robustness at trust boundaries, costly likelihood-versus-value decisions, destinations outside the named scope, and architectural changes as `Report` findings.

Use searches to navigate, then follow each candidate from possible producers through its representation and consumers. Rarity alone does not make a state unsupported.

After fixes, run the narrowest relevant checks and review the diff for orphaned variants, branches, fixtures, tests, and explanations. Finish only when every candidate state is traced to a reachable boundary or current requirement, removed, collapsed into the reachable model, retained as intentional boundary defense, or reported for judgment—and every supporting artifact agrees with that disposition.
