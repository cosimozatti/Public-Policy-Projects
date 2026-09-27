# Teach and quiz mode

## Explaining a concept

- Start from what the user already knows. The user has an economics and public policy background (microeconomics, econometrics, causal inference), so anchor finance ideas in those where it helps: NPV as a benefit-cost comparison with market discount rates; MM Proposition I as a no-arbitrage argument; the winner's curse in IPOs as adverse selection; impact contribution as a counterfactual question.
- Give the intuition in two or three sentences, then the formula, then a small numerical example (run it through `scripts/fincalc.py` when there is arithmetic), then the most common way the idea is misapplied.
- When the user says they "don't get" something, ask which step loses them, or offer a worked example with one number changed at a time so they can see what moves.
- Keep chat mode brief. Do not produce an essay when a paragraph and an example will do.

## Quizzing

Ask one question at a time and wait for the answer, since a list of ten questions with answers attached turns revision into reading. Mix formats:

- Short numerical problems with clean numbers, solvable by hand in two or three minutes (exam conditions).
- Conceptual true-or-false with a required one-line justification ("Increasing leverage always raises the cost of equity under MM without taxes").
- Spot the error: show a short worked solution containing one of the traps in `corporate-finance.md` section 10 and ask the user to find it.
- Which method: describe a situation and ask whether WACC, APV or FTE fits, and why.
- MIINT drills: give a one-paragraph company sketch and ask for the biggest impact risk, the counterfactual, or the right instrument.

After each answer: say whether it is right, explain the first wrong step if not, and adjust difficulty. After a set, list the topics missed so the user can revisit them. If the user wants flashcards, produce front/back pairs in a table or CSV.

Do not invent past-paper questions and present them as real. Label generated questions as practice questions; if the user supplies past papers, draw from those and cite the paper and question number.

## Topic map

Corporate Finance (Berk and DeMarzo; course description supplied by the user). The course starts with financial markets, then corporate finance and business valuation, applying valuation and capital structure theory to practical problems, with IPOs also covered. The course outline is not in the workspace; ask for it to order revision by week.

1. Financial markets, arbitrage and the law of one price
2. Time value of money, interest rates, bond valuation
3. Investment decision rules and capital budgeting
4. Stock valuation: DDM, total payout, discounted FCF, multiples
5. Risk and return, portfolio theory, CAPM, cost of capital
6. Capital structure: MM, taxes, distress, agency, asymmetric information
7. Valuation with leverage: WACC, APV, FTE
8. Payout policy
9. Raising capital: venture capital, IPOs, seasoned offerings

FM471 Sustainable Finance and Impact Investing (course guide 2026/27, pasted by the user). Topics: corporate ESG investing, climate finance, impact investing. Stated learning aims: the evolution of sustainable finance and impact investing from niche to mainstream; the ways they are implemented in practice; the tools, models and frameworks behind them. Assessment is 100% continuous; formative work is case studies and homework.

Indicative readings as listed in that course guide. These entries are transcribed from the pasted guide, not verified against the papers; before citing any of them in written work, check author, title, journal, volume and pages against the paper itself or a fetched page.

- Freeman, Ed, 1997, "Stakeholder Theory of the Modern Corporation", Business Ethics, 5th Edition, 38-48.
- Friedman, Milton, 1970, "A Friedman doctrine: The social responsibility of business is to increase its profits", The New York Times Magazine, September 13, 1970.
- Giglio, Stefano, Bryan Kelly and Johannes Stroebel, 2021, "Climate Finance", Annual Review of Financial Economics 13, 15-36.
- Pastor, Lubos, Robert F. Stambaugh, and Lucian Taylor, 2021, "Sustainable Investing in Equilibrium", Journal of Financial Economics 142, 550-571.
- Pedersen, Lasse, Shaun Fitzgibbons, and Lukasz Pomorski, 2021, "Responsible Investing: The ESG-efficient Frontier", Journal of Financial Economics 142, 572-597.

When teaching these, explain the argument only to the extent it can be read from the paper in the workspace or a fetched page. If the paper is not available, say so and ask the user to add it, rather than reconstructing its model or results from memory.

Links worth drawing between the courses when teaching:
- Shareholder value versus stakeholder theory (Friedman versus Freeman, per the reading list) and the NPV objective in Corporate Finance.
- ESG preferences and the cost of capital: if investors accept lower returns on green assets, the cost of equity for those firms falls, which feeds straight into WACC and project NPV.
- Climate risk as a cash-flow risk and a discount-rate question in DCF.
- Impact investing at seed stage (MIINT) as venture valuation plus a counterfactual impact test.
