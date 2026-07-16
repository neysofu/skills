#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(value: str) -> str:
    cleaned = []
    last_was_dash = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            last_was_dash = False
        elif not last_was_dash:
            cleaned.append("-")
            last_was_dash = True
    slug = "".join(cleaned).strip("-")
    return slug or "pdf-bundle"


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    yaml = require_yaml()
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False, width=120), encoding="utf-8")


def require_yaml():
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit("PyYAML is required. Install `PyYAML` and rerun.") from exc
    return yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a PDF-to-Markdown bundle skeleton.")
    parser.add_argument("bundle_dir", help="Output bundle directory.")
    parser.add_argument("--source-pdf", help="Optional source PDF to copy into raw/source.pdf.")
    parser.add_argument("--source-id", help="Optional stable source identifier.")
    parser.add_argument("--bundle-slug", help="Optional explicit bundle slug.")
    parser.add_argument("--title", help="Optional display title for source.meta.yaml.")
    parser.add_argument("--url", help="Optional canonical URL. Defaults to the local file URI when --source-pdf is set.")
    parser.add_argument("--license", default="unknown", help="License value to record in source.meta.yaml.")
    parser.add_argument("--overwrite", action="store_true", help="Allow writing into an existing bundle directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    raw_dir = bundle_dir / "raw"
    canonical_dir = bundle_dir / "canonical"
    derived_ocr_dir = bundle_dir / "derived" / "ocr"
    derived_assets_dir = bundle_dir / "derived" / "assets"
    derived_renders_dir = bundle_dir / "derived" / "renders"
    traces_dir = bundle_dir / "traces"

    if bundle_dir.exists() and any(bundle_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"Bundle directory is not empty: {bundle_dir}")

    raw_dir.mkdir(parents=True, exist_ok=True)
    canonical_dir.mkdir(parents=True, exist_ok=True)
    derived_ocr_dir.mkdir(parents=True, exist_ok=True)
    derived_assets_dir.mkdir(parents=True, exist_ok=True)
    derived_renders_dir.mkdir(parents=True, exist_ok=True)
    traces_dir.mkdir(parents=True, exist_ok=True)

    source_pdf_path = raw_dir / "source.pdf"
    source_pdf = None
    if args.source_pdf:
        source_pdf = Path(args.source_pdf).expanduser().resolve()
        if not source_pdf.exists():
            raise SystemExit(f"Source PDF does not exist: {source_pdf}")
        if source_pdf != source_pdf_path:
            shutil.copyfile(source_pdf, source_pdf_path)

    slug_source = args.bundle_slug or (source_pdf_path.stem if source_pdf_path.exists() else bundle_dir.name)
    bundle_slug = slugify(slug_source)
    source_id = args.source_id or bundle_slug
    title = args.title or (source_pdf.stem if source_pdf else bundle_dir.name.replace("-", " "))
    url = args.url or (source_pdf.as_uri() if source_pdf else f"local://{bundle_slug}")
    sha256 = sha256_file(source_pdf_path) if source_pdf_path.exists() else ""

    source_meta = {
        "source_id": source_id,
        "bundle_slug": bundle_slug,
        "title": title,
        "url": url,
        "retrieved_at": utc_now_iso(),
        "source_format": "pdf",
        "content_type": "application/pdf",
        "license": args.license,
        "sha256": sha256,
        "canonical_path": "canonical/content.md",
    }
    dump_yaml(bundle_dir / "source.meta.yaml", source_meta)

    canonical_path = canonical_dir / "content.md"
    if not canonical_path.exists():
        canonical_path.write_text("", encoding="utf-8")

    trace = {
        "run_id": "bundle-initialized",
        "started_at": utc_now_iso(),
        "finished_at": utc_now_iso(),
        "source_id": source_id,
        "bundle_slug": bundle_slug,
        "operator": {
            "kind": "script",
            "name": "scripts/init_bundle.py",
        },
        "inputs": {},
        "artifacts": {
            "raw": ["raw/source.pdf"] if source_pdf_path.exists() else [],
            "canonical": ["canonical/content.md"],
            "derived": ["derived/ocr/", "derived/assets/", "derived/renders/"],
        },
        "model": {
            "name": "",
            "notes": "Bundle initialized; OCR not yet run.",
        },
        "validation": {
            "canonical_complete": False,
            "images_accounted_for": False,
            "pdf_image_assets_accounted_for": False,
            "source_hash_recorded": bool(sha256),
            "deviations": [],
        },
        "notes": [
            "Bundle skeleton initialized.",
        ],
    }
    dump_yaml(traces_dir / "run.trace.yaml", trace)

    print(bundle_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
