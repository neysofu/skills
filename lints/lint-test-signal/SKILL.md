---
name: lint-test-signal
description: Lint tests and test changes for weak, redundant, or brittle signal, then concentrate the smallest effective suite on consequential failures.
disable-model-invocation: true
---

# Test Signal Linter

Lint the user-named scope. Read production behavior, contracts, callers, failure boundaries, and the existing suite deeply enough to rank risk; edit only within the scope.

## Signal test

Begin with the behavior, not the current tests. Identify plausible failures in contracts, invariants, state transitions, trust boundaries, durable data, policy, recovery, and concurrency; rank them by consequence and likelihood. Complexity, changed lines, coverage gaps, review requests, and past bugs are evidence about where to look, not reasons to create tests.

For each existing or proposed test, ask:

> Is this the cheapest decisive signal for a consequential, plausible failure?

Decisive signal fails for a plausible wrong implementation and passes across permitted refactors. Its expected result comes from the contract, domain, or another independent oracle—not from reimplementing the system under test. It protects a risk not already covered more directly, and its confidence is worth its runtime, brittleness, and maintenance cost.

Use the lowest-cost test layer that still exercises the risk. Prefer strengthening an existing test over adding one, representative equivalence classes over enumerated cases, and stable outcomes over private state or incidental call sequences. Interaction assertions belong when the interaction is the contract; mocks should isolate irrelevant dependencies without mocking away the behavior under test. Snapshots and golden files belong when the whole representation is reviewable contract surface.

Strengthen or remove tests that replay implementation logic, compute expectations through the tested path, assert only their mock setup, exercise trivial language or framework behavior, or survive meaningful breakage. Consolidate tests whose failure signals and protected risks are materially the same. A regression test earns permanence by protecting a current invariant; express that invariant rather than the review or incident that prompted the test.

Fix generated or vendored tests through their authoritative source or update mechanism.

## Modes

- **Audit:** Report each finding as `path:line — Cover|Strengthen|Consolidate|Remove|Report`. For `Cover`, name the consequential failure and cite the production boundary with insufficient evidence. Otherwise name the protected risk, explain why the test's signal is weak or duplicative, and state the smallest valuable result. Omit ordinary retained tests.
- **Fix:** When the user explicitly asks to fix, improve, minimize, or clean the tests, make the smallest high-confidence test diff: strengthen or merge existing signal before adding tests, add only the smallest decisive coverage at the appropriate layer, and remove tests only when the remaining suite protects the same current risks. Preserve production behavior and external contracts. Report product defects, production changes needed for testability, ambiguous risk judgments, and changes outside the named scope.

Use coverage, mutation results, test names, and similarity searches to navigate, never as verdicts. Inspect the implementation and neighboring tests before judging signal.

After fixes, run the narrowest relevant tests and review the diff for unnecessary cases, fixtures, mocks, snapshots, and harness changes. Finish only when each consequential plausible failure in scope has decisive signal or is reported, and every candidate test is retained for a distinct current risk, strengthened, consolidated, removed, or reported for judgment.
