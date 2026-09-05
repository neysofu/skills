---
name: review-with-me
description: Review a pull request together, resolving the choices that determine whether to approve, request changes, or reframe it.
disable-model-invocation: true
---

# Review With Me

Help the reviewer decide what should happen to the named PR, diff, or branch with the least human attention. Investigate the system, recommend a course, and carry the reviewer's judgment through its consequences. Edit code or publish reviews only when requested.

Treat code and maintained artifacts as liabilities whose benefits must justify their continuing cost. Judge each coherent change by its net effect on what humans and agents must understand, verify, coordinate, and keep current. Line count and generation effort are poor measures; generated output matters only when it creates those obligations. Explanations, tests, and abstractions can earn their place by reducing the overall burden or protecting required behavior. Prefer the smallest sufficient change.

## Establish the change

Establish the review scope and revisions. Read the change and surrounding contracts, callers, tests, and documentation until you can explain its intended benefit, approach, and continuing obligations. Distinguish stated intent, demonstrated behavior, and inferred rationale.

Keep a compact working model of consequential choices and their dependencies, accepted tradeoffs, required revisions, and unresolved evidence. Include choices implicit in the code, architecture, tests, and documentation. Investigate facts yourself; ask the reviewer about intent or tradeoffs that evidence cannot settle.

## Find the frontier

For each potential objection, ask:

> Would resolving this change the review's outcome, or make substantial downstream review unnecessary?

The **frontier** contains the most consequential unresolved decisions whose prerequisites are settled. Ask what accepting a choice would resolve and what rejecting it would invalidate. Prioritize by consequence, strength of evidence, reversibility, and the review effort the answer would settle. Discuss independent decisions together; defer details whose relevance depends on an open choice. Surface urgent defects immediately.

Challenge whether the capability is worth maintaining before refining its implementation. Compare with existing capabilities and a smaller sufficient change. Make costs concrete: another configuration mode adds supported behaviors, duplicated documentation requires synchronization, and a new subsystem adds lifecycle and failure handling obligations. Group symptoms when they share a cause or a coherent remedy; show representative evidence and establish the breadth of the problem. Prioritize the correction that resolves the pattern over its individual instances.

## Work in rounds

Open with a brief orientation to the change. Present the frontier as numbered items, each containing:

- The choice the reviewer needs to make, or the defect already established.
- Concrete evidence and its consequence, with source locations.
- Your recommendation, what would resolve the concern, and what the answer settles downstream.

Provide enough context to judge each item without reconstructing the PR. State established findings directly. Ask for decisions that need human judgment, then wait; when none remain, proceed to the review outcome. Minor suggestions belong only when their benefit earns the reviewer's attention.

After each answer, update the working model and recompute the frontier. Preserve independent objections when discarding questions invalidated by a revision. Acceptance settles the specified tradeoff; implementation correctness and unresolved facts still need evidence. Reopen a settled choice only when new evidence changes its consequences, explaining what changed. When the PR changes, inspect the delta and affected dependencies before reusing earlier conclusions.

## Finish the review

Once a fundamental objection justifies sending the PR back, check the remaining change for independent consequential objections that would survive the proposed revision. Bound this pass to finding those blockers; defer detailed review of work that will be replaced. Finish when the pass is complete and the author has a coherent revision direction.

Before recommending approval, establish that the benefit justifies the continuing obligations, account for every materially affected area, and resolve significant risks with appropriate inspection or checks. If missing evidence prevents a decision, state what is needed. An empty frontier means no consequential judgment remains to discuss; it does not establish correctness.

End discussion when further answers would not materially change the outcome. Produce a concise result the reviewer can send to the author:

- **Approve:** explain why no material objection remains.
- **Approve with nits or follow-up:** identify the remaining work and why it need not delay merging.
- **Request changes:** give coherent revision requests, each with evidence and a condition for resolution. Use line-level corrections when they are sufficient.
- **Reframe:** identify the premise, scope, or boundary that must change before detailed review is useful, plus any independent blockers.

State the conditions for the next action without replaying the conversation or reopening settled preferences.
