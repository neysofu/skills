#!/usr/bin/env python3
"""Download YouTube captions with yt-dlp, without downloading video/audio."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


CAPTION_EXTS = {".vtt", ".srt", ".json3", ".ttml", ".srv1", ".srv2", ".srv3"}


def find_ytdlp(explicit: str | None) -> str:
    if explicit:
        return explicit

    local = Path.cwd() / ".venv" / "bin" / "yt-dlp"
    if local.exists():
        return str(local)

    found = shutil.which("yt-dlp")
    if found:
        return found

    raise SystemExit(
        "yt-dlp was not found. Install it globally or create a workspace-local "
        "virtualenv and pass --yt-dlp ./.venv/bin/yt-dlp."
    )


def caption_files(output_dir: Path) -> set[Path]:
    if not output_dir.exists():
        return set()
    return {
        path.resolve()
        for path in output_dir.iterdir()
        if path.is_file() and path.suffix.lower() in CAPTION_EXTS
    }


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download YouTube caption/subtitle files with yt-dlp only."
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for raw caption files. Default: current directory.",
    )
    parser.add_argument(
        "--langs",
        default="en-orig,en,en.*",
        help="yt-dlp subtitle language selector. Default: en-orig,en,en.*",
    )
    parser.add_argument(
        "--sub-format",
        default="vtt",
        help="Subtitle format preference passed to yt-dlp. Default: vtt",
    )
    parser.add_argument("--yt-dlp", help="Path to yt-dlp executable")
    parser.add_argument("--cookies", help="Path to cookies file for gated videos")
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser name for yt-dlp --cookies-from-browser, e.g. chrome",
    )
    parser.add_argument(
        "--list-subs",
        action="store_true",
        help="List available subtitles instead of downloading them.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    ytdlp = find_ytdlp(args.yt_dlp)

    if args.list_subs:
        cmd = [ytdlp, "--no-config", "--no-playlist", "--skip-download", "--list-subs"]
        if args.cookies:
            cmd += ["--cookies", args.cookies]
        if args.cookies_from_browser:
            cmd += ["--cookies-from-browser", args.cookies_from_browser]
        cmd.append(args.url)
        result = run(cmd)
        print(result.stdout, end="")
        return result.returncode

    before = caption_files(output_dir)
    started = time.time()
    output_template = str(output_dir / "%(title).140B [%(id)s].%(ext)s")

    cmd = [
        ytdlp,
        "--no-config",
        "--no-check-formats",
        "--no-playlist",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        args.langs,
        "--sub-format",
        args.sub_format,
        "-o",
        output_template,
    ]
    if args.cookies:
        cmd += ["--cookies", args.cookies]
    if args.cookies_from_browser:
        cmd += ["--cookies-from-browser", args.cookies_from_browser]
    cmd.append(args.url)

    result = run(cmd)
    print(result.stdout, end="")

    after = caption_files(output_dir)
    created = sorted(after - before)
    touched = sorted(path for path in after if path.stat().st_mtime >= started - 1)
    paths = created or touched

    if paths:
        print("\nCaption files:")
        for path in paths:
            print(path)
        return result.returncode

    print(
        "\nNo caption files were created. Run again with --list-subs to inspect "
        "available caption languages, or choose another --langs value.",
        file=sys.stderr,
    )
    return result.returncode or 2


if __name__ == "__main__":
    raise SystemExit(main())
