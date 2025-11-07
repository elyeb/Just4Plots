"""
Make a Washington State Map of DUI Filings by county and city. 

Used for post: https://www.reddit.com/r/MapPorn/comments/1k05iaf/oc_dui_filings_for_washington_state_2024/

DUI Data: https://www.courts.wa.gov/caseload/?fa=caseload.showReport&level=D&freq=A&tab=&fileID=rpt07
WA shape file: https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html
Population: https://ofm.wa.gov/washington-data-research/population-demographics/population-estimates/april-1-official-population-estimates
"""

import tabula
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import re

# Define file paths
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "../data/dui_raw_pdfs/")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../outputs/plots/")
COUNTY_SHAPE_PATH = os.path.join(os.path.dirname(__file__), '../data/cb_2023_us_county_500k/cb_2023_us_county_500k.shp')
MET_SHAPE_PATH = os.path.join(os.path.dirname(__file__), '../data/cb_2023_us_place_500k/cb_2023_us_place_500k.shp')
COUNTY_POP_PATH = os.path.join(os.path.dirname(__file__), '../data/co-est2024-pop-53.xlsx')
M_POP = os.path.join(os.path.dirname(__file__), '../data/ofm_april1_population_final.xlsx')

# Read and preprocess shapefiles
gdf_county = gpd.read_file(COUNTY_SHAPE_PATH)
gdf_county = gdf_county[['NAMELSAD', 'STUSPS', 'geometry']]
gdf_county.rename(columns={'NAMELSAD': 'Location', 'STUSPS': 'State'}, inplace=True)

gdf_met = gpd.read_file(MET_SHAPE_PATH)
gdf_met = gdf_met[['NAME', 'STUSPS', 'geometry']]
gdf_met.rename(columns={'NAME': 'Location', 'STUSPS': 'State'}, inplace=True)

# Read and preprocess population data
pop = pd.read_excel(M_POP)
col_names = list(pop.iloc[3, :])
pop.columns = col_names
pop = pop.iloc[4:, :]
pop = pop[["Jurisdiction", "2024 Population Estimate"]]
pop.rename(columns={"Jurisdiction": "Location", "2024 Population Estimate": "population"}, inplace=True)
pop = pop[pop["Location"] != "."]
pop["Location"] = pop["Location"].str.replace(" (part)", "").str.strip()
pop.dropna(subset="Location", inplace=True)
pop = pop.groupby("Location").aggregate(sum).reset_index()
pop["population"] = pop["population"].apply(lambda x: x / 100000)

# Define replacement dictionaries
replace_dict = {
    "Sedro Woolley": "Sedro-Woolley",
    "Eatonville (ETN)": "Eatonville",
    "Steilacoom (CST)": "Steilacoom",
    "Tumwater (THD)": "Tumwater"
}

pop_file_replace_dict = {
    "Du Pont M": "Dupont",
}

# Read DUI data
all_pdfs = sorted(os.listdir(DATA_FOLDER))
table_24 = tabula.read_pdf(DATA_FOLDER + '2024.pdf', pages="105-119", multiple_tables=False)

# Handle additional data row
additional_data_row = {"Yakima County": "1,507 1,508 488 0 1 252 697 5 0 1 1,394 11,268 142 2"}
additional_data_row["Yakima County"] = additional_data_row["Yakima County"].split()
additional_data_row = [list(additional_data_row.keys())[0]] + list(additional_data_row.values())[0]

# Function to clean and process the data
def clean_table(df, year, additional_data_row):
    df = pd.DataFrame(df[0])
    df.rename(columns={'Unnamed: 0': "Location"}, inplace=True)
    df.dropna(subset=["Location"], inplace=True)

    if additional_data_row:
        df_add = pd.DataFrame([additional_data_row], columns=df.columns)
        df = pd.concat([df, df_add], ignore_index=True)

    start_index = df[(df["Location"] == "Adams County") & df['Filings'].isna()].index[0]
    df = df[df.index >= start_index]
    county_list = list(df[df['Filings'].isna()].Location)

    # Assign counties to rows
    df['County'] = ''
    df = df.reset_index(drop=True)
    for i in range(0, len(df)):
        if df['Location'].iloc[i] in county_list:
            county = df['Location'].iloc[i]
            df['County'].iat[i] = county
        else:
            df['County'].iat[i] = county

    df.dropna(subset=['Filings'], inplace=True)
    df['Filings'] = df['Filings'].apply(lambda x: x.replace(',', ''))

    # Add extra variables
    df['Year'] = year
    df['State'] = 'WA'

    # Process municipalities
    pattern_M = re.compile(r'\..*\sM')
    df_M = df[df["Location"].str.contains(pattern_M, regex=True)]
    df_M["Location"] = df_M["Location"].apply(lambda x: re.sub("\.", "", x))
    df_M["Location"] = df_M["Location"].apply(lambda x: re.sub("\sM$", "", x))
    df_M["location_type"] = "municipality"
    df_M["Location"] = df_M["Location"].map(replace_dict).fillna(df_M["Location"])
    df_M = df_M.merge(gdf_met, on=['Location', 'State'], how='left')

    # Process counties
    df_county = df[df["Location"].str.contains('County')]
    df_county["location_type"] = "county"
    df_county = df_county.merge(gdf_county, on=['Location', 'State'], how='left')

    # Combine data
    df_out = pd.concat([df_M, df_county], ignore_index=True)
    pop["Location"] = pop["Location"].astype(str)
    df_out = df_out.merge(pop, on='Location', how="left")
    df_out.dropna(subset=["geometry", "population"], inplace=True)

    df_out["Filings"] = df_out["Filings"].astype(int)
    df_out['filings_per_100k'] = df_out["Filings"] / df_out["population"]

    return df_out

# Function to plot the data
def plot_dui_data(df, year):
    # Ensure 'df' is a GeoDataFrame
    if not isinstance(df, gpd.GeoDataFrame):
        df = gpd.GeoDataFrame(df, geometry='geometry')

    # Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Plot counties
    df[df['location_type'] == 'county'].plot(
        column='filings_per_100k',
        cmap='OrRd',
        legend=True,
        ax=ax,
        edgecolor='black',
        alpha=0.8
    )

    # Plot municipalities
    df[df['location_type'] == 'municipality'].plot(
        column='filings_per_100k',
        cmap='OrRd',
        legend=False,
        ax=ax,
        edgecolor='black',
        alpha=1.0
    )

    # Label counties
    for _, row in df[df['location_type'] == 'county'].iterrows():
        if row['geometry'].centroid.is_empty:
            continue
        centroid = row['geometry'].centroid
        if row['Location'] in ['Yakima County', 'Kitsap County']:
            ax.text(
                centroid.x, centroid.y,
                row['Location'].replace(" County", ""),
                fontsize=8,
                ha='right',
                va='bottom',
                color='black',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none')
            )
        elif row['Location'] in ['King County', 'Spokane County']:
            ax.text(
                centroid.x, centroid.y,
                row['Location'].replace(" County", ""),
                fontsize=8,
                ha='left',
                va='top',
                color='black',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none')
            )
        else:
            ax.text(
                centroid.x, centroid.y,
                row['Location'].replace(" County", ""),
                fontsize=8,
                ha='center',
                va='center',
                color='black',
                bbox=dict(facecolor='white', alpha=0.0, edgecolor='none')
            )

    # Add title
    ax.set_title(f"DUI Filings per 100k by County and Municipality for {year}", fontsize=16)

    # Remove axis
    ax.axis('off')

    # Add text below the plot
    fig.text(
        0.5, 0.10,
        "DUI data from https://www.courts.wa.gov/caseload/\n"
        "Population data: https://ofm.wa.gov\n"
        "WA shape file: https://www.census.gov/",
        ha='right',
        fontsize=10,
        color='black'
    )

    # Save the plot
    fig.savefig(f"{OUTPUT_FOLDER}dui_{year}.png", dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(f"{OUTPUT_FOLDER}dui_{year}.pdf", bbox_inches='tight', facecolor='white')

    # Show the plot
    plt.show()

# Clean the data
year = 2024
df = clean_table(table_24, year, additional_data_row)

# Plot the data
plot_dui_data(df, year)