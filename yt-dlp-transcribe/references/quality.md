# Transcript Quality Notes

Use these rules when a user asks for "high quality", "clean", "publication-ready", or similar transcript output.

- Preserve meaning and sequence. The cleaned transcript is not a rewrite.
- Keep raw captions next to cleaned outputs so edits can be audited.
- Prefer native/manual captions over auto-generated captions. Prefer original-language auto captions over auto-translated captions.
- Remove caption mechanics: cue numbers, timings, WebVTT metadata, inline word timestamps, styling tags, and duplicate rolling text.
- Keep speaker markers if the captions provide them. Do not infer speaker names from voice or context unless the text explicitly identifies them.
- Normalize obvious entities and whitespace: `&gt;&gt;` to `>>`, repeated spaces to one space, blank caption cues removed.
- Make a separate note for unresolved uncertainty rather than silently "fixing" uncertain words.
