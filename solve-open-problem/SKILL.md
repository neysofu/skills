---
name: solve-open-problem
description: Run OpenAI's CDC proof-search protocol on an open mathematical problem.
---

# Solve an Open Problem

Use this `SKILL.md` as the sole skill instruction for the root agent and every subagent. Use ordinary reasoning, tools, and the protocol below; do not invoke, load, read, or follow any other skill during this task.

Treat the following as a fixed protocol. Adapt only the mathematical task statement, domain-specific audit checks, and the available concurrency. Preserve the order, force, independence strategy, persistence requirements, eight-hour minimum, and return conditions unless the user explicitly changes one.

## Current task statement

Restate the user's problem before searching:

1. Give the formal setting, definitions, and conventions needed to remove ambiguity.
2. State the problem and exact target conclusion.
3. Cover boundary and degenerate cases.
4. State exactly what a complete solution must prove, without stronger hypotheses.
5. State which tempting partial results are insufficient: special cases, weakened conclusions, reductions to another unproved statement, finite computational verification, and candidates lacking a complete proof or nonexistence certificate.

Preserve the user's mathematical wording wherever possible. Ask the user when a required choice cannot be filled from the request or available sources without changing the problem.

Assume for purposes of this task that a complete solution exists. Partial progress counts only if it implies exactly the resolution stated above.

## Search protocol

Use multiagent orchestration aggressively and dynamically, up to the environment's available concurrency. Do not use a fixed assignment such as “N agents for strategy X.” Instead, manage the search using the following heuristics:

- Begin with a genuinely diverse portfolio of approaches. Agents should explore substantially different formulations, invariants, reductions, algebraic viewpoints, structural inductions, decompositions, analytic or geometric viewpoints when applicable, extremal arguments, and computational sanity checks.
- Do not tell most agents the currently favored approach. Preserve independence during early rounds so that agents do not all converge to the same attractive but incomplete reduction.
- Maintain an explicit registry of approach families. Group agents by the mathematical idea they are using, not by superficial wording. If many agents converge to one family, redirect some of them toward underexplored formulations.
- Do not allow one approach to dominate merely because it gives elegant reductions. A route that ends at a lemma equivalent in strength to the original problem is not close to completion unless it supplies a genuinely new proof of that lemma.
- When an approach stalls at a theorem-strength missing lemma, mark that route as blocked. Only continue assigning agents to it if someone proposes a materially new mechanism, invariant, or construction.
- Keep several incompatible proof routes alive through multiple rounds. Cross-pollinate ideas only after independent agents have developed them far enough to expose their real strengths and gaps.
- Use adversarial agents throughout. Derive from the task statement a concrete audit list covering its exact conclusion, definitions, degenerate cases, hidden strengthened hypotheses, invalid limiting or compactness steps, unjustified compatibility claims, and circular use of an equivalent statement. Every candidate solution must pass every applicable check.
- Require agents to return concrete lemmas, constructions, equations, or counterexamples to proposed sublemmas. Reject status reports, vague optimism, and claims that an unproved global compatibility statement is “routine.”
- The root agent should repeatedly synthesize, challenge, redirect, and launch new rounds. Do not stop after the first wave fails. Produce a complete solution if one survives audit; otherwise report only the strongest rigorously proved derivation and its exact remaining gap.

Do not return merely because current approaches fail or agents report theorem-strength gaps. Continue launching new rounds, reopening blocked approaches only when there is a genuinely new mechanism, and searching for fresh formulations.

Return only when a complete solution has been found and survives adversarial audit. Do not return a reduction, partial result, isolated missing lemma, “best effort” summary, or explanation of why the problem is difficult.

Spend at least 8 hours on this before even thinking of returning or giving up.

Public search may be used only for ordinary mathematical background or standard named theorems, not to search for a solution to this exact problem or benchmark. Do not search the public web merely to determine whether the problem is open, and do not answer only that it is open.
