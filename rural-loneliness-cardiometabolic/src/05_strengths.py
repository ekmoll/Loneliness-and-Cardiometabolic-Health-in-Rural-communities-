"""Step 5: strengths-based analyses.

A. Community asset: social associations (membership organizations per 10,000) by rurality.
B. Loneliness advantage: are rural counties less lonely than their hardship predicts,
   and do social associations account for that?
C. Decoupling: is hardship more weakly tied to loneliness in nonmetro counties?
D. Buffering: is hardship less strongly tied to cardiometabolic burden where loneliness
   is lower or social associations are higher?
E. Positive deviance: high-hardship rural counties with better-than-expected
   cardiometabolic health, and what distinguishes them.

All models: OLS, adjusted for poverty, education, unemployment and Census region,
state-clustered standard errors. Continuous predictors are z-scored so estimates are
"per 1 SD" unless stated otherwise.
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.tools.sm_exceptions import ValueWarning

from config import FIGURES, OUTPUT, PROCESSED, RUCC_LABELS, TABLES

warnings.filterwarnings("ignore", category=ValueWarning)
COV = "poverty + education + unemployment + C(region)"
METRO_COLOR, NONMETRO_COLOR = "#2a78d6", "#eb6834"


def z(s):
    return (s - s.mean()) / s.std()


def fit(formula, d, logit=False):
    model = smf.logit(formula, d) if logit else smf.ols(formula, d)
    return model.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["state_fips"])[0]},
                     **({"disp": 0} if logit else {}))


def row(res, term, label, section):
    ci = res.conf_int().loc[term]
    return {"section": section, "estimate": label, "b": res.params[term],
            "ci_low": ci[0], "ci_high": ci[1], "p": res.pvalues[term], "n": int(res.nobs)}


def lincom(res, terms, label, section):
    names = list(res.params.index)
    c = np.zeros(len(names))
    for t in terms:
        c[names.index(t)] = 1
    t = res.t_test(c)
    ci = np.squeeze(t.conf_int())
    return {"section": section, "estimate": label, "b": float(np.squeeze(t.effect)),
            "ci_low": ci[0], "ci_high": ci[1], "p": float(np.squeeze(t.pvalue)), "n": int(res.nobs)}


def main():
    df = pd.read_csv(PROCESSED / "analytic_county.csv", dtype={"fips": str, "state_fips": str})
    if "social_assoc" not in df:
        raise SystemExit("social_assoc missing: add the CHR 2025 file to data/raw and rebuild.")
    df["nonmetro"] = (df["metro"] == "Nonmetro").astype(int)
    # Winsorize the asset at 1st/99th percentiles (a few tiny counties have extreme rates).
    lo, hi = df["social_assoc"].quantile([.01, .99])
    df["sa_w"] = df["social_assoc"].clip(lo, hi)
    df["sa_z"] = z(df["sa_w"])
    df["lon_z"] = z(df["loneliness"])
    df["sup_z"] = z(df["lack_social_support"])
    out, lines = [], []

    # ---- A. Asset distribution --------------------------------------------
    sa = df.dropna(subset=["social_assoc"])
    by = sa.groupby("rucc")["social_assoc"].agg(["count", "mean", "median", "std"]).round(2)
    by.insert(0, "label", by.index.map(RUCC_LABELS))
    by.to_csv(TABLES / "strengths_A_social_assoc_by_rucc.csv")
    n_, m_ = sa.loc[sa.nonmetro == 1, "social_assoc"], sa.loc[sa.nonmetro == 0, "social_assoc"]
    t = stats.ttest_ind(n_, m_, equal_var=False)
    rs = stats.spearmanr(sa["rucc"], sa["social_assoc"])
    lines += ["## A. Social associations (membership organizations per 10,000)",
              f"- Nonmetro {n_.mean():.1f} vs metro {m_.mean():.1f} (medians {n_.median():.1f} vs "
              f"{m_.median():.1f}); Welch p = {t.pvalue:.2g}",
              f"- Gradient across RUCC 1→9: Spearman rho = {rs.statistic:.2f}, p = {rs.pvalue:.2g}",
              f"- By RUCC (mean): " + ", ".join(f"{k}: {v:.1f}" for k, v in by["mean"].items())]

    # ---- B. Loneliness advantage ------------------------------------------
    d = df.dropna(subset=["sa_z"])
    b0 = fit(f"loneliness ~ nonmetro + {COV}", d)
    b1 = fit(f"loneliness ~ nonmetro + hardship_index + {COV}", d)
    b2 = fit(f"loneliness ~ nonmetro + hardship_index + sa_z + {COV}", d)
    out += [row(b0, "nonmetro", "Nonmetro vs metro loneliness (pts), covariates only", "B"),
            row(b1, "nonmetro", "Nonmetro vs metro loneliness (pts), + hardship", "B"),
            row(b2, "nonmetro", "Nonmetro vs metro loneliness (pts), + hardship + social assoc.", "B"),
            row(b2, "sa_z", "Loneliness (pts) per 1 SD social associations", "B")]
    lines += ["", "## B. Rural loneliness advantage",
              f"- Given their hardship, nonmetro counties' loneliness is {b1.params['nonmetro']:+.2f} pts "
              f"vs metro (95% CI {b1.conf_int().loc['nonmetro'][0]:+.2f} to "
              f"{b1.conf_int().loc['nonmetro'][1]:+.2f}, p = {b1.pvalues['nonmetro']:.2g})",
              f"- Adding social associations: {b2.params['nonmetro']:+.2f} pts; each 1 SD more "
              f"associations = {b2.params['sa_z']:+.2f} pts loneliness (p = {b2.pvalues['sa_z']:.2g})"]

    # ---- C. Decoupling of hardship and loneliness --------------------------
    c = fit(f"loneliness ~ hardship_index * nonmetro + {COV}", df)
    out += [row(c, "hardship_index", "Loneliness (pts) per 1 SD hardship, metro", "C"),
            lincom(c, ["hardship_index", "hardship_index:nonmetro"],
                   "Loneliness (pts) per 1 SD hardship, nonmetro", "C"),
            row(c, "hardship_index:nonmetro", "Difference (nonmetro − metro)", "C")]
    lines += ["", "## C. Hardship–loneliness decoupling",
              f"- Per 1 SD hardship, loneliness rises {c.params['hardship_index']:.2f} pts in metro and "
              f"{c.params['hardship_index'] + c.params['hardship_index:nonmetro']:.2f} pts in nonmetro "
              f"(difference p = {c.pvalues['hardship_index:nonmetro']:.2g})"]

    # ---- D. Buffering ------------------------------------------------------
    d1 = fit(f"cardio_burden ~ hardship_index * lon_z + {COV}", df)
    d2 = fit(f"cardio_burden ~ hardship_index * sa_z + {COV}", df.dropna(subset=["sa_z"]))
    d3 = fit(f"cardio_burden ~ hardship_index * sa_z * nonmetro + {COV}", df.dropna(subset=["sa_z"]))
    out += [row(d1, "hardship_index:lon_z", "Hardship × loneliness (burden)", "D"),
            row(d2, "hardship_index:sa_z", "Hardship × social associations (burden)", "D"),
            row(d3, "hardship_index:sa_z", "Hardship × social assoc., metro", "D"),
            lincom(d3, ["hardship_index:sa_z", "hardship_index:sa_z:nonmetro"],
                   "Hardship × social assoc., nonmetro", "D")]
    # Hardship slope at low (−1 SD) vs high (+1 SD) loneliness
    h_lo = d1.params["hardship_index"] - d1.params["hardship_index:lon_z"]
    h_hi = d1.params["hardship_index"] + d1.params["hardship_index:lon_z"]
    lines += ["", "## D. Buffering (outcome: cardiometabolic burden)",
              f"- Hardship slope where loneliness is low (−1 SD): {h_lo:.3f}; high (+1 SD): {h_hi:.3f} "
              f"(interaction p = {d1.pvalues['hardship_index:lon_z']:.2g})",
              f"- Hardship × social associations: b = {d2.params['hardship_index:sa_z']:+.3f}, "
              f"p = {d2.pvalues['hardship_index:sa_z']:.2g} (negative = buffering)"]

    # ---- E. Social associations and burden directly, by metro --------------
    e = fit(f"cardio_burden ~ sa_z * nonmetro + {COV}", df.dropna(subset=["sa_z"]))
    out += [row(e, "sa_z", "Burden per 1 SD social assoc., metro", "E"),
            lincom(e, ["sa_z", "sa_z:nonmetro"], "Burden per 1 SD social assoc., nonmetro", "E")]
    lines += ["", "## E. Social associations and cardiometabolic burden",
              f"- Per 1 SD associations: metro {e.params['sa_z']:+.3f}, nonmetro "
              f"{e.params['sa_z'] + e.params['sa_z:nonmetro']:+.3f} "
              f"(difference p = {e.pvalues['sa_z:nonmetro']:.2g})"]

    # ---- F. Positive deviance ----------------------------------------------
    # Expected burden from structural factors only; residual < 0 = healthier than expected.
    base = smf.ols(f"cardio_burden ~ hardship_index + {COV}", df).fit()
    df["burden_resid"] = base.resid
    hi_hard = df["hardship_index"] > df["hardship_index"].median()
    rural_hh = df[(df.nonmetro == 1) & hi_hard].copy()
    cut = rural_hh["burden_resid"].quantile(0.25)
    rural_hh["positive_deviant"] = (rural_hh["burden_resid"] <= cut).astype(int)
    comp_vars = ["loneliness", "lack_social_support", "social_assoc", "hardship_index", "poverty",
                 "education", "cardio_burden", "rucc", "pop_18plus"]
    comp = rural_hh.groupby("positive_deviant")[comp_vars].median().T
    comp.columns = ["Other high-hardship rural (median)", "Positive deviants (median)"]
    comp["p (Mann-Whitney)"] = [stats.mannwhitneyu(
        rural_hh.loc[rural_hh.positive_deviant == 1, v].dropna(),
        rural_hh.loc[rural_hh.positive_deviant == 0, v].dropna()).pvalue for v in comp_vars]
    comp.round(3).to_csv(TABLES / "strengths_F_positive_deviance_profile.csv")
    pdv = fit("positive_deviant ~ lon_z + sa_z + " + COV, rural_hh.dropna(subset=["sa_z"]), logit=True)
    for term, lab in [("lon_z", "Odds of positive deviance per 1 SD loneliness"),
                      ("sa_z", "Odds of positive deviance per 1 SD social associations")]:
        ci = pdv.conf_int().loc[term]
        out.append({"section": "F", "estimate": lab, "b": np.exp(pdv.params[term]),
                    "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]), "p": pdv.pvalues[term],
                    "n": int(pdv.nobs)})
    rural_hh.loc[rural_hh.positive_deviant == 1,
                 ["fips", "county", "state_abbr", "rucc", "hardship_index", "loneliness",
                  "social_assoc", "cardio_burden", "burden_resid"]] \
        .sort_values("burden_resid").round(3).to_csv(TABLES / "strengths_F_positive_deviant_counties.csv", index=False)
    pd_ = rural_hh[rural_hh.positive_deviant == 1]
    ot_ = rural_hh[rural_hh.positive_deviant == 0]
    lines += ["", "## F. Positive deviance (high-hardship nonmetro counties)",
              f"- {len(rural_hh)} nonmetro counties with above-median hardship; "
              f"{len(pd_)} positive deviants (healthiest quartile relative to expected burden)",
              f"- Loneliness: {pd_.loneliness.median():.1f}% vs {ot_.loneliness.median():.1f}%; "
              f"social associations: {pd_.social_assoc.median():.1f} vs {ot_.social_assoc.median():.1f} per 10,000",
              f"- Adjusted OR per 1 SD loneliness = {np.exp(pdv.params['lon_z']):.2f} "
              f"(p = {pdv.pvalues['lon_z']:.2g}); per 1 SD associations = "
              f"{np.exp(pdv.params['sa_z']):.2f} (p = {pdv.pvalues['sa_z']:.2g})"]

    res = pd.DataFrame(out)
    res.to_csv(TABLES / "strengths_models.csv", index=False)
    text = "# Strengths-based results\n\n" + "\n".join(lines) + "\n"
    (OUTPUT / "strengths_summary.md").write_text(text)
    print(text)
    plot(df, by)


def plot(df, by):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    # Panel 1: social associations by RUCC
    ax = axes[0]
    colors = [METRO_COLOR if k <= 3 else NONMETRO_COLOR for k in by.index]
    se = by["std"] / np.sqrt(by["count"])
    ax.bar(by.index, by["mean"], color=colors, width=0.7, yerr=1.96 * se,
           error_kw={"ecolor": "#666", "capsize": 2, "lw": 1})
    ax.set_xticks(by.index)
    ax.set_xlabel("Rural-Urban Continuum Code (1 = large metro, 9 = most remote)")
    ax.set_ylabel("Membership associations per 10,000")
    ax.set_title("A. Social associations rise with rurality", loc="left", fontsize=11)
    # Panel 2: hardship vs loneliness
    ax = axes[1]
    for flag, col, lab in [(0, METRO_COLOR, "Metro"), (1, NONMETRO_COLOR, "Nonmetro")]:
        s = df[df.nonmetro == flag]
        ax.scatter(s.hardship_index, s.loneliness, s=6, alpha=.25, color=col, linewidths=0)
        b = np.polyfit(s.hardship_index, s.loneliness, 1)
        xs = np.linspace(df.hardship_index.quantile(.02), df.hardship_index.quantile(.98), 50)
        ax.plot(xs, np.polyval(b, xs), color=col, lw=2, label=lab)
    ax.set_xlabel("Material hardship index (SD)")
    ax.set_ylabel("Loneliness prevalence (%)")
    ax.set_title("B. Hardship and loneliness by rurality", loc="left", fontsize=11)
    ax.legend(frameon=False)
    for a in axes:
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        a.grid(axis="y", color="#eee", lw=.8)
        a.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIGURES / "strengths.png", dpi=200)


if __name__ == "__main__":
    main()
