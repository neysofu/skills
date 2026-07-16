# Evaluation Prompts

Use these when checking whether the skill triggers and produces the right shape of output.

## Should Trigger

- "Audit this repo for agent residue after the verifier rewrite. I want stale docs, comments, and tests called out before we clean them."
- "Find places where the codebase still talks about the old parser even though the new pipeline is landed."
- "Look for tests or fixtures that only exist for a feature we removed last month and give me a cleanup report."
- "This branch feels like it left migration scar tissue in docs. Review and tell me what to delete."
- "After the architecture change, make sure current docs don't say 'no longer' or otherwise narrate the migration unless it's a changelog."
- "Review the diff for history-shaped wording before I merge."

## Should Not Trigger

- "Write a changelog entry for this release."
- "Summarize the migration guide for users upgrading from v1 to v2."
- "Find when this bug was introduced using git history."
- "Add an ADR for the new storage architecture."
- "Generate release notes from the merged pull requests."
- "Explain why the old backend was removed."

## Output Assertions

- The audit distinguishes current-state surfaces from intentionally historical artifacts.
- Findings cite concrete files and, when available, lines.
- Each finding explains why it is residue rather than merely matching a word.
- Each finding includes a concise opinionated suggestion.
- The first audit report does not edit files.
- Cleanup, if requested, rewrites toward current-state behavior and then semantically reviews the diff.
