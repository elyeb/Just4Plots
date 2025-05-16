import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point

# Approximate coordinates for key locations
locations = {
    "Rue Faubourg de Colmar": (7.3407, 47.7576),  # Mulhouse
    "Rouffach": (7.2976, 47.9571),
    "Habsheim": (7.4192, 47.7297),
    "Mulhouse": (7.3386, 47.7508)
}

# Create a GeoDataFrame for the points
gdf_points = gpd.GeoDataFrame(
    {"name": list(locations.keys())},
    geometry=[Point(lon, lat) for lon, lat in locations.values()],
    crs="EPSG:4326"
)

# Download or load a shapefile for France or Alsace region
# For demonstration, let's use the Natural Earth countries dataset
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
france = world[world.name == "France"]

# Crop to a bounding box around Mulhouse
bbox = (7.1, 47.65, 7.5, 48.05)  # (minx, miny, maxx, maxy)
france = france.to_crs(epsg=3857)
gdf_points = gdf_points.to_crs(epsg=3857)

# Plot
fig, ax = plt.subplots(figsize=(10, 10))
france.plot(ax=ax, color='white', edgecolor='black')
gdf_points.plot(ax=ax, color='red', markersize=80)

# Add labels
for x, y, label in zip(gdf_points.geometry.x, gdf_points.geometry.y, gdf_points["name"]):
    ax.text(x, y, label, fontsize=12, ha='left', va='bottom', color='darkblue')

# Set bounds and add basemap
ax.set_xlim(bbox[0]*111319.5, bbox[2]*111319.5)
ax.set_ylim(bbox[1]*111319.5, bbox[3]*111319.5)
ctx.add_basemap(ax, crs=gdf_points.crs, source=ctx.providers.Stamen.Terrain)

ax.set_axis_off()
plt.title("Greater Mulhouse Area, Alsace, France")
plt.show()