---
name: lint-callee-docs
description: Lint comments and documentation for caller concerns stranded on the callee or provider side, then remove them or relocate and adapt them to their owner.
disable-model-invocation: true
---

# Callee Docs Linter

Lint the user-named files, diff, commit, or directory. Read definitions, callers, adapters, tests, and adjacent docs deeply enough to establish ownership; keep edits within the named scope.

## Ownership test

For each meaningful comment, docstring, API description, example, or present-state guide on a callee or provider, ask:

> Who owns this fact, and where can its reader act on it?

Keep provider-owned contracts at the provider: behavior and invariants common to callers, input and output semantics, lifecycle, errors, extension points, and demonstrated compatibility or safety constraints. API documentation belongs at the provider even though callers read it. Placement follows ownership, not grammatical point of view or the mere mention of a caller.

A caller concern explains a particular consumer's choice: why it supplies a value, requires an order, retries, works around a limitation, translates domains, or depends on one path's history or policy. Put that concern at the narrowest durable owner:

- the call site for a one-off decision;
- the caller abstraction for policy shared by its call sites;
- the adapter for a translation between caller and provider models;
- the operator or integration guide for a human workflow.

Remove a note when the code or names already communicate it, it only inventories who calls the provider, it duplicates an owning explanation, or no current behavior supports it. When a note mixes a provider contract with caller motivation, leave a present-tense contract at the provider and adapt the motivation at its caller-side owner. Generated and vendored docs are linted through their authoritative source.

## Modes

- **Audit:** Report each finding as `path:line — Remove|Move|Adapt|Report`, naming the owning destination for `Move` and `Adapt`, explaining the ownership mismatch, and stating the intended result. Omit ordinary retained provider contracts.
- **Fix:** When the user explicitly asks to fix, move, adapt, or clean the docs, apply high-confidence removals, relocations, and adaptations. Preserve behavior. Leave ambiguous ownership, destinations outside the named scope, and changes that require an architectural decision as `Report` findings.

Search terms are navigation aids, never findings. Inspect both sides of each candidate boundary; a provider-side sentence is not misplaced until its owning context is established.

After fixes, run the narrowest relevant checks and review the diff for duplicated or orphaned explanations. Finish only when every candidate is retained as a provider-owned contract, removed, relocated and adapted at its owner, or reported for judgment.
