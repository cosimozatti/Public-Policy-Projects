# Research library

This folder is what Claude reads when it writes or checks academic and financial work. Anything not in here (or in the repo's own reports, or fetched during a session) cannot be cited.

> This repository is public. Committing your Zotero export, reading notes or copyrighted PDFs here publishes them. For private material, create a private repository with the same `research/` layout and `.claude/` folder, and open cloud sessions on that repository instead.

```
research/
├── zotero/library.bib      Better BibTeX auto-export (metadata)
├── sources/<citekey>.pdf   full texts, named by citekey
├── notes/<citekey>.md      Obsidian literature notes with quotes and page numbers
└── drafts/                 drafts, source ledgers and calculation scripts
```

## 1. Zotero (one-time, about 5 minutes)

1. Install the Better BibTeX plugin for Zotero (Tools → Add-ons → install from file; the `.xpi` is on the plugin's GitHub releases page).
2. Set a stable citekey format: Zotero → Settings → Better BibTeX → Citation keys, formula `auth.lower + year + shorttitle(1,0).lower` (for example `duflo2012incentives`).
3. Right-click the library or a collection → Export → format **Better BibLaTeX**, tick **Keep updated**, save as `research/zotero/library.bib` inside your local clone of this repo.
4. Commit and push the file whenever it changes (`git add research/zotero/library.bib && git commit -m "Update library" && git push`). The cloud session only sees what is pushed.

Keep the entries complete in Zotero: authors, title, journal, volume, issue, pages, year, and DOI for articles; publisher for books; institution for reports; URL and access date for web pages. The checker flags any entry missing a field that a full MLA reference needs, and never fills the gap itself.

## 2. Source PDFs

Copy the PDF of each work you want Claude to quote into `research/sources/`, named by its citekey (`duflo2012incentives.pdf`). Zotero can do this: set Better BibTeX's attachment renaming, or use ZotMoov/ZotFile to rename to `{citekey}`. Scanned PDFs need OCR first (they have no text layer).

## 3. Obsidian

Either open `research/notes/` as a vault, or point your existing vault's literature-notes folder at it (symlink on your machine). One note per work, named by citekey, using `notes/_template-literature-note.md`. The rules that make notes usable as evidence:

- the `citekey:` line in the front matter;
- quotations copied verbatim, in quote marks, each with its page number;
- your own paraphrase kept visibly separate from the quotes (the checker only trusts quoted text).

The Zotero Integration plugin for Obsidian can generate these notes from your Zotero annotations with the page numbers already attached.

## 4. graphify

The session-start hook installs graphify in cloud sessions. To build the graph of this folder, ask Claude to run `/graphify research`, or run `graphify extract research` locally with an API key. Commit `graphify-out/graph.json` if you want the graph available in later sessions. The graph helps find which notes and PDFs bear on a question. It is never evidence.

## 5. Checking a draft

```bash
python3 .claude/skills/verified-research/scripts/verify_citations.py research/drafts/essay.md --works-cited
python3 .claude/skills/verified-research/scripts/verify_citations.py --audit-library          # whole library
python3 .claude/skills/verified-research/scripts/verify_citations.py --mla duflo2012incentives  # one reference
```

Add `--online` to compare DOIs with Crossref. This needs `api.crossref.org` in the cloud environment's allowed network domains.
