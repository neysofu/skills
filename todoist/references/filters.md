# Todoist Filter Query Syntax

The `--filter` flag on `td task list` accepts Todoist filter queries.

## Usage

```bash
td task list --filter "today & p1"
td task list --filter "overdue | today" --json
td task list --filter "#Work & @urgent" --all
```

## Basic Filters

| Filter | Description |
| --- | --- |
| `today` | Tasks due today |
| `tomorrow` | Tasks due tomorrow |
| `overdue` | Overdue tasks |
| `no date` | Tasks without a due date |
| `7 days` | Tasks due within the next 7 days |
| `next week` | Tasks due next week |
| `recurring` | Recurring tasks only |

## Date Filters

| Filter | Description |
| --- | --- |
| `due before: Jan 1` | Due before a date |
| `due after: Jan 1` | Due after a date |
| `due: Jan 1` | Due on a date |
| `created: today` | Created today |
| `created before: -7 days` | Created more than 7 days ago |

## Priority Filters

| Filter | Description |
| --- | --- |
| `p1` | Priority 1, urgent |
| `p2` | Priority 2, high |
| `p3` | Priority 3, medium |
| `p4` or `no priority` | Priority 4, normal |

## Label Filters

| Filter | Description |
| --- | --- |
| `@label_name` | Tasks with a label |
| `no labels` | Tasks without labels |

## Project and Section Filters

| Filter | Description |
| --- | --- |
| `#Project Name` | Tasks in a project |
| `##Project Name` | Tasks in a project and its subprojects |
| `/Section Name` | Tasks in a section |

## Assignment Filters

| Filter | Description |
| --- | --- |
| `assigned to: me` | Tasks assigned to the current user |
| `assigned to: <name>` | Tasks assigned to a named collaborator |
| `assigned by: me` | Tasks assigned by the current user |
| `assigned` | All assigned tasks |

## Combining Filters

| Operator | Description | Example |
| --- | --- | --- |
| `&` | AND | `today & p1` |
| `|` | OR | `today | overdue` |
| `!` | NOT | `!#Example` |
| `()` | Grouping | `(today | overdue) & p1` |

## Examples

```bash
td task list --filter "(today | overdue) & (p1 | p2)" --json
td task list --filter "#Example & !assigned" --json
td task list --filter "@waiting & 7 days" --json
td task list --filter "#Example & no date" --json
td task list --filter "assigned to: me & p1" --json
```

## Notes

- Filter queries are case-insensitive.
- Quote project and label names with spaces: `"#My Project"`.
- Complex filters may require paid Todoist plans.
- The CLI handles quoting and escaping for the filter string.
