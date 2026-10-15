---
name: lecture-audio-ingest
description: Transcribe long lectures through OpenRouter with a low-cost default and optional dual-pass audio reconciliation.
disable-model-invocation: true
---

# Lecture Audio Ingest

Transcribe 30–180 minute recordings faithfully in their original language. Preserve substantive repetitions, self-corrections, mistakes, numbers, negation and spoken equations; add punctuation without rewriting the lecture.

Use **standard** mode unless the user explicitly accepts dual-pass cost or a representative pilot shows that one ASR pass is materially inadequate. Standard mode uses one transcription model, five-minute core chunks and bounded concurrency. Dual-pass mode uses two independent ASR drafts plus audio-grounded reconciliation on two-minute chunks.

## Prepare

Resolve the recording and output directory. For a Drive source, use the Google Drive skill to fetch the verified audio. Treat an existing transcript as reference material rather than ground truth. Read [references/openrouter-stt.md](references/openrouter-stt.md) before changing models or API options.

Inspect duration and channels with `ffprobe`. When stereo channels differ in speakers, quality or phase, compare them and select the better channel with `--channel`. Keep the original recording; process it without denoising or time stretching unless an audio comparison supports the change.

Ask for language, subject or vocabulary only when missing and useful. Put dual-pass reconciliation hints in an ignored local context file. Slides can suggest spellings, but the audio establishes what was said.

Tell the user which recording will go to OpenRouter. A request to transcribe identified audio through OpenRouter authorizes that upload. Read credentials only from `~/.config/openrouter/api_key` as specified by `$openrouter-api-auth`; stop when unavailable and never print the key.

## Transcribe

Resolve the script relative to this skill directory. Python 3 and `ffmpeg`/`ffprobe` are required.

```bash
python3 <skill-dir>/scripts/transcribe_lecture.py \
  /path/to/lecture.m4a \
  --output-dir /path/to/output \
  --language en \
  --confirm-external-upload
```

Omit `--language` for unknown or mixed-language audio. Use `--dry-run` to inspect chunk and request counts without reading credentials or uploading audio. For unfamiliar models, accents or recording conditions, first run short excerpts spanning technical speech, numbers and distant questions.

Use `--mode dual-pass` only when the user requested it or accepted its added cost after a failed pilot. For a local problem in an otherwise usable transcript, run dual-pass only over a bounded `--start`/`--end` excerpt in a separate output directory. Apply the resulting acoustic correction to a reviewed copy instead of rerunning the whole lecture.

Core chunks cover the source once without overlap and prefer nearby silence. Padding is off because adjacent speech can leak into the output. Reduce `--jobs` when a provider throttles concurrent standard requests; reduce `--chunk-seconds` in a fresh output directory when longer requests time out.

Successful work is checkpointed atomically. Resume with the identical command plus `--resume`. Changed output-affecting settings require a new output directory. Transport retries are bounded and can incur duplicate charges after a lost response.

## Verify and deliver

The script writes:

- `<title>.transcript.md`: selected transcript text with source chunk ranges.
- `<title>.transcript.json`: source hash, settings, raw model responses, usage and generation IDs; dual-pass runs also retain reconciliation attempts and uncertainty data.
- `<title>.review.md`: unresolved or heuristic boundary/completeness flags.

Read the review file. Check every flagged join, plus the beginning, middle, end and one numerical or technical passage against the source audio. Repair only failed spans. Resolve names, numbers, negations and formulas acoustically; preserve `[unclear]` with its source time when the sound remains ambiguous.

Put corrections in `<title>.reviewed.md` with a local correction log containing source time and evidence. Preserve generated artifacts so resume cannot overwrite editorial work. `complete` means the selected pipeline finished, not that a human verified every word; label pending repairs honestly.

Deliver the transcript and remaining uncertainty. Save to Google Drive only when requested, using the Drive skill and verifying the destination. Keep study notes, summaries and translations outside this transcription workflow.
