#!/usr/bin/env python3
"""Clean VTT/SRT/JSON3 caption files into readable transcript artifacts."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path


TIME_RE = re.compile(
    r"(?P<start>(?:\d+:)?\d{2}:\d{2}[\.,]\d{3})\s+-->\s+"
    r"(?P<end>(?:\d+:)?\d{2}:\d{2}[\.,]\d{3})"
)
INLINE_TS_RE = re.compile(r"<\d{1,2}:\d{2}:\d{2}[\.,]\d{3}>")
TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Cue:
    start: float
    end: float
    text: str


@dataclass
class Paragraph:
    start: float
    text: str


def parse_time(value: str) -> float:
    value = value.replace(",", ".")
    parts = value.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = "0"
        minutes, seconds = parts
    else:
        raise ValueError(f"unsupported timestamp: {value}")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def clean_cue_text(text: str) -> str:
    text = INLINE_TS_RE.sub("", text)
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("\ufeff", "").replace("\u200b", "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_vtt_or_srt(path: Path) -> list[Cue]:
    cues: list[Cue] = []
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = TIME_RE.search(line)
        if not match:
            i += 1
            continue

        start = parse_time(match.group("start"))
        end = parse_time(match.group("end"))
        i += 1
        payload: list[str] = []
        while i < len(lines) and lines[i].strip() != "":
            payload.append(lines[i].strip())
            i += 1

        text = clean_cue_text(" ".join(payload))
        if text:
            cues.append(Cue(start=start, end=end, text=text))
        i += 1
    return cues


def parse_json3(path: Path) -> list[Cue]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    cues: list[Cue] = []
    for event in data.get("events", []):
        segments = event.get("segs") or []
        text = clean_cue_text("".join(segment.get("utf8", "") for segment in segments))
        if not text:
            continue
        start = float(event.get("tStartMs", 0)) / 1000
        duration = float(event.get("dDurationMs", 0)) / 1000
        cues.append(Cue(start=start, end=start + duration, text=text))
    return cues


def parse_captions(path: Path) -> list[Cue]:
    suffix = path.suffix.lower()
    if suffix == ".json3":
        return parse_json3(path)
    if suffix in {".vtt", ".srt"}:
        return parse_vtt_or_srt(path)
    raise ValueError(f"unsupported caption format: {path.suffix}")


def token_key(token: str) -> str:
    key = re.sub(r"[\W_]+", "", token.lower())
    return key or token


def find_overlap(existing: list[str], incoming: list[str], max_overlap: int = 120) -> int:
    limit = min(len(existing), len(incoming), max_overlap)
    for size in range(limit, 0, -1):
        if [token_key(t) for t in existing[-size:]] == [
            token_key(t) for t in incoming[:size]
        ]:
            return size
    return 0


def ends_sentence(tokens: list[str]) -> bool:
    if not tokens:
        return False
    return bool(re.search(r'[.!?]["\')\]]?$', tokens[-1]))


def word_count(tokens: list[str]) -> int:
    return sum(1 for token in tokens if re.search(r"[A-Za-z0-9]", token))


def format_text(tokens: list[str]) -> str:
    text = " ".join(tokens)
    text = re.sub(r"\s+([,.;:!?%])", r"\1", text)
    text = re.sub(r"([(\[{])\s+", r"\1", text)
    text = re.sub(r"\s+([)\]}])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_paragraphs(
    cues: list[Cue],
    max_gap: float,
    min_words: int,
    max_words: int,
) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    current: list[str] = []
    history: list[str] = []
    current_start = 0.0
    last_end: float | None = None

    def flush() -> None:
        nonlocal current, current_start, history
        text = format_text(current)
        if text:
            paragraphs.append(Paragraph(start=current_start, text=text))
            history = (history + current)[-160:]
        current = []

    for cue in cues:
        incoming = cue.text.split()
        if not incoming:
            continue

        if (
            current
            and last_end is not None
            and cue.start - last_end > max_gap
            and (word_count(current) >= min_words or ends_sentence(current))
        ):
            flush()

        if not current:
            current_start = cue.start
            overlap = find_overlap(history, incoming) if history else 0
        else:
            overlap = find_overlap(current, incoming)
            if overlap == 0 and incoming[:1] == [">>"] and not ends_sentence(current):
                incoming = incoming[1:]
                overlap = find_overlap(current, incoming)

        added = incoming[overlap:]
        if not added:
            last_end = cue.end
            continue

        for token in added:
            if token == ">>" and current:
                if ends_sentence(current) or word_count(current) >= min_words:
                    flush()
                    current_start = cue.start
                else:
                    continue
            if not current:
                current_start = cue.start
            current.append(token)

        if word_count(current) >= max_words and ends_sentence(current):
            flush()

        last_end = cue.end

    if current:
        flush()

    return paragraphs


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def write_outputs(
    input_path: Path,
    paragraphs: list[Paragraph],
    output_dir: Path,
    basename: str | None,
    timestamps: bool,
    header: bool,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = basename or f"{input_path.stem}.clean"
    md_path = output_dir / f"{stem}.md"
    txt_path = output_dir / f"{stem}.txt"

    md_lines: list[str] = []
    if header:
        md_lines += [
            "# Transcript",
            "",
            f"Source captions: `{input_path.name}`",
            "",
        ]
    for paragraph in paragraphs:
        if timestamps:
            md_lines.append(f"**[{format_timestamp(paragraph.start)}]** {paragraph.text}")
        else:
            md_lines.append(paragraph.text)
        md_lines.append("")

    txt_lines: list[str] = []
    for paragraph in paragraphs:
        if timestamps:
            txt_lines.append(f"[{format_timestamp(paragraph.start)}] {paragraph.text}")
        else:
            txt_lines.append(paragraph.text)
        txt_lines.append("")

    md_path.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")
    txt_path.write_text("\n".join(txt_lines).rstrip() + "\n", encoding="utf-8")
    return [md_path, txt_path]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean caption files into Markdown and plain-text transcripts."
    )
    parser.add_argument("captions", nargs="+", help="Caption files: .vtt, .srt, .json3")
    parser.add_argument("--output-dir", default=".", help="Directory for cleaned files")
    parser.add_argument("--basename", help="Output basename for one input file")
    parser.add_argument("--max-gap", type=float, default=2.5)
    parser.add_argument("--min-words", type=int, default=18)
    parser.add_argument("--max-words", type=int, default=120)
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Do not prefix paragraphs with timestamps.",
    )
    parser.add_argument("--no-header", action="store_true", help="Skip Markdown header")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    written: list[Path] = []

    caption_paths = [Path(value).expanduser().resolve() for value in args.captions]
    if args.basename and len(caption_paths) != 1:
        raise SystemExit("--basename can only be used with one input file")

    for caption_path in caption_paths:
        cues = parse_captions(caption_path)
        if not cues:
            print(f"No cues found in {caption_path}")
            continue
        paragraphs = build_paragraphs(
            cues,
            max_gap=args.max_gap,
            min_words=args.min_words,
            max_words=args.max_words,
        )
        written.extend(
            write_outputs(
                input_path=caption_path,
                paragraphs=paragraphs,
                output_dir=output_dir,
                basename=args.basename,
                timestamps=not args.no_timestamps,
                header=not args.no_header,
            )
        )

    if not written:
        return 2

    print("Clean transcript files:")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
