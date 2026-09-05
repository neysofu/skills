---
name: deep-code-review
description: Exhaustive PR review of behavior, runtime risks, code quality, tests, and documentation, incorporating every repository lint.
disable-model-invocation: true
---

# Deep Code Review

Be relentless. Treat the first plausible reading as the start of the investigation. Seek counterexamples, follow consequences across boundaries, and challenge both the implementation and your own conclusions. Finding a serious bug is no reason to stop looking. Passing tests are evidence about the cases they exercise, not a verdict on the change.

> What can this change break, misrepresent, or make unnecessarily difficult—and what evidence would prove or disprove it?

Review by default. Apply the linked lints as audit criteria, including those written as authoring guidance. Modify the reviewed work only when the user asks for fixes.

## Establish the review

Resolve the requested comparison and record the base and head revisions. For a PR, use its merge-base unless the user specifies another comparison. For work in progress, include staged, unstaged, and relevant untracked changes. Read every changed artifact, including deletions, configuration, tests, and documentation; inspect generated changes through their source and generation path.

Read the governing repository instructions and obtain the intended behavior from the user's request, acceptance criteria, and available issue or specification. Distinguish stated requirements from inferred intent. If a requirement is unavailable, review against established contracts and identify the uncertainty.

Maintain a compact coverage record of changed areas, affected boundaries, lint applicability, and unresolved questions. Use it to prevent omissions as the investigation expands. Reading a file is not completion: account for what its changes mean.

## Trace behavior and consequences

For each meaningful change, reconstruct the behavior before and after it. Trace inputs through validation, state transitions, side effects, outputs, and consumers. Read callers, callees, sibling implementations, and tests outside the diff wherever they establish a contract or consequence. Check interactions among changes that look correct in isolation.

Investigate the concerns that the affected path exposes:

- **Correctness and contracts:** valid and rejected inputs, boundary cases, missing requirements, changed defaults, error behavior, and compatibility with existing callers or persisted data.
- **Runtime and resources:** concurrency, ordering, cancellation, partial failure, retries, cleanup, ownership, and resource growth. Trace adverse interleavings and failure points rather than assuming the happy path.
- **Security and operations:** trust and authorization boundaries, sensitive data handling, deployment and migration order, recovery, and whether diagnostics make failures actionable.
- **Performance:** changed work, allocations, I/O, contention, and scaling under plausible workloads. Establish the cost mechanism before claiming a regression.
- **Design and maintainability:** whether the same required behavior can be achieved with fewer independent rules, simpler control flow, clearer ownership, or an established repository pattern. Explain the concrete improvement and its tradeoffs.

These are investigation prompts, not a limit on findings. Follow any additional concern supported by the change. Compare tests and documentation against independently established behavior; they can repeat the implementation's mistake.

## Apply every lint

Read all of the following files directly. Paths are relative to this skill's directory, not the repository under review. Apply each lint's governing test and evidence requirements to the review scope; use the reporting format below to combine results.

- [lint-callee-docs/SKILL.md](../lints/lint-callee-docs/SKILL.md)
- [lint-reinvention/SKILL.md](../lints/lint-reinvention/SKILL.md)
- [lint-residue/SKILL.md](../lints/lint-residue/SKILL.md)
- [lint-rust-invariants/SKILL.md](../lints/lint-rust-invariants/SKILL.md)
- [lint-state-space-expansion/SKILL.md](../lints/lint-state-space-expansion/SKILL.md)
- [lint-technical-prose/SKILL.md](../lints/lint-technical-prose/SKILL.md)
- [lint-test-signal/SKILL.md](../lints/lint-test-signal/SKILL.md)
- [lint-vocabulary/SKILL.md](../lints/lint-vocabulary/SKILL.md)

Account for every lint in the coverage record: applied with findings, applied without findings, or inapplicable with a reason. Rust invariants applies only to Rust. A lint's clean result does not replace the broader behavior review.

## Challenge each candidate

For each suspected issue, identify the triggering input, state, or maintenance task and trace it to a concrete consequence. Look for evidence that defeats the concern: an earlier guard, a stronger type, a caller guarantee, an intentional contract, or a justified tradeoff. Resolve competing explanations before promoting a suspicion to a finding.

Run focused checks or small reproductions when they can settle a question. Verify both the behavior exercised and the assertions; a successful command alone does not resolve a semantic concern. Record unavailable checks and their effect on confidence. Continue investigating unresolved candidates while relevant evidence remains accessible.

Quality findings need a concrete benefit, such as removing duplicated authority, preventing a misleading explanation, or simplifying an invariant while preserving required behavior. Keep subjective preferences out of the findings. Establish whether each issue was introduced, worsened, or merely exposed by this change; separate relevant pre-existing issues.

## Complete and report

Finish only when every changed area and affected contract has been examined, every lint has a disposition, and every candidate is supported, disproved, or explicitly unresolved because of missing evidence. Recheck the reviewed revisions and working-tree scope; account for intervening changes before claiming coverage. Stop with an explicit partial-review status if these conditions cannot be met.

Report all supported, actionable findings, ordered by consequence. Merge duplicate root causes while retaining distinct effects. For each finding, give a precise file and line, classify it as a defect or quality improvement, explain the trigger and consequence with evidence, and state a bounded correction. Distinguish required behavior fixes from improvements that preserve behavior.

End with a concise coverage and validation summary, including unresolved questions and limitations. A complete investigation can return zero findings. Claim only the coverage and confidence the evidence supports.
