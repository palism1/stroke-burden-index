## U.S. Census Bureau's ACS Data Collection

This folder contains the notebook for the ACS data collection process, along with its supporting inputs and outputs. The final output is the `acs_data.csv` file in the `data/` folder.

For the full documentation and code, see the HTML export of the notebook: `acs_data_collection.html`.

Inputs:
- `data/acs_data/retrieve_variable_codes.py`
- `reference/ct_crosswalk/ct_town_crosswalk.csv`
- `data/ny_nj_ct_fips.csv`
- `data/acs_data/example.gif`

Outputs:
- `data/acs_data.csv` (Main output)
- `data/acs_data/acs_ct.json`
- `data/acs_data/acs_nynj.json`
- `data/acs_data/acs_data_collection.html`