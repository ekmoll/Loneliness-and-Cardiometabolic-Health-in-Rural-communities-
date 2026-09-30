"""Step 3: rural-urban descriptive comparisons (Table 1 and a by-RUCC table).

Reports both unweighted county means (each county counts once) and adult-population-
weighted means, because the abstract does not say which was used.
"""
import numpy as np
import pandas as pd
from scipy import stats

from config import CARDIOMETABOLIC, HRSN, PROCESSED, RUCC_LABELS, TABLES

VARS = list(HRSN.values()) + list(CARDIOMETABOLIC.values()) + ["poverty", "education", "unemployment"]


def wmean(x, w):
    m = x.notna() & w.notna()
    return np.average(x[m], weights=w[m])


def main():
    df = pd.read_csv(PROCESSED / "analytic_county.csv", dtype={"fips": str})
    TABLES.mkdir(parents=True, exist_ok=True)

    rows = []
    for v in VARS:
        met, non = df.loc[df.metro == "Metro", v], df.loc[df.metro == "Nonmetro", v]
        t = stats.ttest_ind(non, met, equal_var=False)
        d = (non.mean() - met.mean()) / np.sqrt((non.var() + met.var()) / 2)
        rows.append({
            "variable": v,
            "nonmetro_mean": non.mean(), "nonmetro_sd": non.std(),
            "metro_mean": met.mean(), "metro_sd": met.std(),
            "difference": non.mean() - met.mean(),
            "cohens_d": d, "welch_p": t.pvalue,
            "nonmetro_popweighted": wmean(non, df.loc[non.index, "pop_18plus"]),
            "metro_popweighted": wmean(met, df.loc[met.index, "pop_18plus"]),
        })
    t1 = pd.DataFrame(rows)
    t1.to_csv(TABLES / "table1_metro_nonmetro.csv", index=False)

    by = df.groupby("rucc")[VARS + ["cardio_burden"]].mean().round(2)
    by.insert(0, "n_counties", df.groupby("rucc").size())
    by.insert(0, "label", by.index.map(RUCC_LABELS))
    by.to_csv(TABLES / "table2_by_rucc.csv")

    n = df.metro.value_counts()
    print(f"Counties: {n.get('Nonmetro', 0)} nonmetro, {n.get('Metro', 0)} metro\n")
    print("Unweighted county means (nonmetro vs metro)")
    for r in t1.itertuples():
        print(f"  {r.variable:<26} {r.nonmetro_mean:6.2f} vs {r.metro_mean:6.2f}"
              f"   diff {r.difference:+.2f}  d={r.cohens_d:+.2f}  p={r.welch_p:.3g}")

    # Loneliness equivalence check: is the metro/nonmetro gap within +/-1 point?
    lon_n = df.loc[df.metro == "Nonmetro", "loneliness"]
    lon_m = df.loc[df.metro == "Metro", "loneliness"]
    diff = lon_n.mean() - lon_m.mean()
    se = np.sqrt(lon_n.var() / len(lon_n) + lon_m.var() / len(lon_m))
    lo, hi = diff - 1.645 * se, diff + 1.645 * se
    print(f"\nLoneliness difference {diff:+.2f} pts, 90% CI {lo:+.2f} to {hi:+.2f} "
          f"({'within' if lo > -1 and hi < 1 else 'NOT within'} a +/-1-point equivalence margin)")


if __name__ == "__main__":
    main()
