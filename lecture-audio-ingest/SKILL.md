---
name: lecture-audio-ingest
description: Transcribe local lecture audio through OpenRouter into Markdown, JSON, and optional Google Drive artifacts.
disable-model-invocation: true
---

# Lecture Audio Ingest

Use this skill to turn local lecture audio into durable transcript artifacts.
Prefer the bundled script for audio conversion, chunking, OpenRouter calls, retry handling, and transcript assembly.

## Core Workflow

1. Resolve the target audio file and confirm it exists.
2. Use `ffprobe` to inspect duration and format when file size or length matters.
3. Choose a model preset:
   - `quality`: `openai/gpt-4o-transcribe` for highest-quality transcripts.
   - `balanced`: `openai/gpt-4o-mini-transcribe` for cheaper high-volume transcription.
   - `fast`: `openai/whisper-large-v3-turbo` for speed and low cost.
   - `robust`: `openai/whisper-large-v3` for noisy or multilingual audio where Whisper robustness matters.
4. Before any real transcription run, tell the user that the audio bytes will be sent to OpenRouter and get explicit approval for that exact file.
5. Run `scripts/transcribe_lecture.py`, passing `--language en` only when the lecture language is known.
6. Review the generated `.md` transcript and `.json` metadata.
7. If the user requested Google Drive output, save the Markdown transcript as a native Google Doc or upload the Markdown file to the requested Drive folder using available Google Drive connector tools. Verify the destination folder or document link before final handoff.

## Command Pattern

Resolve the script path relative to the directory containing this `SKILL.md`:

```bash
python3 scripts/transcribe_lecture.py \
  "/path/to/lecture.m4a" \
  --output-dir "/path/to/output" \
  --preset quality \
  --language en \
  --confirm-external-upload
```

Use `--model <openrouter-model-slug>` to override the preset. Use `--dry-run` to verify chunking and output paths without calling OpenRouter.

Use `$openrouter-api-auth` to place the OpenRouter API key at `~/.config/openrouter/api_key`, where the script reads it by default.

Never put API keys in prompts, command lines, logs, skill files, transcripts, or final answers.
Never run without user consent for the exact file being uploaded.

## Output Contract

The script writes:

- `<title>.transcript.md`: timestamped transcript with model, source, duration, and chunk metadata.
- `<title>.transcript.json`: raw chunk-level response metadata, generation IDs, timings, and transcript text.

For Google Drive delivery, prefer one native Google Doc per source recording, titled:

```text
<source title> transcript
```

If a folder URL is supplied, verify that exact folder first. If the available connector tools cannot place or move files into folders, create the local transcript artifacts and report the folder-placement limitation plainly instead of pretending the upload happened.

## Model Guidance

Do not claim a single model is permanently best. OpenRouter model availability and pricing change.
For current STT request shape and model discovery, read `references/openrouter-stt.md` when adjusting model choices, debugging API errors, or updating this skill.

For important legal, academic, or assessment recordings, use `quality` first. If the run is too slow, too expensive, or blocked by provider availability, retry with `balanced` or `fast` and record the model used in the transcript metadata.

## Long Audio Rules

- Split lecture audio before upload; direct whole-file uploads often time out.
- Default to 5-minute MP3 chunks at mono 16 kHz, 64 kbps.
- Keep chunk timestamps in the transcript so later summaries can cite approximate source time.
- Avoid deleting raw source audio. Temporary converted chunks can be deleted after successful transcript generation.
