"""Build fake raw files in the same layouts as the real sources, for testing the pipeline.

    python tests/make_synthetic_data.py && make analysis

The numbers are random and mean nothing; they only prove the code runs end to end.
Never commit results produced from synthetic data.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, SOURCES  # noqa: E402

rng = np.random.default_rng(42)
STATES = {"31": "NE", "19": "IA", "20": "KS", "13": "GA", "06": "CA", "36": "NY", "48": "TX", "41": "OR"}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    counties = []
    for sf, ab in STATES.items():
        for i in range(1, 61):
            counties.append((f"{sf}{2 * i - 1:03d}", ab, rng.integers(1, 10)))
    c = pd.DataFrame(counties, columns=["fips", "state", "rucc"])
    n = len(c)
    lon = rng.normal(34, 3, n)
    pov = rng.normal(14, 4, n) + 0.3 * (c.rucc - 5)

    rows = []
    for (fips, ab, rucc), l, p in zip(counties, lon, pov):
        pop = int(rng.lognormal(10.5 - 0.3 * rucc, 1))
        burden = 0.05 * (l - 34) * (1 + rucc / 6) + 0.05 * p + rng.normal(0, 0.5)
        vals = {"BPHIGH": 33 + 3 * burden, "DIABETES": 11 + 1.5 * burden,
                "CHD": 7 + burden, "STROKE": 3.5 + 0.5 * burden,
                "FOODINSECU": 14 + 0.4 * rucc + rng.normal(0, 2),
                "HOUSINSECU": 12.5 + 0.2 * rucc + rng.normal(0, 1.5),
                "SHUTUTILITY": 8.5 + 0.2 * rucc + rng.normal(0, 1.5),
                "LACKTRPT": 8.3 + 0.2 * rucc + rng.normal(0, 1.5),
                "EMOTIONSPT": 24 + rng.normal(0, 2), "LONELINESS": l,
                "CSMOKING": 15 + rng.normal(0, 3), "LPA": 25 + rng.normal(0, 4),
                "OBESITY": 35 + rng.normal(0, 4), "SLEEP": 35 + rng.normal(0, 3),
                "BINGE": 17 + rng.normal(0, 2), "ACCESS2": 11 + rng.normal(0, 3),
                "CHECKUP": 75 + rng.normal(0, 3)}
        for mid, v in vals.items():
            for vt in ("AgeAdjPrv", "CrdPrv"):
                rows.append({"Year": 2023, "StateAbbr": ab, "LocationName": f"County {fips}",
                             "MeasureId": mid, "DataValueTypeID": vt,
                             "Data_Value": round(v + (0.3 if vt == "CrdPrv" else 0), 1),
                             "TotalPopulation": pop, "TotalPop18plus": int(pop * .78),
                             "LocationID": fips})
    pd.DataFrame(rows).to_csv(RAW / SOURCES["places"]["local"], index=False)

    long = lambda attr, vals: pd.DataFrame(  # noqa: E731
        {"FIPS_Code": c.fips, "State": c.state, "Area_Name": "x", "Attribute": attr, "Value": vals})
    pd.DataFrame({"FIPS": c.fips, "State": c.state, "County_Name": "x",
                  "Attribute": "RUCC_2023", "Value": c.rucc}).to_csv(RAW / SOURCES["rucc"]["local"], index=False)
    long("PCTPOVALL_2023", pov.round(1)).to_csv(RAW / SOURCES["poverty"]["local"], index=False)
    long("Percent of adults with a bachelor's degree or higher, 2019-23",
         rng.normal(24, 8, n).round(1)).to_csv(RAW / SOURCES["education"]["local"], index=False)
    long("Unemployment_rate_2023", rng.normal(3.6, 1, n).round(1)).to_csv(
        RAW / SOURCES["unemployment"]["local"], index=False)
    # County Health Rankings layout: label row, then variable-code row, then data.
    chr_ = pd.DataFrame({"statecode": c.fips.str[:2], "countycode": c.fips.str[2:],
                         "fipscode": c.fips, "state": c.state,
                         "v140_rawvalue": rng.gamma(6, 2, n).round(2)})
    with open(RAW / SOURCES["chr"]["local"], "w") as fh:
        fh.write("State FIPS Code,County FIPS Code,5-digit FIPS Code,State Abbreviation,Social Associations raw value\n")
        chr_.to_csv(fh, index=False)
    print(f"Wrote synthetic raw files for {n} counties to {RAW}")


if __name__ == "__main__":
    main()
