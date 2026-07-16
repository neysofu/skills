---
name: code-review
description: Review changes since a fixed point such as a commit, branch, tag, or merge-base. Use when the user wants to review a branch, commit, pull request, or work-in-progress changes.
---

# Code Review

Review a change along two independent axes:

- **Standards** — does the code conform to this repo's documented coding standards?
- **Spec** — does the code faithfully implement the originating request, issue, PRD, or spec?

Run the reviews in parallel sub-agents so their contexts and conclusions stay independent, then report their findings side by side. When no spec is available, run only the Standards review and mark Spec as unavailable.

## Process

### 1. Establish the comparison

Use the fixed point the user supplied. When none was supplied, infer it from the pull request base or repository default branch. Ask the user only when neither source establishes a safe base.

Capture the committed scope once:

- `git diff <fixed-point>...HEAD`
- `git log <fixed-point>..HEAD --oneline`

For work-in-progress reviews, also capture `git diff HEAD` and `git status --short`; inspect relevant untracked files directly.

This step is complete when the fixed point resolves and every committed, staged, unstaged, and relevant untracked change in scope is accounted for. Stop with a concise explanation when the scope is empty.

### 2. Identify the spec source

Gather the intended behavior from the first available sources in this order:

1. The user's request and any acceptance criteria supplied in the conversation.
2. A spec, PRD, issue, or other path the user named.
3. Pull request title/body or issue context already available in the environment.
4. Repository files under likely documentation directories such as `docs/` or `specs/`, matched to the branch name, commit messages, or changed feature.

Use issue-tracker context when it is already available and relevant. Derive intent from independent sources; treat the changed code as evidence of implementation.

This step is complete when the Spec sub-agent can receive an independent statement of intent, or when every listed source has been checked and Spec is explicitly marked `No spec available`.

### 3. Identify the standards sources

Read every repository instruction that governs a changed file, including applicable `AGENTS.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`, style guides, and directory-local guidance. Apply the most specific source when instructions overlap.

Read [the standards baseline](references/standards-baseline.md) before preparing the Standards sub-agent prompt. Repository rules override baseline heuristics, and existing tooling owns checks it can enforce reliably.

This step is complete when every changed file is mapped to its governing instructions and the baseline has been loaded.

### 4. Run independent reviews

Delegate Standards and Spec concurrently. Give each sub-agent the diff command, commit list, working-tree scope, and only the sources for its axis. Keep their prompts and conclusions isolated.

Ask the Standards sub-agent to:

- Report actionable violations of documented standards, citing the source file and rule.
- Report possible baseline smells, clearly labelled as judgement calls.
- Give precise changed-file and line references with concise evidence.

Ask the Spec sub-agent to:

- Report missing or partially implemented requirements.
- Report behavior that contradicts the spec or appears to implement it incorrectly.
- Report material scope creep only when it creates a concrete risk.
- Cite the relevant requirement and give precise changed-file and line references.

Both agents inspect enough surrounding code to validate each finding and return actionable findings ordered by severity. A clean review returns zero findings.

This step is complete when Standards has returned and Spec has either returned or was skipped for lack of an independent spec.

### 5. Aggregate

Validate every finding against the diff and cited source. Retain only actionable, supported findings caused by the reviewed change. Merge duplicates within an axis and preserve the separation between axes.

Present the result under `## Standards` and `## Spec`. Within each axis, order findings by severity and include file/line references. If an axis has no findings, say so. If Spec was skipped, explain why.

End with a one-line summary giving the finding count and highest severity within each axis.

The review is complete when every retained finding cites a changed file and line plus the governing rule or requirement, both axes have an explicit outcome, and the summary counts match the findings.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately prevents one axis from masking the other.
