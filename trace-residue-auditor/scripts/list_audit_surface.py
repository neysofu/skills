#!/usr/bin/env python3
"""Inventory likely current-state audit surfaces for trace-residue review."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "target",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".venv",
    "venv",
    "__pycache__",
}

CURRENT_STATE_NAMES = {
    "agents.md",
    "readme.md",
    "contributing.md",
    "architecture.md",
    "design.md",
    "overview.md",
    "testing.md",
}

HISTORY_MARKERS = {
    "changelog",
    "changes",
    "release-notes",
    "releases",
    "migration",
    "migrations",
    "adr",
    "adrs",
    "incident",
    "incidents",
    "postmortem",
    "postmortems",
    "history",
}

TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".mdx",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


def is_history_path(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    stem = path.stem.lower()
    name = path.name.lower()
    return any(marker in parts or marker in stem or marker in name for marker in HISTORY_MARKERS)


def classify(path: Path) -> str | None:
    lower_name = path.name.lower()
    parts = {p.lower() for p in path.parts}
    if lower_name in CURRENT_STATE_NAMES:
        return "current_doc"
    if "test" in parts or "tests" in parts or path.stem.endswith("_test") or path.stem.endswith("_tests"):
        return "test_or_fixture"
    if "fixtures" in parts or "snapshots" in parts or "goldens" in parts:
        return "test_or_fixture"
    if path.suffix.lower() in {".md", ".mdx", ".txt"}:
        return "doc"
    if path.suffix.lower() in TEXT_SUFFIXES:
        return "source_or_config"
    return None


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for filename in filenames:
            path = base / filename
            if path.is_symlink():
                continue
            yield path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List likely current-state files for semantic trace-residue audits.",
    )
    parser.add_argument("root", type=Path, help="Repository root to inspect.")
    parser.add_argument("--include-history", action="store_true", help="Include intentionally historical files in surfaces.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--limit", type=int, default=400, help="Maximum current-state surface files to print.")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"root is not a directory: {root}")

    surfaces = []
    exempt = []
    for path in iter_files(root):
        rel = path.relative_to(root)
        category = classify(rel)
        if category is None:
            continue
        item = {"path": str(rel), "category": category}
        if is_history_path(rel):
            if args.include_history:
                item["category"] = f"{category}:history"
                surfaces.append(item)
            else:
                exempt.append(item)
        else:
            surfaces.append(item)

    surfaces.sort(key=lambda item: (item["category"], item["path"]))
    exempt.sort(key=lambda item: item["path"])
    limited = surfaces[: max(args.limit, 0)]

    if args.json:
        print(json.dumps({"root": str(root), "surfaces": limited, "exempt_history": exempt}, indent=2))
    else:
        print(f"root: {root}")
        print(f"surfaces: {len(surfaces)} total, showing {len(limited)}")
        for item in limited:
            print(f"{item['category']}\t{item['path']}")
        print(f"exempt_history: {len(exempt)}")
        for item in exempt[:50]:
            print(f"history\t{item['path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
