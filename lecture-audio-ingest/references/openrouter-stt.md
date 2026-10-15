# OpenRouter audio implementation notes

Checked 2026-09-24 against the live catalog and documentation. Recheck before changing models or when availability/options fail. Catalog presence is not proof of accuracy on a particular accent.

## Starting model choices

| Stage | Default | Reason and limitation |
| --- | --- | --- |
| Standard ASR | `microsoft/mai-transcribe-2` | Low quoted per-hour cost plus segment and word timing. Validate it on the actual accent and subject. |
| Dual-pass second ASR | `openai/gpt-transcribe` | Different model family for independent comparison. No lecture-specific accuracy claim. |
| Dual-pass reconciliation | `google/gemini-3.1-pro-preview` | Receives both drafts and actual audio. Preview availability and pricing may change. |

The defaults are candidates to validate, not a permanent leaderboard. `assemblyai/universal-3-5-pro` is a September 2026 flagship candidate for English lectures: it accepts 16-bit WAV clips up to 120 seconds and supports free-text prompts, keyterms and context, but it has not been evaluated on the user's recordings. `google/gemini-3.8-flash` is a newer audio-capable alternative for reconciliation. Compare omission rates and difficult spans before switching solely for recency or speed. GPT-4o Transcribe and Whisper remain possible comparison models, not automatic failure fallbacks. An ASR model's language coverage matters more than its overall benchmark rank.

The live cards quote GPT Transcribe at $0.000075/second ($0.27/hour) and MAI-Transcribe 2 at $0.10/hour. Standard mode therefore starts near $0.10 per audio hour before retries; dual-pass ASR starts near $0.37 per hour before reconciliation. Reconciliation has separate audio/text/token pricing and can dominate cost. The script disables reconciliation reasoning and caps completion tokens, but these are guardrails rather than a price guarantee. Preserve and sum reported `usage.cost`; missing cost means unknown, not free.

Sources: [GPT Transcribe](https://openrouter.ai/openai/gpt-transcribe), [MAI-Transcribe 2](https://openrouter.ai/microsoft/mai-transcribe-2), [AssemblyAI Universal-3.5 Pro](https://openrouter.ai/assemblyai/universal-3-5-pro), [Gemini 3.1 Pro](https://openrouter.ai/google/gemini-3.1-pro-preview), [Gemini 3.8 Flash](https://openrouter.ai/google/gemini-3.8-flash).

## API contracts

Use `POST https://openrouter.ai/api/v1/audio/transcriptions` for each draft. Standard mode sends one request per chunk; dual-pass sends two. JSON contains `model`, `input_audio: {data: <base64 bytes>, format: "wav"}`, optional `language`, and `temperature`. The existing JSON approach remains supported; changing to an SDK is not itself a quality improvement. Multipart also works but has a 25 MB upload cap. Provider processing can time out around 60 seconds regardless of a longer client timeout; shorten chunks when this occurs.

Discover transcription models with `GET /api/v1/models?output_modalities=transcription`; the default catalog can omit them. Query `/api/v1/models/<model-id>/endpoints` for provider `tag` values. Discover reconciliation candidates from the normal catalog and require `audio` in `architecture.input_modalities`.

`response_format: "verbose_json"` and `timestamp_granularities: ["segment", "word"]` work for MAI-Transcribe 2. Support is model/provider-specific; GPT-4o Transcribe, for example, rejects verbose JSON. The script requests structured output only for the known MAI default and preserves it raw. Chunk ranges remain honest approximate navigation for reconciled text: rewriting a word invalidates any assumption that old ASR word alignment is exact.

Top-level `prompt` is ignored by the STT endpoint. Vocabulary and other custom options belong under `provider.options`, keyed by the actual endpoint tag. Routing fields such as `only`/`order` do not constrain STT routing. Some providers silently discard unsupported options: test them before relying on them.

`--provider-options-file` accepts a model-to-options map. For example, after verifying these terms against lecture materials:

```json
{
  "microsoft/mai-transcribe-2": {
    "azure": {
      "phraseList": {"phrases": ["EBITDA", "enterprise value"]}
    }
  }
}
```

The script inserts each model's object under `provider.options`. Use the provider's documented schema, not an invented generic glossary field. The local context file is sent to the reconciliation model in dual-pass mode; a hint must never become permission to invent speech.

Dual-pass audio reconciliation uses `POST /api/v1/chat/completions`, with text and `input_audio` content blocks in a user message. The script requests strict JSON Schema output, checks the finish reason, sets reasoning effort to `none`, caps completion at 4,000 tokens by default and retains every raw attempt. OpenRouter notes that schema enforcement varies by provider, so invalid results receive a small bounded retry. Provider timestamps, uncertainty markers and model agreement are evidence for review, not ground truth. Padding defaults to zero after a live pilot reproduced a word from neighboring context. Use separate, wider repair excerpts for suspect joins.

Sources: [STT endpoint and limitations](https://openrouter.ai/docs/guides/overview/multimodal/stt), [audio chat requests](https://openrouter.ai/docs/guides/overview/multimodal/audio), [structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs), [STT catalog](https://openrouter.ai/api/v1/models?output_modalities=transcription).

## Quality evaluation

Use representative excerpts from different parts of a recording, including accent-heavy terms, quiet student questions, a numerical example and a chunk boundary. Keep original audio and raw drafts. Have a listener establish a short corrected reference before reporting word error rate; an old machine transcript is not such a reference. Count materially important errors separately (numbers, sign/negation, units and entity names), and inspect omissions and hallucinated additions. Compare standard output with dual-pass on the same reference before paying for dual-pass across a full lecture.

Keep recordings, excerpts, personal preferences and evaluation transcripts in ignored local storage. Record model IDs, date, settings, actual reported cost, failures and observations. Synthetic speech is useful for API contract tests, but cannot establish quality on accented classroom recordings.
