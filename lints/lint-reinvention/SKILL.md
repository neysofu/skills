---
name: lint-reinvention
description: Lint competing implementations and independently maintained copies of repository behavior, conventions, documentation, and facts.
disable-model-invocation: true
---

# Reinvention Linter

Lint the user-named scope. Read definitions, consumers, tests, configuration, generated sources, and adjacent documentation deeply enough to establish authority; edit only within the scope.

## Authority test

For every apparent repetition of behavior or repository knowledge, ask:

> Why must this remain an independently editable authority?

A reinvention is a second editable authority for the same concern: duplicated implementation, competing machinery for an established repository pattern, documentation that caches a contract or procedure, or a fact copied across code, configuration, schemas, tests, and documentation. Common sites include parsing, serialization, error or configuration handling, adapters, result shapes, lifecycle conventions, defaults, permissions, and support matrices.

Duplication is a navigation signal, never a finding. Establish that the candidates have the same semantics and applicability, identify their owners and consumers, and compare the maintenance cost of independent evolution with the coupling introduced by sharing. Similar text can express different contracts; different forms can encode the same fact. A local implementation is not reinvention merely because a reusable abstraction could be imagined.

Prefer one durable owner and make other representations reuse, reference, or derive from it. When no candidate is the natural owner, consolidate at the narrowest boundary that owns the shared concern. Preserve independent test oracles and redundancy justified by isolation, reliability, security, performance, platform, or compatibility. Generated mirrors and contextual summaries may repeat information without becoming independent authorities. Keep concerns separate when sharing would cross an ownership boundary or cost more than synchronization. Fix generated or vendored copies through their authoritative source or update mechanism.

## Modes

- **Audit:** Report each finding as `path:line — Reuse|Derive|Consolidate|Remove|Report`, identify the competing expressions, the evidence that they encode the same concern, the current or proposed authority, and the intended relationship. Use `Reuse` when an implementation or pattern should delegate to an existing owner or prose should reference it, `Derive` for a mechanically produced representation, `Consolidate` when peers need a new common owner, and `Remove` for a copy that adds no local value. Omit ordinary retained repetition.
- **Fix:** When the user explicitly asks to fix, consolidate, deduplicate, or clean reinvention, apply high-confidence in-scope reuse, derivation, consolidation, and removal; update affected callers, tests, configuration, and documentation while preserving behavior and external contracts. Leave ownership disputes, destinations outside the named scope, compatibility-sensitive changes, and architectural or coupling decisions as `Report` findings.

Use searches and similarity measures to navigate, then trace each candidate through its owners, producers, consumers, update paths, and exposed contracts. Inspect both sides before deciding that two expressions should evolve together.

After fixes, run the narrowest relevant checks and review the diff for stale copies, broken derivations, displaced ownership, and newly coupled concerns. Finish only when every candidate is retained for a demonstrated independent purpose, made to reuse or derive from an authority, consolidated under a justified owner, removed, or reported for judgment—and every in-scope representation agrees with that disposition.
