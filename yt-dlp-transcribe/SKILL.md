---
name: yt-dlp-transcribe
description: Download and clean YouTube caption tracks into transcript artifacts.
disable-model-invocation: true
---

# YT-DLP Transcribe

Use this skill to produce a clean transcript artifact from YouTube caption tracks. Prefer existing captions/subtitles over audio transcription. Do not invent transcript text if captions are unavailable.

## Workflow

1. Create or choose an output directory in the user's workspace.
2. Run `scripts/download_captions.py` to fetch caption files only:

```bash
python /path/to/yt-dlp-transcribe/scripts/download_captions.py "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir ./transcript
```

3. If the download fails because of sandboxed/network access, rerun the same command with the required network approval.
4. If `yt-dlp` is missing or stale and YouTube extraction fails, install a workspace-local current copy after approval:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade yt-dlp
python /path/to/yt-dlp-transcribe/scripts/download_captions.py URL --yt-dlp ./.venv/bin/yt-dlp --output-dir ./transcript
```

5. Clean the selected caption file:

```bash
python /path/to/yt-dlp-transcribe/scripts/clean_transcript.py ./transcript/*.vtt --output-dir ./transcript/clean
```

6. Deliver both raw and cleaned paths. Mention if captions are auto-generated, translated, unavailable, or manually authored.

## Download Rules

- Always use subtitle-only options: `--skip-download`, `--write-subs`, and `--write-auto-subs`.
- Use `--no-config` so local yt-dlp config cannot accidentally download media or alter output.
- Use `--no-check-formats` to reduce YouTube format probe failures when only captions are needed.
- Prefer language `en-orig,en,en.*` for English requests. Avoid `all` unless the user explicitly asks for every language; downloading every auto-translation can trigger rate limits.
- If the requested language is unavailable, run with `--list-subs` and choose the best exposed caption track with the user-visible language code.
- Keep the raw caption file. It is the audit source for the cleaned transcript.

## Cleanup Standard

Use `scripts/clean_transcript.py` as the default reproducible cleanup pass. It:

- parses VTT, SRT, or YouTube JSON3 captions;
- removes WebVTT/SRT headers, cue timings, inline timestamp tags, cue styling, and HTML entities;
- collapses YouTube rolling-caption duplicates using token suffix/prefix overlap;
- preserves speaker markers such as `>>` when present;
- groups readable paragraphs by speaker turns, pauses, punctuation, and paragraph length;
- emits Markdown with paragraph timestamps plus plain text without timestamps.

After the script, make only conservative manual fixes when clearly supported by the transcript context, such as obvious company/product capitalization or a repeated caption artifact. Do not paraphrase, summarize, reorder, assign speaker names, or remove meaningful hesitations unless the user asks for an edited transcript.

For stricter "high quality" or "publication-ready" requests, read `references/quality.md` before doing the manual review pass.

## Output Expectations

Return the cleaned `.md` as the primary transcript and the `.txt` as a copy/paste friendly version. Also report the raw caption path and any notable warnings from `yt-dlp`, such as missing JavaScript runtime, stale version, rate limiting, or no captions.

For transcript summaries, create the clean transcript first, then summarize from the cleaned artifact and keep the artifact paths in the final answer.
