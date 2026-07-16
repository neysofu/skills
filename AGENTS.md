# Repository conventions

Read every `ATTRIBUTION.md` file in this repository and update each corresponding skill from its relevant upstream source.

Keep personally identifiable information and other personal configuration in files excluded by the relevant `.gitignore`. Keep as much of each skill as possible in checked-in files, cleanly separating reusable skill content from ignored personal data.

For user-invocable-only skills, set `disable-model-invocation: true` in the YAML frontmatter of `SKILL.md` and set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
