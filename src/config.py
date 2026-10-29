"""Central configuration: file locations, source URLs, measure IDs and analysis choices.

Every analytic decision that the abstract leaves open is a named setting here, so a
reviewer can see exactly what was assumed and change it in one place.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUT = ROOT / "output"
TABLES = OUTPUT / "tables"
FIGURES = OUTPUT / "figures"

# ---------------------------------------------------------------------------
# Source files. URLs change when agencies re-host data; if a download fails,
# fetch the file manually from the landing page and save it under the local name.
# ---------------------------------------------------------------------------
SOURCES = {
    "places": {
        "local": "PLACES_County_2025.csv",
        "url": "https://data.cdc.gov/api/views/swc5-untb/rows.csv?accessType=DOWNLOAD",
        "landing": "https://data.cdc.gov/500-Cities-Places/PLACES-Local-Data-for-Better-Health-County-Data-20/swc5-untb",
    },
    "rucc": {
        "local": "Ruralurbancontinuumcodes2023.csv",
        "url": "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/Ruralurbancontinuumcodes2023.csv",
        "landing": "https://www.ers.usda.gov/data-products/rural-urban-continuum-codes",
    },
    "poverty": {
        "local": "Poverty2023.csv",
        "url": "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/48747/Poverty2023.csv",
        "landing": "https://www.ers.usda.gov/data-products/county-level-data-sets",
    },
    "education": {
        "local": "Education2023.csv",
        "url": "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/48747/Education2023.csv",
        "landing": "https://www.ers.usda.gov/data-products/county-level-data-sets",
    },
    "unemployment": {
        "local": "Unemployment2023.csv",
        "url": "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/48747/Unemployment2023.csv",
        "landing": "https://www.ers.usda.gov/data-products/county-level-data-sets",
    },
    "chr": {  # County Health Rankings 2025: Social Associations (v140, CBP 2022)
        "local": "analytic_data2025_v3.csv",
        "url": "https://www.countyhealthrankings.org/sites/default/files/media/document/analytic_data2025_v3.csv",
        "landing": "https://www.countyhealthrankings.org/explore-health-rankings/rankings-data-documentation",
    },
}

# ---------------------------------------------------------------------------
# PLACES measure IDs (column `MeasureId`).
# ---------------------------------------------------------------------------
CARDIOMETABOLIC = {
    "BPHIGH": "hypertension",
    "DIABETES": "diabetes",
    "CHD": "coronary_heart_disease",
    "STROKE": "stroke",
}
HRSN = {
    "FOODINSECU": "food_insecurity",
    "HOUSINSECU": "housing_insecurity",
    "SHUTUTILITY": "utility_insecurity",      # PLACES: utility services shut-off threat
    "LACKTRPT": "transportation_difficulty",  # PLACES: lack of reliable transportation
    "EMOTIONSPT": "lack_social_support",      # PLACES: lack of social and emotional support
    "LONELINESS": "loneliness",               # PLACES: feelings of loneliness
}

# Behavioral risk factors and care access (age-adjusted), used as covariates in
# src/06_behavior_adjustment.py. Several are plausible mediators, not confounders.
BEHAVIORS = {
    "CSMOKING": "smoking",
    "LPA": "physical_inactivity",
    "OBESITY": "obesity",
    "SLEEP": "short_sleep",
    "BINGE": "binge_drinking",
    "ACCESS2": "uninsured",
    "CHECKUP": "routine_checkup",
}

# ---------------------------------------------------------------------------
# Analysis choices the abstract does not pin down (see docs/VERIFICATION.md).
# ---------------------------------------------------------------------------
CARDIO_VALUE_TYPE = "AgeAdjPrv"   # abstract states age-adjusted
HRSN_VALUE_TYPE = "AgeAdjPrv"     # abstract is silent; "CrdPrv" is the alternative
RESTANDARDIZE_COMPOSITE = False   # mean of 4 z-scores (matches the abstract); True re-scales to SD = 1
EDUCATION_MEASURE = "bachelors_or_higher"  # or "less_than_hs"
LONELINESS_UNIT = 10.0            # effect per 10 percentage points, as in the abstract
CLUSTER_SE_BY = "state"           # PLACES estimates share state random effects

RUCC_LABELS = {
    1: "Metro, >=1M",
    2: "Metro, 250K-1M",
    3: "Metro, <250K",
    4: "Nonmetro, urban >=20K, adjacent",
    5: "Nonmetro, urban >=20K, not adjacent",
    6: "Nonmetro, urban 5K-20K, adjacent",
    7: "Nonmetro, urban 5K-20K, not adjacent",
    8: "Nonmetro, urban <5K, adjacent",
    9: "Nonmetro, urban <5K, not adjacent",
}

# Census regions keyed by 2-digit state FIPS.
CENSUS_REGION = {}
for fips in ["09", "23", "25", "33", "44", "50", "34", "36", "42"]:
    CENSUS_REGION[fips] = "Northeast"
for fips in ["17", "18", "26", "39", "55", "19", "20", "27", "29", "31", "38", "46"]:
    CENSUS_REGION[fips] = "Midwest"
for fips in ["10", "11", "12", "13", "24", "37", "45", "51", "54", "01", "21", "28",
             "47", "05", "22", "40", "48"]:
    CENSUS_REGION[fips] = "South"
for fips in ["04", "08", "16", "30", "32", "35", "49", "56", "02", "06", "15", "41", "53"]:
    CENSUS_REGION[fips] = "West"
