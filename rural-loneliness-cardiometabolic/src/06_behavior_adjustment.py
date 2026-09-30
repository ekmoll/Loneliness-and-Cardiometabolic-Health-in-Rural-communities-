"""Step 6: does the loneliness–cardiometabolic association survive behavioral adjustment?

Sequentially adds PLACES behavioral risk factors and care-access measures to the primary
loneliness x RUCC model and reports how much each loneliness slope attenuates.

Interpretation caution: smoking, inactivity, obesity and sleep are plausible *pathways*
from loneliness to cardiometabolic disease. Adjusting for them estimates the association
not operating through those behaviors; attenuation is expected and is not evidence of
confounding. All measures are PLACES model-based estimates sharing the same inputs.
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.sm_exceptions import ValueWarning

from config import LONELINESS_UNIT, OUTPUT, PROCESSED, RUCC_LABELS, TABLES

warnings.filterwarnings("ignore", category=ValueWarning)
BASE = "poverty + education + unemployment + C(region)"
STEPS = [
    ("1. Primary (SES + region)", []),
    ("2. + smoking", ["smoking"]),
    ("3. + physical inactivity, obesity", ["smoking", "physical_inactivity", "obesity"]),
    ("4. + short sleep, binge drinking", ["smoking", "physical_inactivity", "obesity",
                                          "short_sleep", "binge_drinking"]),
    ("5. + uninsured, routine checkup", ["smoking", "physical_inactivity", "obesity",
                                         "short_sleep", "binge_drinking", "uninsured",
                                         "routine_checkup"]),
]


def fit(formula, d):
    return smf.ols(formula, d).fit(cov_type="cluster",
                                   cov_kwds={"groups": pd.factorize(d["state_fips"])[0]})


def slope(res, k):
    names = list(res.params.index)
    c = np.zeros(len(names))
    c[names.index("lon10")] = 1
    if k != 1:
        c[names.index(f"lon10:C(rucc)[T.{k}]")] = 1
    t = res.t_test(c)
    ci = np.squeeze(t.conf_int())
    return float(np.squeeze(t.effect)), ci[0], ci[1], float(np.squeeze(t.pvalue))


def main():
    df = pd.read_csv(PROCESSED / "analytic_county.csv", dtype={"fips": str, "state_fips": str})
    df["lon10"] = df["loneliness"] / LONELINESS_UNIT
    all_b = STEPS[-1][1]
    df = df.dropna(subset=all_b)
    print(f"N = {len(df)} counties with all behavioral measures\n")

    rows, first = [], {}
    for name, covs in STEPS:
        extra = "".join(f" + {c}" for c in covs)
        r = fit(f"cardio_burden ~ lon10 * C(rucc) + {BASE}{extra}", df)
        tr = fit(f"cardio_burden ~ lon10 * rucc + {BASE}{extra}", df)
        for k in sorted(RUCC_LABELS):
            b, lo, hi, p = slope(r, k)
            first.setdefault(k, b)
            rows.append({"model": name, "rucc": k, "slope": b, "ci_low": lo, "ci_high": hi, "p": p,
                         "pct_of_primary": 100 * b / first[k],
                         "trend_interaction_b": tr.params["lon10:rucc"],
                         "trend_interaction_p": tr.pvalues["lon10:rucc"],
                         "adj_r2": r.rsquared_adj})
    res = pd.DataFrame(rows)
    res.to_csv(TABLES / "behavior_adjustment.csv", index=False)

    # Collinearity of loneliness with the full covariate set
    X = pd.get_dummies(df[["loneliness", "poverty", "education", "unemployment", "region"] + all_b],
                       drop_first=True).astype(float).assign(const=1.0)
    vif = variance_inflation_factor(X.values, list(X.columns).index("loneliness"))
    corr = df[["loneliness"] + all_b].corr()["loneliness"].drop("loneliness").round(2)

    lines = ["# Behavioral adjustment", "",
             f"N = {len(df)} counties. Slopes are change in cardiometabolic burden (z-units) per "
             "10-point rise in loneliness, state-clustered 95% CIs.", "",
             "| Model | RUCC 1 (large metro) | RUCC 9 (most remote) | Sig. categories | Trend p |",
             "|---|---|---|---|---|"]
    for name, _ in STEPS:
        s = res[res.model == name].set_index("rucc")
        n_sig = int((s["ci_low"] > 0).sum())
        lines.append(f"| {name} | {s.loc[1,'slope']:.2f} [{s.loc[1,'ci_low']:.2f}, {s.loc[1,'ci_high']:.2f}] "
                     f"| {s.loc[9,'slope']:.2f} [{s.loc[9,'ci_low']:.2f}, {s.loc[9,'ci_high']:.2f}] "
                     f"| {n_sig} of 9 | {s['trend_interaction_p'].iloc[0]:.3g} |")
    lines += ["", f"Correlation of loneliness with each covariate: "
              + ", ".join(f"{k} {v:+.2f}" for k, v in corr.items()),
              f"Variance inflation factor for loneliness in model 5: {vif:.1f}"]
    text = "\n".join(lines) + "\n"
    (OUTPUT / "behavior_adjustment.md").write_text(text)
    print(text)
    wide = res.pivot_table(index="model", columns="rucc", values="slope", sort=False).round(2)
    print(wide.to_string())


if __name__ == "__main__":
    main()
