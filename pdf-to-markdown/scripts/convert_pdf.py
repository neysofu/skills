#!/usr/bin/env python3
"""Convert a PDF with Firecrawl pdf-inspector and enforce completeness gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


class ConversionError(RuntimeError):
    """Base error for an unsuccessful conversion."""


class BackendMissingError(ConversionError):
    """Raised when pdf2md cannot be located."""


class IncompleteExtractionError(ConversionError):
    """Raised when strict mode rejects incomplete Markdown."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a native-text PDF to Markdown through Firecrawl pdf-inspector. "
            "Strict mode refuses OCR-dependent or encoding-damaged output."
        )
    )
    parser.add_argument("source", nargs="?", type=Path, help="input PDF")
    parser.add_argument("output", nargs="?", type=Path, help="output Markdown")
    parser.add_argument(
        "--backend",
        default="pdf2md",
        help="pdf2md executable name or path (default: pdf2md)",
    )
    parser.add_argument(
        "--select-pages",
        metavar="PAGES",
        help="1-indexed pages such as 1,3,5-10",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="enable pdf-inspector's token-saving Markdown profile",
    )
    parser.add_argument(
        "--no-page-markers",
        action="store_true",
        help="omit <!-- Page N --> markers",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="write Markdown even when selected content needs OCR",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="inspection JSON path (default: <output>.pdf-inspector.json)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing output and metadata files after successful processing",
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="print the resolved backend path and exit",
    )
    return parser


def resolve_backend(value: str) -> str:
    if os.path.dirname(value):
        candidate = Path(value).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
    else:
        resolved = shutil.which(value)
        if resolved:
            return resolved
    raise BackendMissingError(
        f"cannot find executable {value!r}; install with "
        "`cargo install pdf-inspector --version 0.1.7 --locked`"
    )


def parse_page_spec(spec: str) -> set[int]:
    pages: set[int] = set()
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            raise ConversionError(f"invalid page selection: {spec!r}")
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            try:
                start, end = int(start_text), int(end_text)
            except ValueError as exc:
                raise ConversionError(f"invalid page range: {part!r}") from exc
            if start < 1 or end < start:
                raise ConversionError(f"invalid page range: {part!r}")
            pages.update(range(start, end + 1))
        else:
            try:
                page = int(part)
            except ValueError as exc:
                raise ConversionError(f"invalid page number: {part!r}") from exc
            if page < 1:
                raise ConversionError("page numbers are 1-indexed")
            pages.add(page)
    return pages


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    try:
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def default_metadata_path(output: Path) -> Path:
    return output.with_suffix(".pdf-inspector.json")


def ensure_distinct_paths(source: Path, output: Path, metadata: Path) -> None:
    resolved = [path.expanduser().resolve() for path in (source, output, metadata)]
    if len(set(resolved)) != len(resolved):
        raise ConversionError("source, Markdown, and metadata paths must be distinct")


def check_destinations(output: Path, metadata: Path, overwrite: bool) -> None:
    if overwrite:
        return
    existing = [str(path) for path in (output, metadata) if path.exists()]
    if existing:
        raise ConversionError(
            "refusing to replace existing artifact(s): "
            + ", ".join(existing)
            + "; pass --overwrite only when replacement is intended"
        )


def run_backend(
    backend: str,
    source: Path,
    page_spec: str | None,
    compact: bool,
    page_markers: bool,
) -> dict[str, Any]:
    command = [backend, str(source), "--json"]
    if compact:
        command.append("--compact")
    if page_markers:
        command.append("--pages")
    if page_spec:
        command.extend(["--select-pages", page_spec])

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no details"
        raise ConversionError(
            f"pdf2md exited {completed.returncode}: {detail[:2000]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ConversionError("pdf2md returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ConversionError("pdf2md JSON root is not an object")
    if payload.get("error"):
        raise ConversionError(f"pdf2md error: {payload['error']}")
    required = {
        "pdf_type": str,
        "page_count": int,
        "pages_needing_ocr": list,
        "has_encoding_issues": bool,
        "markdown": str,
    }
    invalid = [
        key
        for key, expected_type in required.items()
        if key not in payload
        or not isinstance(payload[key], expected_type)
        or (expected_type is int and isinstance(payload[key], bool))
    ]
    if invalid:
        raise ConversionError(
            "pdf2md JSON does not match the audited contract; invalid field(s): "
            + ", ".join(invalid)
        )
    return payload


def blocking_reasons(
    result: dict[str, Any], selected_pages: set[int] | None
) -> list[str]:
    reasons: list[str] = []
    pdf_type = result.get("pdf_type")
    markdown = result.get("markdown")

    if pdf_type in {"scanned", "image_based"}:
        reasons.append(f"PDF type is {pdf_type}")
    if not isinstance(markdown, str) or not markdown.strip():
        reasons.append("backend returned no Markdown")

    raw_ocr_pages = result.get("pages_needing_ocr", [])
    ocr_pages = {
        page for page in raw_ocr_pages if isinstance(page, int) and not isinstance(page, bool)
    }
    relevant_ocr_pages = ocr_pages if selected_pages is None else ocr_pages & selected_pages
    if relevant_ocr_pages:
        reasons.append(
            "pages need OCR: " + ",".join(str(page) for page in sorted(relevant_ocr_pages))
        )
    if result.get("has_encoding_issues") is True:
        reasons.append("backend detected broken font encodings")
    return reasons


def main() -> int:
    args = build_parser().parse_args()
    try:
        backend = resolve_backend(args.backend)
        if args.check_deps:
            print(backend)
            return 0

        if args.source is None or args.output is None:
            raise ConversionError("source and output are required unless --check-deps is used")

        source = args.source.expanduser()
        output = args.output.expanduser()
        metadata = (args.metadata or default_metadata_path(output)).expanduser()
        if not source.is_file():
            raise ConversionError(f"input PDF does not exist: {source}")
        if source.suffix.lower() != ".pdf":
            raise ConversionError(f"input must have a .pdf extension: {source}")
        if output.suffix.lower() not in {".md", ".markdown"}:
            raise ConversionError(f"output must have a .md or .markdown extension: {output}")
        ensure_distinct_paths(source, output, metadata)
        check_destinations(output, metadata, args.overwrite)

        selected_pages = parse_page_spec(args.select_pages) if args.select_pages else None
        result = run_backend(
            backend=backend,
            source=source,
            page_spec=args.select_pages,
            compact=args.compact,
            page_markers=not args.no_page_markers,
        )
        reasons = blocking_reasons(result, selected_pages)
        markdown = result.get("markdown")
        partial = bool(reasons)
        has_markdown = isinstance(markdown, str) and bool(markdown.strip())
        markdown_written = not partial or (args.allow_partial and has_markdown)

        result_metadata = dict(result)
        result_metadata.pop("markdown", None)

        metadata_payload = {
            "backend": "firecrawl/pdf-inspector:pdf2md",
            "source": {
                "filename": source.name,
                "sha256": file_sha256(source),
            },
            "selection": args.select_pages,
            "profile": "compact" if args.compact else "fidelity",
            "page_markers": not args.no_page_markers,
            "markdown_written": markdown_written,
            "blocking_reasons": reasons,
            "result": result_metadata,
        }

        if partial and markdown_written:
            warning = "<!-- Partial pdf-inspector extraction: " + "; ".join(reasons) + " -->\n\n"
            markdown = warning + (markdown if isinstance(markdown, str) else "")

        if markdown_written:
            assert isinstance(markdown, str)
            atomic_write_text(output, markdown)
        atomic_write_text(metadata, json.dumps(metadata_payload, indent=2, sort_keys=True) + "\n")

        summary = {
            "status": "blocked" if not markdown_written else "partial" if partial else "ok",
            "output": str(output) if markdown_written else None,
            "metadata": str(metadata),
            "blocking_reasons": reasons,
        }
        print(json.dumps(summary, sort_keys=True))
        if partial and not markdown_written:
            raise IncompleteExtractionError(
                "incomplete extraction refused; inspect the metadata sidecar"
            )
        return 0
    except BackendMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except IncompleteExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
