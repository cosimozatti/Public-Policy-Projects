# Turner MIINT deliverables

## What the workspace says about the competition

Source: `turner_miint_general_info.docx` (LSE Student Services Centre slides plus Turner MIINT news pages, uploaded by the user). Quote from it rather than paraphrasing when a deliverable needs a fact about the programme.

- LSE sends one team of five; the team sources and diligences "an investment opportunity of a seed stage company" and completes online modules while "submitting eight deliverables" (docx, slide 1).
- Training modules listed (docx, "Learn" section): Introduction to Impact Investing; Investment Thesis and Strategy; Sourcing Early Stage Impact Investments; Conducting Due Diligence: Assessing Business Potential; Conducting Due Diligence: Assessing Potential Impact; Assessing Terms and Structure of Investments.
- Teams present to an investment committee "for a potential investment of up to $50,000" (docx, "Compete" section). In the 2021 write-up, prize investments came from the programme's donor-advised fund at Impact Assets and were "pending further diligence by Impact Assets" (docx, 2021 section).
- Judging factors named in the 2021 write-up: "a compelling and scalable impact proposition, rigorous diligence, and a demonstrated potential for strong financial returns" (docx, 2021 section). Brian Trelstad praised teams that went "beyond just talking with the companies' management teams, but speaking with customers, experts, and others" (same section).
- The Best Diligence award recognises analysis "regardless of investment recommendation" (docx, 2025 section), so a well-argued decline can still win recognition.
- An Impact Analysis Prize was introduced in 2025; LSE won it in 2025 (Zzapp Malaria) and in 2026 (AquaBloom) (docx, 2025 and 2026 sections). Impact diligence is where LSE teams have been recognised, so it deserves at least equal weight with the financial case.
- Finals at Wharton in April 2027 (docx, slide 2). Mentors are assigned to give feedback on deliverables (docx, slide 2).

Not in the workspace: the names, templates, word limits and deadlines of the eight deliverables. Ask the user for the deliverable guide and follow it over the generic structures below. Do not guess the list.

## Working conventions for every deliverable

- Lead with the recommendation and the binding constraint (the one fact that would flip the decision), then the support.
- Keep three layers apart and labelled: company-stated (founder deck, data room, interview notes, each with a locator), team inference, and assumption. Put assumptions in a numbered register with the reason for each value and the sensitivity of the conclusion to it.
- Founder claims are claims until triangulated. For each material claim (traction, pipeline, unit economics, impact outcomes), record who else confirmed it: customers, suppliers, domain experts, public data.
- Mark every market size, benchmark multiple, comparable round or impact benchmark without a source as [SOURCE?]. Never fill one from memory.
- Assume the committee reads the deck first and the memo second; every number in the deck must reconcile with the memo and the model.

## 1. Investment thesis and strategy

A thesis states where the team will look and why that space offers both investable returns and material impact. Cover:
- The problem, the population affected, and why current solutions fail (the market or policy failure the venture addresses).
- Why now: the technology, cost, regulatory or demand change that opens the opportunity.
- The impact logic in theory-of-change form: inputs, activities, outputs, outcomes, and the assumptions linking each step.
- Return logic: how a seed investor in this space exits or earns a return, and the realistic ticket size.
- Screening criteria derived from the thesis (see sourcing).
- What the thesis excludes, and why. A thesis that excludes nothing gives the sourcing screen nothing to do.

## 2. Sourcing screen

Build a funnel: long list, screened list, short list, selected company. Record the source of each lead. A weighted scoring matrix works well; propose criteria and weights and let the team change them:

| Criterion | What to check |
|---|---|
| Thesis fit | Sector, geography, beneficiary group |
| Stage and ticket | Seed stage; can usefully absorb a ticket of up to $50,000 alongside other investors |
| Impact intentionality and measurability | Impact is part of the business model rather than a side activity; outcomes can be measured |
| Business potential | Traction, unit economics, market size, team |
| Diligence access | Founder willing to share data and time; customers and experts reachable |
| Deal feasibility | Open round, terms known, other investors |

Report the kill reasons for dropped companies; judges ask why this company over the others.

## 3. Business due diligence

- Team: founder-market fit, completeness of the team, governance, references.
- Market: bottom-up sizing (units × price × reachable customers) over top-down TAM figures; state the source of each input.
- Product and competition: alternatives the customer uses today (including doing nothing), switching costs, defensibility.
- Business model and unit economics: price, gross margin, customer acquisition cost, lifetime value, payback, cash burn, runway. Build these from the company's data with locators.
- Traction: revenue, pilots, letters of intent, retention; distinguish signed from pipeline.
- Financial projections: rebuild the founder's model; list the three assumptions that drive it; produce base, downside and upside cases.
- Valuation (see section 5) and expected return.
- Key risks with mitigants and the evidence that would reduce each risk.

## 4. Impact due diligence

Structure the impact case so a sceptical judge can test every link:

- Theory of change with the causal assumptions made explicit, and the evidence for each assumption (company data, external evaluations, sector evidence). Rate each link as well evidenced, plausible, or untested.
- A five-dimension framing is common in practice: what outcome, who experiences it (and how underserved they are), how much (scale, depth, duration), contribution (what would have happened otherwise, the counterfactual), and risk (the chance impact differs from expectation). This framing is associated with the Impact Management Project and its successor Impact Frontiers; the session that wrote this skill could not verify the reference, so cite it only from a fetched page or the MIINT course material, otherwise [CITATION NEEDED].
- Metrics: choose a small set of outcome metrics, not only outputs; where a standard catalogue such as IRIS+ is used, take metric definitions from the catalogue itself, fetched in session.
- Investor contribution: what this $50,000 and the investor's non-financial support change, separate from company contribution.
- Impact risks: evidence risk, execution risk, drop-off, unexpected negative effects, displacement, stakeholder participation. Name the most material one.
- Impact-return alignment: does growth of the business increase impact, or can the company grow by drifting away from the target population?
- Where the user has LSE methods training (causal inference, stated-preference methods), propose how the company could measure its counterfactual impact, for example a comparison group, a phased roll-out, or a willingness-to-pay survey. Say how strong identification would be.

## 5. Seed-stage valuation and terms

Valuation at seed stage rests on assumptions, so present a range and the assumption driving it.

- VC method (`fincalc.py vc`): exit value = exit-year metric × exit multiple; discount at a target IRR or money multiple; adjust for expected dilution from later rounds via a retention ratio; required ownership = investment / post-money. Target IRRs and exit multiples need a source [SOURCE?].
- Comparable rounds: recent seed rounds of similar companies, with sources.
- Practitioner heuristics (scorecard, checklist methods) can supplement but not replace the above; name them as heuristics.
- Cap table (`fincalc.py round`): pre-money, round size, option pool top-up ("option pool shuffle" dilutes existing holders only if the top-up is in the pre-money), conversion of SAFEs and convertible notes. The calculator uses a pre-money cap convention; a post-money SAFE converts to a fixed ownership of amount / post-money cap, so compute that case by hand and say so.
- Instruments: priced equity, SAFE, convertible note (interest, discount, cap, maturity), revenue-based financing, and impact-specific structures such as impact-linked terms or demand dividends. Explain why the chosen instrument suits a company at this stage and a ticket of this size.
- Terms to address: valuation or cap, liquidation preference, pro rata rights, information rights, board or observer rights, and impact covenants or reporting requirements.
- Returns: expected multiple and IRR under base, downside and upside; the probability-weighted view matters more than the upside case.

## 6. Investment memo

Recommended order, to be replaced by the MIINT template if the user supplies it:

1. Recommendation and proposed terms, with the binding condition.
2. Company and deal summary (one paragraph, one table).
3. Thesis fit.
4. Business case: market, model, unit economics, team, traction.
5. Financial projections, valuation and expected returns.
6. Impact case: theory of change, five-dimension assessment, metrics, investor contribution, impact risks.
7. Key risks and mitigants, business and impact together.
8. Diligence performed: who the team spoke to, what data was reviewed, what could not be verified.
9. Open questions and conditions precedent.
10. Assumption register and sources.

For narrative sections, apply the user's house style (the `drafting-analytical-prose` skill where installed, in professional drafting mode).

## 7. IC deck and Q&A preparation

- One message per slide, with the recommendation on slide 2.
- Each number on a slide carries a footnote to the memo or model.
- Build a Q&A bank: for each section, the three hardest questions a judge could ask, the short answer, and the backup slide. Always include: why this company over the others screened; what the counterfactual is for the beneficiaries; what happens to impact if the company pivots; what the $50,000 changes; the weakest assumption in the model; what the team would need to see to change its recommendation.
- Rehearse a two-minute version; judges interrupt.
