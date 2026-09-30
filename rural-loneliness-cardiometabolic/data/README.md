# Data

The shareable merged county dataset is in [`analytic/`](analytic/) with its codebook. Raw source
files are not committed (they are large and public). To rebuild from scratch, run
`make download`, or fetch each file by hand and save it in `data/raw/` under the name shown.
Files used for the published analysis were downloaded September 30, 2026.

| Save as | Source | Notes |
|---|---|---|
| `PLACES_County_2025.csv` | [CDC PLACES County Data, 2025 release](https://data.cdc.gov/500-Cities-Places/PLACES-Local-Data-for-Better-Health-County-Data-20/swc5-untb) → Export → CSV | Long format, one row per county × measure × prevalence type |
| `Ruralurbancontinuumcodes2023.csv` | [USDA ERS Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes) | 2023 codes |
| `Poverty2023.csv` | [USDA ERS County-Level Data Sets](https://www.ers.usda.gov/data-products/county-level-data-sets) → Poverty | Uses `PCTPOVALL_2023` |
| `Education2023.csv` | same page → Education | Uses % adults with bachelor's or higher, 2019–23 |
| `Unemployment2023.csv` | same page → Unemployment and median household income | Uses `Unemployment_rate_2023` |
| `analytic_data2025_v3.csv` | [County Health Rankings, Rankings Data & Documentation](https://www.countyhealthrankings.org/explore-health-rankings/rankings-data-documentation) → 2025 CHR CSV Analytic Data | Uses `v140_rawvalue` (Social Associations) |

ERS occasionally renames files or attributes. `src/02_build_analytic.py` matches attributes by
pattern and prints which one it used; if it stops with "no attribute matches", open the file,
find the attribute name, and update the pattern.

**Record the download date** of each file in your methods — CDC and ERS revise files in place.

**Connecticut:** RUCC 2023 uses Connecticut's nine planning regions (FIPS 09110–09190). If
the PLACES file uses the eight legacy counties, those rows will not match and the build step
prints a warning.
