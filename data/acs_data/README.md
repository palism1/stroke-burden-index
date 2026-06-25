## U.S. Census Bureau's ACS Data Collection

This folder contains the notebook for the ACS data collection process, along with its supporting inputs and outputs. The final output is the `acs_data.csv` file in the `data/` folder.

For the full documentation and code, see the HTML export of the notebook: `acs_data_collection.html`.

### Inputs
- `data/acs_data/retrieve_variable_codes.py`
- `reference/ct_crosswalk/ct_town_crosswalk.csv`
- `data/ny_nj_ct_fips.csv`
- `data/acs_data/example.gif`

### Outputs
- `data/acs_data.csv` (Main output)
- `data/acs_data/acs_ct.json`
- `data/acs_data/acs_nynj.json`
- `data/acs_data/acs_data_collection.html`

#### Final Output Variables

| Column Name | Data Type | Description |
|---|---|---|
| `fips` | Integer | County-level FIPS code identifying the county and state |
| `county` | String | County name |
| `state` | String | Two-letter U.S. state postal abbreviation |
| `total_pop` | Integer | Total population of the county |
| `pcnt_65_plus` | Float | Percentage of the population aged 65 and older |
| `poverty_rate` | Float | Percentage of the population living below the poverty line |
| `pcnt_insured` | Float | Percentage of the population with health insurance |
| `pcnt_bachelors` | Float | Percentage of adults with a bachelor's degree or higher |
| `pcnt_low_income` | Float | Percentage of households classified as low income |
| `pcnt_middle_class` | Float | Percentage of households classified as middle class |
| `pcnt_upper_class` | Float | Percentage of households classified as upper class |

