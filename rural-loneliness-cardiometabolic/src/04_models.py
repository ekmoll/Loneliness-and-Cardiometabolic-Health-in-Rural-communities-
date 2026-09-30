"""Step 4: loneliness x rurality models for cardiometabolic burden.

Primary model (matches the abstract):
    burden ~ loneliness10 * C(RUCC) + poverty + education + unemployment + C(region)
with standard errors clustered by state, because PLACES estimates share state-level
random effects and counties in a state are not independent.

Outputs:
    output/tables/model_primary_coefficients.csv
    output/tables/simple_slopes.csv          (loneliness slope within each RUCC)
    output/tables/sensitivity.csv            (slopes under alternative specifications)
    output/figures/simple_slopes.png
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.tools.sm_exceptions import ValueWarning

# The overall-model F statistic in summaries is rank-deficient under clustering; it is
# not used anywhere, so silence that one warning.
warnings.filterwarnings("ignore", category=ValueWarning, message="covariance of constraints")

from config import (CARDIOMETABOLIC, CLUSTER_SE_BY, FIGURES, LONELINESS_UNIT, PROCESSED,
                    RUCC_LABELS, TABLES)

COVARS = "poverty + education + unemployment + C(region)"


def fit(df, formula, weights=None, cluster=True):
    model = (smf.wls(formula, df, weights=weights) if weights is not None
             else smf.ols(formula, df))
    if cluster:
        col = "state_fips" if CLUSTER_SE_BY == "state" else CLUSTER_SE_BY
        groups = pd.factorize(df[col])[0]
        res = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
        res._n_clusters = len(np.unique(groups))
        return res
    return model.fit(cov_type="HC3")


def simple_slopes(res, lon="lon10"):
    """Loneliness slope in each RUCC category = main effect + interaction term."""
    names = list(res.params.index)
    out = []
    for k in sorted(RUCC_LABELS):
        c = np.zeros(len(names))
        c[names.index(lon)] = 1
        term = f"{lon}:C(rucc)[T.{k}]"
        if term in names:
            c[names.index(term)] = 1
        elif k != 1:
            continue  # category absent from this sample
        t = res.t_test(c)
        est, se = float(np.squeeze(t.effect)), float(np.squeeze(t.sd))
        ci = np.squeeze(t.conf_int())
        out.append({"rucc": k, "label": RUCC_LABELS[k], "slope": est, "se": se,
                    "ci_low": ci[0], "ci_high": ci[1], "p": float(np.squeeze(t.pvalue))})
    return pd.DataFrame(out)


def interaction_test(res, lon="lon10"):
    """Joint Wald F test that all loneliness x RUCC terms are zero.

    A cluster-robust covariance has rank <= (clusters - 1); if that is not larger than
    the number of constraints the test is degenerate, so fall back to HC3 and say so.
    """
    names = list(res.params.index)
    terms = [n for n in names if n.startswith(f"{lon}:C(rucc)")]
    R = np.zeros((len(terms), len(names)))
    for i, t in enumerate(terms):
        R[i, names.index(t)] = 1
    n_clusters = getattr(res, "_n_clusters", None)
    if n_clusters is not None and n_clusters - 1 <= len(terms):
        print(f"  note: {n_clusters} clusters is too few for a {len(terms)}-df clustered test; "
              "using HC3 for the joint interaction test")
        res = res.model.fit(cov_type="HC3")
    f = res.f_test(R)
    return float(np.squeeze(f.fvalue)), int(f.df_num), float(np.squeeze(f.pvalue))


def main():
    df = pd.read_csv(PROCESSED / "analytic_county.csv", dtype={"fips": str, "state_fips": str})
    df["lon10"] = df["loneliness"] / LONELINESS_UNIT
    df["lon10_alt"] = df["loneliness_alt"] / LONELINESS_UNIT
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    # --- Unadjusted and primary models -------------------------------------
    unadj = fit(df, "cardio_burden ~ lon10")
    main_f = f"cardio_burden ~ lon10 * C(rucc) + {COVARS}"
    prim = fit(df, main_f)
    prim.summary2().tables[1].to_csv(TABLES / "model_primary_coefficients.csv")

    slopes = simple_slopes(prim)
    slopes.to_csv(TABLES / "simple_slopes.csv", index=False)
    F, dfn, p_int = interaction_test(prim)

    trend = fit(df, f"cardio_burden ~ lon10 * rucc + {COVARS}")

    print(f"N = {int(prim.nobs)} counties, {df['state_fips'].nunique()} state clusters")
    print(f"Unadjusted slope (all counties): {unadj.params['lon10']:.3f} SD per 10 pts "
          f"(p={unadj.pvalues['lon10']:.3g})")
    print(f"Primary model adj. R^2 = {prim.rsquared_adj:.3f}")
    print(f"Loneliness x RUCC (joint, {dfn} df): F = {F:.2f}, p = {p_int:.3g}")
    print(f"Loneliness x RUCC (linear trend): b = {trend.params['lon10:rucc']:+.3f} per RUCC step, "
          f"p = {trend.pvalues['lon10:rucc']:.3g}")
    print("\nAdjusted loneliness slope by RUCC (burden z-units per 10-point rise)")
    for r in slopes.itertuples():
        print(f"  {r.rucc}  {r.label:<38} {r.slope:5.2f}  [{r.ci_low:5.2f}, {r.ci_high:5.2f}]  p={r.p:.3g}")

    # --- Sensitivity analyses ----------------------------------------------
    specs = {
        "Primary (region, state-clustered SE)": (main_f, None, True, df),
        "Robust HC3 SE instead of clustering": (main_f, None, False, df),
        "State fixed effects instead of region":
            (f"cardio_burden ~ lon10 * C(rucc) + poverty + education + unemployment + C(state_fips)", None, True, df),
        "Weighted by adult population": (main_f, df["pop_18plus"], True, df),
        "Also adjusting for lack of social support":
            (main_f + " + lack_social_support", None, True, df),
        "Alternate HRSN prevalence type (crude/age-adj.)":
            (main_f.replace("lon10", "lon10_alt"), None, True, df),
    }
    sens = []
    for name, (f, w, cl, d) in specs.items():
        r = fit(d, f, weights=w, cluster=cl)
        lon = "lon10_alt" if "lon10_alt" in f else "lon10"
        s = simple_slopes(r, lon=lon)
        _, _, p = interaction_test(r, lon=lon)
        for row in s.itertuples():
            sens.append({"specification": name, "rucc": row.rucc, "slope": row.slope,
                         "ci_low": row.ci_low, "ci_high": row.ci_high, "p": row.p,
                         "interaction_p": p})
    # Each condition separately, as outcome (standardized)
    for cond in CARDIOMETABOLIC.values():
        d = df.assign(outcome=(df[cond] - df[cond].mean()) / df[cond].std())
        r = fit(d, main_f.replace("cardio_burden", "outcome"))
        _, _, p = interaction_test(r)
        for row in simple_slopes(r).itertuples():
            sens.append({"specification": f"Outcome: {cond} only", "rucc": row.rucc,
                         "slope": row.slope, "ci_low": row.ci_low, "ci_high": row.ci_high,
                         "p": row.p, "interaction_p": p})
    sens = pd.DataFrame(sens)
    sens.to_csv(TABLES / "sensitivity.csv", index=False)

    wide = sens.pivot_table(index="specification", columns="rucc", values="slope", sort=False).round(2)
    print("\nSensitivity: loneliness slope by RUCC under each specification")
    print(wide.to_string())

    plot_slopes(slopes)


def plot_slopes(slopes):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#2a6f97" if k <= 3 else "#b5651d" for k in slopes["rucc"]]
    ax.errorbar(slopes["rucc"], slopes["slope"],
                yerr=[slopes["slope"] - slopes["ci_low"], slopes["ci_high"] - slopes["slope"]],
                fmt="none", ecolor="#888", capsize=3, zorder=1)
    ax.scatter(slopes["rucc"], slopes["slope"], c=colors, s=45, zorder=2)
    ax.axhline(0, color="#ccc", lw=1)
    ax.axvline(3.5, color="#ddd", lw=1, ls="--")
    ax.set_xticks(slopes["rucc"])
    ax.set_xlabel("Rural-Urban Continuum Code (1 = large metro, 9 = most remote)")
    ax.set_ylabel("Change in cardiometabolic burden (z-units)\nper 10-point rise in loneliness")
    ax.set_title("Adjusted loneliness–cardiometabolic association by rurality", fontsize=11)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "simple_slopes.png", dpi=200)


if __name__ == "__main__":
    main()
