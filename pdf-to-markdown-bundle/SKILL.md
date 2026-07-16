---
name: pdf-to-markdown-bundle
description: Faithful PDF-to-Markdown bundle creation with page-image OCR, per-page JSON artifacts, extracted figure assets, canonical Markdown, and run traces. Use when Codex needs to turn any PDF into a source-preserving corpus bundle.
---

# PDF To Markdown Bundle

Convert a PDF into a staged local bundle that keeps the original bytes, a faithful Markdown transcription, per-page OCR records, extracted page-local figure assets, and a reproducible trace. This skill covers only direct PDF -> bundle conversion; it does not cover source discovery, catalog scraping, HTML normalization, or corpus-wide indexing.

## Workflow

1. Initialize a bundle.

```bash
python3 scripts/init_bundle.py /path/to/output/bundle --source-pdf /path/to/input.pdf
```

This creates:

```text
<bundle>/
  source.meta.yaml
  raw/source.pdf
  canonical/content.md
  derived/ocr/
  derived/assets/
  derived/renders/
  traces/run.trace.yaml
```

2. Check local prerequisites before OCR.

```bash
python3 scripts/ocr_pdf_openrouter.py --check-deps
```

If needed, install:

```bash
python3 -m pip install PyYAML PyMuPDF pypdf
```

3. Request a fresh OpenRouter key for the current run only.

```bash
export OPENROUTER_API_KEY='...'
```

Never write that key to repo files, `.env`, trace files, or shell startup files.
If no key is available, stop and ask the user for one before running OCR.
Do not silently fall back to other OCR providers, local OCR workflows, or alternate PDF parsing methods.

4. Smoke test representative pages before large runs.

The default OCR model is `qwen/qwen3-vl-32b-instruct`. Override it with `--model` only when benchmarking or rerunning difficult pages.

```bash
python3 scripts/ocr_pdf_openrouter.py /path/to/bundle \
  --pages 2,8,16 \
  --mode auto \
  --render-format png \
  --dpi 300 \
  --save-renders \
  --max-workers 1
```

Use a small slice first if the PDF mixes prose, tables, diagrams, or fillable-form pages.
For PDFs with a real text layer or interactive form fields, prefer `--mode auto` over `--mode ocr`.

5. Run the full OCR pass when the prompt and page renders look correct.

```bash
python3 scripts/ocr_pdf_openrouter.py /path/to/bundle \
  --mode auto \
  --render-format png \
  --dpi 300 \
  --save-renders \
  --max-workers 2
```

The script writes:

- `derived/ocr/page-*.json`
- `derived/assets/`
- `derived/renders/` when `--save-renders` is enabled
- `canonical/content.md`
- `traces/run.trace.yaml`

6. Validate the output.

- Check every page JSON has `status: ok`.
- Confirm `finish_reason` is not a truncation signal.
- Read `review_notes` for pages with missing figures, noisy text layers, or layout mismatches.
- Inspect `page_profile` and `text_layer.used_in_prompt` on form-heavy or text-layer PDFs.
- Inspect `derived/renders/` for hard pages so you can see exactly what the OCR model saw.
- Confirm `canonical/content.md` preserves page order, headers, footers, tables, lists, and image placeholders or exact asset links.
- Re-run with `--overwrite-ocr` after changing the prompt, model, or DPI.

If only a subset of pages has been processed, the script leaves `canonical/content.md` alone until all pages have valid OCR results.

## Decision Notes

- Prefer this skill when a PDF must become an audit-friendly local corpus, not just extracted text.
- Prefer a simpler extraction path when the PDF already has a clean text layer and page-faithful Markdown is unnecessary.
- This skill is OpenRouter-keyed. If `OPENROUTER_API_KEY` is missing, ask for a fresh key and stop instead of switching to another method.
- For fillable forms, preserve blank lines, checkbox groups, matrices, signature lines, and repeated applicant sections instead of flattening them into prose.
- Keep diagrams and figures as exact image references or hidden markers in canonical Markdown. Do not replace them with prose descriptions.
- Re-run only affected pages while iterating on prompt or model choices.

## References

- Read `references/pdf-workflow.md` for the artifact contract, page JSON schema, and validation checklist.
- Read `references/ocr-pdf-page.md` when you need the OCR prompt text or want to tune it.
