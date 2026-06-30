## Population Density Data Collection

This folder contains the notebook for the process of collectin population density, along with its supporting inputs and outputs.

The final output is the `pop_density.csv` file in the `data/` folder.

For the full documentation and code, see the HTML export of the notebook: `cdcplaces_data_collection.html`.

### Inputs

- `data\pop_density_data\tl_2023_us_county\tl_2023_us_county.shp` - raw download from TIGER/Line (tl_2023_us_county.zip)
- `data\pop_density_data\tl_2023_09_cousub\tl_2023_09_cousub.shp` - raw download from TIGER/Line (tl_2023_09_cousub.zip)
- `reference/ct_crosswalk/2022tractcrosswalk.csv` - tract-town-county crosswalk file


### Outputs
- `data/pop_density.csv`

#### Final Output Variables

| Column Name | Data Type | Description |
|---|---|---|
| `fips` | Integer | County-level FIPS code identifying the county and state |
| `county` | String | County name |
| `state` | String | Two-letter U.S. state postal abbreviation |
| `pop_density` | Float | Population density (per square mile) |
