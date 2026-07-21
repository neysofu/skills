#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
archive_path="${1:-"$repo_root/skills-repository.zip"}"

if [[ "$archive_path" != /* ]]; then
  archive_path="$PWD/$archive_path"
fi

archive_dir="$(cd -- "$(dirname -- "$archive_path")" && pwd)"
archive_path="$archive_dir/$(basename -- "$archive_path")"

for command_name in git zip; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Required command not found: $command_name" >&2
    exit 1
  fi
done

temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/skills-repository.XXXXXX")"
trap 'rm -rf -- "$temp_dir"' EXIT

file_list="$temp_dir/files.txt"
temp_archive="$temp_dir/archive.zip"

cd -- "$repo_root"
git ls-files --cached --others --exclude-standard |
  while IFS= read -r file; do
    if [[ ( -f "$file" || -L "$file" ) && "$repo_root/$file" != "$archive_path" ]]; then
      printf '%s\n' "$file"
    fi
  done >"$file_list"

zip -q -y "$temp_archive" -@ <"$file_list"
mv -f -- "$temp_archive" "$archive_path"

echo "Created $archive_path"
