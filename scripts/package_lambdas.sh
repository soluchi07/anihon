#!/usr/bin/env bash
set -euo pipefail

# Package each Lambda directory as a zip artifact for CI/deploy checks.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAMBDA_ROOT="$ROOT_DIR/backend/lambdas"
OUT_DIR="$ROOT_DIR/build/lambdas"

mkdir -p "$OUT_DIR"

package_dir() {
  local src_dir="$1"
  local out_zip="$2"

  if command -v zip >/dev/null 2>&1; then
    (
      cd "$src_dir"
      zip -qr "$out_zip" .
    )
    return
  fi

  python3 - "$src_dir" "$out_zip" <<'PY'
import pathlib
import sys
import zipfile

src = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]).resolve()

with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in src.rglob("*"):
        if path.is_file():
            zf.write(path, path.relative_to(src))
PY
}

count=0
for dir in "$LAMBDA_ROOT"/*; do
  [[ -d "$dir" ]] || continue

  name="$(basename "$dir")"
  [[ "$name" == "__pycache__" ]] && continue
  [[ -f "$dir/handler.py" ]] || continue

  zip_path="$OUT_DIR/${name}.zip"
  rm -f "$zip_path"

  echo "Packaging ${name} -> ${zip_path}"
  package_dir "$dir" "$zip_path"
  count=$((count + 1))
done

if [[ "$count" -eq 0 ]]; then
  echo "No Lambda handlers found to package."
  exit 1
fi

echo "Done. Packaged ${count} Lambda artifact(s) into $OUT_DIR"
