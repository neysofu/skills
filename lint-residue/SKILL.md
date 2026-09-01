---
name: lint-residue
description: Lint checked-in artifacts for implementation-history residue and make them read as if the current system had been built directly.
disable-model-invocation: true
---

# Lint Residue

Lint the user-named files, diff, commit, or directory. Read adjacent material for context; keep edits within the named scope.

## Purpose gate

First classify purpose. An artifact or coherent section whose purpose is to preserve change over time—such as Git history, changelogs, release notes, migration records, retrospective RFC or ADR material, and archival handoffs—is a history surface and outside the lint. Present-state source, tests, documentation, comments, configuration, fixtures, snapshots, diagnostics, and current architecture descriptions are lint surfaces.

Classify by actual purpose, not filename. Audit present-state sections inside mixed documents. Generated or vendored residue belongs in its authoritative source or update mechanism.

## Greenfield test

For every lint surface, ask of each meaningful unit:

> Would this exist, and read this way, if the current requirements had been implemented directly from scratch?

A failed test includes both unnecessary artifacts and otherwise accurate text that sounds strangely specific because it answers an old prompt, review, migration, rejected alternative, or implementation sequence. Preserve the current fact when it matters, but express it naturally at its present scope; often the historical qualification has no replacement.

Keep intrinsic rationale: what the current design guarantees and why that guarantee matters. Convert journey-shaped rationale into that present-tense form.

Treat compatibility as a current contract only when the user states it or an old client, peer, protocol, persisted value, deployment, or data format is demonstrably reachable. Speculative compatibility is residue. A regression test remains when it protects a current invariant; rewrite its name and narrative around that invariant. Delete a test whose only contract is the continued absence of a removed feature.

## Modes

- **Audit:** Report each finding as `path:line — Remove|Rewrite|Report`, with why it fails the greenfield test and the intended present state. Omit ordinary retained candidates.
- **Fix:** When the user explicitly asks to clean, fix, simplify, or remove residue, delete or rewrite high-confidence findings, including code and tests. Leave ambiguous behavior, transitional features, and architecture changes as `Report` findings.

Search terms are navigation aids, never findings. Inspect every checked-in artifact in the named scope sufficiently to find semantic residue rather than stopping at keyword matches.

After fixes, run the narrowest relevant checks and review the diff with the greenfield test. Finish only when every candidate has a disposition: history surface, remove, rewrite, retain for a demonstrated current contract, or report for judgment—and the cleanup itself has left no residue.
