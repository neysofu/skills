# Retrieving Completed Tasks

Use `td completed` first.

## CLI Usage

```bash
td completed
td completed --json
td completed --all --json
```

## Date Ranges

```bash
td completed --since 2024-01-01 --until 2024-01-31
td completed --since 2024-01-01 --json
```

## Project Filter

```bash
td completed --project "Example Project" --json
```

## Options

- `--since <date>`: start date, `YYYY-MM-DD`; default is today.
- `--until <date>`: end date, `YYYY-MM-DD`; default is tomorrow.
- `--project <name>`: filter by project name.
- `--limit <n>`: limit results; default is 300.
- `--all`: fetch all results.
- `--json`: output JSON.
- `--ndjson`: output newline-delimited JSON.
- `--full`: include all fields.

## Direct API Fallback

Use the API only when the CLI cannot provide the needed data.

By completion date:

```bash
curl -s -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  "https://api.todoist.com/api/v1/tasks/completed/by_completion_date?since=2024-01-01T00:00:00Z&until=2024-01-31T23:59:59Z"
```

By due date:

```bash
curl -s -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  "https://api.todoist.com/api/v1/tasks/completed/by_due_date?since=2024-01-01T00:00:00Z"
```

Parameters:

- `since`: ISO 8601 start date.
- `until`: ISO 8601 end date.
- `project_id`: project ID.
- `limit`: results per page.
- `cursor`: pagination cursor.

Completed task objects include IDs, content, project ID, completion time, and metadata.

Notes:

- Completed-task history may have plan-based retention limits.
- Use `td task uncomplete id:xxx` to reopen a completed task.
- Recurring tasks create new instances when completed.
