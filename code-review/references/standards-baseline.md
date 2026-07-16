# Standards Baseline

Use this baseline for design concerns left unsettled by repository rules and existing tooling. Repository rules override it. Report each match as a possible smell—a judgement call supported by a changed-file reference—rather than a hard violation.

- **Mysterious Name** — a name does not reveal what a value or abstraction represents.
- **Duplicated Code** — the same logic shape appears in multiple changed locations.
- **Feature Envy** — code works more with another object's data than its own.
- **Data Clumps** — the same fields or parameters repeatedly travel together.
- **Primitive Obsession** — a primitive stands in for a domain concept.
- **Repeated Switches** — equivalent conditionals recur on the same discriminator.
- **Shotgun Surgery** — one logical change requires scattered edits.
- **Divergent Change** — one module changes for multiple unrelated reasons.
- **Speculative Generality** — abstractions or hooks serve no present requirement.
- **Message Chains** — callers depend on long navigation chains.
- **Middle Man** — an abstraction mostly delegates without adding value.
- **Refused Bequest** — an implementation rejects most inherited behavior.
