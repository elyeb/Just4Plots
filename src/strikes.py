"""
Visualizing trends in strikes data for OECD countries.

Data source: https://ilostat.ilo.org/methods/concepts-and-definitions/description-industrial-relations-data/
Indicator: "Number of strikes and lockouts by economic activity"

Author: Elye Bliss
Date: April 2025
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from adjustText import adjust_text
import matplotlib as mpl

# Set global font to Arial for a clean look
mpl.rcParams['font.family'] = 'Arial'

# Define file paths
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "../data/")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../outputs/plots/")
DATA_FILE = "STR_TSTR_ECO_NB_A-20250419T0034.csv"

# List of OECD countries
OECD_COUNTRIES = [
    'Australia', 'Austria', 'Belgium', 'Canada', 'Switzerland', 'Chile', 'Colombia', 'Costa Rica',
    'Czechia', 'Germany', 'Denmark', 'Spain', 'Estonia', 'Finland', 'France',
    'United Kingdom of Great Britain and Northern Ireland', 'Greece', 'Hungary', 'Ireland',
    'Iceland', 'Israel', 'Italy', 'Japan', 'Republic of Korea', 'Lithuania', 'Latvia', 'Mexico',
    'Netherlands', 'Norway', 'New Zealand', 'Poland', 'Portugal', 'Slovakia', 'Sweden', 'Türkiye',
    'United States of America'
]

# Load the dataset
df = pd.read_csv(os.path.join(DATA_FOLDER, DATA_FILE))

# Rename columns for clarity
df.columns = [
    "country", "data_source", "indicator", "sector", "year", "strikes",
    "label_status", "label_class", "label_note", "note_source"
]

# Filter data for the total economic activity sector
df = df[df["sector"] == "Economic activity (Broad sector): Total"]

# Keep only relevant columns
df = df[["country", "year", "strikes"]]

# Filter for OECD countries
df = df[df["country"].isin(OECD_COUNTRIES)]

# Drop rows with missing strikes data and convert strikes to integers
df.dropna(subset=["strikes"], inplace=True)
df["strikes"] = df["strikes"].astype(int)

# Create the plot
fig, ax = plt.subplots(1, 1, figsize=(10, 10))

# Plot scatter points for each country
for country in df["country"].unique():
    country_data = df[df["country"] == country]
    ax.scatter(country_data["year"], country_data["strikes"], label=country)

# Collect text objects for annotation adjustment
texts = []

# Annotate countries with strikes > 50% higher than the next highest for each year
for year in df["year"].unique():
    year_data = df[df["year"] == year].sort_values(by="strikes", ascending=False)
    if len(year_data) > 1:
        top_row = year_data.iloc[0]  # Country with the highest strikes
        second_row = year_data.iloc[1]  # Country with the second-highest strikes
        if top_row["strikes"] > 1.3 * second_row["strikes"]:  # Check if 50% greater
            text = ax.text(
                top_row["year"], top_row["strikes"],  # Coordinates for the label
                top_row["country"],                  # Country name to display
                fontsize=10,                         # Font size
                ha="center",                         # Horizontal alignment
                va="bottom",                         # Vertical alignment
                color="black",                       # Text color
                fontweight="bold",
                bbox=dict(facecolor="white", alpha=0.3, edgecolor="none")  # Background box
            )
            texts.append(text)  # Add the text object to the list for adjustment

# Adjust text positions to avoid overlaps
adjust_text(
    texts,
    ax=ax
)

# Format the y-axis with commas for better readability
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

# Add title and axis labels
ax.set_title("Number of Strikes and Lockouts in OECD Countries", pad=15, size=20, fontweight="bold")
ax.set_xlabel("Year", size=12, fontweight="bold")
ax.set_ylabel("Total", size=12, fontweight="bold")

# Add text below the plot for data source
fig.text(
    0.12, 0.035,
    "Strikes data from:\nhttps://ilostat.ilo.org/methods/concepts-and-definitions/description-industrial-relations-data/",
    ha="left",
    fontsize=10,
    color="black"
)

# Save the plot as a high-quality PNG
fig.savefig(f"{OUTPUT_FOLDER}strikes_oecd.png", bbox_inches="tight", facecolor="white", dpi=300)

# Show the plot
plt.show()