## CDC WONDER Stroke Mortality Data

This folder contains the notebook for CDC WONDER data collection, along with its outputs. The final output is the `stroke_mortality.csv` file in the `data/` folder.

For the full documentation and code, see the HTML export of the notebook: `cdcwonder_data_collection.html`.

### Collection notes

Source: CDC WONDER Underlying Cause of Death, Single Race edition. ICD-10 codes:
- Acute stroke: I60–I66 (output column: `acute_stroke_mortality_rate`)
- Stroke sequelae: I69 (output column: `sequelae_stroke_mortality_rate`)

Years pooled: 2018–2024. Single-year county mortality is suppressed for many small counties; pooling across years reduces suppression and produces more stable rates.

Rates are age-adjusted per 100,000 population.

### Outputs

- `data/stroke_mortality.csv` (main output) — one row per county (91 total: 62 NY, 21 NJ, 8 CT)
- `data/cdcwonder_data/cdcwonder_data_collection.html` — notebook export

### Inputs

- `data/cdcwonder_data/Acute Stroke_Underlying Cause of Death, 2018-2024, Single Race.csv` — raw WONDER download
- `data/cdcwonder_data/Sequelae of Stroke_Underlying Cause of Death, 2018-2024, Single Race.csv` — raw WONDER download
