---
name: "trace-residue-auditor"
description: "Audit repositories for stale history traces and agent residue before optional cleanup."
disable-model-invocation: true
---

# Trace Residue Auditor

Audit repositories for residue left by feature removals, architecture changes, bug fixes, and agent edits: current-state docs, comments, tests, fixtures, and diagnostics that narrate history instead of describing the project as it should exist now. Produce a report first; edit only after the user chooses findings to remove.

## Workflow

1. Establish the current-state sources of truth.
   - Read the repo's agent/contributor instructions first when present.
   - Identify current source, tests, and docs that define behavior now. Prefer code and executable tests over prose when they disagree.
   - Treat changelogs, release notes, migration guides, ADRs, incident writeups, commit history, and explicitly historical docs as exempt unless the user asks to audit them.

2. Build the audit surface.
   - Run `python3 scripts/list_audit_surface.py <repo>` from this skill directory for a bounded file inventory. Use it to choose files to inspect; do not treat it as the audit result.
   - Prioritize current-state docs (`AGENTS.md`, README, architecture docs), comments around changed subsystems, tests and fixtures for recently changed behavior, snapshots/goldens, CLI diagnostics, and public API docs.
   - Use search only as navigation when context names a concrete obsolete concept. Do not reduce the audit to keyword hits.

3. Judge residue semantically.
   - Ask whether the text or test describes the desired current system, or whether it preserves the path taken to get there.
   - Useful guardrails should be rewritten into current-state invariants, not historical warnings.
   - Tests that still protect real behavior should be renamed or reframed around the current invariant. Tests that only verify dead behavior are cleanup candidates.
   - Keep intentional history where history is the artifact's purpose.

4. Report before editing.
   - Use `references/report-format.md` for the concise report shape.
   - Every finding needs a location, why it is residue, and one opinionated suggestion. Keep each suggestion terse: usually one word such as `Remove`, `Rewrite`, `Rename`, `Move`, or `Keep`; add a few sentences only when the fix is nuanced.
   - Ask which findings to clean up. Do not apply cleanup during the audit phase.

5. Cleanup, if selected.
   - Make only the selected edits.
   - Rewrite toward final-state prose and behavior. Avoid documenting that something was removed unless the target file is intentionally historical or the user asked for that.
   - Preserve real invariants, public contracts, and regression coverage by expressing them without obsolete narrative.

6. Validate the cleanup.
   - Run the narrowest relevant docs, format, compile, or test checks for the touched files.
   - Review the final diff semantically: it should look like the project was written directly in its current form, not like an agent left a record of the cleanup operation.
   - If historical wording remains, it must be user-requested, clearly part of a history artifact, or necessary domain content.

## Resources

- `scripts/list_audit_surface.py`: run at the start of an audit to inventory likely current-state files and exempt history files.
- `references/report-format.md`: read before writing the audit report or cleanup follow-up.
- `references/evaluation-prompts.md`: use when validating or improving this skill's trigger behavior and output quality.
