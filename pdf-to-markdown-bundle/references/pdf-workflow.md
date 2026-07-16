# PDF Workflow

## Contents

- Scope
- Bundle Contract
- Source Metadata
- Per-Page OCR JSON
- Canonical Markdown Rules
- Trace Rules
- Smoke Test Strategy
- Validation Checklist

## Scope

This reference distills only the direct PDF workflow from FerrumFIX `docs/specs/`.

Keep:

- `raw/source.pdf`
- per-page OCR JSON under `derived/ocr/`
- extracted figure assets under `derived/assets/`
- source-preserving Markdown under `canonical/content.md`
- a process trace under `traces/run.trace.yaml`

Do not pull in:

- FIX-specific semantics
- source-discovery prompts
- catalog scraping
- corpus-wide indexes
- direct-image bundle rules unless a PDF page image is extracted as an asset

## Bundle Contract

Expected shape:

```text
<bundle>/
  source.meta.yaml
  raw/
    source.pdf
  canonical/
    content.md
  derived/
    assets/
    renders/
    ocr/
      page-0001.json
  traces/
    run.trace.yaml
```

Lane rules:

- `raw/` stores original bytes without editorial changes.
- `canonical/` stores the faithful Markdown representation used for retrieval.
- `derived/` stores helper artifacts only. It may add structure, but not new authoritative content.
- `traces/` stores process evidence such as prompt path, prompt hash, model, timestamps, and validation notes.

## Source Metadata

`source.meta.yaml` should include at least:

- `source_id`
- `bundle_slug`
- `title`
- `url`
- `retrieved_at`
- `source_format`
- `content_type`
- `license`
- `sha256`
- `canonical_path`

Helpful optional fields:

- `page_count`
- `catalog_id`
- `catalog_path`
- any project-specific grouping fields

For local PDFs without a public URL, a `file://` URI is acceptable.

## Per-Page OCR JSON

Each `derived/ocr/page-*.json` should carry at least:

- `page_number`
- `source_pdf_path`
- `rendered_image_path`
- `dpi`
- `render_media_type`
- `render_dimensions`
- `render_sha256`
- `model`
- `ocr_mode`
- `prompt_path`
- `prompt_sha256`
- `page_prompt_sha256`
- `source_pdf_sha256`
- `status`
- `page_profile`
- `text_layer`
- `images`
- `ocr_markdown`
- `review_notes`
- `finish_reason`
- `processed_at`

Use these field meanings:

- `ocr_markdown`: faithful page transcription in Markdown
- `rendered_image_path`: usually `null` when page renders are regenerated in memory
- `images`: page-local figures detected on the page, each with:
  - `page_image_index`
  - `asset_path`
  - `bbox`
  - `extractable`
  - `kind`
  - `notes`
- `text_layer`: summary of embedded-text-layer evidence used for hybrid OCR, including whether it was supplied to the model
- `review_notes`: non-fatal issues such as mismatched figure placeholders or OCR uncertainty
- `finish_reason`: provider stop signal; truncation reasons should be treated as failures, not successful OCR

Treat page JSON as derived. The PDF remains authoritative.

## Canonical Markdown Rules

Build `canonical/content.md` by concatenating `ocr_markdown` in page order.

Use hidden page markers so boundaries stay machine-readable:

```text
<!-- PAGE 0001 -->
```

Preserve:

- heading hierarchy
- paragraph order
- headers, footers, and visible page numbers
- tables as Markdown tables when possible
- blank form fields using ASCII placeholders when they are visibly present
- checkbox and Yes/No groups using ASCII markers when visually appropriate
- lists as lists
- visible labels, identifiers, and numeric codes

Handle figures like this:

- Use exact Markdown image references when a page-local asset exists:

```text
![IMAGE 001](<../derived/assets/page-0001-image-001.png>)
```

- Otherwise keep a hidden placeholder:

```text
<!-- IMAGE 001 -->
```

Do not:

- summarize
- simplify
- reorder content
- normalize semantics into JSON or prose
- describe diagrams inline inside canonical Markdown

If a table cannot be rendered cleanly as a Markdown table, keep row order and note the limitation inline.

## Trace Rules

`traces/run.trace.yaml` should record:

- run id
- start and finish timestamps
- source id and bundle slug
- operator identity
- prompt path and prompt hash
- output artifact paths
- model id
- validation state
- deviations
- notes such as page count, OCR mode, raster DPI, render format, pages with text layers, and pages with extracted assets

If an operator deviates from the normal prompt or persists page renders for debugging, record that deviation explicitly.

## Smoke Test Strategy

Before a full run, prefer a representative subset:

- one text-heavy page
- one table-heavy page
- one page with figures or mixed layout

If the model drifts into summarization or drops visible page furniture, tighten the prompt before scaling out.

## Validation Checklist

After a run, check:

- `raw/source.pdf` exists and its checksum matches `source.meta.yaml`
- every processed page JSON has `status: ok`
- every processed page JSON has a non-truncated `finish_reason`
- `ocr_markdown` preserves visible layout cues instead of paraphrasing
- image placeholders and extracted asset references line up with `images`
- form pages preserve blank fields, checkbox groups, and repeated columns instead of flattening them
- `derived/renders/` matches the operator's expectations for representative difficult pages
- `canonical/content.md` contains all page markers in order
- `traces/run.trace.yaml` records the final model, prompt, and validation result

If not all pages succeeded, do not rebuild canonical Markdown from partial results.
