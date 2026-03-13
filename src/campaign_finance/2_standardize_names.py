"""
Key variables
pdc_raw:
filer_name is candidate name. Include both individual and PACs
for_or_against is whether the donation was for or against the candidate
contributor_name is donor name

"""

import pandas as pd
import os
import datetime

DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/intermediate_processing/"
)

PDC_FILE_NAME = "pdc_contributions_cleaned_lat_long.csv"
IE_FILE_NAME = "pdc_ind_exp_cleaned_lat_long.csv"

contr_df = pd.read_csv(os.path.join(DATA_FOLDER, PDC_FILE_NAME))
ind_df = pd.read_csv(os.path.join(DATA_FOLDER, IE_FILE_NAME))

len(ind_df["sponsor_name"].unique())
len(ind_df["sponsor_id"].unique())


# Standardize PAC sponsor names ##############################################

# Define/update maps
replace_map_sponsors = {
    "DEMOCRATIC WOODINVILLE SPONSORED BY JEFFREY LYON": "DEMOCRATIC WOODINVILLE SPONSORED BY JEFF LYON",
    "NEW DIRECTION PAC.": "NEW DIRECTION PAC",
    "CHILDREN'S CAMPAIGN FUND": "CHILDRENS CAMPAIGN FUND",
    "CONCERNED TAXPAYER ACCOUNTABILITY CENTER": "CONCERNED TAXPAYERS ACCOUNTABILITY CENTER",
    "EASTSIDE PROGRESS PAC": "EASTSIDE PROGRESS",
    "ENERGIZE WA PAC": "ENERGIZE WASHINGTON",
    "EQUAL RIGHTS WA PAC": "EQUAL RIGHT WASHINGTON PAC",
    "MAINSTREAM REPUB OF WA": "MAINSTREAM REPUBLICANS OF WA",
    "MASTER BUILDERS ASSN OF KING & SNOHOMISH CO AFFORDABLE HOUSING COUNCIL": "MASTER BUILDERS ASSC OF KING & SNO COUNTIES - AFFORDABLE HOUSING COUNCIL",
    "MASTER BUILDERS ASSN OF KING & SNOHOMISH COUNTIES": "MASTER BUILDERS ASSC OF KING & SNO COUNTIES - AFFORDABLE HOUSING COUNCIL",
    "NATIONAL ASSN OF REALTORS FUND": "NATIONAL ASSOCIATION OF REALTORS FUND",
    "NATIONAL ASSOC. OF REALTORS FUND": "NATIONAL ASSOCIATION OF REALTORS FUND",
    "NATL ASSOCIATION OF REALTORS FUND": "NATIONAL ASSOCIATION OF REALTORS FUND",
    "NATIONAL ASSOCIATION OF REALTORS": "NATIONAL ASSOCIATION OF REALTORS FUND",
    "PLANNED PARENTHOOD VOTES WASHINGTON PAC": "PLANNED PARENTHOOD VOTES! WASHINGTON",
    "REPUBLICAN STATE LEADERSHIP COMMITTEE -WASHINGTON PAC (RSLC-WASHINGTON PAC)": "REPUBLICAN STATE LEADERSHIP COMMITTEE -WASHINGTON",
    "STAND FOR CHILDREN WASHINGTON PAC": "STAND FOR CHILDREN WA PAC",
    "THE AFFORDABLE HOUSING COUNCIL OF THE OLYMPIA MASTER BUILDERS": "THE AFFORDABLE HOUSING COUNCIL OF OLYMPIA MASTER BUILDERS",
    "WA ST COUNCIL OF CO & CITY EMPLOYEES": "WA ST COUNCIL OF COUNTY & CITY EMPLOYEES",
    "WASHINGTON STATE DENTAL PAC": "WASHINGTON STATE DENTAL POLITICAL ACTION COMMITTEE",
    "WORKING WASHINGTON PAC": "WORKING WASHINGTON",
    "WASHINGTON ASSOCIATION OF REALTORS®": "WASHINGTON REALTORS POLITICAL ACTION COMMITTEE",
    "FUSE VOTERS": "FUSE VOTES",
    "SERVICE EMPLOYEES INTERNATIONAL UNION 775 QUALITY CARE COMMITTEE": "SEIU 775 QUALITY CARE COMMITTEE",
}

replace_map_filer = {
    "HARRELL BRUCE A (BRUCE HARRELL)": "BRUCE HARRELL",
    "BRUCE A. HARRELL (BRUCE HARRELL)": "BRUCE HARRELL",
    "KATHERINE BARRETT WILSON (KATIE WILSON)": "KATIE WILSON",
}

replace_map_candidate = {
    "AL FRENCH": "ALFRED AL FRENCH",
    "T. PLESE  KIM": "KIM T. PLESE",
    "NADINE NADINE MARIE WOODWARD": "MARIE WOODWARD NADINE NADINE",
}

# Clean name fields and apply maps ##############################################

# Trim important fields names
ind_df["sponsor_name"] = ind_df["sponsor_name"].str.strip()
ind_df["candidate_name"] = ind_df["candidate_name"].str.strip().str.upper()
ind_df["candidate_office"] = ind_df["candidate_office"].str.strip().str.upper()
ind_df["candidate_jurisdiction"] = (
    ind_df["candidate_jurisdiction"].str.strip().str.upper()
)
contr_df["filer_name"] = contr_df["filer_name"].str.strip().str.upper()
contr_df["contributor_name"] = contr_df["contributor_name"].str.strip().str.upper()


# Apply maps
contr_df["filer_name"] = contr_df["filer_name"].replace(replace_map_filer)
ind_df["sponsor_name"] = ind_df["sponsor_name"].replace(replace_map_sponsors)
ind_df["candidate_name"] = ind_df["candidate_name"].replace(replace_map_candidate)


# save output #####################################################################

contr_df.to_csv(os.path.join(DATA_FOLDER, PDC_FILE_NAME), index=False)
ind_df.to_csv(os.path.join(DATA_FOLDER, IE_FILE_NAME), index=False)
