#!/usr/bin/env bash
# Implements: reports/paper-source
# The writing loop: serve paper/build/, and on every save of the paper's
# sources or figures rebuild the HTML, then the .tex, then the PDF and its
# page images, and touch a stamp the preview page polls to reload itself.
set -u
BUILD=${PAPER_BUILD:-paper/build}
PORT=${PAPER_PORT:-8765}
SOURCES=(paper/paper.md paper/body.md paper/appendix.md paper/include.lua paper/references.bib paper/style.css paper/apart.html paper/apart.latex paper/preview.html reports/paper/figures)

command -v fswatch >/dev/null || { echo "paper-watch needs fswatch: brew install fswatch"; exit 1; }

build() {
  cp paper/preview.html "$BUILD/"
  # only what the writer needs: our rule warnings, TeX errors, undefined refs
  make -s paper-html paper-pdf 2>&1 | grep -iE 'abstract is|pages before|error|Undefined|undefined' | awk '!seen[$0]++' || true
  rm -f "$BUILD"/pages/*.png; mkdir -p "$BUILD/pages"
  [ -f "$BUILD/paper.pdf" ] && pdftoppm -r 110 -png "$BUILD/paper.pdf" "$BUILD/pages/p" 2>/dev/null
  (cd "$BUILD/pages" && ls p-*.png 2>/dev/null) > "$BUILD/pages.txt"
  date +%s > "$BUILD/stamp"
  echo "rebuilt $(date +%H:%M:%S)"
}

mkdir -p "$BUILD"
build
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$BUILD" >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT
echo "preview: http://127.0.0.1:$PORT/preview.html  (HTML left, PDF pages right; Ctrl-C to stop)"
fswatch -o -l 0.3 "${SOURCES[@]}" | while read -r _; do build; done
