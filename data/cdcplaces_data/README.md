## CDC PLaces Data Collection

This folder contains the notebook for the CDC Places data collection process, along with its supporting inputs and outputs.

The final output is the `cdcplaces_data.csv` file in the `data/` folder.

For the full documentation and code, see the HTML export of the notebook: `cdcplaces_data_collection.html`.

### Input
- `data/cdcplaces_data/PLACES__Census_Tract_Data_(GIS_Friendly_Format),_2025_release_20260622.csv` - raw download
- `data/cdcplaces_data/PLACES__County_Data_(GIS_Friendly_Format),_2025_release_20260622.csv` - raw download

### Output
- `data/cdcplaces_data.csv`

### Columns in the Final Output

| Column Name | Data Type | Description |
|---|---|---|
| `fips` | Integer | County-level FIPS code identifying the county and state |
| `county` | String | County name |
| `state` | String | Two-letter U.S. state postal abbreviation |
| `binge_drinking_prevalence` | Float | Percentage of adults who report binge drinking |
| `smoking_prevalence` | Float | Percentage of adults who currently smoke cigarettes |
| `physical_inactivity` | Float | Percentage of adults reporting no leisure-time physical activity |
| `hypertension_prevalence` | Float | Percentage of adults with diagnosed high blood pressure |
| `high_cholesterol_prevalence` | Float | Percentage of adults with diagnosed high cholesterol |
| `diabetes_prevalence` | Float | Percentage of adults with diagnosed diabetes |
| `obesity_prevalence` | Float | Percentage of adults with a BMI of 30 or higher |
| `stroke_prevalence` | Float | Percentage of adults who report having had a stroke |