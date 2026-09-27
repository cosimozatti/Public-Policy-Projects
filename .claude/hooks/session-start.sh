#!/bin/bash
# Prepares cloud sessions for the verified-research protocol and reports the state of the research library.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

# pypdf needs cffi next to the system cryptography package; graphify indexes the research folder.
if ! python3 -c "import pypdf" >/dev/null 2>&1 || ! command -v graphify >/dev/null 2>&1; then
  pip install -q --disable-pip-version-check cffi pypdf "graphifyy[pdf]" >/dev/null 2>&1 || true
fi
# User-level install only: adds the /graphify skill, no PreToolUse hooks, no repo CLAUDE.md edits.
if command -v graphify >/dev/null 2>&1 && [ ! -f "$HOME/.claude/skills/graphify/SKILL.md" ]; then
  graphify install >/dev/null 2>&1 || true
fi

# Status report, read by Claude at session start.
bib=$(ls research/zotero/*.bib research/zotero/*.json 2>/dev/null || true)
entries=0
for f in $bib; do
  n=$(grep -c -E '^@[A-Za-z]+\{' "$f" 2>/dev/null || true)
  [ "${f##*.}" = "json" ] && n=$(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(len(d if isinstance(d,list) else d.get('items',[])))" "$f" 2>/dev/null || echo 0)
  entries=$((entries + ${n:-0}))
done
notes=$(find research/notes -name '*.md' ! -name '_template*' 2>/dev/null | wc -l)
pdfs=$(find research/sources -iname '*.pdf' 2>/dev/null | wc -l)
graph="absent"; [ -f graphify-out/graph.json ] && graph="present"
pdfok="yes"; python3 -c "import pypdf" >/dev/null 2>&1 || pdfok="NO"
gfy="yes"; command -v graphify >/dev/null 2>&1 || gfy="NO"

echo "Research library status: Zotero export ${entries} entries ($( [ -n "$bib" ] && echo "$bib" | tr '\n' ' ' || echo 'MISSING: citations must be [CITATION NEEDED]')); Obsidian notes ${notes}; source PDFs ${pdfs}; graphify graph ${graph}; pypdf ${pdfok}; graphify CLI ${gfy}. Follow .claude/skills/verified-research/SKILL.md for academic and financial tasks."
