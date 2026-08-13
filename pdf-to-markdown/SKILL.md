---
name: pdf-to-markdown
description: Convert a local PDF to validated Markdown with Firecrawl pdf-inspector.
disable-model-invocation: true
---

# PDF To Markdown

Convert a local PDF with Firecrawl's `pdf-inspector` backend. This path is fast, local, and keyless; its contract is native-text extraction, not OCR or visual reconstruction.

## Workflow

1. Resolve the input PDF, a new output `.md` path, and this skill's directory. Check the backend before conversion:

```bash
python3 <skill-dir>/scripts/convert_pdf.py --check-deps
```

If `pdf2md` is missing, install the audited backend release, then repeat the check:

```bash
cargo install pdf-inspector --version 0.1.7 --locked
```

The check is complete when it prints the resolved `pdf2md` executable.

2. Run a fidelity-first conversion:

```bash
python3 <skill-dir>/scripts/convert_pdf.py \
  /path/to/input.pdf \
  /path/to/output.md
```

The wrapper inserts `<!-- Page N -->` markers and writes `output.pdf-inspector.json` beside the Markdown. Use the following options only when the request calls for them:

- `--select-pages 1,3,5-10` for a page subset.
- `--compact` when token economy is more important than source-character fidelity.
- `--no-page-markers` when the user wants continuous Markdown.
- `--overwrite` when the user has authorized replacing existing output artifacts.
- `--allow-partial` only when the user explicitly accepts missing OCR-dependent content.

The conversion step is complete only when the wrapper exits zero and reports `status: ok` or explicitly permitted `status: partial`.

3. Validate the result.

- Read the sidecar and confirm `markdown_written` is `true`.
- For a complete conversion, confirm `blocking_reasons` is empty, `result.has_encoding_issues` is `false`, and no selected page appears in `result.pages_needing_ocr`.
- Confirm the Markdown is non-empty and inspect its beginning and end. If the sidecar lists tables or columns, inspect at least one listed page.
- Treat images and diagrams as outside this backend's completeness contract; it extracts their surrounding native text but does not reconstruct their visual content.

The skill is complete when the output passes every applicable check and the final response links both artifacts.

## Failure Gate

Exit code `2` means `pdf-inspector` found scanned pages, image-only pages, broken encodings, or no extractable Markdown. Read `blocking_reasons`, `result.pages_needing_ocr`, and `result.ocr_reasons_by_page` from the sidecar, report the exact limitation, and stop with the Markdown unwritten. Use the OCR bundle skill only after the user chooses that separate path.

Exit code `3` means the backend is unavailable. Install it or report the missing prerequisite. For any other nonzero exit, report the backend error and leave existing artifacts intact.
