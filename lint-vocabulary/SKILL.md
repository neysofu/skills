---
name: lint-vocabulary
description: Lint repository vocabulary for needless synonyms, harmful overload, and terms that misstate the implemented model.
disable-model-invocation: true
---

# Vocabulary Linter

Lint the user-named scope. Read definitions, data flow, behavior, contracts, consumers, domain standards, and repository usage deeply enough to establish meaning; edit only within the scope.

## Vocabulary test

For every meaningful term in identifiers, types, APIs and schemas, configuration, diagnostics, tests, comments, or documentation, ask:

> Does the vocabulary preserve exactly the distinctions the system does?

Every lexical distinction must carry a demonstrated system distinction, and every demonstrated distinction must remain legible. Vocabulary should be as complex as necessary and as simple as possible.

Unify terms that name the same concept when no difference in audience, layer, representation, or domain meaning earns them. Disambiguate a term that names materially different concepts where the overlap suggests false substitutability. Rename a term whose implications about the model—such as ownership, direction, lifecycle, behavior, or certainty—are false. Shared spelling across unrelated, well-qualified contexts is not overload.

Establish meaning from what the system accepts, preserves, produces, and exposes, not from spelling or occurrence counts. Judge semantic fit rather than elegance. Preserve audience adaptation, established domain language, useful boundary translations, and natural prose.

Treat public APIs and protocols, serialized or persisted names, externally consumed diagnostics, and other compatibility-sensitive terms as contracts. Clarify internal vocabulary or document a necessary translation when changing an external term would break a demonstrated consumer. Fix generated or vendored artifacts through their authoritative source or update mechanism.

## Modes

- **Audit:** Report each finding as `path:line — Rename|Unify|Disambiguate|Report`, identify the concepts and system evidence that establish their relationship or distinction, and state the intended vocabulary. For `Unify` and `Disambiguate`, name the affected peer terms or meanings. Omit ordinary retained terms.
- **Fix:** When the user explicitly asks to fix, rename, unify, disambiguate, or clean the vocabulary, apply high-confidence in-scope changes consistently across owning definitions, references, tests, diagnostics, and documentation. Preserve behavior and external contracts. Leave ambiguous semantics, breaking contract changes, destinations outside the named scope, and choices requiring domain or architectural judgment as `Report` findings.

Use searches and term counts to navigate, then trace each candidate through its definitions, values, behavior, producers, consumers, and exposed contracts. Resemblance alone does not prove synonymy; difference alone does not prove a useful distinction.

After fixes, run the narrowest relevant checks and review the diff for stale aliases, newly ambiguous uses, mismatched schemas or diagnostics, and vocabulary changes that accidentally alter behavior. Finish only when every candidate term is retained for a demonstrated distinction or deliberate translation, renamed to match its concept, unified with its true synonym, disambiguated across materially different concepts, preserved as an external contract, or reported for judgment—and all in-scope representations agree with that disposition.
