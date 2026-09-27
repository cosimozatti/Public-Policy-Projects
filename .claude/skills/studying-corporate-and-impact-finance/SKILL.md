---
name: studying-corporate-and-impact-finance
description: Corporate finance and impact investing analysis, with a bundled calculator, built for LSE Corporate Finance (Berk and DeMarzo), FM471 Sustainable Finance and Impact Investing and the Turner MIINT. Solves and checks NPV, IRR, capital budgeting, CAPM, WACC, beta, DCF, APV, FTE, capital structure, payout, IPO and multiples problems; values firms, projects and startups; builds MIINT deliverables (thesis, sourcing, business and impact diligence, seed valuation, SAFE and cap table, memo, IC deck); teaches and quizzes. Use whenever a prompt asks for financial analysis of a company, project, startup or investment: valuation, cost of capital, cash flow forecasts, returns, leverage, dilution or deal terms, and whenever the user mentions a problem set, past paper, revision, Berk DeMarzo, FM471, ESG, climate finance, impact investing or MIINT, even when no course is named. For IFI, FAO, EIB or agrifood appraisal notes (ENPV, EIRR, PAM), prefer appraising-agrifood-investments and use this skill only for its calculator.
---

# Corporate and impact finance companion

Three courses and projects share this skill, since they draw on one toolkit:

- Corporate Finance, taught from Berk and DeMarzo, *Corporate Finance*, Pearson International Edition (edition number not yet confirmed by the user). Financial markets, valuation, capital structure, payout, IPOs.
- FM471 Sustainable Finance and Impact Investing (Winter Term 2026/27, Dr Greg Fischer). ESG investing, climate finance, impact investing, stakeholder versus shareholder views of the firm.
- Turner MIINT, where a team of five LSE students sources a seed-stage impact company, runs business and impact diligence, submits eight deliverables and pitches to an investment committee for a potential $50,000 investment.

Identify which of the three modes the request needs, then read the matching reference file. Most requests need one; a MIINT valuation question needs both the MIINT and the corporate finance files.

| Mode | Trigger | Read |
|---|---|---|
| Solve or check | A numerical or conceptual problem, a past paper, "check my answer", a valuation with given inputs | `references/corporate-finance.md` |
| MIINT deliverable | Thesis, sourcing, diligence, term sheet, cap table, memo, deck, IC prep for a startup | `references/miint.md` (plus the corporate finance file for valuation) |
| Teach or quiz | "Explain", "I don't get", "quiz me", "test me", revision, flashcards | `references/teaching.md` |

## Calculator

`scripts/fincalc.py` (Python 3, standard library only) does the arithmetic and prints the formula alongside every result, so the output can go straight into a worked answer. Use it for any computation beyond a line or two instead of computing by hand, since hand arithmetic across a multi-year DCF is where errors enter.

```
python scripts/fincalc.py tvm annuity --c 100 --r 0.05 --n 10 [--g 0.02] [--due]
python scripts/fincalc.py npv --cfs=-100,60,60 --r 0.10         # NPV, all IRR roots, MIRR, payback, PI
python scripts/fincalc.py wacc --E 600 --D 400 --rE 0.12 --rD 0.06 --t 0.25
python scripts/fincalc.py beta unlever --beta 1.5 --DE 0.5 --bD 0.1 [--policy fixed --t 0.25]
python scripts/fincalc.py dcf --fcf 10,11,12 --wacc 0.10 --g 0.02 --net-debt 20 --shares 10
python scripts/fincalc.py apv --fcf 10,10,10 --rU 0.10 --rD 0.05 --t 0.25 --debt 50,50,50
python scripts/fincalc.py vc --investment 1e6 --exit-metric 20e6 --exit-multiple 3 --years 5 --target-irr 0.4 --retention 0.7
python scripts/fincalc.py round --pre 8e6 --investment 2e6 --shares 1e7 --pool-existing 5e5 --pool-target 0.10 \
    --convertibles '[{"amount":500000,"cap":5e6,"discount":0.2}]'
```

Pass negative first cash flows with `--cfs=-100,...` (the equals sign stops the minus being read as a flag). Rates are decimals.

## Standing rules

These come from the user's own working conventions and apply in every mode.

**Show the method before the number.** Write the formula in symbols, then substitute, then give the result with units and timing (for example "value at t=0, £m"). The user needs to reproduce the method under exam conditions, so an answer without the setup has little value even when the number is right.

**State every assumption at the point it is made.** Timing (end-of-year, annuity due, mid-year), nominal versus real, tax rate, debt policy (constant D/E or fixed debt), whether a growth rate applies from year 1 or year N+1. When a problem is silent, choose the textbook default, say so, and show how the answer moves if the other convention applies.

**Sanity-check before reporting.** Does the NPV sign match the intuition? Is WACC between the after-tax cost of debt and the cost of equity? Is g below the discount rate and below long-run nominal GDP growth? Does the terminal value exceed three quarters of enterprise value (the calculator flags this)? Does the cap table sum to 100%? Say what the check found.

**Separate source, inference and assumption.** In MIINT work especially, keep three categories visibly apart: what a company document or the user's data states (with its locator, meaning document name plus page or section), what is inferred from it, and what is assumed. Collect assumptions in one labelled list. Any figure without a locator is marked [SOURCE?]. Never fill a market size, comparable multiple, default rate or impact benchmark from memory; mark it and say where it could be found.

**Citations only from verifiable sources.** A reference is admissible only if it comes from a file in the workspace, the user's Zotero export, or a page fetched during the session. The Berk and DeMarzo edition is unconfirmed, so do not cite chapter, section, equation or page numbers from memory; name the concept ("the WACC method with a constant debt-equity ratio") and write [CHECK B&D edition] if the user will need the location. Where a claim needs a citation that cannot be verified, write [CITATION NEEDED] rather than supplying a plausible reference.

**Take a position.** When approaches disagree (WACC versus APV when leverage changes, VC method versus comparables at seed stage, whether an impact claim meets a contribution test), recommend one and give the reason, then say what would change the recommendation. Differentiate confidence: say when something is textbook-settled, when it rests on a single study, and when it is a projection.

**Writing style.** No em-dashes or en-dashes in body text (en-dashes only in page and date ranges). No bold for emphasis inside running prose. Avoid filler vocabulary (for example delve, leverage as a verb, robust as decoration, crucial, pivotal, holistic, seamless) unless it is a technical term such as "robust standard errors" or "financial leverage". For long-form MIINT prose (memo narrative, thesis rationale) the `drafting-analytical-prose` skill, where installed, holds the full house style and self-check; use it for that text.

**Ask one question when the deliverable is unclear.** If it is not clear whether the user wants a worked solution, a check of their own attempt, or a hint, ask once before writing. For a "check my answer" request, locate the first step where the user's working diverges and explain that step; do not simply print a model answer, since the user wants to learn where their reasoning broke.

## Datasets

If the user supplies a spreadsheet or data file (a company's financials, a cap table, a comparables set), audit it before any valuation: missing values, duplicates, unit and currency inconsistencies (thousands versus millions, local currency versus USD), impossible values, and inconsistent date or fiscal-year coding. The `auditing-datasets` skill, where installed, has a script for this. Report the audit, then proceed.

## Known gaps

- The Turner MIINT deliverable guide (the list and deadlines of the eight deliverables) is not in the workspace. The session that built this skill could not reach the Turner MIINT site. Ask the user for the guide before drafting a specific deliverable, and follow its template over the generic structure in `references/miint.md`.
- The Corporate Finance course outline and the Berk and DeMarzo edition are not in the workspace. When the user shares them, prefer their notation and topic order.
