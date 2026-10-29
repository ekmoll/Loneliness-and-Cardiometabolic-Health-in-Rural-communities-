"""Step 2: merge PLACES, RUCC 2023 and ERS socioeconomic data into one county file.

Writes data/processed/analytic_county.csv and output/tables/sample_flow.csv, which
records how many counties survive each restriction (needed for a methods section).
"""
import re
import sys

import numpy as np
import pandas as pd

from config import (BEHAVIORS, CARDIO_VALUE_TYPE, CARDIOMETABOLIC, CENSUS_REGION, EDUCATION_MEASURE,
                    HRSN, HRSN_VALUE_TYPE, PROCESSED, RAW, RESTANDARDIZE_COMPOSITE,
                    SOURCES, TABLES)


def read_csv_any(path):
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path}")


def fips5(series):
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)


# ---------------------------------------------------------------------------
def load_places():
    df = read_csv_any(RAW / SOURCES["places"]["local"])
    df = df[df["StateAbbr"] != "US"]  # national summary row
    df["fips"] = fips5(df["LocationID"])
    df["value"] = pd.to_numeric(df["Data_Value"], errors="coerce")

    found = set(df["MeasureId"].unique())
    missing = (set(CARDIOMETABOLIC) | set(HRSN) | set(BEHAVIORS)) - found
    if missing:
        sys.exit(f"PLACES file lacks MeasureIds {sorted(missing)}. "
                 f"Available IDs: {sorted(found)}. Update config.py.")

    def wide(ids, vtype):
        sub = df[df["MeasureId"].isin(ids) & (df["DataValueTypeID"] == vtype)]
        out = sub.pivot_table(index="fips", columns="MeasureId", values="value", aggfunc="first")
        return out.rename(columns=ids)

    cardio = wide(CARDIOMETABOLIC, CARDIO_VALUE_TYPE)
    behav = wide(BEHAVIORS, "AgeAdjPrv")
    cardio = cardio.join(behav)
    hrsn = wide(HRSN, HRSN_VALUE_TYPE)
    hrsn_alt = wide(HRSN, "CrdPrv" if HRSN_VALUE_TYPE == "AgeAdjPrv" else "AgeAdjPrv")
    hrsn_alt.columns = [f"{c}_alt" for c in hrsn_alt.columns]

    meta = (df.groupby("fips")
              .agg(state_abbr=("StateAbbr", "first"), county=("LocationName", "first"),
                   pop_total=("TotalPopulation", "first"), pop_18plus=("TotalPop18plus", "first"))
              .reset_index())
    for col in ("pop_total", "pop_18plus"):
        meta[col] = pd.to_numeric(meta[col].str.replace(",", ""), errors="coerce")
    return meta.merge(cardio.join(hrsn).join(hrsn_alt).reset_index(), on="fips", how="left")


def load_rucc():
    df = read_csv_any(RAW / SOURCES["rucc"]["local"])
    df.columns = [c.strip() for c in df.columns]
    if "Attribute" in df.columns:  # long format
        df = df[df["Attribute"].str.strip() == "RUCC_2023"].rename(columns={"Value": "RUCC_2023"})
    df["fips"] = fips5(df["FIPS"])
    df["rucc"] = pd.to_numeric(df["RUCC_2023"], errors="coerce")
    return df[["fips", "rucc"]].dropna()


def ers_attribute(path, patterns, label):
    """Pull one attribute from an ERS county file (long or wide layout)."""
    df = read_csv_any(path)
    df.columns = [c.strip() for c in df.columns]
    fips_col = next(c for c in df.columns if c.lower().replace(" ", "_") in ("fips_code", "fips", "fipstxt"))
    if "Attribute" in df.columns:
        attrs = df["Attribute"].dropna().unique()
        chosen = next((a for p in patterns for a in attrs if re.search(p, a, re.I)), None)
        if chosen is None:
            sys.exit(f"No attribute in {path.name} matches {patterns}.")
        sub = df[df["Attribute"] == chosen][[fips_col, "Value"]]
    else:
        chosen = next((c for p in patterns for c in df.columns if re.search(p, c, re.I)), None)
        if chosen is None:
            sys.exit(f"No column in {path.name} matches {patterns}.")
        sub = df[[fips_col, chosen]].rename(columns={chosen: "Value"})
    print(f"  {label:<13} <- {path.name}: '{chosen}'")
    out = pd.DataFrame({"fips": fips5(sub[fips_col]),
                        label: pd.to_numeric(sub["Value"].astype(str).str.replace(",", ""),
                                             errors="coerce")})
    return out[~out["fips"].str.endswith("000")]  # drop state and national rows


def load_ers():
    edu_patterns = {
        "bachelors_or_higher": [r"^Percent of adults with a bachelor.*higher, 2019-23",
                                r"^Percent of adults with a bachelor.*higher"],
        "less_than_hs": [r"^Percent of adults (who are not high school graduates|with less than).*2019-23",
                         r"^Percent of adults (who are not high school graduates|with less than)"],
    }[EDUCATION_MEASURE]
    pov = ers_attribute(RAW / SOURCES["poverty"]["local"], [r"^PCTPOVALL_2023$", r"PCTPOVALL"], "poverty")
    edu = ers_attribute(RAW / SOURCES["education"]["local"], edu_patterns, "education")
    une = ers_attribute(RAW / SOURCES["unemployment"]["local"],
                        [r"^Unemployment_rate_2023$", r"Unemployment_rate_20\d\d$"], "unemployment")
    return pov.merge(edu, on="fips", how="outer").merge(une, on="fips", how="outer")


def load_chr():
    """Social Associations (membership associations per 10,000) from CHR 2025.

    The CHR CSV has two header rows: labels, then variable codes (v140_rawvalue).
    """
    path = RAW / SOURCES["chr"]["local"]
    if not path.exists():
        print(f"  (no {path.name}; social associations will be missing)")
        return None
    df = pd.read_csv(path, dtype=str, skiprows=[0], encoding="latin-1")
    df = df[df["countycode"] != "000"]
    out = pd.DataFrame({"fips": fips5(df["fipscode"]),
                        "social_assoc": pd.to_numeric(df["v140_rawvalue"], errors="coerce")})
    print(f"  social_assoc  <- {path.name}: 'v140_rawvalue' (Social Associations, per 10,000)")
    return out


# ---------------------------------------------------------------------------
def zscore(s):
    return (s - s.mean()) / s.std(ddof=1)


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    print("Loading sources")
    places, rucc, ers = load_places(), load_rucc(), load_ers()

    flow = [("PLACES counties", len(places), places["state_abbr"].nunique())]
    df = places.merge(rucc, on="fips", how="left")
    unmatched = df[df["rucc"].isna()]
    if len(unmatched):
        print(f"  WARNING {len(unmatched)} PLACES counties have no RUCC 2023 match "
              f"(states: {sorted(unmatched['state_abbr'].unique())}). "
              "Connecticut planning-region FIPS changes are the usual cause.")
    df = df.dropna(subset=["rucc"])
    flow.append(("Matched to RUCC 2023", len(df), df["state_abbr"].nunique()))

    df = df.dropna(subset=list(CARDIOMETABOLIC.values()))
    flow.append(("With all 4 cardiometabolic measures", len(df), df["state_abbr"].nunique()))

    df = df.dropna(subset=list(HRSN.values()))
    flow.append(("With all 6 social-needs measures", len(df), df["state_abbr"].nunique()))

    df = df.merge(ers, on="fips", how="left").dropna(subset=["poverty", "education", "unemployment"])
    flow.append(("With ERS covariates (analytic sample)", len(df), df["state_abbr"].nunique()))

    df["rucc"] = df["rucc"].astype(int)
    df["metro"] = np.where(df["rucc"] <= 3, "Metro", "Nonmetro")
    df["state_fips"] = df["fips"].str[:2]
    df["region"] = df["state_fips"].map(CENSUS_REGION)

    # Composite: z-score each condition within the analytic sample, average them.
    zcols = []
    for name in CARDIOMETABOLIC.values():
        df[f"z_{name}"] = zscore(df[name])
        zcols.append(f"z_{name}")
    df["cardio_burden"] = df[zcols].mean(axis=1)
    if RESTANDARDIZE_COMPOSITE:
        df["cardio_burden"] = zscore(df["cardio_burden"])
    alpha = cronbach_alpha(df[zcols])

    # Material hardship index: mean of the four z-scored hardship measures.
    hard = ["food_insecurity", "housing_insecurity", "utility_insecurity", "transportation_difficulty"]
    df["hardship_index"] = zscore(pd.concat([zscore(df[c]) for c in hard], axis=1).mean(axis=1))

    # Community asset (does not restrict the primary sample).
    chr_ = load_chr()
    if chr_ is not None:
        df = df.merge(chr_, on="fips", how="left")
        print(f"  social associations available for {df['social_assoc'].notna().sum()} "
              f"of {len(df)} analytic counties")

    out = PROCESSED / "analytic_county.csv"
    df.to_csv(out, index=False)
    pd.DataFrame(flow, columns=["step", "counties", "states"]).to_csv(TABLES / "sample_flow.csv", index=False)

    print("\nSample flow")
    for step, n, s in flow:
        print(f"  {step:<42} {n:>5} counties  {s:>2} states")
    print(f"\nStates in analytic sample: {', '.join(sorted(df['state_abbr'].unique()))}")
    print(f"Composite Cronbach's alpha (4 z-scored conditions): {alpha:.3f}")
    print(f"Wrote {out.relative_to(PROCESSED.parents[1])}")


def cronbach_alpha(items):
    k = items.shape[1]
    return k / (k - 1) * (1 - items.var(ddof=1).sum() / items.sum(axis=1).var(ddof=1))


if __name__ == "__main__":
    main()
