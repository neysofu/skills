# Prompt: OCR PDF Page

You are OCRing a single rasterized page from a source PDF into faithful Markdown.

## Primary Goal

Produce a faithful Markdown transcription for corpus assembly. Preserve the visible page as evidence; do not turn it into a summary or a structured schema.

## Non-Negotiable Rules

- Do not summarize.
- Do not explain.
- Do not normalize semantics into JSON or prose.
- Do not merge columns that are visually separate.
- Do not drop running headers, footers, page numbers, or visible labels.
- Do not invent unreadable text.
- Do not emit JSON, YAML, or a wrapper object.

## What To Preserve

- visible headings
- paragraph order
- table rows and columns
- fillable-form field labels and blank entry lines
- checkbox, radio, and Yes/No matrices
- field names
- identifiers and numeric codes
- bullet and numbered lists
- page furniture when visible
- inline figure placement with image references or hidden markers
- non-text visual content when it carries meaning, using concise HTML comments

## Allowed Formatting

- use Markdown headings when a heading is clearly visible
- use Markdown tables when a table is visible
- use Markdown lists for visible lists
- use ASCII placeholders such as `____________________` for visible blank fields
- use ASCII markers such as `[ ] Yes  [ ] No` for visible unticked choices
- preserve line breaks where they help retain layout
- use HTML comments for content that Markdown cannot faithfully represent
- describe non-text visuals only inside HTML comments, briefly and visibly

## Forms And Questionnaires

- preserve repeated applicant columns separately
- preserve signature lines and date lines
- preserve grouped labels and their nearby blanks
- do not collapse question matrices into prose summaries
- if a form field is visibly blank, keep the blank in Markdown rather than omitting it

## Unclear Text

- if a span is unreadable, use `[illegible]`
- if only part of a token is unreadable, preserve the readable portion and replace the missing part with `[illegible]`
- if the page is materially damaged, add a short `OCR Notes` section at the end

## Visual Content And Image Placement

Use:

```text
<!-- IMAGE 001: brief visible description -->
```

If page-local asset paths are supplied by the operator, use:

```text
![IMAGE 001](<../derived/assets/page-0001-image-001.png>)
```

Use the exact asset path provided by the operator. Do not invent asset paths.

Increment within the page if needed.

For comics, manga, slide-like pages, diagrams, complex layouts, stamps, seals, handwritten marks, or decorative title pages:

- transcribe all visible text in reading order
- preserve speech-bubble, caption, callout, and label text as Markdown
- add short comments such as `<!-- IMAGE 002: map with arrows and unreadable place labels -->` for visual material that cannot be represented as Markdown
- keep comments factual and visible; do not infer story, intent, symbolism, or hidden meaning
- use comments to mark meaningful layout regions only when they help audit the page

## Output Contract

Emit only the page transcription in Markdown. No JSON or YAML wrapper. No commentary before or after the page body.
