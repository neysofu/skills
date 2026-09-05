---
name: review-with-me
description: Review a pull request together through rounds of potential objections, from architecture and taste to correctness.
disable-model-invocation: true
---

# Review With Me

Build shared judgment with the reviewer about the named PR, diff, or branch. Map its consequential choices as a **decision tree** and work through potential objections in rounds. Your first substantive response is the current frontier for discussion; the review verdict follows that discussion. Edit code or publish reviews only when requested.

Treat code and maintained artifacts as liabilities whose benefits must justify their continuing cost. Judge each coherent change by its net effect on what humans and agents must understand, verify, coordinate, and keep current. Line count and generation effort are poor measures; generated output matters only when it creates those obligations. Explanations, tests, and abstractions can earn their place by reducing the overall burden or protecting required behavior. Prefer the smallest sufficient change.

## Establish the change

Establish the review scope and revisions. Read the change and surrounding contracts, callers, tests, and documentation until you can explain its intended benefit, approach, and continuing obligations. Distinguish stated intent, demonstrated behavior, and inferred rationale.

Map explicit and implicit choices across purpose, scope, architecture, code, tests, and documentation. Examine engineering taste as well as correctness: unnecessary concepts, misplaced boundaries, verbose implementations, low-value tests, and explanations that add more burden than understanding. Keep track of dependencies, accepted tradeoffs, required revisions, and unresolved evidence. Investigate facts yourself; the reviewer supplies judgment.

## Find the frontier

For each potential objection, ask:

> What might a discerning staff reviewer object to here, and what would accepting or rejecting this choice settle downstream?

The **frontier** contains every material potential objection whose prerequisites are settled. Present the whole frontier in each round, ordered by consequence and the downstream review it could settle. Defer questions whose relevance depends on an open choice. A confirmed bug is one item in this tree, not a reason to stop exploring independent branches. Surface urgent defects immediately.

Favor surfacing plausible, consequential objections over filtering for concerns you are certain the reviewer will endorse. A concern the reviewer dismisses is useful calibration. Ground each in an observed choice and a concrete possible cost; distinguish established defects from risks and taste judgments. Include reasonable tradeoffs the reviewer may happily accept. Keep hypothetical objections tied to this change, and let minor preferences earn their attention through cumulative impact rather than padding the list.

Challenge whether the capability is worth maintaining before refining its implementation. Compare with existing capabilities and a smaller sufficient change. Make costs concrete: another configuration mode adds supported behaviors, duplicated documentation requires synchronization, and a new subsystem adds lifecycle and failure handling obligations. Group symptoms when they share a cause or a coherent remedy; show representative evidence and establish the breadth of the problem. Prioritize the correction that resolves the pattern over its individual instances.

## Work in rounds

Open with a brief orientation to the change, then a numbered list of the frontier's concerns. For each item, give:

- A question putting the potential objection to the reviewer.
- The observed choice, source locations, and why it might matter. Make uncertainty explicit.
- Your recommended answer and its tradeoff, including what the decision settles or opens downstream.

Provide enough context to answer without reconstructing the PR. State established defects directly within their items; ask about the appropriate remedy or review consequence rather than whether the facts are true. Invite the reviewer to accept, dismiss, or refine the concerns, then stop and wait for their answers. Your recommendation on an item does not settle it on the reviewer's behalf.

After each answer, update the working model and recompute the frontier. Preserve independent objections when discarding questions invalidated by a revision. Acceptance settles the specified tradeoff; implementation correctness and unresolved facts still need evidence. Reopen a settled choice only when new evidence changes its consequences, explaining what changed. When the PR changes, inspect the delta and affected dependencies before reusing earlier conclusions.

## Finish the review

When the reviewer agrees that a fundamental objection warrants sending the PR back, inspect the remaining change for independent material concerns that would survive the revision. Put those on the frontier; defer detailed review of work that will be replaced. A likely request-changes verdict does not settle the remaining concerns.

Before recommending approval, establish that the benefit justifies the continuing obligations, account for every materially affected area, and resolve significant risks with appropriate inspection or checks. If missing evidence prevents a decision, state what is needed. An empty frontier means no consequential judgment remains to discuss; it does not establish correctness.

Finish when the reviewer has resolved the material concerns, dependent branches have been examined or made irrelevant, and no consequential choice remains silently assumed, or when the reviewer explicitly asks to conclude. If investigation yields no material concerns, explain the basis and ask whether the reviewer wants to conclude. Then produce a concise result the reviewer can send to the author:

- **Approve:** explain why no material objection remains.
- **Approve with nits or follow-up:** identify the remaining work and why it need not delay merging.
- **Request changes:** give coherent revision requests, each with evidence and a condition for resolution. Use line-level corrections when they are sufficient.
- **Reframe:** identify the premise, scope, or boundary that must change before detailed review is useful, plus any independent blockers.

State the conditions for the next action without replaying the conversation or reopening settled preferences.
