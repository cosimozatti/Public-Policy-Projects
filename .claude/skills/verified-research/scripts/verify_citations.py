#!/usr/bin/env python3
"""Verify a draft's citations against the Zotero export and the source texts in the workspace.

Checks, per draft:
  1. every cited key exists in the Zotero export (Better BibTeX .bib or CSL JSON);
  2. the cited entry carries the fields a full MLA reference needs;
  3. page locators fall inside the entry's printed page range;
  4. every direct quotation is found verbatim in the source PDF or in an Obsidian note,
     with the PDF page on which it was found;
  5. sentences carrying figures (%, currency, millions, ratios) have a citation with a locator,
     or an explicit [SOURCE?] / [CITATION NEEDED] marker;
  6. optionally (--online), entry metadata against Crossref.

It can also audit the whole library (--audit-library) and print an MLA 9 Works Cited list built
only from the keys the draft cites (--works-cited), so the bibliography is generated from the
export rather than typed from memory.

Citation syntax recognised: Pandoc/Quarto ([@key, p. 12], [see @a, pp. 3-4; @b, sec. 2], @key [p. 5])
and LaTeX (\\cite{key}, \\parencite[12]{key}, \\textcite[see][4]{a,b}).

Standard library only; pypdf is used for PDF text when installed.
Exit code 1 when any ERROR is reported (use --no-fail to always exit 0).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- library

BIB_TYPE_MAP = {
    "article": "article",
    "book": "book", "mvbook": "book",
    "incollection": "chapter", "inbook": "chapter", "inproceedings": "chapter", "conference": "chapter",
    "techreport": "report", "report": "report",
    "online": "web", "webpage": "web", "electronic": "web",
    "thesis": "thesis", "phdthesis": "thesis", "mastersthesis": "thesis",
    "unpublished": "other", "misc": "other", "manual": "report",
}
CSL_TYPE_MAP = {
    "article-journal": "article", "article": "article", "article-magazine": "article",
    "article-newspaper": "article", "review": "article",
    "book": "book", "chapter": "chapter", "paper-conference": "chapter",
    "report": "report", "webpage": "web", "post-weblog": "web", "post": "web",
    "thesis": "thesis", "legislation": "other", "legal_case": "other", "dataset": "other",
}

REQUIRED = {
    "article": ["authors", "title", "container", "year", "volume", "pages"],
    "book": ["authors|editors", "title", "publisher", "year"],
    "chapter": ["authors", "title", "container", "publisher", "year", "pages"],
    "report": ["authors|institution", "title", "institution|publisher", "year"],
    "web": ["title", "url", "authors|container"],
    "thesis": ["authors", "title", "institution", "year"],
    "other": ["authors|institution", "title", "year"],
}
RECOMMENDED = {
    "article": ["issue", "doi"],
    "chapter": ["editors"],
    "report": ["url"],
    "web": ["urldate"],
}


@dataclass
class Entry:
    key: str
    type: str
    raw_type: str
    authors: list = field(default_factory=list)   # list of (family, given)
    editors: list = field(default_factory=list)
    title: str = ""
    container: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    year: str = ""
    publisher: str = ""
    institution: str = ""
    doi: str = ""
    url: str = ""
    urldate: str = ""
    thesis_type: str = ""

    def has(self, name: str) -> bool:
        return any(bool(getattr(self, n)) for n in name.split("|"))

    def page_range(self):
        nums = re.findall(r"\d+", self.pages or "")
        if not nums:
            return None
        start = int(nums[0])
        end = int(nums[1]) if len(nums) > 1 else start
        if end < start:  # abbreviated ranges such as 123-45
            end = int(str(start)[: len(str(start)) - len(str(end))] + str(end))
        return start, end


def _strip_latex(s: str) -> str:
    s = re.sub(r"\\(?:textit|emph|textbf|textsc|mkbibquote|mkbibemph)\s*\{", "{", s)
    s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_").replace("\\$", "$")
    s = s.replace("--", "–").replace("~", " ")
    s = re.sub(r"\\['`^\"~=.uvHck]\{?([A-Za-z])\}?", r"\1", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def _split_top(s: str, sep: str) -> list:
    """Split on a separator word/char only at brace depth 0."""
    out, depth, buf, i = [], 0, "", 0
    while i < len(s):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if depth == 0 and s.startswith(sep, i):
            out.append(buf)
            buf, i = "", i + len(sep)
            continue
        buf += c
        i += 1
    out.append(buf)
    return out


def _bib_names(raw: str) -> list:
    names = []
    for part in _split_top(raw, " and "):
        part = part.strip()
        if not part:
            continue
        if part.startswith("{") and part.endswith("}") and part.count("{") == 1:
            names.append((_strip_latex(part), ""))  # institutional author
            continue
        pieces = _split_top(part, ",")
        if len(pieces) >= 2:
            names.append((_strip_latex(pieces[0]), _strip_latex(pieces[-1])))
        else:
            words = _strip_latex(part).split(" ")
            names.append((words[-1], " ".join(words[:-1])))
    return names


def parse_bib(text: str) -> dict:
    entries, i, n = {}, 0, len(text)
    while True:
        at = text.find("@", i)
        if at < 0:
            break
        m = re.match(r"@(\w+)\s*([{(])", text[at:])
        if not m:
            i = at + 1
            continue
        etype = m.group(1).lower()
        j = at + m.end()
        depth, k = 1, j
        while k < n and depth:
            if text[k] in "{(":
                depth += 1
            elif text[k] in "})":
                depth -= 1
            k += 1
        body = text[j:k - 1]
        i = k
        if etype in ("comment", "preamble", "string"):
            continue
        key, _, rest = body.partition(",")
        fields, pos = {}, 0
        while pos < len(rest):
            fm = re.compile(r"\s*([\w\-]+)\s*=\s*").match(rest, pos)
            if not fm:
                break
            name, pos = fm.group(1).lower(), fm.end()
            if pos < len(rest) and rest[pos] == "{":
                depth, start = 1, pos + 1
                pos += 1
                while pos < len(rest) and depth:
                    depth += {"{": 1, "}": -1}.get(rest[pos], 0)
                    pos += 1
                val = rest[start:pos - 1]
            elif pos < len(rest) and rest[pos] == '"':
                end = rest.find('"', pos + 1)
                val, pos = rest[pos + 1:end], end + 1
            else:
                vm = re.compile(r"[^,]*").match(rest, pos)
                val, pos = vm.group(0).strip(), vm.end()
            fields[name] = val
            comma = rest.find(",", pos)
            pos = comma + 1 if comma >= 0 else len(rest)
        f = {k2: _strip_latex(v) for k2, v in fields.items()}
        date = f.get("date", "")
        e = Entry(
            key=key.strip(), type=BIB_TYPE_MAP.get(etype, "other"), raw_type=etype,
            authors=_bib_names(fields.get("author", "")), editors=_bib_names(fields.get("editor", "")),
            title=f.get("title", ""),
            container=f.get("journaltitle") or f.get("journal") or f.get("booktitle") or f.get("maintitle", ""),
            volume=f.get("volume", ""), issue=f.get("number") or f.get("issue", ""),
            pages=f.get("pages", ""), year=f.get("year") or (date[:4] if date else ""),
            publisher=f.get("publisher", ""), institution=f.get("institution") or f.get("school", ""),
            doi=f.get("doi", ""), url=f.get("url", ""), urldate=f.get("urldate", ""),
            thesis_type=f.get("type", ""),
        )
        if e.type == "other" and e.url and etype in ("misc", "online"):
            e.type = "web"
        entries[e.key] = e
    return entries


def _csl_names(lst) -> list:
    out = []
    for a in lst or []:
        if "literal" in a:
            out.append((a["literal"], ""))
        else:
            out.append((a.get("family", ""), a.get("given", "")))
    return out


def parse_csl(items) -> dict:
    if isinstance(items, dict):
        items = items.get("items", [])
    entries = {}
    for it in items:
        dp = (it.get("issued") or {}).get("date-parts") or [[""]]
        acc = (it.get("accessed") or {}).get("date-parts") or [[]]
        t = it.get("type", "")
        e = Entry(
            key=it.get("citation-key") or it.get("id", ""), type=CSL_TYPE_MAP.get(t, "other"), raw_type=t,
            authors=_csl_names(it.get("author")), editors=_csl_names(it.get("editor")),
            title=it.get("title", ""), container=it.get("container-title", ""),
            volume=str(it.get("volume", "")), issue=str(it.get("issue", "")), pages=str(it.get("page", "")),
            year=str(dp[0][0]) if dp and dp[0] else "", publisher=it.get("publisher", ""),
            institution=it.get("publisher", "") if t in ("report", "thesis") else "",
            doi=it.get("DOI", ""), url=it.get("URL", ""),
            urldate="-".join(str(x) for x in acc[0]) if acc and acc[0] else "",
            thesis_type=it.get("genre", ""),
        )
        entries[e.key] = e
    return entries


def load_library(paths) -> dict:
    lib = {}
    for p in paths:
        text = Path(p).read_text(encoding="utf-8", errors="replace")
        lib.update(parse_csl(json.loads(text)) if str(p).endswith(".json") else parse_bib(text))
    return lib


# --------------------------------------------------------------------------- draft

def read_draft(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        paras = []
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
            paras.append("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)))
        import html
        return html.unescape("\n\n".join(paras))
    text = path.read_text(encoding="utf-8", errors="replace")
    blank = lambda m: "\n" * m.group(0).count("\n")                 # keep line numbers stable
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)    # YAML front matter
    text = re.sub(r"```.*?```", blank, text, flags=re.S)              # code blocks
    return text


ABBREV = ["et al.", "e.g.", "i.e.", "cf.", "pp.", "p.", "vol.", "no.", "sec.", "ch.", "para.", "fig.",
          "Fig.", "Vol.", "No.", "Sec.", "Ch.", "ed.", "eds.", "Dr.", "Mr.", "Ms.", "St.", "U.S.", "U.K.", "approx."]


def sentences(text: str):
    """Yield (line_no, sentence) pairs; abbreviations and citation brackets never end a sentence."""
    out = []
    for block_start, block in _blocks(text):
        protected = block
        for a in ABBREV:
            protected = protected.replace(a, a.replace(".", "\x00"))
        protected = re.sub(r"\[[^\]]*\]", lambda m: m.group(0).replace(".", "\x00"), protected)
        protected = re.sub(r"(\d)\.(\d)", "\\1\x00\\2", protected)
        parts = re.split(r"(?<=[.!?])[\"”’)]*\s+(?=[A-Z\"“(\[])", protected)
        offset = 0
        for part in parts:
            idx = protected.find(part, offset)
            line = block_start + protected.count("\n", 0, max(idx, 0))
            offset = idx + len(part)
            s = part.replace("\x00", ".").strip()
            if s:
                out.append((line, s))
    return out


def _blocks(text: str):
    """Yield (first line number, paragraph) for each run of non-blank lines."""
    for m in re.finditer(r"(?:[^\n]*\S[^\n]*(?:\n|$))+", text):
        yield text.count("\n", 0, m.start()) + 1, m.group(0)


@dataclass
class Citation:
    key: str
    locator: str
    line: int
    sentence: str


PANDOC_GROUP = re.compile(r"\[([^\[\]]*?@[^\[\]]*)\]")
PANDOC_ITEM = re.compile(r"-?@([\w:.#$%&+?<>~/\-]*[\w])\s*(?:,\s*(.*))?$")
PANDOC_NARR = re.compile(r"(?<![\w@\[])@([\w:.#$%&+?<>~/\-]*[\w])(?:\s*\[([^\]@]*)\])?")
LATEX_CITE = re.compile(r"\\(?:[a-zA-Z]*cite[a-zA-Z]*)\*?(?:\[([^\]]*)\])?(?:\[([^\]]*)\])?\{([^}]+)\}")


def extract_citations(line: int, s: str) -> list:
    cites = []
    masked = s
    for m in PANDOC_GROUP.finditer(s):
        for item in m.group(1).split(";"):
            im = PANDOC_ITEM.search(item.strip())
            if im:
                cites.append(Citation(im.group(1), (im.group(2) or "").strip(), line, s))
        masked = masked.replace(m.group(0), " " * len(m.group(0)))
    for m in PANDOC_NARR.finditer(masked):
        cites.append(Citation(m.group(1), (m.group(2) or "").strip(), line, s))
    for m in LATEX_CITE.finditer(s):
        loc = m.group(2) if m.group(2) is not None else (m.group(1) or "")
        for k in m.group(3).split(","):
            cites.append(Citation(k.strip(), loc.strip(), line, s))
    return cites


LOCATOR_RE = re.compile(r"(\bpp?\.?\s*\d|§|\bsec(tion)?\.?\s*\d|\bpara(graph)?\.?\s*\d|\bch(apter|ap)?\.?\s*\d|"
                        r"\btable\s*\w|\bfig(ure)?\.?\s*\w|\bannex\s*\w|\bart(icle)?\.?\s*\d|^\s*\d+\s*([-–]\s*\d+)?\s*$|"
                        r"\bslide\s*\d|\bline\s*\d|\bat\s*\d)", re.I)


def locator_pages(loc: str):
    m = re.search(r"(?:\bpp?\.?\s*|^\s*)(\d+)(?:\s*[-–]+\s*(\d+))?", loc)
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return a, b


FIGURE_RE = re.compile(
    r"(\d+(?:[.,]\d+)?\s?(?:%|per ?cent|percent|pp\b|percentage points?|bps?\b|basis points)|"
    r"(?:USD|EUR|GBP|CHF|JPY|KES|NGN|SOS|US\$|€|£|\$)\s?\d|"
    r"\d+(?:[.,]\d+)?\s?(?:million|billion|trillion|bn|mn)\b|"
    r"\b\d+(?:\.\d+)?\s?(?:times|x)\s+(?:higher|lower|more|less)|"
    r"\bratio of \d|\b\d+:\d+\b)", re.I)
QUOTE_RE = re.compile(r"[\"“]([^\"”]{25,}?)[\"”]")
MARKER_RE = re.compile(r"\[(?:CITATION NEEDED|SOURCE\?)\]", re.I)


# --------------------------------------------------------------------------- source texts

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)        # de-hyphenate line breaks
    s = s.lower().replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"[^\w]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class Corpus:
    """Text of every note and source file, split into pages where the format has them."""

    def __init__(self, notes_dir: Path | None, sources_dir: Path | None, cache_dir: Path | None):
        self.docs = {}   # label -> list of (page_label, normalized text)
        self.cache_dir = cache_dir
        self.pdf_warning = ""
        for d in [x for x in (notes_dir, sources_dir) if x and x.exists()]:
            for p in sorted(d.rglob("*")):
                if p.is_dir() or p.name.startswith("_template") or ".obsidian" in p.parts:
                    continue
                suf = p.suffix.lower()
                if suf in (".md", ".txt"):
                    self.docs[str(p)] = [("", norm(p.read_text(encoding="utf-8", errors="replace")))]
                elif suf == ".pdf":
                    pages = self._pdf_pages(p)
                    if pages is not None:
                        self.docs[str(p)] = pages

    def _pdf_pages(self, p: Path):
        cache = None
        if self.cache_dir:
            cache = self.cache_dir / (re.sub(r"[^\w.-]", "_", str(p)) + f".{int(p.stat().st_mtime)}.json")
            if cache.exists():
                return [tuple(x) for x in json.loads(cache.read_text())]
        try:
            from pypdf import PdfReader
        except Exception:
            self.pdf_warning = "pypdf not importable: PDFs were not searched (pip install pypdf)."
            return None
        try:
            reader = PdfReader(str(p))
            pages = [(str(i + 1), norm(pg.extract_text() or "")) for i, pg in enumerate(reader.pages)]
        except Exception as exc:  # scanned or damaged PDF
            self.pdf_warning = f"Could not read {p.name}: {exc}"
            return None
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(pages))
        return pages

    def docs_for_key(self, key: str) -> list:
        k = key.lower()
        own = []
        for label, pages in self.docs.items():
            name = Path(label).stem.lower()
            if name == k or name.startswith(k + "_") or name.startswith(k + " ") or name.startswith(k + "-"):
                own.append(label)
            elif any(re.search(r"citekey:\s*\"?" + re.escape(k) + r"\b", t) for _, t in pages[:1]):
                own.append(label)
        return own

    def find(self, quote: str, labels=None):
        """Return (label, page) of the first doc containing every fragment of the quote."""
        frags = [norm(f) for f in re.split(r"\.\.\.|…|\[\s*…?\.*\s*\]", quote)]
        frags = [f for f in frags if len(f.split()) >= 3]
        if not frags:
            return None
        for label in (labels if labels is not None else self.docs):
            pages = self.docs[label]
            joined = " ".join(t for _, t in pages)
            if all(f in joined for f in frags):
                for pg, t in pages:
                    if frags[0] in t:
                        return label, pg
                return label, "across pages"
        return None

    def best_partial(self, quote: str, labels):
        target = norm(quote).split()
        grams = {" ".join(target[i:i + 4]) for i in range(max(len(target) - 3, 1))}
        best = (0.0, None, None)
        for label in labels:
            for pg, t in self.docs[label]:
                score = sum(1 for g in grams if g in t) / max(len(grams), 1)
                if score > best[0]:
                    best = (score, label, pg)
        return best


# --------------------------------------------------------------------------- crossref

def _ssl_context():
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "NODE_EXTRA_CA_CERTS"):
        path = os.environ.get(var)
        if path and Path(path).exists():
            return ssl.create_default_context(cafile=path)
    return ssl.create_default_context()


def crossref(doi: str):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi.strip())
    req = urllib.request.Request(url, headers={"User-Agent": "verify_citations/1.0 (mailto:research@example.org)"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=_ssl_context()) as r:
            return json.loads(r.read().decode())["message"], None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}" + (" (DOI not registered with Crossref)" if exc.code == 404 else "")
    except Exception as exc:
        return None, f"network blocked or unreachable ({exc.__class__.__name__}); allow api.crossref.org"


def _tokens(s):
    return set(norm(s).split())


def compare_crossref(e: Entry, msg: dict) -> list:
    issues = []
    cr_title = (msg.get("title") or [""])[0]
    a, b = _tokens(e.title), _tokens(cr_title)
    if a and b and len(a & b) / len(a | b) < 0.8:
        issues.append(f"title differs: Crossref has \"{cr_title}\"")
    parts = ((msg.get("published-print") or msg.get("published-online") or msg.get("issued") or {})
             .get("date-parts") or [[None]])[0]
    if parts and parts[0] and e.year and str(parts[0]) != e.year[:4]:
        issues.append(f"year {e.year} vs Crossref {parts[0]}")
    for mine, theirs, label in ((e.volume, msg.get("volume"), "volume"), (e.issue, msg.get("issue"), "issue")):
        if mine and theirs and str(mine) != str(theirs):
            issues.append(f"{label} {mine} vs Crossref {theirs}")
    if e.pages and msg.get("page"):
        if re.findall(r"\d+", e.pages)[:1] != re.findall(r"\d+", msg["page"])[:1]:
            issues.append(f"pages {e.pages} vs Crossref {msg['page']}")
    cr_auth = msg.get("author") or []
    if e.authors and cr_auth and norm(e.authors[0][0]) != norm(cr_auth[0].get("family", cr_auth[0].get("name", ""))):
        issues.append(f"first author {e.authors[0][0]} vs Crossref {cr_auth[0].get('family', cr_auth[0].get('name'))}")
    cont = (msg.get("container-title") or [""])[0]
    if e.container and cont and len(_tokens(e.container) & _tokens(cont)) / max(len(_tokens(e.container) | _tokens(cont)), 1) < 0.6:
        issues.append(f"container \"{e.container}\" vs Crossref \"{cont}\"")
    return issues


# --------------------------------------------------------------------------- MLA 9

def _name_list(names, first_inverted=True) -> str:
    def fmt(n, inv):
        fam, giv = n
        if not giv:
            return fam
        return f"{fam}, {giv}" if inv else f"{giv} {fam}"
    if not names:
        return ""
    if len(names) == 1:
        return fmt(names[0], first_inverted)
    if len(names) == 2:
        return f"{fmt(names[0], first_inverted)}, and {fmt(names[1], False)}"
    return f"{fmt(names[0], first_inverted)}, et al."


def _dot(s: str) -> str:
    s = s.strip()
    return s if s.endswith((".", "?", "!")) else s + "."


def mla(e: Entry) -> str:
    miss = lambda f: f"[MISSING: {f}]"
    pages = e.pages.replace("--", "–").replace("-", "–")
    pp = (("pp. " if "–" in pages else "p. ") + pages) if pages else ""
    author = _name_list(e.authors) or (_name_list(e.editors) + (", editors" if len(e.editors) > 1 else ", editor")
                                       if e.editors else "")
    head = _dot(author) + " " if author else ""
    doi = f"https://doi.org/{e.doi}" if e.doi else e.url
    year = e.year or miss("year")
    if e.type == "article":
        bits = [f"*{e.container or miss('journal')}*"]
        bits.append(f"vol. {e.volume}" if e.volume else miss("volume"))
        if e.issue:
            bits.append(f"no. {e.issue}")
        bits += [year, pp or miss("pages")]
        body = f"\"{_dot(e.title or miss('title'))}\" " + ", ".join(bits) + "."
    elif e.type == "chapter":
        bits = [f"*{e.container or miss('book title')}*"]
        if e.editors and e.authors:
            bits.append("edited by " + " and ".join(f"{g} {f}".strip() for f, g in e.editors[:2])
                        + (" et al." if len(e.editors) > 2 else ""))
        bits += [e.publisher or miss("publisher"), year, pp or miss("pages")]
        body = f"\"{_dot(e.title or miss('title'))}\" " + ", ".join(bits) + "."
    elif e.type == "book":
        body = f"*{e.title or miss('title')}*. {e.publisher or miss('publisher')}, {year}."
    elif e.type == "report":
        pub = e.institution or e.publisher or miss("institution")
        body = f"*{e.title or miss('title')}*. " + (f"{pub}, " if norm(pub) != norm(author) else "") + f"{year}."
    elif e.type == "thesis":
        body = f"*{e.title or miss('title')}*. {year}. {e.institution or miss('institution')}, {e.thesis_type or 'thesis'}."
    elif e.type == "web":
        bits = [f"*{e.container}*"] if e.container else []
        bits.append(e.year or "n.d.")
        body = f"\"{_dot(e.title or miss('title'))}\" " + ", ".join(bits) + "."
    else:
        body = f"*{e.title or miss('title')}*. {year}."
    out = head + body
    if doi:
        out = out.rstrip(".") + f", {doi}."
    if e.type == "web":
        out += f" Accessed {e.urldate}." if e.urldate else " [MISSING: access date]"
    return out


# --------------------------------------------------------------------------- reporting

class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, where, msg):
        self.rows.append((level, where, msg))

    def count(self, level):
        return sum(1 for r in self.rows if r[0] == level)

    def render(self, title):
        out = [f"# {title}", "",
               f"ERROR {self.count('ERROR')} · WARN {self.count('WARN')} · OK {self.count('OK')} · INFO {self.count('INFO')}", ""]
        for level in ("ERROR", "WARN", "OK", "INFO"):
            rows = [r for r in self.rows if r[0] == level]
            if rows:
                out.append(f"## {level}")
                out += [f"- {w}: {m}" if w else f"- {m}" for _, w, m in rows]
                out.append("")
        return "\n".join(out)


def check_entry(e: Entry, rep: Report, where: str):
    missing = [f for f in REQUIRED.get(e.type, REQUIRED["other"]) if not e.has(f)]
    if missing:
        rep.add("ERROR", where, f"@{e.key} ({e.raw_type}) lacks required field(s): {', '.join(missing)}. "
                                "Complete it in Zotero before citing.")
    soft = [f for f in RECOMMENDED.get(e.type, []) if not e.has(f)]
    if soft:
        rep.add("INFO", where, f"@{e.key} has no {', '.join(soft)}")


def find_root(start: Path) -> Path:
    for d in [start, *start.parents]:
        if (d / "research").is_dir() or (d / ".git").exists():
            return d
    return start


def default_library(root: Path) -> list:
    zdir = root / "research" / "zotero"
    return sorted([*zdir.glob("*.bib"), *zdir.glob("*.json")]) if zdir.exists() else []


def audit_library(lib: dict, online: bool) -> Report:
    rep = Report()
    seen_doi, seen_title = {}, {}
    for e in lib.values():
        check_entry(e, rep, "library")
        if e.doi:
            if e.doi.lower() in seen_doi:
                rep.add("WARN", "library", f"@{e.key} and @{seen_doi[e.doi.lower()]} share DOI {e.doi}")
            seen_doi[e.doi.lower()] = e.key
        t = (norm(e.title), e.year)
        if e.title and t in seen_title:
            rep.add("WARN", "library", f"@{e.key} and @{seen_title[t]} look like duplicates (same title and year)")
        seen_title[t] = e.key
        if online and e.doi:
            _online_check(e, rep, "library")
    rep.add("INFO", "", f"{len(lib)} entries audited")
    return rep


_blocked = {"flag": False}


def _online_check(e: Entry, rep: Report, where: str):
    if _blocked["flag"]:
        return
    msg, err = crossref(e.doi)
    if err:
        if "network" in err:
            _blocked["flag"] = True
            rep.add("WARN", where, f"Crossref check skipped: {err}")
        else:
            rep.add("WARN", where, f"@{e.key} DOI {e.doi}: {err}")
        return
    issues = compare_crossref(e, msg)
    if issues:
        rep.add("ERROR", where, f"@{e.key} disagrees with Crossref: " + "; ".join(issues))
    else:
        rep.add("OK", where, f"@{e.key} matches Crossref ({e.doi})")


def verify_draft(draft: Path, lib: dict, corpus: Corpus, online: bool) -> tuple:
    rep = Report()
    text = read_draft(draft)
    cited, checked_online = [], set()
    for line, s in sentences(text):
        where = f"L{line}"
        cites = [c for c in extract_citations(line, s) if not c.key.startswith(("fig:", "tbl:", "sec:", "eq:"))]
        has_marker = bool(MARKER_RE.search(s))
        for c in cites:
            e = lib.get(c.key)
            if not e:
                rep.add("ERROR", where, f"@{c.key} is not in the Zotero export. Add it in Zotero or replace with [CITATION NEEDED].")
                continue
            if c.key not in cited:
                cited.append(c.key)
                check_entry(e, rep, where)
            if online and e.doi and c.key not in checked_online:
                checked_online.add(c.key)
                _online_check(e, rep, where)
            lp, rng = locator_pages(c.locator) if c.locator else None, e.page_range()
            if lp and rng and e.type in ("article", "chapter") and (lp[0] < rng[0] or lp[1] > rng[1]):
                rep.add("ERROR", where, f"@{c.key} locator \"{c.locator}\" falls outside the printed page range {e.pages}")
        # direct quotations
        for qm in QUOTE_RE.finditer(s):
            quote = qm.group(1)
            if len(quote.split()) < 6:
                continue
            short = (quote[:70] + "…") if len(quote) > 70 else quote
            if not cites:
                rep.add("ERROR", where, f"quotation without citation: \"{short}\"")
                continue
            own = [l for c in cites for l in corpus.docs_for_key(c.key)]
            hit = corpus.find(quote, own) if own else None
            if hit:
                pg = f", PDF page {hit[1]}" if hit[1] else ""
                loc = "; ".join(c.locator for c in cites if c.locator) or "none"
                rep.add("OK", where, f"quote found in {Path(hit[0]).name}{pg} (draft locator: {loc})")
                continue
            elsewhere = corpus.find(quote)
            if elsewhere:
                rep.add("ERROR", where, f"quote found in {Path(elsewhere[0]).name}, not in the source text for "
                        f"{', '.join('@' + c.key for c in cites)}: check attribution. \"{short}\"")
            elif own:
                score, lbl, pg = corpus.best_partial(quote, own)
                hint = f" (closest: {Path(lbl).name}{' PDF p. ' + pg if pg else ''}, {score:.0%} overlap)" if lbl and score >= 0.3 else ""
                rep.add("ERROR", where, f"quote NOT found verbatim in the cited source{hint}: \"{short}\"")
            else:
                rep.add("WARN", where, f"no source text in the workspace for {', '.join('@' + c.key for c in cites)}; "
                        f"quote unverifiable: \"{short}\"")
        # figures
        if FIGURE_RE.search(s) and not has_marker:
            fig = FIGURE_RE.search(s).group(0)
            if not cites:
                rep.add("WARN", where, f"figure \"{fig}\" has no citation or [SOURCE?] marker")
            elif not any(LOCATOR_RE.search(c.locator) for c in cites):
                rep.add("WARN", where, f"figure \"{fig}\" is cited without a page/section locator")
        if has_marker:
            rep.add("INFO", where, f"open marker: {MARKER_RE.search(s).group(0)}")
    if corpus.pdf_warning:
        rep.add("WARN", "", corpus.pdf_warning)
    rep.add("INFO", "", f"{len(cited)} distinct works cited; {len(corpus.docs)} source/note files searched")
    return rep, cited


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", nargs="?", help="draft file (.md, .qmd, .tex, .txt, .docx)")
    ap.add_argument("--library", action="append", help="Zotero export (.bib or CSL .json); default research/zotero/*")
    ap.add_argument("--notes", help="Obsidian notes folder (default research/notes)")
    ap.add_argument("--sources", help="source PDFs folder (default research/sources)")
    ap.add_argument("--online", action="store_true", help="also check DOIs against Crossref")
    ap.add_argument("--works-cited", action="store_true", help="append an MLA 9 Works Cited list of the cited keys")
    ap.add_argument("--mla", nargs="+", metavar="KEY", help="print MLA 9 references for these keys and exit")
    ap.add_argument("--audit-library", action="store_true", help="audit every entry in the library")
    ap.add_argument("--out", help="write the report to this file as well")
    ap.add_argument("--no-fail", action="store_true", help="exit 0 even when errors are found")
    a = ap.parse_args(argv)

    root = find_root(Path(a.draft).resolve().parent if a.draft else Path.cwd())
    lib_paths = a.library or default_library(root)
    if not lib_paths:
        print(f"No Zotero export found in {root / 'research' / 'zotero'}. Export the library with Better BibTeX "
              "(keep updated) to research/zotero/library.bib, or pass --library.", file=sys.stderr)
        return 2
    lib = load_library(lib_paths)

    if a.mla:
        for k in a.mla:
            print(mla(lib[k]) if k in lib else f"@{k}: not in the Zotero export")
        return 0
    if a.audit_library:
        rep = audit_library(lib, a.online)
        out = rep.render(f"Library audit: {', '.join(Path(p).name for p in lib_paths)}")
    else:
        if not a.draft:
            ap.error("give a draft, --mla KEY or --audit-library")
        notes = Path(a.notes) if a.notes else root / "research" / "notes"
        sources = Path(a.sources) if a.sources else root / "research" / "sources"
        corpus = Corpus(notes, sources, root / "research" / ".cache" / "text")
        rep, cited = verify_draft(Path(a.draft), lib, corpus, a.online)
        out = rep.render(f"Citation check: {Path(a.draft).name}")
        if a.works_cited and cited:
            refs = sorted((lib[k] for k in cited), key=lambda e: norm(_name_list(e.authors) or e.title))
            out += "\n## Works Cited (MLA 9, generated from the Zotero export)\n\n" + "\n\n".join(mla(e) for e in refs) + "\n"
    print(out)
    if a.out:
        Path(a.out).write_text(out, encoding="utf-8")
    return 0 if a.no_fail or rep.count("ERROR") == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
