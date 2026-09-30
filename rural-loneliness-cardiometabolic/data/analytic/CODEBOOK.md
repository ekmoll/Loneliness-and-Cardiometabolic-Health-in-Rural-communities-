# Codebook: county_analytic_dataset.csv

2,289 counties in 38 states and the District of Columbia; one row per county. All prevalence measures are CDC PLACES model-based small-area estimates. Loneliness and the other social-needs measures exist only for states that administered the optional BRFSS Social Determinants and Health Equity module, which defines the sample.

| Variable | Description | Source | Units | N | Mean | Min | Max |
|---|---|---|---|---|---|---|---|
| `fips` | 5-digit county FIPS code | PLACES | text | 2289 | | |  |
| `county` | County name | PLACES | text | 2289 | | |  |
| `state_abbr` | State abbreviation | PLACES | text | 2289 | | |  |
| `state_fips` | 2-digit state FIPS code | derived | text | 2289 | | |  |
| `region` | Census region | derived from state FIPS | category | 2289 | | |  |
| `rucc` | Rural-Urban Continuum Code 2023 (1 = metro ≥1M … 9 = urban pop <5,000, not metro-adjacent) | USDA ERS RUCC 2023 | 1–9 | 2289 | | |  |
| `metro` | Metro (RUCC 1–3) or Nonmetro (RUCC 4–9) | derived | category | 2289 | | |  |
| `pop_total` | Total population | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | persons | 2289 | 102007.25 | 383.00 | 9663345.00 |
| `pop_18plus` | Adult population, 18+ | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | persons | 2289 | 79818.69 | 313.00 | 7710575.00 |
| `food_insecurity` | Food insecurity in past 12 months, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 17.31 | 5.90 | 46.80 |
| `housing_insecurity` | Housing insecurity in past 12 months, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 13.97 | 5.90 | 33.60 |
| `utility_insecurity` | Utility services shut-off threat in past 12 months, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 9.67 | 3.70 | 27.80 |
| `transportation_difficulty` | Lack of reliable transportation in past 12 months, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 9.45 | 4.10 | 26.80 |
| `lack_social_support` | Lack of social and emotional support, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 24.29 | 16.70 | 37.80 |
| `loneliness` | Feelings of loneliness, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 34.20 | 27.30 | 43.80 |
| `hypertension` | High blood pressure, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 33.91 | 23.90 | 53.10 |
| `diabetes` | Diagnosed diabetes, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 11.13 | 6.70 | 21.30 |
| `coronary_heart_disease` | Coronary heart disease, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 5.99 | 3.80 | 10.10 |
| `stroke` | Stroke, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 3.29 | 1.90 | 6.50 |
| `smoking` | Current cigarette smoking, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 16.53 | 6.50 | 36.90 |
| `physical_inactivity` | No leisure-time physical activity, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 27.21 | 12.70 | 46.20 |
| `obesity` | Obesity, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 38.11 | 17.10 | 54.00 |
| `short_sleep` | Short sleep duration (<7 h), age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 37.16 | 25.70 | 51.00 |
| `binge_drinking` | Binge drinking, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 17.78 | 8.20 | 26.30 |
| `uninsured` | No health insurance, ages 18–64, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 10.56 | 4.00 | 26.70 |
| `routine_checkup` | Routine checkup within past year, age-adjusted | CDC PLACES County Data, 2025 release (BRFSS 2023; short sleep BRFSS 2022) | % adults | 2289 | 75.58 | 62.40 | 84.00 |
| `poverty` | Percent of people in poverty, 2023 (SAIPE) | USDA ERS County-Level Data Sets — Poverty | % | 2289 | 14.34 | 3.80 | 49.60 |
| `education` | Percent of adults with a bachelor's degree or higher, 2019–23 (ACS) | USDA ERS County-Level Data Sets — Education | % | 2289 | 24.10 | 4.40 | 79.73 |
| `unemployment` | Unemployment rate, 2023 (LAUS) | USDA ERS County-Level Data Sets — Unemployment | % | 2289 | 3.53 | 1.10 | 17.30 |
| `social_assoc` | Membership associations per 10,000 population (civic, religious, sports, political, labor, business, professional) | County Health Rankings 2025 (County Business Patterns 2022) | per 10,000 | 2289 | 11.68 | 0.00 | 59.61 |
| `cardio_burden` | Cardiometabolic burden: mean of the z-scores of hypertension, diabetes, coronary heart disease and stroke (z-scores computed within the analytic sample) | derived | z units | 2289 | 0.00 | -2.12 | 4.46 |
| `hardship_index` | Material hardship index: mean of z-scored food, housing, utility and transportation insecurity, re-standardized to SD = 1 | derived | SD units | 2289 | 0.00 | -1.87 | 4.99 |

## Source citations

- Centers for Disease Control and Prevention. PLACES: Local Data for Better Health, County Data, 2025 release. https://data.cdc.gov/d/swc5-untb
- USDA Economic Research Service. Rural-Urban Continuum Codes, 2023. https://www.ers.usda.gov/data-products/rural-urban-continuum-codes
- USDA Economic Research Service. County-Level Data Sets (Poverty, Education, Unemployment). https://www.ers.usda.gov/data-products/county-level-data-sets
- University of Wisconsin Population Health Institute. County Health Rankings & Roadmaps 2025. https://www.countyhealthrankings.org
