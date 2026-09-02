---
name: lint-residue
description: Lint checked-in artifacts for implementation-history residue and make them read as if the current system had been built directly.
disable-model-invocation: true
---

# Residue Linter

Lint the user-named scope. Read adjacent material as needed to establish purpose; edit only within the scope.

## Purpose gate

First classify each artifact or coherent section by purpose. History surfaces preserve change over time—Git history, changelogs, release notes, migrations, retrospective RFCs or ADRs, and archival handoffs—and are outside the lint. Present-state source, tests, documentation, comments, configuration, fixtures, snapshots, diagnostics, and architecture descriptions are lint surfaces.

Classify mixed artifacts section by section, not by filename. Fix generated or vendored material through its authoritative source or update mechanism.

## Greenfield test

For every lint surface, ask of each meaningful unit:

> Would this exist, and read this way, if the current requirements had been implemented directly from scratch?

A failure is either an unnecessary artifact or otherwise accurate material shaped by an old prompt, review, migration, rejected alternative, or implementation sequence. Preserve current facts, but express them at their present scope; historical qualification often has no replacement.

Keep intrinsic rationale: what the current design guarantees and why that guarantee matters. Convert journey-shaped rationale into that present-tense form.

Treat compatibility as a current contract only when the user states it or an old client, peer, protocol, persisted value, deployment, or data format is demonstrably reachable. Speculative compatibility is residue. A regression test remains when it protects a current invariant; rewrite its name and narrative around that invariant. Delete a test whose only contract is the continued absence of a removed feature.

## Modes

- **Audit:** Report each finding as `path:line — Remove|Rewrite|Report`, with why it fails the greenfield test and the intended present state. Omit ordinary retained candidates.
- **Fix:** When the user explicitly asks to clean, fix, simplify, or remove residue, delete or rewrite high-confidence findings, including code and tests. Leave ambiguous behavior, transitional features, and architecture changes as `Report` findings.

Use searches to navigate, then inspect every checked-in artifact in scope deeply enough to find semantic residue.

After fixes, run the narrowest relevant checks and review the diff with the greenfield test. Finish only when every candidate has a disposition: history surface, remove, rewrite, retain for a demonstrated current contract, or report for judgment—and the cleanup itself has left no residue.
