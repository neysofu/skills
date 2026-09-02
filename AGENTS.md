# Repository conventions

Last successful global upstream sync: `2026-09-02T12:24:08-04:00`.

Once this timestamp is more than 7 days old, read every `ATTRIBUTION.md`, sync all corresponding skills, and replace it with the completion time after the full sync succeeds.

Keep personally identifiable information and other personal configuration in files excluded by the relevant `.gitignore`. Keep as much of each skill as possible in checked-in files, cleanly separating reusable skill content from ignored personal data.

For user-invocable-only skills, set `disable-model-invocation: true` in the YAML frontmatter of `SKILL.md` and set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
