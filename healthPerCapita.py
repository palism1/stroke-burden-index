import pandas as pd

url = "https://www.health.ny.gov/diseases/cardiovascular/stroke/designation/stroke_designated_centers.htm"
tables = pd.read_html(url)
df = tables[0]  # first table on the page
df.to_csv("ny_stroke_centers.csv", index=False)
print(df.head())