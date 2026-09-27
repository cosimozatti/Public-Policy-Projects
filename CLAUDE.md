# Working rules for this repository

## Academic and financial work

For any essay, literature review, policy brief, thesis chapter, research memo, replication or evaluation write-up, investment or appraisal note, or financial analysis, follow `.claude/skills/verified-research/SKILL.md` in full. In short:

- Evidence comes only from `research/sources/` (PDFs named by citekey), `research/notes/` (Obsidian literature notes), the reports in this repo, or pages fetched in the session. Bibliographic metadata comes only from `research/zotero/library.bib`. Nothing is cited from memory; gaps are marked `[CITATION NEEDED]` or `[SOURCE?]`.
- Build a source ledger with verbatim passages and page locators before drafting, and reason from the ledger.
- graphify output (`graphify-out/`) is for finding files. It is never quoted or cited.
- Before delivery, run `python3 .claude/skills/verified-research/scripts/verify_citations.py <draft> --works-cited` and clear every ERROR, then report the results in a verification note.
- Do arithmetic in Python scripts kept next to the draft, and audit any dataset first (`auditing-datasets`).

The session-start hook prints the state of the research library (Zotero entries, notes, PDFs, graph). If the Zotero export is missing, say so before starting the task.

## Layout

- `research/` holds the Zotero export, Obsidian notes, source PDFs and drafts. See `research/README.md` for setup.
- The project reports at the repo root (Nepal SSDP replication, EIB Climate Hackathon, tertiary education and life expectancy, health and PISA 2022) are the user's own work and can be cited as such.

## Checks

```bash
python3 -m unittest discover -s .claude/skills/verified-research/tests
python3 .claude/skills/verified-research/scripts/verify_citations.py --audit-library
```
