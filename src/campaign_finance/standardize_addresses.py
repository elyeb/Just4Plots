"""
Make cleaned column of addresses for donation data and extract coordinates
for mapping.
"""
import pandas as pd
import geopandas as gpd
import os
import re
from geopy.geocoders import Nominatim # used to look up coordinates
from geopy.extra.rate_limiter import RateLimiter

# Load data ##########################################################################
DATA_FOLDER =  os.path.join(os.path.dirname(__file__), '../../data/lobbying/pdc_downloads/')
PDC_FILE_NAME = "pdc_contributions_2025_2025-11-05_name_cleaned.csv"
PDC_OUTFILE_NAME = PDC_FILE_NAME.replace(".csv", "_lat_long.csv")

pdc = pd.read_csv(os.path.join(DATA_FOLDER, PDC_FILE_NAME))

######################################################################################

# Explore data #######################################################################

pdc[~pdc['contributor_address'].isna()][['contributor_address', 'contributor_city', 'contributor_state',
       'contributor_zip', 'contributor_location']].head()


pdc[~pdc['contributor_location'].isna()]['contributor_location'].nunique()

# how many addresses just don't have coordinates? about half
len(pdc[pdc['contributor_location'].isna()&~pdc['contributor_address'].isna()])

# get examples
target_addresses =pdc[pdc['contributor_location'].isna()&~pdc['contributor_address'].isna()][['contributor_address']]
[a for a in target_addresses['contributor_address'].unique()]
def extract_lat_from_coord(coord_str):
    if pd.isna(coord_str):
        return None
    coord_str= "{'type': 'Point', 'coordinates': [-122.798349, 48.109438]}"
    # get portion within brackets
    match = re.findall(r"\[([-.\d]+),\s*([-.\d]+)\]", coord_str)
    match = match[0]
    lat = match[0]
    return float(lat)

def extract_long_from_coord(coord_str):
    if pd.isna(coord_str):
        return None
    coord_str= "{'type': 'Point', 'coordinates': [-122.798349, 48.109438]}"
    # get portion within brackets
    match = re.findall(r"\[([-.\d]+),\s*([-.\d]+)\]", coord_str)
    match = match[0]
    long = match[1]
    return float(long)

pdc["Latitude"] = pdc['contributor_location'].apply(extract_lat_from_coord)
pdc["Longitude"] = pdc['contributor_location'].apply(extract_long_from_coord)

######################################################################################

# Define functions ###################################################################


def clean_address(str_address, city, state, zip) -> str:
    """
    Function to return single most likely address from the site address column. 

    Rules:
    no PO BOX
    everything capitalized
    cut everything off Ste [no], Suite 
    cut everything off after # [no]
    cut everything off after Apt [no], Apartment 
    cut everything off after Unit [no]
    Ln to LANE
    Ave. to AVENUE
    Blvd to BOULEVARD
    Rd to ROAD
    DR to DRIVE
    PL to PLACE
    CT to COURT
    Pkwy to PARKWAY
    trim address
    concat pieces together
    make zip integer

    Returns:
        address_clean: a cleaned, single address
    """

    if pd.isna(str_address):
        return None

    ## Rules
    # no PO BOX
    address = str_address.upper()
    if 'PO BOX' in address:
        return None
    # everything capitalized
    address = address.upper()
    # cut everything off Ste [no], Suite 
    address = re.sub('STE.*$','',address)
    address = re.sub('SUITE.*$','',address)
    # cut everything off after # [no]
    address = re.sub('#.*$','',address)
    # cut everything off after Apt [no], Apartment 
    address = re.sub('APT.*$','',address)
    address = re.sub('APARTMENT.*$','',address)
    # cut everything off after NO. [no], NUMBER
    address = re.sub('NO\..*$','',address)
    address = re.sub('NUMBER.*$','',address)
    # cut everything off after Unit [no]
    address = re.sub('UNIT.*$','',address)
    # Ln to LANE
    address = re.sub(' LN',' LANE',address)
    # Ave. to AVENUE. Dont make AVENUENUE 
    address = re.sub(' AVE\.',' AVENUE',address)
    address = re.sub(' AVE$',' AVENUE',address)
    address = re.sub(' AVE ',' AVENUE ',address)
    # Blvd to BOULEVARD
    address = re.sub(' BLVD',' BOULEVARD',address)
    # Rd to ROAD
    address = re.sub(' RD',' ROAD',address)
    # DR to DRIVE
    address = re.sub(' DR',' DRIVE',address)
    # PL to PLACE
    address = re.sub(' PL',' PLACE',address)
    # CT to COURT
    address = re.sub(' CT$',' COURT',address)
    address = re.sub(' CT ',' COURT ',address)
    # Pkwy to PARKWAY
    address = re.sub(' PKWY',' PARKWAY',address)
    # trim address, white space, trailing commas, extra spaces between words 
    address = address.strip()
    address = re.sub(',$','',address)
    address = re.sub('\s+',' ',address)
    if len(address)==0:
        print("empty address after cleaning:", str_address)
        return None
    # concat pieces together, make zip integer
    full_address = address
    try:
        full_address +=', '+city.upper()
    except:
        pass
    try:
        full_address+=', '+state.upper()
    except:
        pass
    try:
        full_address+=', '+str(int(zip))
    except:
        pass
    return full_address

        
######################################################################################


# Apply functions ####################################################################
pdc['cleaned_address'] = pdc.apply(lambda row: clean_address(row['contributor_address'],
                                                             row['contributor_city'],
                                                            row['contributor_state'],
                                                            row['contributor_zip']), axis=1)



# initialize Nominatim
geolocator = Nominatim(user_agent="test_app")

# borrow code from https://geopy.readthedocs.io/en/stable/#usage-with-pandas
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
pdc['coordinates'] = pdc['cleaned_address'].apply(geocode)

# extract lat/lon/point 
pdc['point']     = pdc['coordinates'].apply(lambda loc: tuple(loc.point) if loc else None)
pdc['Latitude']  = pdc['coordinates'].apply(lambda loc: loc.latitude if loc else None)
pdc['Longitude'] = pdc['coordinates'].apply(lambda loc: loc.longitude if loc else None)