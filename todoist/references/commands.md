# Todoist CLI Commands

Use `--json`, `--ndjson`, or `--full` when structured output is useful.

## Tasks

```bash
td task list --json
td task list --project "Example Project" --json
td task list --filter "today & p1" --all --json
td task view <ref> --json
td task update <ref> --content "New content" --due "next week"
td task complete <ref>
td task uncomplete id:xxx
td task delete <ref>
td task move <ref> --project "New Project"
td task browse <ref>
```

List filters include `--project`, `--label`, `--priority`, `--due`, `--filter`, `--assignee`, `--workspace`, and `--personal`.

Creation options include `--content`, `--project`, `--section`, `--parent`, `--due`, `--deadline`, `--priority`, `--labels`, `--description`, `--assignee`, and `--duration`.

Update options include `--content`, `--due`, `--deadline`, `--no-deadline`, `--priority`, `--labels`, `--description`, `--assignee`, `--unassign`, and `--duration`.

## Projects, Sections, and Labels

```bash
td project list --json
td project view <ref> --json
td project create --name "Project Name" --color "blue" --parent "Parent Project" --view-style board --favorite
td project update <ref> --name "New Name" --color "red"
td project archive <ref>
td project unarchive <ref>
td project delete <ref>
td project collaborators <ref>

td section list <project> --json
td section create --name "Section Name" --project "Project Name"
td section update <id> --name "New Name"
td section delete <id>

td label list --json
td label create --name "label-name" --color "green" --favorite
td label update <ref> --name "new-name" --color "blue"
td label delete <name>
```

## Comments and Reminders

```bash
td comment list <task-ref>
td comment list <project-ref> --project
td comment add <task-ref> --content "Comment text"
td comment add <project-ref> --project --content "Comment text"
td comment update <id> --content "Updated text"
td comment delete <id>

td reminder list <task-ref>
td reminder add <task-ref> --due "tomorrow 9am"
td reminder delete <id>
```

## Filters and History

```bash
td filter list --json
td filter show <filter-ref> --json
td filter create --name "My Filter" --query "today & p1"

td completed --json
td completed --since 2024-01-01 --until 2024-01-31 --json
td completed --project "Example Project" --json
td completed --all --json

td today
td upcoming 7
td inbox
td activity
td stats
```
