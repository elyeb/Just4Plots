"""
Make cleaned column of addresses for donation data and extract coordinates
for mapping.

TODO:
- what addresses are getting dropped while using Census mapper?
"""

import csv
import pandas as pd
import geopandas as gpd
import os
import re
import requests
import datetime
import math
import shutil
from pathlib import Path
from typing import List

TODAY = datetime.date.today()
TODAY_STR = TODAY.strftime("%Y-%m-%d")

# Load data ##########################################################################
DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/pdc_downloads/"
)
CENSUS_UPLOADS = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/census_uploads/"
)

PDC_FILE_NAME = "pdc_contributions_2025_2026-01-02.csv"
IE_FILE_NAME = "pdc_ind_exp_all_time_2026-01-02.csv"

OUTPUT_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/intermediate_processing/"
)

PDC_OUTFILE_NAME = PDC_FILE_NAME.replace(".csv", "_cleaned_lat_long.csv")
IE_OUTFILE_NAME = IE_FILE_NAME.replace(".csv", "_cleaned_lat_long.csv")

os.makedirs(CENSUS_UPLOADS, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# delete contents of upload folder
directory = Path(CENSUS_UPLOADS)

for item in directory.iterdir():
    if item.is_dir():
        shutil.rmtree(item)
    else:
        item.unlink()

pdc = pd.read_csv(os.path.join(DATA_FOLDER, PDC_FILE_NAME))
ie = pd.read_csv(os.path.join(DATA_FOLDER, IE_FILE_NAME))
######################################################################################

# Explore data #######################################################################

pdc[~pdc["contributor_address"].isna()][
    [
        "contributor_address",
        "contributor_city",
        "contributor_state",
        "contributor_zip",
        "contributor_location",
    ]
].head()


pdc[~pdc["contributor_location"].isna()]["contributor_location"].nunique()

# how many addresses just don't have coordinates? about half
len(pdc[pdc["contributor_location"].isna() & ~pdc["contributor_address"].isna()])

# get examples
target_addresses = pdc[
    pdc["contributor_location"].isna() & ~pdc["contributor_address"].isna()
][["contributor_address"]]
[a for a in target_addresses["contributor_address"].unique()]


######################################################################################

# Define functions ###################################################################


def extract_lat_from_coord(coord_str):
    if pd.isna(coord_str):
        return None
    coord_str = "{'type': 'Point', 'coordinates': [-122.798349, 48.109438]}"
    # get portion within brackets
    match = re.findall(r"\[([-.\d]+),\s*([-.\d]+)\]", coord_str)
    match = match[0]
    lat = match[1]
    return float(lat)


def extract_long_from_coord(coord_str):
    if pd.isna(coord_str):
        return None
    coord_str = "{'type': 'Point', 'coordinates': [-122.798349, 48.109438]}"
    # get portion within brackets
    match = re.findall(r"\[([-.\d]+),\s*([-.\d]+)\]", coord_str)
    match = match[0]
    long = match[0]
    return float(long)


def clean_url(url_str):
    if pd.isna(url_str):
        return None
    match = re.search(r"'(https?://[^']+)'", url_str)
    if match:
        return match.group(1)
    return None


# , city, state, zip
def clean_address(str_address) -> str:
    """
    Function to return single most likely address from the site address column.

    Rules:
    no PO BOX
    everything capitalized
    cut everything off Ste [no], Suite
    cut everything off after # [no]
    cut everything off after Apt [no], Apartment
    cut everything off after Unit [no]
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
    if ("PO BOX" in address) or ("P.O. BOX" in address) or ("P O BOX" in address):
        return None
    # everything capitalized
    address = address.upper()
    # cut everything off Ste [no], Suite
    address = re.sub("STE.*$", "", address)
    address = re.sub("SUITE.*$", "", address)
    # cut everything off after # [no]
    address = re.sub("#.*$", "", address)
    # cut everything off after Apt [no], Apartment
    address = re.sub("APT.*$", "", address)
    address = re.sub("APARTMENT.*$", "", address)
    # cut everything off after NO. [no], NUMBER
    address = re.sub("NO\..*$", "", address)
    address = re.sub("NUMBER.*$", "", address)
    # cut everything off after Unit [no]
    address = re.sub("UNIT.*$", "", address)
    # Ave. to AVENUE. Dont make AVENUENUE
    address = re.sub(" AVE\.", " AVENUE", address)
    address = re.sub(" AVE$", " AVENUE", address)
    address = re.sub(" AVE ", " AVENUE ", address)
    # Blvd to BOULEVARD
    address = re.sub(" BLVD", " BOULEVARD", address)
    # Rd to ROAD
    address = re.sub(" RD", " ROAD", address)
    # DR to DRIVE
    address = re.sub(" DR", " DRIVE", address)
    # PL to PLACE
    address = re.sub(" PL", " PLACE", address)
    # CT to COURT
    address = re.sub(" CT$", " COURT", address)
    address = re.sub(" CT ", " COURT ", address)
    # Pkwy to PARKWAY
    address = re.sub(" PKWY", " PARKWAY", address)
    # trim address, white space, trailing commas, extra spaces between words
    address = address.strip()
    address = re.sub(",$", "", address)
    address = re.sub("\s+", " ", address)

    if len(address) == 0:
        print("empty address after cleaning:", str_address)
        return None
    return address


def census_geocode(address):
    # use for single address geocode only, not batch
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {"address": address, "benchmark": "Public_AR_Census2020", "format": "json"}
    r = requests.get(url, params=params).json()
    try:
        coords = r["result"]["addressMatches"][0]["coordinates"]
        return coords["y"], coords["x"]
    except:
        return None, None


def read_census_output(file) -> pd.DataFrame:

    file_df = pd.DataFrame()
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace("\n", "")
            line = re.sub('^"', "", line)
            line = re.sub('"$', "", line)
            line = line.replace('","', ":").split(":")
            if line[1] == "ADDRESS":
                line = line[:1] + line[2:]  # some strange rows
            file_df = pd.concat([file_df, pd.DataFrame([line])], ignore_index=True)
    file_df.columns = [
        "id",
        "input_address",
        "match_status",
        "match_exactness",
        "matched_address",
        "coordinates",
        "tiger_line_id",
        "side",
    ]
    return file_df


######################################################################################

# CONTRIBUTOR DATA ######################################################################

# Prep uploads #######################################################################

# Clean address - perform on full pdc first to make it mergable later
pdc["cleaned_address"] = pdc["contributor_address"].apply(clean_address)
pdc["contributor_address"] = pdc["contributor_address"].str.replace(
    ",", "", regex=False
)
pdc["contributor_address"] = pdc["contributor_address"].str.replace(
    '"', "", regex=False
)
pdc["contributor_address"] = pdc["contributor_address"].str.replace(
    ",", "", regex=False
)
pdc["contributor_address"] = (
    pdc["contributor_address"]
    .str.strip()
    .str.replace(r"[\u200b\xa0\r]", "", regex=True)
)

# only use time to apply geocode to addresses that are not none
pdc_not_none = pdc[~pdc["cleaned_address"].isna()]

# Create df of unique addresses to geocode
# addresses_df = pd.DataFrame(pdc_not_none['cleaned_address'].unique(), columns=['cleaned_address'])
addresses_df = (
    pdc_not_none[
        ["cleaned_address", "contributor_city", "contributor_state", "contributor_zip"]
    ]
    .drop_duplicates()
    .reset_index()
    .rename(columns={"index": "id"})
)

upload_df = addresses_df[
    [
        "id",
        "cleaned_address",
        "contributor_city",
        "contributor_state",
        "contributor_zip",
    ]
]

# Clean State
upload_df["contributor_state"] = upload_df["contributor_state"].apply(
    lambda x: str(x).upper()
)
upload_df["contributor_state"] = upload_df["contributor_state"].str.strip()
upload_df["state_len"] = upload_df["contributor_state"].apply(lambda x: len(x))
upload_df = upload_df[upload_df["state_len"] == 2]
upload_df = upload_df.drop(columns=["state_len"])

# Clean Zip
upload_df["contributor_zip"] = (
    upload_df["contributor_zip"]
    .fillna("")  # replace NaN
    .astype(str)  # ensure string
    .str.strip()  # just in case
    .str.replace(r"\.0$", "", regex=True)  # remove trailing .0
)

upload_df["contributor_zip_len"] = upload_df["contributor_zip"].apply(lambda x: len(x))
upload_df = upload_df[upload_df["contributor_zip_len"] == 5]
upload_df = upload_df.drop(columns=["contributor_zip_len"])

# remove any single/double quotations from all fields, as well as commas
for col in [
    "contributor_city",
    "contributor_state",
    "contributor_zip",
]:
    upload_df["contributor_city"] = upload_df["contributor_city"].str.replace(
        "\\", "", regex=False
    )
    upload_df[col] = upload_df[col].str.replace("'", "", regex=False)
    upload_df[col] = upload_df[col].str.replace('"', "", regex=False)
    upload_df[col] = upload_df[col].str.replace(",", "", regex=False)
    upload_df[col] = (
        upload_df[col].str.strip().str.replace(r"[\u200b\xa0\r]", "", regex=True)
    )

# any missing values
upload_df = upload_df.dropna()
######################################################################################

# Upload, download results and merge #################################################

# ---- split into chunks of 100 ----
CHUNK_SIZE = 100
num_chunks = math.ceil(len(upload_df) / CHUNK_SIZE)

upload_files = []
result_files = []

for i in range(num_chunks):
    chunk = upload_df.iloc[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]

    # Save chunk to file
    upload_file = f"{CENSUS_UPLOADS}census_upload_{TODAY_STR}_{i}.csv"
    chunk.to_csv(upload_file, index=False, header=False, sep=",", encoding="utf-8")

    upload_files.append(upload_file)

    # Send to Census API
    with open(upload_file, "rb") as f:
        files = {"addressFile": f, "benchmark": (None, "Public_AR_Census2020")}
        r = requests.post(
            "https://geocoding.geo.census.gov/geocoder/locations/addressbatch",
            files=files,
        )

    # Save result
    result_file = f"{CENSUS_UPLOADS}census_results_{TODAY_STR}_{i}.csv"
    with open(result_file, "wb") as f:
        f.write(r.content)
    result_files.append(result_file)

    returned = sum(1 for _ in open(result_file))
    expected = len(chunk)
    if returned != expected:
        print(f"Batch {i}: expected {expected}, got {returned}")

# combine results
results_df = pd.DataFrame(
    columns=[
        "id",
        "input_address",
        "match_status",
        "match_exactness",
        "matched_address",
        "coordinates",
        "tiger_line_id",
        "side",
    ]
)
for file in result_files:
    try:
        file_df = read_census_output(file)
        results_df = pd.concat([results_df, file_df], ignore_index=True)
    except Exception as e:
        print(f"Error reading {file}: {e}")

print(f"Original addresses sent: {len(upload_df)}")
print(f"Rows returned: {len(results_df)}")


# ---- merge results back to pdc ----
results_df["Latitude"] = results_df["coordinates"].apply(
    lambda x: float(x.split(",")[1].strip()) if pd.notna(x) else None
)
results_df["Longitude"] = results_df["coordinates"].apply(
    lambda x: float(x.split(",")[0].strip()) if pd.notna(x) else None
)

results_df = results_df[results_df["Latitude"].notna()]
print(f"Addresses with coordinates: {len(results_df)}")


results_df.rename(
    columns={"input_address": "cleaned_full_address", "id": "row_num"}, inplace=True
)
results_df.drop(columns=["tiger_line_id", "side"], inplace=True)
results_df[["Latitude", "Longitude"]] = results_df[["Latitude", "Longitude"]].astype(
    float
)
results_df["row_num"] = results_df["row_num"].astype(int)
merged_pdc = pd.merge(pdc, results_df, left_index=True, right_on="row_num", how="left")

######################################################################################


# Save output ########################################################################


merged_pdc["url"] = merged_pdc["url"].apply(lambda x: clean_url(x))
merged_pdc["contributor_longitude_given"] = merged_pdc["contributor_location"].apply(
    extract_long_from_coord
)
merged_pdc["contributor_latitude_given"] = merged_pdc["contributor_location"].apply(
    extract_lat_from_coord
)
merged_pdc.drop(columns=["contributor_location"], inplace=True)
merged_pdc.drop(columns=["coordinates"], inplace=True)
text_cols = merged_pdc.select_dtypes(include=["object"]).columns
for col in text_cols:
    merged_pdc[col] = (
        merged_pdc[col]
        .astype(str)
        .str.replace('"', "")
        .str.replace("\n", " ")
        .str.replace("\r", " ")
        # .str.replace(",", " ")
    )

# add index column
merged_pdc["row_num_index"] = range(len(merged_pdc))

merged_pdc.to_csv(
    os.path.join(OUTPUT_FOLDER, PDC_OUTFILE_NAME),
    index=False,
    sep=",",
    quotechar='"',
    quoting=csv.QUOTE_ALL,  # quotes text columns only
    lineterminator="\n",  # avoids \r\n issues on Windows
    encoding="utf-8",
)

test_df = pd.read_csv(os.path.join(OUTPUT_FOLDER, PDC_OUTFILE_NAME))
test_df.head()
######################################################################################


# IE DATA ############################################################################

# Prep uploads #######################################################################

# Clean address - perform on full ie first to make it mergable later
ie["cleaned_address"] = ie["sponsor_address"].apply(clean_address)
ie["sponsor_address"] = ie["sponsor_address"].str.replace(",", "", regex=False)
ie["sponsor_address"] = ie["sponsor_address"].str.replace('"', "", regex=False)
ie["sponsor_address"] = ie["sponsor_address"].str.replace(",", "", regex=False)
ie["sponsor_address"] = (
    ie["sponsor_address"].str.strip().str.replace(r"[\u200b\xa0\r]", "", regex=True)
)

# only use time to apply geocode to addresses that are not none
ie_not_none = ie[~ie["cleaned_address"].isna()]

# Create df of unique addresses to geocode
# addresses_df = pd.DataFrame(ie_not_none['cleaned_address'].unique(), columns=['cleaned_address'])
addresses_df = (
    ie_not_none[["cleaned_address", "sponsor_city", "sponsor_state", "sponsor_zip"]]
    .drop_duplicates()
    .reset_index()
    .rename(columns={"index": "id"})
)

upload_df = addresses_df[
    [
        "id",
        "cleaned_address",
        "sponsor_city",
        "sponsor_state",
        "sponsor_zip",
    ]
]

# Clean State
upload_df["sponsor_state"] = upload_df["sponsor_state"].apply(lambda x: str(x).upper())
upload_df["sponsor_state"] = upload_df["sponsor_state"].str.strip()
upload_df["state_len"] = upload_df["sponsor_state"].apply(lambda x: len(x))
upload_df = upload_df[upload_df["state_len"] == 2]
upload_df = upload_df.drop(columns=["state_len"])

# Clean Zip
upload_df["sponsor_zip"] = (
    upload_df["sponsor_zip"]
    .fillna("")  # replace NaN
    .astype(str)  # ensure string
    .str.strip()  # just in case
    .str.replace(r"\.0$", "", regex=True)  # remove trailing .0
)

upload_df["sponsor_zip_len"] = upload_df["sponsor_zip"].apply(lambda x: len(x))
upload_df = upload_df[upload_df["sponsor_zip_len"] == 5]
upload_df = upload_df.drop(columns=["sponsor_zip_len"])

# remove any single/double quotations from all fields, as well as commas
for col in [
    "sponsor_city",
    "sponsor_state",
    "sponsor_zip",
]:
    upload_df["sponsor_city"] = upload_df["sponsor_city"].str.replace(
        "\\", "", regex=False
    )
    upload_df[col] = upload_df[col].str.replace("'", "", regex=False)
    upload_df[col] = upload_df[col].str.replace('"', "", regex=False)
    upload_df[col] = upload_df[col].str.replace(",", "", regex=False)
    upload_df[col] = (
        upload_df[col].str.strip().str.replace(r"[\u200b\xa0\r]", "", regex=True)
    )

# any missing values
upload_df = upload_df.dropna()
######################################################################################

# Upload, download results and merge #################################################

# ---- split into chunks of 100 ----
CHUNK_SIZE = 100
num_chunks = math.ceil(len(upload_df) / CHUNK_SIZE)

upload_files = []
result_files = []

for i in range(num_chunks):
    chunk = upload_df.iloc[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]

    # Save chunk to file
    upload_file = f"{CENSUS_UPLOADS}census_upload_{TODAY_STR}_{i}.csv"
    chunk.to_csv(upload_file, index=False, header=False, sep=",", encoding="utf-8")

    upload_files.append(upload_file)

    # Send to Census API
    with open(upload_file, "rb") as f:
        files = {"addressFile": f, "benchmark": (None, "Public_AR_Census2020")}
        r = requests.post(
            "https://geocoding.geo.census.gov/geocoder/locations/addressbatch",
            files=files,
        )

    # Save result
    result_file = f"{CENSUS_UPLOADS}census_results_{TODAY_STR}_{i}.csv"
    with open(result_file, "wb") as f:
        f.write(r.content)
    result_files.append(result_file)

    returned = sum(1 for _ in open(result_file))
    expected = len(chunk)
    if returned != expected:
        print(f"Batch {i}: expected {expected}, got {returned}")

# combine results
results_df = pd.DataFrame(
    columns=[
        "id",
        "input_address",
        "match_status",
        "match_exactness",
        "matched_address",
        "coordinates",
        "tiger_line_id",
        "side",
    ]
)
for file in result_files:
    try:
        file_df = read_census_output(file)
        results_df = pd.concat([results_df, file_df], ignore_index=True)
    except Exception as e:
        print(f"Error reading {file}: {e}")

print(f"Original addresses sent: {len(upload_df)}")
print(f"Rows returned: {len(results_df)}")


# ---- merge results back to ie ----
results_df["Latitude"] = results_df["coordinates"].apply(
    lambda x: float(x.split(",")[1].strip()) if pd.notna(x) else None
)
results_df["Longitude"] = results_df["coordinates"].apply(
    lambda x: float(x.split(",")[0].strip()) if pd.notna(x) else None
)

results_df = results_df[results_df["Latitude"].notna()]
print(f"Addresses with coordinates: {len(results_df)}")


results_df.rename(
    columns={"input_address": "cleaned_full_address", "id": "row_num"}, inplace=True
)
results_df.drop(columns=["tiger_line_id", "side"], inplace=True)
results_df[["Latitude", "Longitude"]] = results_df[["Latitude", "Longitude"]].astype(
    float
)
results_df["row_num"] = results_df["row_num"].astype(int)
merged_ie = pd.merge(ie, results_df, left_index=True, right_on="row_num", how="left")

######################################################################################


# Save output ########################################################################


merged_ie["url"] = merged_ie["url"].apply(lambda x: clean_url(x))
merged_ie["sponsor_longitude_given"] = merged_ie["sponsor_location"].apply(
    extract_long_from_coord
)
merged_ie["sponsor_latitude_given"] = merged_ie["sponsor_location"].apply(
    extract_lat_from_coord
)
merged_ie.drop(columns=["sponsor_location"], inplace=True)
merged_ie.drop(columns=["coordinates"], inplace=True)
text_cols = merged_ie.select_dtypes(include=["object"]).columns
for col in text_cols:
    merged_ie[col] = (
        merged_ie[col]
        .astype(str)
        .str.replace('"', "")
        .str.replace("\n", " ")
        .str.replace("\r", " ")
        # .str.replace(",", " ")
    )

# add index column
merged_ie["row_num_index"] = range(len(merged_ie))

merged_ie.to_csv(
    os.path.join(OUTPUT_FOLDER, IE_OUTFILE_NAME),
    index=False,
    sep=",",
    quotechar='"',
    quoting=csv.QUOTE_ALL,  # quotes text columns only
    lineterminator="\n",  # avoids \r\n issues on Windows
    encoding="utf-8",
)


######################################################################################
