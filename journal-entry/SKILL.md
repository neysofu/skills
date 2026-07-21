---
name: journal-entry
description: Save a new entry to your journal.
disable-model-invocation: true
---

# Journal Entry

## Setup

Read the gitignored `config.yaml` beside this file:

```yaml
journal_directory: "/absolute/path/to/journal"
```

If `journal_directory` is missing or invalid, ask for it and update the file.

## Capture

Capture the journal entry, which may either be dictated by the user or supplied as a typed message. Separate clear operational instructions from journal prose.

## Save

1. Assign the entry to the user's **waking day**: the date it belongs to from the user's perspective. Treat the system date and time only as a hint; the right date is usually the system date or one day on either side. Infer it from the entry and the previous entry's date. Entries captured before 6:00 a.m. usually belong to the previous calendar day. An explicitly assigned date wins; ask only if the date remains genuinely ambiguous.
2. Lightly copyedit the full session: fix punctuation, capitalization, paragraphing, obvious transcription errors, empty disfluencies, repetitions, and abandoned false starts. Preserve every thought once, in order, with the user's meaning, voice, uncertainty, emphasis, and profanity intact. Mark unintelligible material `[unclear]`; add no summary, interpretation, advice, or invented detail.
3. Write a new UTF-8 file in `journal_directory` named `YYYYMMDD.md`, using the entry date as a filename. On collision, append `-part2`, `-part3`, and so on.

Use this exact shape:

```markdown
---
journal_date: YYYYMMDD
---

Cleaned journal prose.
```

Read the file back, verify its path, frontmatter, and complete cleaned body, then return a brief confirmation with its clickable absolute path.
