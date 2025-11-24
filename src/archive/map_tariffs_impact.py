"""
Make a map showing 2023 imports to US divided by GDP for countries with recently-
imposed tariffs.

GDP data: https://data.worldbank.org/
Imports data: Census
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os

# Constants
ROOT = os.path.join(os.path.dirname(__file__), "../data/")
GDP_FILE = ROOT + "gdp_global.xlsx"
IMPORTS_FILE = ROOT + "country.xlsx"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../outputs/plots/","imports_gdp_ratio_map.png") 

# Load GDP data
gdp = pd.read_excel(GDP_FILE)
gdp.rename(columns={"Country Name": "country", 2023: "GDP"}, inplace=True)

# Load imports data
imports = pd.read_excel(IMPORTS_FILE)
imports = imports[["year", "CTYNAME", "IYR", "EYR"]]
imports = imports[imports["year"] == 2023]
imports.rename(columns={"CTYNAME": "country"}, inplace=True)
imports.drop(columns="year", inplace=True)

# Harmonize country names in imports data
remap_imports = {
    "Hong Kong": "Hong Kong SAR, China",
    "Venezuela": "Venezuela, RB",
    "Czech Republic": "Czechia",
    "Russia": "Russian Federation",
    "Kyrgyzstan": "Kyrgyz Republic",
    "Macedonia": "North Macedonia",
    "Turkey": "Turkiye",
    "Syria": "Syrian Arab Republic",
    "Lebanon": "Lebanon",
    "Iran": "Iran, Islamic Rep.",
    "Republic of Yemen": "Yemen, Rep.",
    "Burma": "Myanmar",
    "Vietnam": "Viet Nam",
    "Laos": "Lao PDR",
    "East Timor": "Timor-Leste",
    "Brunei": "Brunei Darussalam",
    "Korea, South": "Korea, Rep.",
    "Egypt": "Egypt, Arab Rep.",
    "South Sudan": "South Sudan",
    "Gambia": "Gambia, The",
}
imports["country"] = (
    imports["country"].replace(remap_imports).fillna(imports["country"])
)

# Merge GDP and imports data
gdp = gdp.merge(imports, on="country", how="left")
gdp = gdp[gdp["IYR"].notna()]
gdp["imports_to_us_to_gdp_ratio"] = 100 * ((gdp["IYR"] * 1_000_000) / gdp["GDP"])
gdp.sort_values("imports_to_us_to_gdp_ratio", ascending=False, inplace=True)

# Load world geometry
# world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
world = gpd.read_file(
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"
)
# Harmonize country names in GDP data
gdp_remap = {
    "Lao PDR": "Laos",
    "Viet Nam": "Vietnam",
    "Korea, Rep.": "South Korea",
    "Venezuela, RB": "Venezuela",
    "Yemen, Rep.": "Yemen",
    "Turkiye": "Turkey",
    "Syrian Arab Republic": "Syria",
}
gdp["country"] = gdp["country"].replace(gdp_remap).fillna(gdp["country"])

# Merge world geometry with GDP data
world = world.merge(
    gdp[["country", "imports_to_us_to_gdp_ratio"]],
    how="left",
    left_on="name",
    right_on="country",
)

# Create the map
fig, ax = plt.subplots(1, 1, figsize=(15, 10))
world.plot(
    column="imports_to_us_to_gdp_ratio",
    missing_kwds={"color": "lightgrey", "label": "No data"},
    legend=True,
    legend_kwds={
        "label": "Exports to US / GDP Ratio (%)",
        "shrink": 0.5,
        "fraction": 0.046,
        "aspect": 20,
        "pad": 0.01,
    },
    cmap="Blues",
    ax=ax,
)

# Customize plot
ax.axis("off")
plt.title("2023 US Imports as Percentage of GDP by Country", pad=20, size=14)

# Save the map
plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
