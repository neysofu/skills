---
name: lint-rust-invariants
description: Lint Rust invariants enforced by runtime logic that types could encode, reducing invalid states and repeated validation.
disable-model-invocation: true
---

# Rust Invariants Linter

Audit Rust code in the user-named scope. Trace construction, mutation, and use before proposing a stronger type.

> Which invariant must callers remember or recheck that a Rust type could enforce?

## Invariant test

Start from a demonstrated requirement and a concrete invalid state or operation. Look for checks, assertions, and call-order rules that compensate for a representation accepting more than the contract permits. A finding must show how the proposed type prevents that failure or makes repeated checks unnecessary.

Prefer the smallest encoding that carries the guarantee: an existing standard or repository type, an enum for mutually exclusive states and their associated data, or a newtype with private fields and checked construction. Use ownership, borrowing, or typestate when they enforce a demonstrated lifecycle rule without disproportionate API complexity.

Validate untrusted input at the boundary, then pass the validated type to code that relies on its invariant. Trace every way to create or change the value, including deserialization, conversions, defaults, and mutable access. A wrapper earns no guarantee if these paths bypass validation. Remove downstream checks only where the type actually establishes their precondition.

Keep validation for external or changing facts that the type cannot guarantee. Judge the encoding by errors prevented and logic simplified, accounting for conversion overhead, public compatibility, and maintenance cost. A nominal distinction or elaborate type protocol with no concrete benefit is not a finding.

## Audit and fix

Default to audit. Report each finding with `path:line`, the invariant, where runtime logic currently enforces it, the proposed encoding, and the checks or failure modes it would eliminate. Explain material tradeoffs; leave uncertain invariants as questions supported by the code.

When asked to fix, apply bounded changes within scope. Preserve accepted inputs, error behavior, and external contracts; report changes requiring a contract or architectural decision. Update construction and consumers together so the guarantee holds throughout the affected path.

After fixes, run the relevant Rust checks and focused tests for boundary validation and preserved behavior. Finish by checking that safe construction and mutation preserve each claimed invariant and that removed checks are covered by that guarantee.
