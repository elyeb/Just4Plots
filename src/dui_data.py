"""

WA shape file: https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html
"""

import tabula
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import re

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "../data/dui_raw_pdfs/")

COUNTY_SHAPE_PATH = os.path.join(os.path.dirname(__file__), '../data/cb_2023_us_county_500k/cb_2023_us_county_500k.shp')
MET_SHAPE_PATH = os.path.join(os.path.dirname(__file__), '../data/cb_2023_us_place_500k/cb_2023_us_place_500k.shp')
COUNTY_POP_PATH = os.path.join(os.path.dirname(__file__), '../data/co-est2024-pop-53.xlsx')
# PAGES_DICT = {
#     1998: 

# }

# Read the shapefile
gdf_county = gpd.read_file(COUNTY_SHAPE_PATH)
gdf_county = gdf_county[['NAMELSAD','STUSPS','geometry']]
gdf_county.rename(columns={'NAMELSAD':'Location','STUSPS':'State'},inplace=True)

gdf_met = gpd.read_file(MET_SHAPE_PATH)
gdf_met = gdf_met[['NAME','STUSPS','geometry']]
gdf_met.rename(columns={'NAME':'Location','STUSPS':'State'},inplace=True)

# county pop
county_pop_20_24 = pd.read_excel(COUNTY_POP_PATH)
years = list(county_pop_20_24.iloc[2,2:])
years = [int(c) for c in years]
year_cols = ["County",'total']+years
county_pop_20_24 = county_pop_20_24.iloc[3:,:]
county_pop_20_24.columns = year_cols
county_pop_20_24 = county_pop_20_24.iloc[1:,:]

county_pop_20_24.drop(columns='total', axis=1, inplace=True)
county_pop_20_24["County"] = county_pop_20_24["County"].apply(lambda x: re.sub("\.","",x))
county_pop_20_24["County"] = county_pop_20_24["County"].apply(lambda x: x.replace(', Washington',''))
county_pop_20_24[years] = county_pop_20_24[years].apply(lambda x: x/100000)

# town wording replacements
replace_dict = {
    "Sedro Woolley":"Sedro-Woolley",
    "Eatonville (ETN)":"Eatonville",
    "Steilacoom (CST)":"Steilacoom",
    "Tumwater (THD)":"Tumwater"
}

all_pdfs = sorted(os.listdir(DATA_FOLDER))

# table_98 = tabula.read_pdf(DATA_FOLDER+all_pdfs[0], pages="24-37", multiple_tables=True)
table_24 = tabula.read_pdf(DATA_FOLDER+'2024.pdf', pages="105-119", multiple_tables=False)



def clean_table(df,year):
    """
    df = table_24.copy()
    year = 2024
    """
    df = pd.DataFrame(df[0])
    df.columns
    df.rename(columns={'Unnamed: 0':"Location"},inplace=True)
    df.dropna(subset=["Location"],inplace=True)

    start_index = df[(df["Location"]=="Adams County")&df['Filings'].isna()].index[0]
    df = df[df.index>=start_index]
    county_list = list(df[df['Filings'].isna()].Location)

    # deal with county rows
    df['County'] =''
    
    df = df.reset_index(drop=True)
    for i in range(0,len(df)):
        if df['Location'].iloc[i] in county_list:
            county = df['Location'].iloc[i]
            df['County'].iat[i] =county
        else:
            df['County'].iat[i] =county

    df.dropna(subset=['Filings'],inplace=True)

    df['Filings'] = df['Filings'].apply(lambda x: x.replace(',',''))

    # add extra variables
    df['Year'] = year
    df['State'] = 'WA'

    # only keep Counties and Metropolitan areas
    pattern_M = re.compile(r'\..*\sM')
    df_M = df[df["Location"].str.contains(pattern_M,regex=True)]
    df_M["Location"] = df_M["Location"].apply(lambda x: re.sub("\.","",x))
    df_M["Location"] = df_M["Location"].apply(lambda x: re.sub("\sM$","",x))
    df_M["location_type"] = "municipality"
    # Replace values in the "Location" column using the dictionary
    df_M["Location"] = df_M["Location"].map(replace_dict).fillna(df_M["Location"])

    df_M = df_M.merge(gdf_met,on=['Location','State'],how='left')


    df_county = df[df["Location"].str.contains('County')]
    df_county["location_type"] = "county"

    df_county = df_county.merge(gdf_county,on=['Location','State'],how='left')

    pop = county_pop_20_24[['County',year]].copy()
    pop.rename(columns={year:'population'},inplace=True)
    pop.rename(columns={"County":'Location'},inplace=True)
    df_county  = df_county.merge(pop,on='Location',how="left")
    # df_out = pd.concat([df_M,df_county],ignore_index=True)
    df_county['Filings'] = df_county['Filings'].astype(int)

    return df_county #df


df_county['filings_per_100k'] = df_county['Filings']/df_county['population']

df_county[['Location','Filings','filings_per_100k']].sort_values('filings_per_100k')


# Ensure 'df_county' is a GeoDataFrame
if not isinstance(df_county, gpd.GeoDataFrame):
    df_county = gpd.GeoDataFrame(df_county, geometry='geometry')

# Plot the map
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
df_county.plot(
    column='filings_per_100k',#'Filings',  # Column to color-fill
    cmap='OrRd',               # Colormap (e.g., 'OrRd' for orange-red gradient)
    legend=True,               # Add a legend
    legend_kwds={'label':"Filings per 100k"},#'Filings'},  # Customize legend label
    ax=ax,                     # Plot on the specified axis
    edgecolor='black'          # Add black borders to polygons
)

# Add a title
ax.set_title("Filings per 100k by County", fontsize=16)

# Remove axis for a cleaner map
ax.axis('off')

# Show the plot
plt.show()