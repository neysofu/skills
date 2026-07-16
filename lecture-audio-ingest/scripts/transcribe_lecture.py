#!/usr/bin/env python3
"""Transcribe long lecture audio with OpenRouter speech-to-text models."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OPENROUTER_TRANSCRIPTIONS_URL = "https://openrouter.ai/api/v1/audio/transcriptions"
DEFAULT_API_KEY_FILE = Path.home() / ".config/openrouter/api_key"

PRESET_MODELS = {
    "quality": "openai/gpt-4o-transcribe",
    "balanced": "openai/gpt-4o-mini-transcribe",
    "fast": "openai/whisper-large-v3-turbo",
    "robust": "openai/whisper-large-v3",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk lecture audio and transcribe it with OpenRouter STT."
    )
    parser.add_argument("audio_file", help="Path to a local audio file.")
    parser.add_argument(
        "--output-dir",
        default="transcripts",
        help="Directory for transcript outputs. Defaults to ./transcripts.",
    )
    parser.add_argument("--title", help="Transcript title. Defaults to source stem.")
    parser.add_argument(
        "--preset",
        choices=sorted(PRESET_MODELS),
        default="quality",
        help="Model preset to use when --model is not supplied.",
    )
    parser.add_argument("--model", help="Explicit OpenRouter STT model slug.")
    parser.add_argument(
        "--language",
        help="Optional ISO-639-1 language code, such as en, ja, or it.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="STT sampling temperature. Defaults to 0.",
    )
    parser.add_argument(
        "--chunk-seconds",
        type=int,
        default=300,
        help="Audio seconds per chunk. Defaults to 300.",
    )
    parser.add_argument(
        "--bitrate",
        default="64k",
        help="MP3 chunk bitrate. Defaults to 64k.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Chunk sample rate in Hz. Defaults to 16000.",
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=DEFAULT_API_KEY_FILE,
        help="OpenRouter API key file. Defaults to ~/.config/openrouter/api_key.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Retries per failed chunk for transient API errors.",
    )
    parser.add_argument(
        "--keep-chunks",
        action="store_true",
        help="Keep converted MP3 chunks beside the outputs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Probe, split, and report outputs without calling OpenRouter.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing chunk records from the JSON output when present.",
    )
    parser.add_argument(
        "--confirm-external-upload",
        action="store_true",
        help="Confirm the user approved sending audio bytes to OpenRouter.",
    )
    return parser.parse_args()


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Required tool not found on PATH: {name}")


def run_json(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def ffprobe(path: Path) -> dict[str, Any]:
    return run_json(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,format_name",
            "-of",
            "json",
            str(path),
        ]
    )


def duration_seconds(path: Path) -> float:
    data = ffprobe(path)
    return float(data.get("format", {}).get("duration") or 0.0)


def format_hms(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "lecture"


def split_audio(
    source: Path,
    chunk_dir: Path,
    chunk_seconds: int,
    sample_rate: int,
    bitrate: str,
) -> list[Path]:
    chunk_dir.mkdir(parents=True, exist_ok=True)
    pattern = chunk_dir / "chunk_%04d.mp3"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-map",
        "0:a:0",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-b:a",
        bitrate,
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-reset_timestamps",
        "1",
        str(pattern),
    ]
    subprocess.run(command, check=True)
    chunks = sorted(chunk_dir.glob("chunk_*.mp3"))
    if not chunks:
        raise RuntimeError("ffmpeg did not produce any audio chunks")
    return chunks


def resolve_api_key(api_key_file: Path) -> str:
    try:
        key = api_key_file.expanduser().read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(
            f"Unable to read OpenRouter API key file: {api_key_file}"
        ) from exc
    if not key:
        raise RuntimeError(f"OpenRouter API key file is empty: {api_key_file}")
    return key


def transcribe_chunk(
    chunk_path: Path,
    *,
    api_key: str,
    model: str,
    language: str | None,
    temperature: float,
    max_retries: int,
) -> dict[str, Any]:
    audio_b64 = base64.b64encode(chunk_path.read_bytes()).decode("ascii")
    payload: dict[str, Any] = {
        "model": model,
        "input_audio": {
            "data": audio_b64,
            "format": "mp3",
        },
        "temperature": temperature,
    }
    if language:
        payload["language"] = language

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://agent.local/lecture-audio-ingest",
        "X-Title": "Agent Lecture Audio Ingest",
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        request = urllib.request.Request(
            OPENROUTER_TRANSCRIPTIONS_URL,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_body = response.read().decode("utf-8")
                parsed = json.loads(response_body)
                return {
                    "response": parsed,
                    "generation_id": response.headers.get("X-Generation-Id"),
                    "status": response.status,
                }
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {error_body[:1000]}"
            if exc.code not in {408, 409, 429, 500, 502, 503, 504}:
                break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = repr(exc)

        if attempt < max_retries:
            time.sleep(min(30, 2**attempt))

    raise RuntimeError(f"OpenRouter transcription failed for {chunk_path.name}: {last_error}")


def write_outputs(
    *,
    source: Path,
    title: str,
    output_dir: Path,
    model: str,
    preset: str,
    source_duration: float,
    chunk_seconds: int,
    chunks: list[dict[str, Any]],
    dry_run: bool,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_title = slugify(title)
    md_path = output_dir / f"{safe_title}.transcript.md"
    json_path = output_dir / f"{safe_title}.transcript.json"
    generated_at = datetime.now(timezone.utc).isoformat()

    metadata = {
        "title": title,
        "source_file": str(source),
        "source_size_bytes": source.stat().st_size,
        "duration_seconds": source_duration,
        "duration_hms": format_hms(source_duration),
        "model": model,
        "preset": preset,
        "chunk_seconds": chunk_seconds,
        "generated_at": generated_at,
        "dry_run": dry_run,
        "chunks": chunks,
    }
    json_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        f"# {title} transcript",
        "",
        f"- Source: `{source.name}`",
        f"- Duration: {format_hms(source_duration)}",
        f"- Model: `{model}`",
        f"- Preset: `{preset}`",
        f"- Transcribed at: {generated_at}",
        f"- Chunks: {len(chunks)}",
        "",
        "## Transcript",
        "",
    ]
    for chunk in chunks:
        start = format_hms(float(chunk["start_seconds"]))
        end = format_hms(float(chunk["end_seconds"]))
        lines.append(f"### [{start} - {end}]")
        lines.append("")
        text = chunk.get("text") or ""
        lines.append(text.strip() if text.strip() else "[No transcript text returned.]")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, json_path


def main() -> int:
    args = parse_args()
    require_tool("ffmpeg")
    require_tool("ffprobe")

    source = Path(args.audio_file).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Audio file not found: {source}")
    if not args.dry_run and not args.confirm_external_upload:
        raise SystemExit(
            "Refusing to send audio to OpenRouter without --confirm-external-upload."
        )

    output_dir = Path(args.output_dir).expanduser().resolve()
    title = args.title or source.stem
    model = args.model or PRESET_MODELS[args.preset]
    source_duration = duration_seconds(source)

    chunk_parent = output_dir / "_chunks" if args.keep_chunks else Path(tempfile.mkdtemp())
    chunk_dir = chunk_parent / slugify(source.stem)

    try:
        print(f"Splitting {source.name} ({format_hms(source_duration)}) into MP3 chunks...", flush=True)
        chunk_paths = split_audio(
            source,
            chunk_dir,
            args.chunk_seconds,
            args.sample_rate,
            args.bitrate,
        )
        print(f"Prepared {len(chunk_paths)} chunk(s).", flush=True)

        api_key = None if args.dry_run else resolve_api_key(args.api_key_file)
        chunk_records: list[dict[str, Any]] = []
        output_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = output_dir / f"{slugify(title)}.transcript.json"
        if args.resume and checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            existing_chunks = checkpoint.get("chunks", [])
            if isinstance(existing_chunks, list):
                chunk_records = existing_chunks
                print(f"Loaded {len(chunk_records)} existing chunk record(s).", flush=True)

        completed_indexes = {
            int(record.get("index"))
            for record in chunk_records
            if record.get("text") or args.dry_run
        }
        start_seconds = 0.0

        for index, chunk_path in enumerate(chunk_paths, start=1):
            chunk_duration = duration_seconds(chunk_path)
            end_seconds = min(source_duration, start_seconds + chunk_duration)
            print(
                f"Chunk {index}/{len(chunk_paths)} "
                f"[{format_hms(start_seconds)} - {format_hms(end_seconds)}]",
                flush=True,
            )

            if index in completed_indexes:
                print(f"Skipping chunk {index}; existing transcript found.", flush=True)
                start_seconds = end_seconds
                continue

            record: dict[str, Any] = {
                "index": index,
                "file_name": chunk_path.name,
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "duration_seconds": chunk_duration,
            }
            if args.dry_run:
                record["text"] = ""
                record["generation_id"] = None
                record["usage"] = None
            else:
                assert api_key is not None
                result = transcribe_chunk(
                    chunk_path,
                    api_key=api_key,
                    model=model,
                    language=args.language,
                    temperature=args.temperature,
                    max_retries=args.max_retries,
                )
                response = result["response"]
                record["text"] = response.get("text", "")
                record["generation_id"] = result.get("generation_id")
                record["usage"] = response.get("usage")
            chunk_records.append(record)
            chunk_records.sort(key=lambda item: int(item.get("index", 0)))
            write_outputs(
                source=source,
                title=title,
                output_dir=output_dir,
                model=model,
                preset=args.preset,
                source_duration=source_duration,
                chunk_seconds=args.chunk_seconds,
                chunks=chunk_records,
                dry_run=args.dry_run,
            )
            start_seconds = end_seconds

        md_path, json_path = write_outputs(
            source=source,
            title=title,
            output_dir=output_dir,
            model=model,
            preset=args.preset,
            source_duration=source_duration,
            chunk_seconds=args.chunk_seconds,
            chunks=chunk_records,
            dry_run=args.dry_run,
        )
        print(f"Wrote Markdown transcript: {md_path}")
        print(f"Wrote JSON metadata: {json_path}")
        return 0
    finally:
        if not args.keep_chunks and chunk_parent.exists():
            shutil.rmtree(chunk_parent, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit("Interrupted")
