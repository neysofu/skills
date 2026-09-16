---
name: pin-pr
description: Rename the current task for its pull request and pin it in the sidebar.
disable-model-invocation: true
---

Rename and pin the current Codex task using its pull request.

1. Resolve the PR from the user's arguments or current conversation; otherwise look up the current branch's PR. Use the repository's PR tools or `gh pr view` to confirm its number, title, and linked issues. If the PR is missing or ambiguous, ask for its URL before changing the task.
2. Compose the title as `#PR_NUMBER short label` with an optional ` (TICKET)` suffix.
   - Use one or two words that broadly identify the area or kind of work.
   - Include a ticket only when it is relevant to this PR and its existence is verified through a linked issue record or a successful lookup in its tracker. A plausible ID in a branch name or title is a lookup candidate, not verification. Prefer the primary ticket the PR fixes; omit the suffix when no single ticket is established or verification is unavailable.
   - Use `#22` for an issue in the PR's repository, `owner/repo#22` for another repository's issue, or the tracker's canonical key, such as `LINE-98`.
3. Use the Codex app tools to rename and pin the current task:
   - Resolve its ID from trusted current-session metadata, such as `CODEX_THREAD_ID`. If unavailable, use app-provided current-task context; ask for clarification if the current task cannot be identified reliably. Recency or a similar title alone is insufficient.
   - Call `set_thread_title` with the composed title, omitting `threadId` to target the calling task.
   - Call `move_thread_to_sidebar_section` with the resolved current `threadId` and `sectionId: "pinned"`. An already pinned task stays pinned.
   - Confirm both operations succeeded; use `list_threads` to check the title and pinned membership when a response is inconclusive. Report the resulting title and pin status, including any operation that remains incomplete.

Examples:

```text
#100 ui polish
#12 data cleanup (#22)
#123 api updates (LINE-98)
```
