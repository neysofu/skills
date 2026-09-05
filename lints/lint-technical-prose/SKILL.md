---
name: lint-technical-prose
description: Editorial judgment for technical prose. Use when writing or revising documentation, docstrings, or code comments, including during code changes.
---

# Technical Prose Linter

Write for a capable engineer who knows the tools but may not know this system. Follow the existing documentation structure and the requested scope.

> What does this prose help the reader understand or decide that they would otherwise have to reconstruct?

## Earn the reader's attention

Choose detail by the reader's task. Explain the model, contract, or constraint they need to use or change the system correctly.

A comment earns its place by preserving hidden reasoning, explaining a surprising consequence, or summarizing complicated code at a useful level of abstraction. Repetition is only worthwhile when it saves substantial reconstruction.

Make consequences concrete: “Keep the lease until the write completes; releasing it earlier lets another worker publish over an unfinished write.”

## Write from the system

Check claims against the implementation and authoritative contracts. Separate guarantees from implementation details. When rationale is unknown, describe the observable constraint or state the uncertainty.

Describe the current design independently of the conversation that produced it. Include alternatives only when they clarify a present choice or misunderstanding. Preserve relevant history in documents intended to record decisions or changes.

## Choose detail that can be maintained

Prefer stable relationships and invariants. Include exact details when readers need them to act correctly.

Use references and hyperlinks to keep knowledge at one maintained source. Internal docs can explain a configuration's purpose and link to its defining type for fields and defaults. When code organization is in scope, a cohesive configuration definition can make that source easier to understand and reference.

Choose stable, specific targets the reader can access, and make clear what each link provides. Keep enough explanation locally to follow the argument or complete the immediate task; a link earns its place when it saves duplication or supplies useful depth without forcing unnecessary navigation. Verify that targets support the surrounding claims.

Place shared contracts with the interface, consumer reasoning near the consumer, and broader explanations in existing docs.

## Make the explanation easy to follow

Lead with the behavior or idea, then its mechanism and necessary qualifications. Use established terms and explain local concepts. Add an example when it makes a difficult distinction clear.

Read the result beside its source. Remove sentences whose absence costs the reader nothing; retain details that change correct use or safe modification. A removed comment may need no replacement.
