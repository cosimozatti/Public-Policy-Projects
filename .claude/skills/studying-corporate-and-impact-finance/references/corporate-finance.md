# Corporate finance toolkit (solve and check mode)

Notation follows the Berk and DeMarzo convention as far as it is known without the book at hand: rU unlevered cost of capital, rE cost of equity, rD cost of debt, rwacc, tc corporate tax rate, FCF free cash flow, E, D, V = E + D market values. If the user's edition or lecture slides use different symbols, switch to theirs. Chapter and page locations are not given here on purpose, since the edition is unconfirmed.

## Contents
1. Procedure for any problem
2. Time value, rates, bonds, stocks
3. Capital budgeting
4. Risk, return and the cost of capital
5. Capital structure
6. Valuation with leverage: WACC, APV, FTE
7. Payout policy
8. Multiples and DCF practice
9. IPOs and raising equity
10. Traps that cost marks

## 1. Procedure for any problem

1. Restate what is asked and at which date the value is wanted.
2. Draw the timeline: list each cash flow with its date. Most errors are timing errors (a perpetuity valued at t=N sits one period before its first cash flow; an annuity due starts at t=0).
3. Match the rate to the cash flow: nominal with nominal, real with real; the period of the rate with the period of the flow; rU for unlevered flows, rE for equity flows, rwacc for FCF under a constant leverage ratio.
4. Write the formula, substitute, compute (use `scripts/fincalc.py`).
5. Check sign, magnitude and one limiting case, then interpret in one sentence ("the project creates £4.1m of value at t=0, so accept").

## 2. Time value, rates, bonds, stocks

- PV of lump sum: C / (1 + r)^n. Annuity: C/r [1 − 1/(1+r)^n]. Growing annuity: C/(r − g) [1 − ((1+g)/(1+r))^n]. Perpetuity: C/r. Growing perpetuity: C1/(r − g), needs r > g, first flow one period out.
- Annuity due = ordinary annuity × (1 + r).
- EAR = (1 + APR/m)^m − 1. Converting an annual rate to a k-period rate: (1 + EAR)^(1/k) − 1, not EAR/k.
- Real rate: (1 + r_real) = (1 + r_nominal) / (1 + inflation). The approximation r_nominal − inflation is fine only for low rates; say which one is used.
- Bond price = PV of coupons + PV of face at the yield to maturity. Price above par when coupon rate > YTM. Clean versus dirty price if accrued interest appears.
- Law of one price and no-arbitrage: if two portfolios have identical cash flows they must trade at the same price; many "prove this" questions reduce to building the replicating portfolio.
- Dividend discount model: P0 = Div1 / (rE − g). Implied rE = Div1/P0 + g. Sustainable growth g = retention rate × return on new investment. Growth adds value only when the return on new investment exceeds rE.
- Total payout model: value equity as PV of dividends plus repurchases, then divide by current shares.
- Discounted FCF model: EV = PV(FCF at rwacc); equity = EV + cash − debt; per share = equity / shares outstanding.

## 3. Capital budgeting

Incremental free cash flow:

FCF = (Revenue − Costs − Depreciation)(1 − tc) + Depreciation − CapEx − ΔNWC

equivalently FCF = (Revenue − Costs)(1 − tc) − CapEx − ΔNWC + tc × Depreciation (the depreciation tax shield).

Include: opportunity cost of assets the firm already owns, cannibalisation of existing sales, side effects, working capital build-up and its recovery at the end, after-tax salvage value = Sale price − tc (Sale price − Book value).
Exclude: sunk costs, allocated overhead that does not change, interest payments (financing enters through the discount rate, not the cash flows).

Decision rules:
- NPV is the rule of record. Accept NPV > 0; among mutually exclusive projects choose the highest NPV.
- IRR fails when cash flows change sign more than once (multiple roots; the calculator lists them), when projects differ in scale or timing, and when the term structure is not flat. For mutually exclusive projects use NPV or the IRR of the incremental cash flows.
- Payback ignores flows after the cutoff and the time value of money.
- Profitability index ranks projects under a single resource constraint; it breaks down with several constraints.
- Sensitivity, scenario and break-even analysis: vary one input (sensitivity), several consistently (scenario), or solve for the input that sets NPV = 0 (break-even). Report which input the decision is most exposed to.
- Real options (expand, abandon, delay) add value to flexible projects; a static NPV understates them.

## 4. Risk, return and the cost of capital

- Portfolio return: weighted average. Portfolio variance: w'Σw; for two assets w1²σ1² + w2²σ2² + 2w1w2ρσ1σ2.
- Diversification removes idiosyncratic risk only; systematic risk is priced.
- CAPM: r_i = rf + β_i (E[R_mkt] − rf). β_i = Cov(R_i, R_mkt) / Var(R_mkt). Sharpe ratio = (E[R] − rf)/σ.
- Security market line: assets above it have positive alpha.
- Cost of debt: yield to maturity overstates the expected return when default risk is material; rD = rf + βD × market risk premium is the alternative.
- Project cost of capital: use the unlevered beta of comparable pure-play firms, averaged, then relever to the project's target leverage. Do not use the firm's WACC for a project with a different risk profile.

Levering and unlevering (`fincalc.py beta`):
- Constant D/E (the usual textbook default): βU = E/V βE + D/V βD, equivalently βE = βU + D/E (βU − βD).
- Permanent fixed debt with the tax shield as risky as the debt: βE = βU + (D/E)(1 − tc)(βU − βD). With βD = 0 this is the Hamada formula. Say which policy is assumed, since the two give different answers when tc > 0.

WACC: rwacc = E/V rE + D/V rD (1 − tc). Pre-tax WACC = E/V rE + D/V rD = rU when leverage is held constant. Hence rwacc = rU − D/V tc rD.

## 5. Capital structure

Modigliani-Miller, perfect markets:
- Proposition I: VL = VU. Leverage does not change firm value.
- Proposition II: rE = rU + D/E (rU − rD). Equity gets riskier as leverage rises; WACC is constant.
- Homemade leverage: investors can replicate any capital structure themselves, which is the arbitrage argument behind Proposition I.

With corporate taxes:
- VL = VU + PV(interest tax shields).
- Permanent debt D: PV(ITS) = tc D.
- Constant D/V ratio: tax shields are discounted at rU (they scale with firm value), so PV(ITS) is below tc D.
- Personal taxes (Miller): effective tax advantage of debt τ* = 1 − (1 − tc)(1 − te)/(1 − ti), where te is the personal tax on equity income and ti on interest income.

Beyond taxes:
- Trade-off theory: VL = VU + PV(ITS) − PV(financial distress costs) − PV(agency costs of debt) + PV(agency benefits of debt). Optimal leverage balances the marginal tax benefit against marginal distress cost.
- Agency costs of debt: asset substitution (risk shifting), debt overhang (underinvestment), cashing out.
- Agency benefits of debt: disciplines managers with free cash flow, concentrates ownership.
- Asymmetric information: equity issues signal overvaluation (lemons problem), so the announcement return is negative; this gives the pecking order (internal funds, then debt, then equity) and market timing.
- Where the question asks for a verdict, say that tax shield and distress cost arguments are textbook-settled in direction but that the magnitude of distress costs is contested empirically, and mark any specific estimate [CITATION NEEDED] unless it comes from the course material.

## 6. Valuation with leverage: WACC, APV, FTE

All three give the same answer when applied consistently; the choice depends on the debt policy.

| Method | Discount | Cash flows | Best when |
|---|---|---|---|
| WACC | rwacc | FCF | D/V held constant |
| APV | rU for FCF; rD or rU for tax shields | FCF, then add PV(ITS), subtract distress and issuance costs | Debt follows a known schedule (LBO, project finance), or leverage changes |
| FTE | rE | FCFE = FCF − (1 − tc) Interest + Net borrowing | Equity is the object of interest, or the question asks for it |

APV steps (`fincalc.py apv`):
1. VU = PV(FCF at rU).
2. Interest tax shield in year t = tc × rD × D(t−1).
3. Discount at rD if the debt schedule is fixed in advance, at rU if debt is rebalanced continuously to a target ratio. If debt is reset to the target once a year, each year's shield is known one year ahead, so discount it one period at rD and the earlier periods at rU: ITS_t / [(1 + rU)^(t−1)(1 + rD)]. The calculator covers the two pure cases only; say which is used.
4. VL = VU + PV(ITS) − other frictions.

Cost of equity with a fixed debt schedule: rE = rU + (D − Ts)/E (rU − rD), where Ts = PV(ITS) on predetermined tax shields. With constant D/E this collapses to MM II.

Adjustments the course may test: issuance costs (subtract from value), security mispricing, financial distress and agency costs (subtract), periodically adjusted leverage, and personal taxes (replace tc by τ*).

## 7. Payout policy

- Under perfect markets, payout policy is irrelevant (MM): a dividend and an open-market repurchase of the same size leave shareholder wealth unchanged. Share price falls by the dividend on the ex-date; a repurchase at market price leaves the price unchanged.
- Taxes: where dividends are taxed more heavily than capital gains, repurchases dominate; the effective dividend tax rate matters.
- Retaining cash: with corporate taxes, retained cash earns interest taxed at tc, a cost relative to paying out; agency costs of free cash flow add to this.
- Signaling: dividend smoothing, and the market reads increases as confidence about future earnings; repurchases can signal undervaluation.
- Stock dividends and splits do not change value.

## 8. Multiples and DCF practice

- Match numerator and denominator: enterprise multiples (EV/EBITDA, EV/Sales) with enterprise value; equity multiples (P/E) with equity value. Mixing them is a common mark loss.
- Use forward multiples when growth is high; adjust for differences in leverage, growth and margins across comparables, and say how.
- DCF sequence (`fincalc.py dcf`): forecast revenue, margins, CapEx, NWC; compute unlevered FCF; discount at rwacc; terminal value by Gordon growth or exit multiple; EV to equity by subtracting net debt (and preferred, minorities, adding non-operating assets).
- Terminal value checks: g at or below long-run nominal growth; the implied exit multiple from the Gordon formula should be plausible against current trading multiples; when TV is above about 75% of EV, run a sensitivity table on g and rwacc and say so.
- Mid-year convention raises value by roughly (1 + rwacc)^0.5; apply it only when the question or the model convention calls for it.

## 9. IPOs and raising equity

- Sources for private firms: angels, venture capital, private equity, institutional and corporate investors. Venture terms: pre-money = post-money − new investment; post-money = price per share × post-round shares. Liquidation preferences, participation and anti-dilution protection mean the headline post-money overstates common equity value.
- IPO mechanics: underwriter or syndicate, firm commitment versus best efforts, book building, pricing, over-allotment (greenshoe) option, lock-up period. State specific percentages or durations only from the course material or a fetched source; otherwise mark [SOURCE?].
- IPO puzzles the course is likely to treat: underpricing (first-day returns), cyclicality and hot issue markets, high underwriting costs, long-run underperformance. Explanations for underpricing: winner's curse (uninformed investors get full allocations in bad deals, so average pricing must compensate), information revelation in book building, underwriter incentives and risk. Take a position on which explanation fits the facts in the question.
- Seasoned equity offerings: negative announcement return, consistent with adverse selection; cash offers versus rights offers.

## 10. Traps that cost marks

- Discounting a perpetuity that starts at t = N+1 back from t = N+1 instead of t = N.
- Including interest in project FCF, then also discounting at WACC (double counting the tax shield).
- Forgetting the recovery of working capital or taxing the whole salvage value instead of the gain over book.
- Using the firm WACC for a division with different risk.
- Relevering with market D/E in one step and book D/E in another.
- Applying the IRR rule with non-conventional cash flows or to mutually exclusive projects of different scale.
- Growth rate above the discount rate, or above long-run economic growth for a terminal value.
- Dividing a valuation by basic rather than fully diluted shares when options or convertibles are in the money.
