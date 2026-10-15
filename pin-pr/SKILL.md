---
name: pin-pr
description: Name and pin the current task for its pull request, and open its worktree in a named Ghostty tab when Ghostty is open.
disable-model-invocation: true
---

Rename and pin the current Codex task using its pull request, then open the PR's existing worktree in Ghostty when available.

1. Resolve the PR from the user's arguments or current conversation; otherwise look up the current branch's PR. Use the repository's PR tools or `gh pr view` to confirm its number, title, and linked issues. If the PR is missing or ambiguous, ask for its URL before changing the task.
2. Compose the title as `#PR_NUMBER short label` with an optional ` (TICKET)` suffix.
   - Use one or two concrete, memorable words naming the specific behavior, object, or detail changed. Ground the label in the PR and conversation; inspect the relevant diff if these leave the change unclear. Choose the detail that helps a human distinguish this task from others in the same area.
   - Include a ticket only when it is relevant to this PR and its existence is verified through a linked issue record or a successful lookup in its tracker. A plausible ID in a branch name or title is a lookup candidate, not verification. Prefer the primary ticket the PR fixes; omit the suffix when no single ticket is established or verification is unavailable.
   - Use `#22` for an issue in the PR's repository, `owner/repo#22` for another repository's issue, or the tracker's canonical key, such as `LINE-98`.
3. Use the Codex app tools to rename and pin the current task:
   - Resolve its ID from trusted current-session metadata, such as `CODEX_THREAD_ID`. If unavailable, use app-provided current-task context; ask for clarification if the current task cannot be identified reliably. Recency or a similar title alone is insufficient.
   - Call `set_thread_title` with the composed title, omitting `threadId` to target the calling task.
   - Call `move_thread_to_sidebar_section` with the resolved current `threadId` and `sectionId: "pinned"`. An already pinned task stays pinned.
   - Confirm both operations succeeded; use `list_threads` to check the title and pinned membership when a response is inconclusive.
4. Resolve an existing local worktree for this PR. Prefer an active worktree attached to the current task through `list_artifacts`; otherwise inspect `git worktree list --porcelain` in the PR's repository. Verify the repository and PR head branch before selecting a path; for a detached checkout, verify its association with the PR and its head commit. Keep existing local changes. If no worktree is present or the match is ambiguous, skip the terminal step rather than creating a worktree or switching branches.
5. On macOS, run [scripts/open_ghostty_tab.applescript](scripts/open_ghostty_tab.applescript) with the worktree's absolute path and the composed task title as two separate arguments:

   ```bash
   osascript <skill-dir>/scripts/open_ghostty_tab.applescript "$worktree_path" "$pr_title"
   ```

   The helper uses Ghostty's [AppleScript API](https://ghostty.org/docs/features/applescript) to create a tab in the front Ghostty window, start its shell in the worktree, and set a persistent tab title. It skips when Ghostty is closed or has no window. Pass paths and titles as data; the helper does not type shell commands into an existing terminal. If automation is unavailable or denied, retain the successful task changes and report the terminal limitation. If creation succeeds but verification fails, inspect the returned tab ID before retrying so a retry does not create duplicate tabs. On other platforms, report this helper as unsupported.
6. Report the task title and pin status, plus the Ghostty tab title and worktree path, or the reason the terminal step was skipped or remains incomplete.

Examples:

```text
#100 signed qty
#12 sidebar radius (#22)
#123 token expiry (LINE-98)
```
