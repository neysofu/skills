# OpenRouter STT Reference

Use this reference when the lecture-audio-ingest skill needs current OpenRouter speech-to-text behavior.

## Endpoint

OpenRouter supports speech-to-text through:

```text
POST https://openrouter.ai/api/v1/audio/transcriptions
```

The request body is JSON:

```json
{
  "model": "openai/gpt-4o-transcribe",
  "input_audio": {
    "data": "<base64 raw audio bytes>",
    "format": "mp3"
  },
  "language": "en",
  "temperature": 0
}
```

`language` is optional. Use ISO-639-1 codes only when known. The response includes a `text` field and may include usage. The `X-Generation-Id` response header is useful for traceability.

## Discovery

Discover STT models with:

```text
GET https://openrouter.ai/api/v1/models?output_modalities=transcription
```

The public Speech-to-Text collection ranked these options highly in May 2026:

- `openai/gpt-4o-transcribe`: highest-quality default.
- `openai/gpt-4o-mini-transcribe`: lower-cost high-volume option.
- `openai/whisper-large-v3-turbo`: fast and inexpensive.
- `openai/whisper-large-v3`: robust Whisper-family option.

## Formats

Common supported formats include `wav`, `mp3`, `flac`, `m4a`, `ogg`, `webm`, and `aac`.
For long local files, convert chunks to MP3 before sending to reduce payload size and timeout risk.

## Sources

- OpenRouter STT docs: https://openrouter.ai/docs/guides/overview/multimodal/stt
- OpenRouter Speech-to-Text collection: https://openrouter.ai/collections/speech-to-text-models
