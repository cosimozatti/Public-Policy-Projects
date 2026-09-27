#!/usr/bin/env python3
"""Corporate finance and venture calculator (standard library only).

Every subcommand prints the inputs it used, the formula applied and the
result, so the output can be pasted into a worked answer and checked line
by line. Rates are decimals (0.08, not 8). Cash flows are listed from t=0.

Subcommands
  tvm       present / future value of lump sums, annuities, perpetuities
  npv       NPV, IRR (with multiple-root scan), MIRR, payback, PI
  wacc      weighted average cost of capital
  beta      unlever or relever an equity beta
  dcf       enterprise and equity value from a FCF forecast
  apv       adjusted present value with a debt schedule
  vc        venture capital method (exit value back to post/pre-money)
  round     priced round with option-pool top-up and convertible conversion

Run `python fincalc.py <subcommand> -h` for the arguments of each.
"""
import argparse
import json
import sys


def fmt(x, nd=4):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:,.{nd}f}"
    return str(x)


def line(label, value, nd=4):
    print(f"  {label:<38} {fmt(value, nd)}")


def parse_list(s):
    return [float(v) for v in s.replace(";", ",").split(",") if v.strip()]


# ---------------------------------------------------------------- TVM

def annuity_pv(c, r, n, g=0.0, due=False):
    if abs(r - g) < 1e-12:
        pv = c * n / (1 + r)
    else:
        pv = c / (r - g) * (1 - ((1 + g) / (1 + r)) ** n)
    return pv * (1 + r) if due else pv


def cmd_tvm(a):
    print("TVM")
    if a.kind == "lump":
        pv = a.fv / (1 + a.r) ** a.n
        print("  formula: PV = FV / (1+r)^n")
        line("PV", pv)
    elif a.kind == "fv":
        fv = a.pv * (1 + a.r) ** a.n
        print("  formula: FV = PV (1+r)^n")
        line("FV", fv)
    elif a.kind == "annuity":
        pv = annuity_pv(a.c, a.r, a.n, a.g, a.due)
        print("  formula: PV = C/(r-g) [1 - ((1+g)/(1+r))^n]" + (" x (1+r) [annuity due]" if a.due else ""))
        line("PV", pv)
        line("FV at n", pv * (1 + a.r) ** a.n)
    elif a.kind == "perpetuity":
        if a.r <= a.g:
            sys.exit("  r must exceed g for a growing perpetuity to have finite value")
        pv = a.c / (a.r - a.g)
        print("  formula: PV = C1/(r-g), first cash flow one period from now")
        line("PV", pv)
    elif a.kind == "rate":
        # effective annual rate from APR with m compounding periods
        ear = (1 + a.r / a.m) ** a.m - 1
        print("  formula: EAR = (1 + APR/m)^m - 1")
        line("EAR", ear, 6)


# ---------------------------------------------------------------- NPV / IRR

def npv(r, cfs):
    return sum(cf / (1 + r) ** t for t, cf in enumerate(cfs))


def irr_roots(cfs, lo=-0.99, hi=10.0, steps=20000):
    """Scan for every sign change of NPV(r) on [lo, hi], refine by bisection."""
    roots = []
    step = (hi - lo) / steps
    r0, f0 = lo, npv(lo, cfs)
    for i in range(1, steps + 1):
        r1 = lo + i * step
        f1 = npv(r1, cfs)
        if f0 == 0:
            roots.append(r0)
        elif f0 * f1 < 0:
            a, b, fa = r0, r1, f0
            for _ in range(200):
                m = (a + b) / 2
                fm = npv(m, cfs)
                if fa * fm <= 0:
                    b = m
                else:
                    a, fa = m, fm
            roots.append((a + b) / 2)
        r0, f0 = r1, f1
    return roots


def cmd_npv(a):
    cfs = parse_list(a.cfs)
    print("NPV / IRR")
    line("cash flows t=0..T", ", ".join(fmt(c, 2) for c in cfs))
    line("discount rate", a.r)
    v = npv(a.r, cfs)
    print("  formula: NPV = sum_t CF_t / (1+r)^t")
    line("NPV", v, 2)
    signs = sum(1 for i in range(1, len(cfs)) if cfs[i] * cfs[i - 1] < 0 and cfs[i] != 0)
    roots = irr_roots(cfs)
    line("sign changes in cash flows", signs)
    if not roots:
        print("  IRR: none found in [-99%, 1000%]; use NPV")
    elif len(roots) == 1:
        line("IRR", roots[0], 6)
    else:
        print("  WARNING: multiple IRRs; the IRR rule is unreliable here, decide on NPV")
        for rt in roots:
            line("IRR root", rt, 6)
    # MIRR: finance negatives at r, reinvest positives at r (or a.reinvest)
    rr = a.reinvest if a.reinvest is not None else a.r
    T = len(cfs) - 1
    pv_neg = sum(cf / (1 + a.r) ** t for t, cf in enumerate(cfs) if cf < 0)
    fv_pos = sum(cf * (1 + rr) ** (T - t) for t, cf in enumerate(cfs) if cf > 0)
    if pv_neg < 0 and fv_pos > 0 and T > 0:
        line("MIRR (reinvest at %.4f)" % rr, (fv_pos / -pv_neg) ** (1 / T) - 1, 6)
    # payback (undiscounted and discounted)
    for label, disc in (("payback (years)", False), ("discounted payback", True)):
        cum, pb = 0.0, None
        for t, cf in enumerate(cfs):
            x = cf / (1 + a.r) ** t if disc else cf
            if cum < 0 <= cum + x and t > 0:
                pb = t - 1 + (-cum / x)
                break
            cum += x
        line(label, pb)
    if cfs[0] < 0:
        line("profitability index", npv(a.r, [0] + cfs[1:]) / -cfs[0])


# ---------------------------------------------------------------- WACC / beta

def cmd_wacc(a):
    v = a.E + a.D + a.P
    w = a.E / v * a.rE + a.D / v * a.rD * (1 - a.t) + a.P / v * a.rP
    print("WACC")
    print("  formula: rWACC = E/V rE + P/V rP + D/V rD (1 - tc)")
    line("E/V", a.E / v)
    line("D/V", a.D / v)
    if a.P:
        line("P/V", a.P / v)
    line("after-tax rD", a.rD * (1 - a.t))
    line("WACC", w, 6)
    pre = a.E / v * a.rE + a.D / v * a.rD + a.P / v * a.rP
    line("pre-tax WACC (= rU if D/V constant)", pre, 6)


def cmd_beta(a):
    print("BETA (%s, %s debt policy)" % (a.mode, a.policy))
    DE = a.DE
    if a.policy == "target":
        # constant D/E: bU = E/(D+E) bE + D/(D+E) bD
        if a.mode == "unlever":
            b = (a.beta + DE * a.bD) / (1 + DE)
            print("  formula: bU = [bE + (D/E) bD] / (1 + D/E)")
        else:
            b = a.beta + DE * (a.beta - a.bD)
            print("  formula: bE = bU + (D/E)(bU - bD)")
    else:
        # permanent fixed debt, tax shield as risky as debt (Hamada when bD = 0)
        k = DE * (1 - a.t)
        if a.mode == "unlever":
            b = (a.beta + k * a.bD) / (1 + k)
            print("  formula: bU = [bE + (D/E)(1-t) bD] / (1 + (D/E)(1-t))")
        else:
            b = a.beta + k * (a.beta - a.bD)
            print("  formula: bE = bU + (D/E)(1-t)(bU - bD)")
    line("input beta", a.beta)
    line("D/E", DE)
    line("debt beta", a.bD)
    line("output beta", b, 6)
    if a.rf is not None and a.mrp is not None:
        line("CAPM r = rf + beta x MRP", a.rf + b * a.mrp, 6)


# ---------------------------------------------------------------- DCF / APV

def cmd_dcf(a):
    fcf = parse_list(a.fcf)
    print("DCF (FCF forecast years 1..N, discounted at WACC)")
    shift = 0.5 if a.midyear else 0.0
    pv_fcf = 0.0
    for t, f in enumerate(fcf, start=1):
        d = (1 + a.wacc) ** (t - shift)
        pv_fcf += f / d
        line(f"  FCF{t} / (1+WACC)^{t - shift:g}", f / d, 2)
    N = len(fcf)
    if a.exit_multiple is not None:
        tv = a.exit_multiple * a.exit_metric
        print(f"  terminal value: exit multiple {a.exit_multiple} x metric {a.exit_metric}")
    else:
        if a.wacc <= a.g:
            sys.exit("  WACC must exceed g")
        tv = fcf[-1] * (1 + a.g) / (a.wacc - a.g)
        print("  terminal value: FCF_N (1+g) / (WACC - g)")
    pv_tv = tv / (1 + a.wacc) ** N
    ev = pv_fcf + pv_tv
    line("PV of forecast FCF", pv_fcf, 2)
    line("terminal value at N", tv, 2)
    line("PV of terminal value", pv_tv, 2)
    line("enterprise value", ev, 2)
    line("TV share of EV", pv_tv / ev)
    if a.exit_multiple is None and a.wacc > 0:
        line("implied TV / FCF_N", tv / fcf[-1] if fcf[-1] else None, 2)
    eq = ev - a.net_debt
    line("less net debt", a.net_debt, 2)
    line("equity value", eq, 2)
    if a.shares:
        line("value per share", eq / a.shares, 4)
    if pv_tv / ev > 0.75:
        print("  NOTE: terminal value exceeds 75% of EV; the answer is mostly the g/WACC assumption")


def cmd_apv(a):
    fcf = parse_list(a.fcf)
    debt = parse_list(a.debt)  # debt outstanding at t=0..N-1 (interest paid t+1)
    print("APV = V_U + PV(interest tax shields)")
    vu = sum(f / (1 + a.rU) ** t for t, f in enumerate(fcf, start=1))
    N = len(fcf)
    if a.g is not None:
        tv = fcf[-1] * (1 + a.g) / (a.rU - a.g)
        vu += tv / (1 + a.rU) ** N
        line("unlevered TV at N", tv, 2)
    line("V_U (FCF at rU)", vu, 2)
    disc = a.rD if a.shield == "fixed" else a.rU
    pvts = 0.0
    for t in range(1, len(debt) + 1):
        ts = a.t * a.rD * debt[t - 1]
        pvts += ts / (1 + disc) ** t
    print(f"  tax shields discounted at {'rD (fixed debt schedule)' if a.shield == 'fixed' else 'rU (debt rebalanced to target)'}")
    line("PV(tax shields)", pvts, 2)
    line("APV (levered value)", vu + pvts, 2)


# ---------------------------------------------------------------- venture

def cmd_vc(a):
    print("VC METHOD")
    exit_value = a.exit_metric * a.exit_multiple
    line("exit value = metric x multiple", exit_value, 2)
    if a.target_irr is not None:
        factor = (1 + a.target_irr) ** a.years
        print(f"  discount factor = (1 + {a.target_irr})^{a.years}")
    else:
        factor = a.target_multiple
        print(f"  discount factor = target money multiple {a.target_multiple}")
    post = exit_value / factor
    line("post-money today (before dilution)", post, 2)
    own_exit = a.investment * factor / exit_value
    own_now = own_exit / a.retention
    line("ownership needed at exit", own_exit)
    line("retention ratio (1 - later dilution)", a.retention)
    line("ownership needed now", own_now)
    post_adj = a.investment / own_now
    line("implied post-money", post_adj, 2)
    line("implied pre-money", post_adj - a.investment, 2)
    if own_now > 1:
        print("  NOTE: required ownership exceeds 100%; the deal cannot meet the target return")


def cmd_round(a):
    print("PRICED ROUND")
    print("  convention: pre-money is fully diluted and includes the pool top-up")
    print("  (option pool shuffle); convertibles convert at the lower of cap price and")
    print("  discount price, cap price = cap / pre-round FD shares (pre-money cap basis)")
    existing = a.shares
    pool_now = a.pool_existing
    conv = json.loads(a.convertibles) if a.convertibles else []
    # iterate: pool top-up and conversions change FD shares, which change price
    price = a.pre / existing
    for _ in range(200):
        conv_shares = 0.0
        for c in conv:
            amt = c["amount"] * (1 + c.get("interest", 0.0) * c.get("years", 0.0))
            cap_price = c["cap"] / existing if c.get("cap") else float("inf")
            disc_price = price * (1 - c.get("discount", 0.0))
            conv_shares += amt / min(cap_price, disc_price)
        new_shares = a.investment / price
        if a.pool_target:
            # pool_now + top_up = target x post_fd, post_fd = existing + top_up + conv + new
            post_fd = (existing - pool_now + conv_shares + new_shares) / (1 - a.pool_target)
            top_up = max(a.pool_target * post_fd - pool_now, 0.0)
        else:
            top_up = 0.0
        pre_fd = existing + top_up + conv_shares
        new_price = a.pre / pre_fd
        if abs(new_price - price) < 1e-12:
            break
        price = new_price
    post_fd = pre_fd + new_shares
    line("price per share", price, 6)
    line("new investor shares", new_shares, 0)
    line("pool top-up shares", top_up, 0)
    line("convertible shares", conv_shares, 0)
    line("post-money FD shares", post_fd, 0)
    line("post-money valuation", price * post_fd, 2)
    line("new investor ownership", new_shares / post_fd)
    line("convertible holders ownership", conv_shares / post_fd)
    line("pool ownership (total)", (pool_now + top_up) / post_fd)
    line("existing holders excl. pool", (existing - pool_now) / post_fd)
    line("effective pre-money to founders", price * (existing - pool_now), 2)


# ---------------------------------------------------------------- CLI

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)

    t = s.add_parser("tvm")
    t.add_argument("kind", choices=["lump", "fv", "annuity", "perpetuity", "rate"])
    t.add_argument("--r", type=float, required=True)
    t.add_argument("--n", type=float, default=1)
    t.add_argument("--c", type=float, default=0)
    t.add_argument("--g", type=float, default=0.0)
    t.add_argument("--pv", type=float, default=0)
    t.add_argument("--fv", type=float, default=0)
    t.add_argument("--m", type=float, default=12, help="compounding periods per year")
    t.add_argument("--due", action="store_true")
    t.set_defaults(f=cmd_tvm)

    n = s.add_parser("npv")
    n.add_argument("--cfs", required=True, help="comma-separated, t=0 first")
    n.add_argument("--r", type=float, required=True)
    n.add_argument("--reinvest", type=float)
    n.set_defaults(f=cmd_npv)

    w = s.add_parser("wacc")
    for k in ("E", "D", "rE", "rD", "t"):
        w.add_argument("--" + k, type=float, required=True)
    w.add_argument("--P", type=float, default=0.0)
    w.add_argument("--rP", type=float, default=0.0)
    w.set_defaults(f=cmd_wacc)

    b = s.add_parser("beta")
    b.add_argument("mode", choices=["unlever", "relever"])
    b.add_argument("--beta", type=float, required=True)
    b.add_argument("--DE", type=float, required=True)
    b.add_argument("--bD", type=float, default=0.0)
    b.add_argument("--t", type=float, default=0.0)
    b.add_argument("--policy", choices=["target", "fixed"], default="target",
                   help="target = constant D/E (default); fixed = permanent debt level")
    b.add_argument("--rf", type=float)
    b.add_argument("--mrp", type=float)
    b.set_defaults(f=cmd_beta)

    d = s.add_parser("dcf")
    d.add_argument("--fcf", required=True, help="FCF years 1..N")
    d.add_argument("--wacc", type=float, required=True)
    d.add_argument("--g", type=float, default=0.02)
    d.add_argument("--exit-multiple", type=float)
    d.add_argument("--exit-metric", type=float)
    d.add_argument("--net-debt", type=float, default=0.0)
    d.add_argument("--shares", type=float)
    d.add_argument("--midyear", action="store_true")
    d.set_defaults(f=cmd_dcf)

    ap = s.add_parser("apv")
    ap.add_argument("--fcf", required=True)
    ap.add_argument("--rU", type=float, required=True)
    ap.add_argument("--rD", type=float, required=True)
    ap.add_argument("--t", type=float, required=True)
    ap.add_argument("--debt", required=True, help="debt outstanding at t=0..N-1")
    ap.add_argument("--g", type=float)
    ap.add_argument("--shield", choices=["fixed", "target"], default="fixed")
    ap.set_defaults(f=cmd_apv)

    v = s.add_parser("vc")
    v.add_argument("--investment", type=float, required=True)
    v.add_argument("--exit-metric", type=float, required=True, help="e.g. revenue or EBITDA in exit year")
    v.add_argument("--exit-multiple", type=float, required=True)
    v.add_argument("--years", type=float, default=5)
    v.add_argument("--target-irr", type=float)
    v.add_argument("--target-multiple", type=float)
    v.add_argument("--retention", type=float, default=1.0)
    v.set_defaults(f=cmd_vc)

    r = s.add_parser("round")
    r.add_argument("--pre", type=float, required=True, help="pre-money valuation")
    r.add_argument("--investment", type=float, required=True)
    r.add_argument("--shares", type=float, required=True, help="existing FD shares incl. existing pool")
    r.add_argument("--pool-existing", type=float, default=0.0)
    r.add_argument("--pool-target", type=float, default=0.0, help="post-money pool share, e.g. 0.10")
    r.add_argument("--convertibles", help='JSON list: [{"amount":250000,"cap":4e6,"discount":0.2,"interest":0.05,"years":1.5}]')
    r.set_defaults(f=cmd_round)

    a = p.parse_args()
    if a.cmd == "vc" and (a.target_irr is None) == (a.target_multiple is None):
        sys.exit("give exactly one of --target-irr or --target-multiple")
    if a.cmd == "dcf" and a.exit_multiple is not None and a.exit_metric is None:
        sys.exit("--exit-multiple needs --exit-metric")
    a.f(a)


if __name__ == "__main__":
    main()
