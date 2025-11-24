import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import os

# Constants
ROOT = os.path.join(os.path.dirname(__file__), "../data/")


filename = "Streetlight_Repair_Status_6911197660317267174.csv"

df = pd.read_csv("/Users/elyebliss/Documents/Just4Plots/data/"+filename)
seattle_shape_file = "/Users/elyebliss/Documents/Just4Plots/data/seattle_shape/Neighborhood_Map_Atlas_Neighborhoods.shp"
seattle_gdf = gpd.read_file(seattle_shape_file)

# Create a GeoDataFrame from the DataFrame
geometry = [Point(xy) for xy in zip(df['POLE_EASTING'], df['POLE_NORTHING'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")


gdf = gdf.to_crs(seattle_gdf.crs)


# Define a color mapping for TROUBLE_TICKET_COLOR
color_mapping = {
    "Green": "green",
    "Yellow": "yellow",
    "Red": "red"
}

# Map the TROUBLE_TICKET_COLOR values to colors
gdf["color"] = gdf["TROUBLE_TICKET_COLOR"].map(color_mapping)

# Plot the GeoDataFrame
fig, ax = plt.subplots(figsize=(10, 10))
seattle_gdf.plot(ax=ax, color='lightgrey', edgecolor='black', alpha=0.5)

# Plot the data points with color coding
gdf.plot(ax=ax, color=gdf["color"], markersize=15)

# Hide the axes
ax.axis('off')

plt.title("Seattle Streetlight Repair Status")
plt.show()