# Report Format

Keep the report compact and evidence-backed. Do not over-systematize uncertainty; use engineering judgment.

## Audit Report

```text
Findings
1. path/to/file.ext:line
   Residue: <why this preserves history or obsolete behavior instead of current state>
   Suggestion: <Remove|Rewrite|Rename|Move|Keep>. <optional nuance>

2. path/to/file.ext:line
   Residue: <one or two sentences>
   Suggestion: <single opinionated action, plus brief rationale if needed>

Exempt
- path/to/history-artifact.md: intentional history surface, not audited by default.

Cleanup
Tell me which findings to remove or rewrite.
```

## Suggestion Vocabulary

- `Remove`: the text/test only preserves obsolete context.
- `Rewrite`: the idea still matters, but should be current-state prose or a current invariant.
- `Rename`: the test/file/snapshot still matters, but its name anchors it to an old bug or migration.
- `Move`: the material is useful history but belongs in a changelog, migration guide, ADR, or release note.
- `Keep`: the candidate looks history-shaped but is required by the current domain, API, or user request.

## Cleanup Summary

After applying selected findings:

```text
Cleaned up the selected residue in:
- path/to/file.ext

Validation:
- <command>: passed
- <command>: not run (<reason>)

Diff review: current-state wording only; any remaining history wording is intentional because <reason>.
```
