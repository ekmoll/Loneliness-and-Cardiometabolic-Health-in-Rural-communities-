"""Step 7: export the county analytic dataset and its codebook for sharing.

Writes:
    data/analytic/county_analytic_dataset.csv   one row per county in the analytic sample
    data/analytic/CODEBOOK.md                   every variable: meaning, source, units, summary

All inputs are public (CDC PLACES, USDA ERS, County Health Rankings), so the merged
county file can be shared openly with attribution.
"""
import pandas as pd

from config import (BEHAVIORS, CARDIOMETABOLIC, HRSN, PROCESSED, ROOT)

OUT = ROOT / "data" / "analytic"

PLACES = "CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022)"
ERS = "USDA ERS County-Level Data Sets"
DESCRIPTIONS = {
    "fips": ("5-digit county FIPS code", "PLACES", "text"),
    "county": ("County name", "PLACES", "text"),
    "state_abbr": ("State abbreviation", "PLACES", "text"),
    "state_fips": ("2-digit state FIPS code", "derived", "text"),
    "region": ("Census region", "derived from state FIPS", "category"),
    "rucc": ("Rural-Urban Continuum Code 2023 (1 = metro ≥1M … 9 = urban pop <5,000, not metro-adjacent)",
             "USDA ERS RUCC 2023", "1–9"),
    "metro": ("Metro (RUCC 1–3) or Nonmetro (RUCC 4–9)", "derived", "category"),
    "pop_total": ("Total population", PLACES, "persons"),
    "pop_18plus": ("Adult population, 18+", PLACES, "persons"),
    "food_insecurity": ("Food insecurity in past 12 months, age-adjusted", PLACES, "% adults"),
    "housing_insecurity": ("Housing insecurity in past 12 months, age-adjusted", PLACES, "% adults"),
    "utility_insecurity": ("Utility services shut-off threat in past 12 months, age-adjusted", PLACES, "% adults"),
    "transportation_difficulty": ("Lack of reliable transportation in past 12 months, age-adjusted", PLACES, "% adults"),
    "lack_social_support": ("Lack of social and emotional support, age-adjusted", PLACES, "% adults"),
    "loneliness": ("Feelings of loneliness, age-adjusted", PLACES, "% adults"),
    "loneliness_alt": ("Feelings of loneliness, crude prevalence (used in the sensitivity analysis)", PLACES, "% adults"),
    "hypertension": ("High blood pressure, age-adjusted", PLACES, "% adults"),
    "diabetes": ("Diagnosed diabetes, age-adjusted", PLACES, "% adults"),
    "coronary_heart_disease": ("Coronary heart disease, age-adjusted", PLACES, "% adults"),
    "stroke": ("Stroke, age-adjusted", PLACES, "% adults"),
    "smoking": ("Current cigarette smoking, age-adjusted", PLACES, "% adults"),
    "physical_inactivity": ("No leisure-time physical activity, age-adjusted", PLACES, "% adults"),
    "obesity": ("Obesity, age-adjusted", PLACES, "% adults"),
    "short_sleep": ("Short sleep duration (<7 h), age-adjusted", PLACES, "% adults"),
    "binge_drinking": ("Binge drinking, age-adjusted", PLACES, "% adults"),
    "uninsured": ("No health insurance, ages 18–64, age-adjusted", PLACES, "% adults"),
    "routine_checkup": ("Routine checkup within past year, age-adjusted", PLACES, "% adults"),
    "poverty": ("Percent of people in poverty, 2023 (SAIPE)", ERS + " — Poverty", "%"),
    "education": ("Percent of adults with a bachelor's degree or higher, 2019–23 (ACS)", ERS + " — Education", "%"),
    "unemployment": ("Unemployment rate, 2023 (LAUS)", ERS + " — Unemployment", "%"),
    "social_assoc": ("Membership associations per 10,000 population (civic, religious, sports, political, "
                     "labor, business, professional)", "County Health Rankings 2025 (County Business Patterns 2022)",
                     "per 10,000"),
    "cardio_burden": ("Cardiometabolic burden: mean of the z-scores of hypertension, diabetes, coronary heart "
                      "disease and stroke (z-scores computed within the analytic sample)", "derived", "z units"),
    "hardship_index": ("Material hardship index: mean of z-scored food, housing, utility and transportation "
                       "insecurity, re-standardized to SD = 1", "derived", "SD units"),
}


def main():
    df = pd.read_csv(PROCESSED / "analytic_county.csv", dtype={"fips": str, "state_fips": str})
    cols = [c for c in DESCRIPTIONS if c in df.columns]
    out = df[cols].sort_values("fips")
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "county_analytic_dataset.csv", index=False, float_format="%.4g")

    lines = ["# Codebook: county_analytic_dataset.csv", "",
             f"{len(out):,} counties in {out.loc[out.state_abbr != 'DC', 'state_abbr'].nunique()} states and the "
             "District of Columbia; one row per county. "
             "All prevalence measures are CDC PLACES model-based small-area estimates. "
             "Loneliness and the other social-needs measures exist only for states that administered "
             "the optional BRFSS Social Determinants and Health Equity module, which defines the sample.", "",
             "| Variable | Description | Source | Units | N | Mean | Min | Max |",
             "|---|---|---|---|---|---|---|---|"]
    for c in cols:
        desc, src, unit = DESCRIPTIONS[c]
        s = out[c]
        if pd.api.types.is_numeric_dtype(s) and c not in ("rucc",):
            stats = f"{s.notna().sum()} | {s.mean():.2f} | {s.min():.2f} | {s.max():.2f}"
        else:
            stats = f"{s.notna().sum()} | | | "
        lines.append(f"| `{c}` | {desc} | {src} | {unit} | {stats} |")
    lines += ["", "## Source citations", "",
              "- Centers for Disease Control and Prevention. PLACES: Local Data for Better Health, County "
              "Data, 2025 release. https://data.cdc.gov/d/swc5-untb",
              "- USDA Economic Research Service. Rural-Urban Continuum Codes, 2023. "
              "https://www.ers.usda.gov/data-products/rural-urban-continuum-codes",
              "- USDA Economic Research Service. County-Level Data Sets (Poverty, Education, "
              "Unemployment). https://www.ers.usda.gov/data-products/county-level-data-sets",
              "- University of Wisconsin Population Health Institute. County Health Rankings & "
              "Roadmaps 2025. https://www.countyhealthrankings.org"]
    (OUT / "CODEBOOK.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(out):,} counties × {len(cols)} variables to data/analytic/")


if __name__ == "__main__":
    main()
