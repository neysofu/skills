#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT_PATH = SKILL_ROOT / "references" / "ocr-pdf-page.md"
DEFAULT_API_URL = "https://openrouter.ai/api/v1/chat/completions"
USER_AGENT = "Codex PDF OCR Bundle/1.0"
FULL_PAGE_IMAGE_THRESHOLD = 0.95
DEFAULT_RENDER_FORMAT = "png"
DEFAULT_DPI = 300
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_INITIAL_RETRY_SECONDS = 2.0
DEFAULT_MAX_COMPLETION_TOKENS = 8192
DEFAULT_OCR_MODE = "auto"
TEXT_LAYER_PROMPT_CHAR_LIMIT = 12000
TEXT_LAYER_MIN_CHARS = 80
FORM_ANNOTATION_THRESHOLD = 8
SMALL_CONTROL_MAX_WIDTH = 24.0
SMALL_CONTROL_MAX_HEIGHT = 24.0
DENSE_FORM_MIN_DPI = 450
SCAN_MIN_DPI = 400
TRUNCATED_FINISH_REASONS = {"length", "max_tokens"}
LEGACY_IMAGE_PLACEHOLDER_RE = re.compile(r"\[\[IMAGE (?P<number>\d{3})(?P<attrs>(?: \| [^\]]+)*)\]\]")
LEGACY_IMAGE_ATTR_RE = re.compile(r'([a-z_]+)="([^"]+)"')
IMAGE_COMMENT_RE = re.compile(r"<!--\s*IMAGE\s+(\d{3})(?::\s*[^>]*)?\s*-->")
IMAGE_MARKDOWN_RE = re.compile(r"!\[IMAGE (\d{3})\]\(")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_ext(ext: str | None) -> str:
    if not ext:
        return "bin"
    clean = "".join(ch for ch in ext.lower() if ch.isalnum())
    return clean or "bin"


def media_type_for_render_format(render_format: str) -> str:
    if render_format == "png":
        return "image/png"
    if render_format == "jpeg":
        return "image/jpeg"
    raise ValueError(f"Unsupported render format: {render_format}")


def round_bbox(bbox: tuple[float, float, float, float] | list[float] | None) -> list[float] | None:
    if bbox is None:
        return None
    return [round(float(value), 2) for value in bbox]


def escape_markdown_image_alt(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def canonical_asset_href(bundle_relative_path: str) -> str:
    return (PurePosixPath("..") / PurePosixPath(bundle_relative_path)).as_posix()


def canonical_markdown_image(alt: str, bundle_relative_path: str) -> str:
    return f"![{escape_markdown_image_alt(alt)}](<{canonical_asset_href(bundle_relative_path)}>)"


def canonical_image_comment(image_index: int) -> str:
    return f"<!-- IMAGE {image_index:03d} -->"


def placeholder_attrs(raw_attrs: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in LEGACY_IMAGE_ATTR_RE.finditer(raw_attrs)}


def normalize_legacy_image_placeholders(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        image_index = int(match.group("number"))
        attrs = placeholder_attrs(match.group("attrs") or "")
        asset_path = attrs.get("asset") or attrs.get("source")
        alt = attrs.get("alt") or f"IMAGE {image_index:03d}"
        if asset_path:
            return canonical_markdown_image(alt, asset_path)
        return canonical_image_comment(image_index)

    return LEGACY_IMAGE_PLACEHOLDER_RE.sub(replace, markdown)


def ensure_relative_to_bundle(bundle_dir: Path, path: Path) -> str:
    return path.relative_to(bundle_dir).as_posix()


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    yaml = require_yaml()
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=120), encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    yaml = require_yaml()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_fitz():
    try:
        import fitz  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit("PyMuPDF is required. Install `PyMuPDF` and rerun.") from exc
    return fitz


def require_yaml():
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit("PyYAML is required. Install `PyYAML` and rerun.") from exc
    return yaml


def require_pypdf():
    try:
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        from pypdf import PdfReader  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit("pypdf is required. Install `pypdf` and rerun.") from exc
    return PdfReader


def resolve_pdf_object(value: Any) -> Any:
    return value.get_object() if hasattr(value, "get_object") else value


def sanitize_text_layer_text(text: str) -> str:
    sanitized = "".join(ch if ord(ch) >= 32 or ch in "\n\r\t" else " " for ch in text)
    return sanitized.replace("\r\n", "\n").replace("\r", "\n").strip()


def build_empty_text_layer() -> dict[str, Any]:
    return {
        "has_text": False,
        "char_count": 0,
        "control_character_count": 0,
        "control_character_codes": [],
        "annotation_count": 0,
        "text_sha256": None,
        "prompt_text": "",
    }


def extract_text_layers(pdf_path: Path) -> dict[int, dict[str, Any]]:
    PdfReader = require_pypdf()
    reader = PdfReader(pdf_path.as_posix())
    pages: dict[int, dict[str, Any]] = {}

    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        prompt_text = sanitize_text_layer_text(raw_text)
        control_character_codes = sorted({ord(ch) for ch in raw_text if ord(ch) < 32 and ch not in "\n\r\t"})
        control_character_count = sum(1 for ch in raw_text if ord(ch) < 32 and ch not in "\n\r\t")
        annots = resolve_pdf_object(page.get("/Annots"))
        annotation_count = len(annots) if isinstance(annots, list) else 0

        pages[page_number] = {
            "has_text": bool(prompt_text),
            "char_count": len(prompt_text),
            "control_character_count": control_character_count,
            "control_character_codes": control_character_codes,
            "annotation_count": annotation_count,
            "text_sha256": sha256_bytes(prompt_text.encode("utf-8")) if prompt_text else None,
            "prompt_text": prompt_text[:TEXT_LAYER_PROMPT_CHAR_LIMIT],
        }

    return pages


def classify_page(page_images: list[dict[str, Any]], text_layer: dict[str, Any]) -> list[str]:
    profile: list[str] = []
    if text_layer.get("annotation_count", 0) >= FORM_ANNOTATION_THRESHOLD:
        profile.append("fillable_form")
    if text_layer.get("char_count", 0) >= 1800:
        profile.append("dense_text")
    if text_layer.get("control_character_count", 0) > 0:
        profile.append("noisy_text_layer")
    if any(image.get("kind") == "full_page_scan" for image in page_images):
        profile.append("full_page_scan")
    profile.append("text_layer_present" if text_layer.get("has_text") else "ocr_primary")
    return profile


def should_attach_text_layer(mode: str, text_layer: dict[str, Any]) -> bool:
    if mode == "ocr":
        return False
    if not text_layer.get("has_text"):
        return False
    if mode == "hybrid":
        return True
    return (
        text_layer.get("char_count", 0) >= TEXT_LAYER_MIN_CHARS
        or text_layer.get("annotation_count", 0) >= FORM_ANNOTATION_THRESHOLD
    )


def effective_dpi_for_page(base_dpi: int, page_profile: list[str], text_layer: dict[str, Any]) -> int:
    dpi = base_dpi
    if "full_page_scan" in page_profile:
        dpi = max(dpi, SCAN_MIN_DPI)
    if "fillable_form" in page_profile and text_layer.get("annotation_count", 0) >= 40:
        dpi = max(dpi, DENSE_FORM_MIN_DPI)
    return dpi


def prompt_user_for_key_message() -> str:
    return (
        "OPENROUTER_API_KEY is not set. Stop and ask for a fresh OpenRouter key for this run before doing any OCR. "
        "Keep it session-scoped only, and do not store it in files, traces, or shell startup configuration. "
        "Do not fall back to any other OCR provider, PDF parser, or local OCR workflow."
    )


def parse_pages_spec(spec: str, page_count: int) -> list[int]:
    pages: set[int] = set()
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise SystemExit(f"Invalid page range: {part}")
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    normalized = sorted(page for page in pages if 1 <= page <= page_count)
    if not normalized:
        raise SystemExit("No valid pages were selected.")
    return normalized


@dataclass
class BundlePaths:
    bundle_dir: Path
    source_pdf: Path
    ocr_dir: Path
    assets_dir: Path
    renders_dir: Path
    canonical_path: Path
    trace_path: Path
    source_meta_path: Path


class OpenRouterTransientError(RuntimeError):
    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OCR a PDF bundle into canonical Markdown plus per-page JSON artifacts.")
    parser.add_argument("bundle_dir", nargs="?", help="Bundle directory containing raw/source.pdf.")
    parser.add_argument("--source-pdf", help="Optional local PDF to copy into raw/source.pdf before processing.")
    parser.add_argument("--prompt-path", default=str(DEFAULT_PROMPT_PATH), help="Prompt file for OCR page requests.")
    parser.add_argument("--model", default="qwen/qwen3-vl-32b-instruct", help="OpenRouter model id.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="OpenRouter chat completions endpoint.")
    parser.add_argument(
        "--mode",
        choices=["auto", "ocr", "hybrid"],
        default=DEFAULT_OCR_MODE,
        help="`ocr` sends only the page image, `hybrid` also includes the embedded PDF text layer, and `auto` uses it when useful.",
    )
    parser.add_argument("--pages", help="Optional page selection such as 1-3,7,9.")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI, help="Rasterization DPI.")
    parser.add_argument(
        "--render-format",
        choices=["png", "jpeg"],
        default=DEFAULT_RENDER_FORMAT,
        help="Raster image format sent to the OCR model.",
    )
    parser.add_argument(
        "--save-renders",
        action="store_true",
        help="Persist rendered page images under derived/renders/ for debugging and quality review.",
    )
    parser.add_argument("--max-workers", type=int, default=8, help="Maximum concurrent OCR requests.")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="HTTP timeout per OCR request.")
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS, help="Maximum OCR attempts per page.")
    parser.add_argument(
        "--max-completion-tokens",
        type=int,
        default=DEFAULT_MAX_COMPLETION_TOKENS,
        help="Maximum completion tokens requested from the OCR model.",
    )
    parser.add_argument(
        "--initial-retry-seconds",
        type=float,
        default=DEFAULT_INITIAL_RETRY_SECONDS,
        help="Initial retry delay for transient provider errors.",
    )
    parser.add_argument("--overwrite-ocr", action="store_true", help="Re-run OCR even if page JSON already exists.")
    parser.add_argument("--check-deps", action="store_true", help="Report local dependency status and exit.")
    return parser.parse_args()


def build_paths(bundle_dir: Path) -> BundlePaths:
    return BundlePaths(
        bundle_dir=bundle_dir,
        source_pdf=bundle_dir / "raw/source.pdf",
        ocr_dir=bundle_dir / "derived/ocr",
        assets_dir=bundle_dir / "derived/assets",
        renders_dir=bundle_dir / "derived/renders",
        canonical_path=bundle_dir / "canonical/content.md",
        trace_path=bundle_dir / "traces/run.trace.yaml",
        source_meta_path=bundle_dir / "source.meta.yaml",
    )


def dependency_report(prompt_path: Path) -> tuple[int, dict[str, Any]]:
    report = {
        "prompt_path": prompt_path.as_posix(),
        "prompt_exists": prompt_path.exists(),
        "yaml_available": False,
        "pymupdf_available": False,
        "pypdf_available": False,
        "openrouter_key_present": bool(os.environ.get("OPENROUTER_API_KEY")),
    }
    try:
        require_yaml()
        report["yaml_available"] = True
    except SystemExit:
        report["yaml_available"] = False
    try:
        require_fitz()
        report["pymupdf_available"] = True
    except SystemExit:
        report["pymupdf_available"] = False
    try:
        require_pypdf()
        report["pypdf_available"] = True
    except SystemExit:
        report["pypdf_available"] = False
    exit_code = (
        0
        if report["prompt_exists"] and report["yaml_available"] and report["pymupdf_available"] and report["pypdf_available"]
        else 1
    )
    return exit_code, report


def prepare_bundle(paths: BundlePaths, source_pdf_arg: str | None) -> None:
    paths.ocr_dir.mkdir(parents=True, exist_ok=True)
    paths.assets_dir.mkdir(parents=True, exist_ok=True)
    paths.renders_dir.mkdir(parents=True, exist_ok=True)
    paths.canonical_path.parent.mkdir(parents=True, exist_ok=True)
    paths.trace_path.parent.mkdir(parents=True, exist_ok=True)

    if source_pdf_arg:
        source_pdf = Path(source_pdf_arg).expanduser().resolve()
        if not source_pdf.exists():
            raise SystemExit(f"Source PDF does not exist: {source_pdf}")
        if source_pdf != paths.source_pdf:
            shutil.copyfile(source_pdf, paths.source_pdf)
    if not paths.source_pdf.exists():
        raise SystemExit(f"Missing bundle source PDF: {paths.source_pdf}")


def render_page_image(
    pdf_path: Path,
    page_number: int,
    dpi: int,
    render_format: str,
    render_path: Path | None,
) -> dict[str, Any]:
    fitz = require_fitz()
    doc = fitz.open(pdf_path.as_posix())
    try:
        page = doc[page_number - 1]
        pixmap = page.get_pixmap(dpi=dpi, alpha=False)
        image_bytes = pixmap.tobytes(render_format)
        if render_path is not None:
            render_path.write_bytes(image_bytes)
        return {
            "bytes": image_bytes,
            "width": int(pixmap.width),
            "height": int(pixmap.height),
            "sha256": sha256_bytes(image_bytes),
        }
    finally:
        doc.close()


def _bbox_sort_key(bbox: Any) -> tuple[float, float, float, float]:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return (float("inf"), float("inf"), float("inf"), float("inf"))
    return (float(bbox[1]), float(bbox[0]), float(bbox[3]), float(bbox[2]))


def extract_linkable_images(doc, bundle_dir: Path, assets_dir: Path) -> dict[int, list[dict[str, Any]]]:
    asset_cache: dict[str, str] = {}
    pages: dict[int, list[dict[str, Any]]] = {}

    for page_number, page in enumerate(doc, start=1):
        page_area = max(float(page.rect.width * page.rect.height), 1.0)
        page_dict = page.get_text("dict")
        image_blocks = [block for block in page_dict.get("blocks", []) if block.get("type") == 1]
        image_blocks.sort(key=lambda block: _bbox_sort_key(block.get("bbox")))

        page_images: list[dict[str, Any]] = []
        for block_index, block in enumerate(image_blocks, start=1):
            bbox = round_bbox(block.get("bbox"))
            width = float(block.get("bbox", [0, 0, 0, 0])[2] - block.get("bbox", [0, 0, 0, 0])[0])
            height = float(block.get("bbox", [0, 0, 0, 0])[3] - block.get("bbox", [0, 0, 0, 0])[1])
            area_ratio = max(width, 0.0) * max(height, 0.0) / page_area

            image_bytes = block.get("image")
            asset_path: str | None = None
            extractable = True
            kind = "embedded_raster"
            notes: list[str] = []

            if width <= SMALL_CONTROL_MAX_WIDTH and height <= SMALL_CONTROL_MAX_HEIGHT:
                extractable = False
                kind = "small_form_control"
                notes.append("Tiny repeated control icon ignored for image-linking and placeholder reconciliation.")
            elif area_ratio >= FULL_PAGE_IMAGE_THRESHOLD:
                extractable = False
                kind = "full_page_scan"
                notes.append("Image occupies most of the page and is treated as the page scan, not a linkable figure asset.")
            elif not image_bytes:
                extractable = False
                kind = "unrecoverable_image_block"
                notes.append("Visible image block had no recoverable binary payload.")
            else:
                digest = sha256_bytes(image_bytes)
                ext = sanitize_ext(block.get("ext"))
                asset_name = asset_cache.get(digest)
                if asset_name is None:
                    asset_name = f"page-{page_number:04d}-image-{block_index:03d}.{ext}"
                    (assets_dir / asset_name).write_bytes(image_bytes)
                    asset_cache[digest] = asset_name
                asset_path = ensure_relative_to_bundle(bundle_dir, assets_dir / asset_name)

            page_images.append(
                {
                    "page_image_index": block_index,
                    "asset_path": asset_path,
                    "bbox": bbox,
                    "extractable": extractable,
                    "kind": kind,
                    "notes": notes,
                }
            )

        pages[page_number] = page_images
    return pages


def build_page_prompt(
    base_prompt: str,
    page_images: list[dict[str, Any]],
    text_layer: dict[str, Any],
    page_profile: list[str],
    mode: str,
) -> str:
    lines = [base_prompt]

    if "fillable_form" in page_profile:
        lines.extend(
            [
                "",
                "This page appears to be a fillable form or questionnaire.",
                "- Preserve visible blank entry lines using ASCII placeholders such as `Name: ____________________`.",
                "- Preserve checkbox or radio groups using ASCII markers such as `[ ] Yes  [ ] No` when the choices are unselected.",
                "- For a selected radio pair, emit both options explicitly, for example `[x] Yes  [ ] No` or `[ ] Yes  [x] No`.",
                "- Keep repeated applicant columns and Yes/No matrices distinct; do not flatten them into prose.",
                "- Preserve signature and date lines exactly where they appear.",
            ]
        )

    if "full_page_scan" in page_profile:
        lines.extend(
            [
                "",
                "This page appears to be a full-page scan or image-first page.",
                "- Still transcribe all visible text in Markdown; do not emit only an image placeholder.",
                "- If the page is comic-like, manga-like, slide-like, diagram-heavy, or mostly illustration, preserve text in visible reading order.",
                "- Use concise HTML comments such as `<!-- IMAGE 001: brief visible description -->` for meaningful non-text visual content that Markdown cannot represent.",
                "- Keep visual comments factual and short; do not infer narrative meaning beyond what is visible.",
            ]
        )

    extracted = [image for image in page_images if image.get("asset_path")]
    if extracted:
        lines.extend(
            [
                "",
                "Page-local extracted image assets are available for this page.",
                "If a visible figure matches one of these extracted assets, use the exact Markdown image string provided.",
                "These entries are ordered from top to bottom on the page.",
            ]
        )
        for image in extracted:
            asset_path = image["asset_path"]
            image_index = int(image["page_image_index"])
            lines.append(f'- `{canonical_markdown_image(f"IMAGE {image_index:03d}", asset_path)}`')
        lines.append(
            "If the page contains additional figures without an extracted asset, use HTML comments such as "
            "`<!-- IMAGE 001: brief visible description -->` and increment the number as needed."
        )

    if should_attach_text_layer(mode, text_layer):
        lines.extend(
            [
                "",
                "An embedded PDF text-layer extraction is supplied below as a secondary aid.",
                "Use it to recover exact spellings, identifiers, and long labels when it agrees with the page image.",
                "Prefer the page image for layout, blank fields, checkbox state, and any conflicting or garbled glyphs.",
                "If the embedded text layer contains obvious encoding noise, ignore the noisy span instead of copying it blindly.",
                "",
                "Embedded PDF text layer:",
                "```text",
                text_layer["prompt_text"],
                "```",
            ]
        )

    return "\n".join(lines)


def encode_image_as_data_url(image_bytes: bytes, render_media_type: str) -> str:
    payload = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{render_media_type};base64,{payload}"


def post_openrouter_request(
    api_key: str,
    api_url: str,
    model: str,
    prompt_text: str,
    image_bytes: bytes,
    render_media_type: str,
    timeout_seconds: int,
    max_completion_tokens: int,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "temperature": 0,
        "max_completion_tokens": max_completion_tokens,
        "reasoning": {
            "effort": "none",
            "exclude": True,
        },
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": encode_image_as_data_url(image_bytes, render_media_type)}},
                ],
            }
        ],
    }
    request = Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        retry_after_seconds: float | None = None
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            metadata = payload.get("error", {}).get("metadata", {})
            retry_after_raw = metadata.get("retry_after_seconds")
            if isinstance(retry_after_raw, (int, float)):
                retry_after_seconds = float(retry_after_raw)
        if exc.code in {429, 500, 502, 503, 504}:
            raise OpenRouterTransientError(
                f"OpenRouter returned HTTP {exc.code}: {body}",
                retry_after_seconds=retry_after_seconds,
            ) from exc
        raise RuntimeError(f"OpenRouter returned HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise OpenRouterTransientError(f"OpenRouter request failed: {exc}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenRouter returned non-JSON response: {body[:500]}") from exc


def extract_response_text(response: dict[str, Any]) -> tuple[str, str | None]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"OpenRouter response had no choices: {json.dumps(response)[:500]}")
    choice = choices[0]
    finish_reason = choice.get("finish_reason")
    if finish_reason in TRUNCATED_FINISH_REASONS:
        raise RuntimeError(
            f"OpenRouter truncated the page output with finish_reason={finish_reason}. "
            "Increase --max-completion-tokens or split the run to fewer pages per request."
        )

    message = choice.get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content.strip(), finish_reason
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        joined = "\n".join(part for part in parts if part.strip()).strip()
        if joined:
            return joined, finish_reason
    raise RuntimeError(f"OpenRouter response content was not usable text: {json.dumps(response)[:500]}")


def image_reference_numbers(markdown: str) -> list[int]:
    numbers: list[int] = []
    for match in LEGACY_IMAGE_PLACEHOLDER_RE.finditer(markdown):
        numbers.append(int(match.group("number")))
    for match in IMAGE_COMMENT_RE.finditer(markdown):
        numbers.append(int(match.group(1)))
    for match in IMAGE_MARKDOWN_RE.finditer(markdown):
        numbers.append(int(match.group(1)))
    return numbers


def reconcile_images(
    page_images: list[dict[str, Any]],
    ocr_markdown: str,
    review_notes: list[str],
) -> list[dict[str, Any]]:
    reconciled = copy.deepcopy(page_images)
    placeholder_count = max(image_reference_numbers(ocr_markdown), default=0)

    if placeholder_count > len(reconciled):
        for image_index in range(len(reconciled) + 1, placeholder_count + 1):
            reconciled.append(
                {
                    "page_image_index": image_index,
                    "asset_path": None,
                    "bbox": None,
                    "extractable": False,
                    "kind": "ocr_placeholder_only",
                    "notes": ["OCR output referenced a figure without a separately extracted asset."],
                }
            )
    elif len(reconciled) > placeholder_count and any(image.get("asset_path") for image in reconciled):
        review_notes.append(
            f"OCR output referenced {placeholder_count} image placeholders but {len(reconciled)} visible image blocks "
            "were detected on the page."
        )

    return reconciled


def load_existing_page_result(
    path: Path,
    *,
    model: str,
    page_prompt_sha256: str,
    dpi: int,
    source_pdf_sha256: str,
    render_media_type: str,
    ocr_mode: str,
    save_renders: bool,
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        isinstance(data, dict)
        and data.get("status") == "ok"
        and data.get("model") == model
        and data.get("page_prompt_sha256") == page_prompt_sha256
        and int(data.get("dpi", -1)) == dpi
        and data.get("source_pdf_sha256") == source_pdf_sha256
        and data.get("source_pdf_path") == "raw/source.pdf"
        and data.get("render_media_type") == render_media_type
        and data.get("ocr_mode") == ocr_mode
        and isinstance(data.get("render_dimensions"), list)
        and isinstance(data.get("render_sha256"), str)
        and (not save_renders or isinstance(data.get("rendered_image_path"), str))
    ):
        return data
    return None


def write_page_result(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_ocr_with_retries(
    *,
    api_key: str,
    api_url: str,
    model: str,
    prompt_text: str,
    image_bytes: bytes,
    render_media_type: str,
    timeout_seconds: int,
    max_completion_tokens: int,
    max_attempts: int,
    initial_retry_seconds: float,
) -> dict[str, Any]:
    attempt = 1
    delay = max(initial_retry_seconds, 0.1)
    while True:
        try:
            return post_openrouter_request(
                api_key=api_key,
                api_url=api_url,
                model=model,
                prompt_text=prompt_text,
                image_bytes=image_bytes,
                render_media_type=render_media_type,
                timeout_seconds=timeout_seconds,
                max_completion_tokens=max_completion_tokens,
            )
        except OpenRouterTransientError as exc:
            if attempt >= max_attempts:
                raise RuntimeError(f"{exc} after {attempt} attempts") from exc
            retry_after = exc.retry_after_seconds if exc.retry_after_seconds is not None else delay
            time.sleep(max(retry_after, 0.1))
            attempt += 1
            delay *= 2


def render_output_path_for_page(
    paths: BundlePaths,
    page_number: int,
    render_format: str,
    save_renders: bool,
) -> Path | None:
    if not save_renders:
        return None
    return paths.renders_dir / f"page-{page_number:04d}.{render_format}"


def ocr_one_page(
    *,
    bundle_dir: Path,
    render_path: Path | None,
    source_pdf: Path,
    page_number: int,
    page_images: list[dict[str, Any]],
    text_layer: dict[str, Any],
    page_profile: list[str],
    api_key: str,
    api_url: str,
    model: str,
    page_prompt: str,
    prompt_path: Path,
    prompt_sha256: str,
    page_prompt_sha256: str,
    ocr_mode: str,
    dpi: int,
    render_format: str,
    max_completion_tokens: int,
    timeout_seconds: int,
    source_pdf_sha256: str,
    max_attempts: int,
    initial_retry_seconds: float,
) -> dict[str, Any]:
    review_notes: list[str] = []
    rendered = render_page_image(source_pdf, page_number, dpi, render_format, render_path)
    render_media_type = media_type_for_render_format(render_format)

    if text_layer.get("control_character_count", 0) > 0 and should_attach_text_layer(ocr_mode, text_layer):
        review_notes.append(
            f"Embedded text layer contained control characters with codes {text_layer['control_character_codes']} "
            "and was treated as secondary prompt context only."
        )

    response = run_ocr_with_retries(
        api_key=api_key,
        api_url=api_url,
        model=model,
        prompt_text=page_prompt,
        image_bytes=rendered["bytes"],
        render_media_type=render_media_type,
        timeout_seconds=timeout_seconds,
        max_completion_tokens=max_completion_tokens,
        max_attempts=max_attempts,
        initial_retry_seconds=initial_retry_seconds,
    )
    ocr_markdown, finish_reason = extract_response_text(response)
    reconciled_images = reconcile_images(page_images, ocr_markdown, review_notes)
    return {
        "page_number": page_number,
        "source_pdf_path": ensure_relative_to_bundle(bundle_dir, source_pdf),
        "rendered_image_path": ensure_relative_to_bundle(bundle_dir, render_path) if render_path is not None else None,
        "dpi": dpi,
        "render_media_type": render_media_type,
        "render_dimensions": [rendered["width"], rendered["height"]],
        "render_sha256": rendered["sha256"],
        "model": model,
        "ocr_mode": ocr_mode,
        "page_profile": page_profile,
        "prompt_path": prompt_path.as_posix(),
        "prompt_sha256": prompt_sha256,
        "page_prompt_sha256": page_prompt_sha256,
        "source_pdf_sha256": source_pdf_sha256,
        "status": "ok",
        "images": reconciled_images,
        "text_layer": {
            "has_text": text_layer["has_text"],
            "char_count": text_layer["char_count"],
            "control_character_count": text_layer["control_character_count"],
            "control_character_codes": text_layer["control_character_codes"],
            "annotation_count": text_layer["annotation_count"],
            "text_sha256": text_layer["text_sha256"],
            "used_in_prompt": should_attach_text_layer(ocr_mode, text_layer),
        },
        "ocr_markdown": ocr_markdown,
        "review_notes": review_notes,
        "openrouter_response_id": response.get("id"),
        "usage": response.get("usage"),
        "finish_reason": finish_reason,
        "processed_at": utc_now_iso(),
    }


def build_canonical_markdown(page_results: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for page_result in sorted(page_results, key=lambda item: int(item["page_number"])):
        page_number = int(page_result["page_number"])
        ocr_markdown = normalize_legacy_image_placeholders(str(page_result["ocr_markdown"]).strip())
        chunks.append(f"<!-- PAGE {page_number:04d} -->\n\n{ocr_markdown}")
    return "\n\n".join(chunks).strip() + "\n"


def maybe_update_source_meta(source_meta_path: Path, page_count: int) -> None:
    source_meta = load_yaml(source_meta_path)
    if not source_meta:
        return
    source_meta["page_count"] = page_count
    if "canonical_path" not in source_meta:
        source_meta["canonical_path"] = "canonical/content.md"
    dump_yaml(source_meta_path, source_meta)


def write_trace(
    *,
    paths: BundlePaths,
    run_id: str,
    started_at: str,
    finished_at: str,
    model: str,
    prompt_path: Path,
    prompt_sha256: str,
    ocr_mode: str,
    dpi: int,
    render_format: str,
    save_renders: bool,
    page_count: int,
    selected_pages: list[int],
    max_workers: int,
    extracted_asset_pages: list[int],
    nonextractable_asset_pages: list[int],
    pages_with_text_layer: list[int],
    fillable_form_pages: list[int],
    pages_with_elevated_dpi: list[int],
    validation_complete: bool,
    source_sha256: str,
) -> None:
    source_meta = load_yaml(paths.source_meta_path) or {}
    trace = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "source_id": source_meta.get("source_id", paths.bundle_dir.name),
        "bundle_slug": source_meta.get("bundle_slug", paths.bundle_dir.name),
        "operator": {
            "kind": "script",
            "name": "scripts/ocr_pdf_openrouter.py",
        },
        "inputs": {
            "prompt_pdf_ocr": prompt_path.as_posix(),
            "prompt_pdf_ocr_sha256": prompt_sha256,
        },
        "artifacts": {
            "raw": ["raw/source.pdf"],
            "canonical": ["canonical/content.md"],
            "derived": ["derived/ocr/", "derived/assets/"] + (["derived/renders/"] if save_renders else []),
        },
        "model": {
            "name": model,
            "notes": "OpenRouter page-image OCR workflow with optional embedded text-layer assistance",
        },
        "validation": {
            "canonical_complete": validation_complete,
            "images_accounted_for": True,
            "pdf_image_assets_accounted_for": True,
            "source_hash_recorded": bool(source_sha256),
            "deviations": [],
        },
        "notes": [
            f"source_pdf_sha256={source_sha256}",
            f"page_count={page_count}",
            f"selected_pages={json.dumps(selected_pages)}",
            f"ocr_mode={ocr_mode}",
            f"rasterization_dpi={dpi}",
            f"render_format={render_format}",
            f"page_renders_saved={json.dumps(save_renders)}",
            "image_extraction_strategy=PyMuPDF page image blocks with best-effort asset recovery",
            "text_layer_strategy=pypdf extraction used as secondary prompt context for compatible pages",
            f"pages_with_embedded_text_layer={json.dumps(pages_with_text_layer)}",
            f"pages_classified_as_fillable_forms={json.dumps(fillable_form_pages)}",
            f"pages_with_elevated_dpi={json.dumps(pages_with_elevated_dpi)}",
            f"pages_with_extracted_image_assets={json.dumps(extracted_asset_pages)}",
            f"pages_where_image_extraction_was_not_possible={json.dumps(nonextractable_asset_pages)}",
            f"max_workers={max_workers}",
        ],
    }
    dump_yaml(paths.trace_path, trace)


def main() -> int:
    args = parse_args()
    prompt_path = Path(args.prompt_path).expanduser().resolve()

    if args.check_deps:
        exit_code, report = dependency_report(prompt_path)
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return exit_code

    if not args.bundle_dir:
        raise SystemExit("bundle_dir is required unless --check-deps is used.")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(prompt_user_for_key_message(), file=sys.stderr)
        return 2

    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    paths = build_paths(bundle_dir)
    prepare_bundle(paths, args.source_pdf)

    prompt_text = load_text(prompt_path).strip()
    prompt_sha256 = sha256_bytes(prompt_text.encode("utf-8"))
    fitz = require_fitz()

    started_at = utc_now_iso()
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    source_sha256 = sha256_file(paths.source_pdf)
    render_media_type = media_type_for_render_format(args.render_format)

    doc = fitz.open(paths.source_pdf.as_posix())
    try:
        page_images = extract_linkable_images(doc, bundle_dir, paths.assets_dir)
        page_count = int(doc.page_count)
    finally:
        doc.close()

    text_layers = extract_text_layers(paths.source_pdf)
    maybe_update_source_meta(paths.source_meta_path, page_count)
    selected_pages = parse_pages_spec(args.pages, page_count) if args.pages else list(range(1, page_count + 1))
    page_contexts: dict[int, dict[str, Any]] = {}
    for page_number in range(1, page_count + 1):
        text_layer = text_layers.get(page_number, build_empty_text_layer())
        page_profile = classify_page(page_images.get(page_number, []), text_layer)
        page_prompt = build_page_prompt(
            prompt_text,
            page_images.get(page_number, []),
            text_layer,
            page_profile,
            args.mode,
        )
        page_contexts[page_number] = {
            "text_layer": text_layer,
            "page_profile": page_profile,
            "effective_dpi": effective_dpi_for_page(args.dpi, page_profile, text_layer),
            "page_prompt": page_prompt,
            "page_prompt_sha256": sha256_bytes(page_prompt.encode("utf-8")),
        }

    page_results: dict[int, dict[str, Any]] = {}
    pages_to_process: list[int] = []
    for page_number in range(1, page_count + 1):
        output_path = paths.ocr_dir / f"page-{page_number:04d}.json"
        existing = None
        if not args.overwrite_ocr:
            existing = load_existing_page_result(
                output_path,
                model=args.model,
                page_prompt_sha256=page_contexts[page_number]["page_prompt_sha256"],
                dpi=page_contexts[page_number]["effective_dpi"],
                source_pdf_sha256=source_sha256,
                render_media_type=render_media_type,
                ocr_mode=args.mode,
                save_renders=args.save_renders,
            )
        if existing:
            page_results[page_number] = existing
        if page_number in selected_pages and not existing:
            pages_to_process.append(page_number)

    if pages_to_process:
        with ThreadPoolExecutor(max_workers=max(args.max_workers, 1)) as pool:
            futures = {
                pool.submit(
                    ocr_one_page,
                    bundle_dir=bundle_dir,
                    render_path=render_output_path_for_page(paths, page_number, args.render_format, args.save_renders),
                    source_pdf=paths.source_pdf,
                    page_number=page_number,
                    page_images=page_images.get(page_number, []),
                    text_layer=page_contexts[page_number]["text_layer"],
                    page_profile=page_contexts[page_number]["page_profile"],
                    api_key=api_key,
                    api_url=args.api_url,
                    model=args.model,
                    page_prompt=page_contexts[page_number]["page_prompt"],
                    prompt_path=prompt_path,
                    prompt_sha256=prompt_sha256,
                    page_prompt_sha256=page_contexts[page_number]["page_prompt_sha256"],
                    ocr_mode=args.mode,
                    dpi=page_contexts[page_number]["effective_dpi"],
                    render_format=args.render_format,
                    max_completion_tokens=args.max_completion_tokens,
                    timeout_seconds=args.timeout_seconds,
                    source_pdf_sha256=source_sha256,
                    max_attempts=args.max_attempts,
                    initial_retry_seconds=args.initial_retry_seconds,
                ): page_number
                for page_number in pages_to_process
            }
            for future in as_completed(futures):
                page_number = futures[future]
                output_path = paths.ocr_dir / f"page-{page_number:04d}.json"
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001
                    render_path = render_output_path_for_page(paths, page_number, args.render_format, args.save_renders)
                    failure = {
                        "page_number": page_number,
                        "source_pdf_path": ensure_relative_to_bundle(bundle_dir, paths.source_pdf),
                        "rendered_image_path": ensure_relative_to_bundle(bundle_dir, render_path) if render_path else None,
                        "dpi": page_contexts[page_number]["effective_dpi"],
                        "render_media_type": render_media_type,
                        "render_dimensions": None,
                        "render_sha256": None,
                        "model": args.model,
                        "ocr_mode": args.mode,
                        "page_profile": page_contexts[page_number]["page_profile"],
                        "prompt_path": prompt_path.as_posix(),
                        "prompt_sha256": prompt_sha256,
                        "page_prompt_sha256": page_contexts[page_number]["page_prompt_sha256"],
                        "source_pdf_sha256": source_sha256,
                        "status": "error",
                        "images": page_images.get(page_number, []),
                        "text_layer": {
                            "has_text": page_contexts[page_number]["text_layer"]["has_text"],
                            "char_count": page_contexts[page_number]["text_layer"]["char_count"],
                            "control_character_count": page_contexts[page_number]["text_layer"]["control_character_count"],
                            "control_character_codes": page_contexts[page_number]["text_layer"]["control_character_codes"],
                            "annotation_count": page_contexts[page_number]["text_layer"]["annotation_count"],
                            "text_sha256": page_contexts[page_number]["text_layer"]["text_sha256"],
                            "used_in_prompt": should_attach_text_layer(args.mode, page_contexts[page_number]["text_layer"]),
                        },
                        "ocr_markdown": "",
                        "review_notes": [str(exc)],
                        "finish_reason": None,
                        "processed_at": utc_now_iso(),
                    }
                    write_page_result(output_path, failure)
                    page_results[page_number] = failure
                    print(f"page {page_number:04d}: error: {exc}", file=sys.stderr)
                    continue

                write_page_result(output_path, result)
                page_results[page_number] = result
                print(f"page {page_number:04d}: ok", file=sys.stderr)

    ordered_results = [page_results[number] for number in sorted(page_results)]
    have_all_pages = len(ordered_results) == page_count
    all_ok = have_all_pages and all(result.get("status") == "ok" for result in ordered_results)
    if all_ok:
        canonical_markdown = build_canonical_markdown(ordered_results)
        paths.canonical_path.write_text(canonical_markdown, encoding="utf-8")
    else:
        print("Canonical markdown was not rebuilt because not all pages have valid OCR results.", file=sys.stderr)

    extracted_asset_pages = sorted(
        number for number, images in page_images.items() if any(image.get("asset_path") for image in images)
    )
    nonextractable_asset_pages = sorted(
        number for number, images in page_images.items() if any(not image.get("extractable", False) for image in images)
    )
    pages_with_text_layer = sorted(number for number, text_layer in text_layers.items() if text_layer.get("has_text"))
    fillable_form_pages = sorted(
        number
        for number, context in page_contexts.items()
        if "fillable_form" in context["page_profile"]
    )
    pages_with_elevated_dpi = sorted(
        number
        for number, context in page_contexts.items()
        if int(context["effective_dpi"]) > int(args.dpi)
    )
    finished_at = utc_now_iso()
    write_trace(
        paths=paths,
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        model=args.model,
        prompt_path=prompt_path,
        prompt_sha256=prompt_sha256,
        ocr_mode=args.mode,
        dpi=args.dpi,
        render_format=args.render_format,
        save_renders=args.save_renders,
        page_count=page_count,
        selected_pages=selected_pages,
        max_workers=args.max_workers,
        extracted_asset_pages=extracted_asset_pages,
        nonextractable_asset_pages=nonextractable_asset_pages,
        pages_with_text_layer=pages_with_text_layer,
        fillable_form_pages=fillable_form_pages,
        pages_with_elevated_dpi=pages_with_elevated_dpi,
        validation_complete=all_ok,
        source_sha256=source_sha256,
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
