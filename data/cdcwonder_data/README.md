## CDC WONDER Stroke Mortality Data

This folder contains the notebook for CDC WONDER data collection, along with its outputs. The final output is the `stroke_mortality.csv` file in the `data/` folder.

For the full documentation and code, see the HTML export of the notebook: `cdcwonder_data_collection.html`.

### Collection notes

Source: CDC WONDER Underlying Cause of Death, Single Race edition. ICD-10 codes:
- Acute stroke: I60–I66 (output column: `acute_stroke_mortality_per_100k`)
- Stroke sequelae: I69 (output column: `sequelae_stroke_mortality_per_100k`)

Years pooled: 2018–2024. Single-year county mortality is suppressed for many small counties; pooling across years reduces suppression and produces more stable rates.

Rates are per 100,000 population.

### Inputs

- `data/cdcwonder_data/Acute Stroke_Underlying Cause of Death, 2018-2024, Single Race.csv` — raw WONDER download
- `data/cdcwonder_data/Sequelae of Stroke_Underlying Cause of Death, 2018-2024, Single Race.csv` — raw WONDER download

### Outputs

- `data/stroke_mortality.csv`

#### Final Output Variables

| Column Name | Data Type | Description |
|---|---|---|
| `fips` | String | 5-character zero-padded county FIPS code (e.g. "09001") |
| `county` | String | County name |
| `state` | String | Two-letter U.S. state postal abbreviation |
| `acute_stroke_mortality_per_100k` | Float | Deaths from acute stroke per 100,000 population |
| `sequelae_stroke_mortality_per_100k` | Float | Deaths from long-term complications (sequelae) of stroke per 100,000 population |






