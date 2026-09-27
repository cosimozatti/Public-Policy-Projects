---
name: verified-research
description: Evidence protocol for academic and financial work. Every citation must come from the Zotero export, every quotation and figure must be traced to a page in a source PDF or Obsidian note in the workspace, and a bundled script checks the draft before delivery. Use whenever the user asks for an essay, literature review, policy brief, thesis chapter, research memo, referee-style critique, replication or impact-evaluation write-up, investment or appraisal note, financial or fiscal analysis, cost-benefit analysis, or any answer that will carry citations, quotations or figures, including when the request does not mention sources.
---

# Verified research protocol

This protocol decides what counts as evidence and how a draft is checked before the user sees it. Style is handled by `drafting-analytical-prose`, IFI appraisal conventions by `appraising-agrifood-investments`, data checks by `auditing-datasets`. Load the ones that apply alongside this skill.

## Where the material lives

| Path | Content | Can support |
|---|---|---|
| `research/zotero/library.bib` (or `.json`) | Better BibTeX auto-export of the Zotero library | bibliographic metadata only |
| `research/sources/<citekey>.pdf` | full texts, named by citekey | quotations, figures, claims |
| `research/notes/` | Obsidian literature notes, one per citekey, quotes with page numbers | quotations and claims, via the quoted passage |
| `research/drafts/` | drafts and their source ledgers | nothing (never cite your own draft) |
| `graphify-out/` | graphify knowledge graph of the research folder | finding things; never evidence |
| rest of the repo | the user's own project reports and data | claims about the user's own work |

## Source hierarchy

Accept a claim only from the highest tier available, and say which tier it came from.

1. The primary text in the workspace (PDF in `research/sources/`, or a report elsewhere in the repo). Quote the passage, record the page.
2. An Obsidian literature note that quotes the passage with a page number.
3. A web page fetched in this session (institutional statistics, legal texts, working papers). Record URL and access date and quote the passage.
4. Discovery tools (Consensus, Elicit, Scholar Gateway MCP servers). Use them to find candidate works. A claim resting only on an abstract or a tool summary is labelled "abstract only" in the ledger and in the text, and the work is not cited until the user has added it to Zotero.

Training data is never a tier. When no tier supports a claim, write `[CITATION NEEDED]` (for a missing work) or `[SOURCE?]` (for a figure without a locator) and keep going. Do not substitute a plausible reference and do not drop the claim silently.

Zotero metadata proves that a work exists and how to cite it. It does not prove what the work says; for that, the text or a note with the passage is required.

## Workflow

1. **Inventory before drafting.** List what is in `research/zotero`, `research/sources`, `research/notes` and the repo that bears on the task. If the Zotero export is missing, tell the user at the outset that every citation will be `[CITATION NEEDED]` until it is added. If a source the argument needs is not in the workspace, say so now, not in the verification note.
2. **Locate.** For corpora above roughly 15 files, run `graphify query "<question>"` (see graphify section) to find candidate files and passages, then open those files. For smaller corpora, `grep` the notes and the cached PDF text.
3. **Build the source ledger** in `research/drafts/<slug>.ledger.md` before writing prose. One row per claim that will carry a citation or a figure:

   | Claim | Key | Locator | Passage (verbatim) | Tier | Status |
   |---|---|---|---|---|---|

   Status is one of: verified in PDF, verified in note, fetched page, abstract only, unverified. Reason from the passages in this ledger, not from memory of the paper and not from the graph.
4. **Draft with citekeys.** Write citations as Pandoc keys with locators, `[@key, p. 12]`, `[@a, pp. 3-4; @b, sec. 2]`, so the script can check them. Put direct quotations in double quotes followed by their citation in the same sentence.
5. **Run the gate.**
   ```bash
   python3 .claude/skills/verified-research/scripts/verify_citations.py research/drafts/<file>.md --works-cited
   ```
   Fix every ERROR: a missing key, an incomplete Zotero entry, a locator outside the page range, a quote not found verbatim, a quote found in a different source than the one cited, or an uncited quotation. Treat WARN lines (figures without a locator, sources not in the workspace) as items for the verification note unless they can be fixed. Then run the style checker from `drafting-analytical-prose` if it is installed.
6. **Bibliography.** Build the Works Cited list from the `--works-cited` output, which the script generates from the Zotero export and limits to works cited in the draft. Any `[MISSING: field]` it prints is a gap in Zotero, reported to the user, never filled from memory. Convert citekeys to the target citation style only at the last step.
7. **Deliver with a verification note:** the script's ERROR/WARN counts, the open `[CITATION NEEDED]` and `[SOURCE?]` markers, claims resting on one study, claims marked abstract only, and page references the user should check against the printed edition (the script reports PDF page numbers, which can differ from printed page numbers).

## Raising the standard

Academic tasks:
- State the identification strategy of every empirical study the argument leans on and what would threaten it (selection, attrition, spillovers, weak first stage, multiple testing). A correlation is reported as a correlation.
- Report effect sizes with their uncertainty and units (SD, percentage points, elasticities) from the ledger passage, not from recollection.
- Engage the strongest opposing position with a named author whose argument appears in a source in the workspace. If none is available, state that the position exists and mark `[CITATION NEEDED]`.
- Label confidence claim by claim: well established across studies, single study, weak identification, projection rather than outturn, not verified.

Financial and appraisal tasks:
- Every figure carries its document and page or table. State currency, price basis (nominal or real, base year), FX rate and date, and whether a figure is an outturn, a budget or a projection.
- Do arithmetic in Python, not in prose: totals, shares, NPV, IRR, DSCR, switching values. Keep the script in `research/drafts/` so the numbers can be reproduced, and reconcile every total with its components.
- Keep an assumption register separate from source-backed figures, and a sensitivity or switching-value analysis for the decision variable.
- Run `auditing-datasets` on any dataset before using it.

## graphify

graphify (`pip install "graphifyy[pdf]"`, command `graphify`) builds a knowledge graph of the research folder so relevant files can be found quickly. It is a navigation aid, and its semantic edges on PDFs and notes are generated by a model, so they carry the same risk as any summary:

- Build: `/graphify research` in Claude Code (the assistant does the semantic pass on PDFs and notes), or `graphify extract research` where an LLM API key is set. Refresh after adding files with `/graphify research --update`. Output goes to `graphify-out/`. (`graphify update` alone re-extracts code only and will not pick up new papers.)
- Query: `graphify query "<question>"`, `graphify path "<concept A>" "<concept B>"`.
- Use the result only to decide which files to open. Never quote `GRAPH_REPORT.md`, a node label or an edge as evidence, and never cite the graph.
- Do not run `graphify install --strict` in this repo: strict mode blocks reading the raw source files, which this protocol requires.

## Network note

The cloud environment may block `api.crossref.org`, `doi.org` and `api.openalex.org`. Without them `--online` reports "network blocked" and metadata rests on the Zotero export alone; say so in the verification note. The user can add those hosts to the environment's allowed domains.
