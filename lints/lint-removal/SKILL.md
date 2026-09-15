---
name: lint-removal
description: Find code, abstractions, architecture, and supporting artifacts whose removal would reduce maintenance cost. Use when reviewing or simplifying a system for unnecessary machinery.
---

# Removal Linter

Audit the user-named scope by default. Read consumers, contracts, operational needs, and adjacent artifacts deeply enough to establish purpose; edit only within the scope when fixes are requested.

## Removal test

Start with a concrete version of the system in which the candidate is gone:

> What becomes worse if this disappears, and is that loss worth its continuing cost?

Favor removal. Existing code has no entitlement to remain because it works, follows a pattern, or took effort to build. Seek the smallest system that serves demonstrated requirements. When two designs meet them with comparable clarity and risk, choose the one with fewer concepts, dependencies, and maintenance obligations.

Inspect meaningful units at every scale: expressions, branches, helpers, types, interfaces, configuration options, dependencies, modules, services, build steps, tests, and documentation. Look beyond dead code. Active machinery can exist only to support other dispensable machinery; assess the whole cluster against the requirement it ultimately serves.

For each candidate, establish its current benefit and recurring cost. Trace who depends on it, which behavior or invariant it owns, and what its removal would require of consumers. Costs include indirection, coupling, synchronization, configuration, deployment, debugging, and reader effort. A deletion earns its place when the resulting system has less total burden, including any replacement and migration work.

Search for layers that only forward calls, abstractions whose flexibility has no demonstrated use, configuration that could be a fixed decision, parallel representations, and infrastructure whose job an existing component can absorb. Treat these as leads. A single implementation can justify an interface through isolation or ownership; a small helper can preserve a valuable name or invariant. Count the obligations removed, not the lines deleted.

Prefer deletion without replacement. Where behavior still matters, consider inlining, collapsing a layer, narrowing a contract, or using an existing facility. Make the simpler end state concrete enough to expose displaced complexity: removing a shared helper while duplicating its policy across callers may increase the burden.

## Establish what must survive

Ground retention in current contracts, accepted inputs, external consumers, persisted data, deployment needs, or concrete reliability, security, performance, and comprehension benefits. Follow dynamic registration, generated consumers, and public entry points where relevant; an empty reference search alone does not establish disuse. Preserve rare but consequential defenses when their boundaries can encounter the failure.

Distinguish demonstrated value from hypothetical future reuse or compatibility. Investigate uncertainty far enough to name the missing evidence; report that specific uncertainty when it prevents a sound decision. A clean audit can find nothing worth removing.

## Modes

- **Audit:** Report each finding as `path:line — Remove|Simplify|Report`. Name the candidate or connected cluster, evidence about its purpose and consumers, the proposed end state, and the net benefit and material tradeoff. Rank by maintenance burden removed and confidence. Omit ordinary retained artifacts.
- **Fix:** When the user asks to remove, simplify, or clean up, apply high-confidence changes within the authorized scope, including collapsing architectural layers when their contracts can be preserved. Update affected callers and supporting artifacts. Preserve required behavior and external contracts; report proposed feature retirement, contract changes, uncertain tradeoffs, or work beyond the scope with the decision needed to proceed.

Change generated or vendored artifacts through their authoritative source. After fixes, run the narrowest relevant checks and inspect the diff for orphaned dependencies, configuration, tests, and explanations. Finish when each candidate has been removed, simplified, retained for a concrete benefit, or reported with the unresolved decision, and the remaining artifacts agree with the resulting system.
