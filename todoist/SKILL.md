---
name: todoist
description: Manage Todoist through the `td` CLI.
disable-model-invocation: true
---

# Todoist

Use the `td` CLI.

## Personal Configuration

Read `references/personal.md` before inferring projects, sections, labels, priorities, dates, or other user-specific conventions. This file is local and ignored by Git.

If it is absent, do not infer organization or preferences. Leave optional metadata unset and ask only when a missing choice blocks the request.

Never write personal Todoist data, learned preferences, resource names, IDs, or account details into tracked skill files. Put durable personal conventions only in `references/personal.md`.

## Operating Loop

1. Verify access with `td auth status` when uncertain. If `td` is missing, ask the user to install `@doist/todoist-cli`; if unauthenticated, ask them to run `td auth login`.
2. Read the minimum data needed. Prefer `--json`, `--ndjson`, and `--full` for parsing; use `--all` only for exhaustive requests.
3. Resolve the target and metadata according to Personal Configuration.
4. Confirm the exact mutation before updating, completing, deleting, moving, archiving, or otherwise changing an existing resource. One confirmation may cover one clearly described group.
5. Execute with explicit flags. Prefer `td task add` when metadata matters; reserve quick add for simple captures.
6. Report the changed resource and every field set. The task is complete when the requested Todoist state is verified.

Read-only operations do not require confirmation.

## Task Creation

Use explicit creation when metadata is known:

```bash
td task add --content "Task title" \
  --project "Project Name" \
  --due "tomorrow" \
  --deadline "2026-06-01" \
  --priority p3 \
  --labels "label-one,label-two" \
  --description "Useful context, links, references, or checklist"
```

Omit fields that do not apply. Use `--due` for an action date or recurrence and `--deadline` for a hard final date.

Quick add is acceptable for simple captures:

```bash
td add "Buy milk tomorrow p1 #Shopping"
```

Quick add supports due dates, priorities, `#Project`, `/Section`, and `@label` syntax.

## Command References

- Read `references/commands.md` for task, project, section, label, comment, reminder, and history commands.
- Read `references/filters.md` before building a non-trivial Todoist filter query.
- Read `references/completed-tasks.md` when completed-task history needs date ranges, full fields, retention caveats, or an API fallback.

Resource refs accept names, partial matches, numeric IDs, or `id:xxx`. Use `id:xxx` when an operation must target exactly one resource.
