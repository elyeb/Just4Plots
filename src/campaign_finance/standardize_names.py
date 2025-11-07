"""
Key variables
pdc_raw:
filer_name is candidate name. Include both individual and PACs
for_or_against is whether the donation was for or against the candidate
contributor_name is donor name
amount
contributor_address
contributor_city 
contributor_state
contributor_zip 
contributor_occupation
contributor_location
contributor_employer_name
contributor_employer_city
contributor_employer_state
"""

import pandas as pd
from sodapy import Socrata
import os
import datetime

TODAY = datetime.date.today()
TODAY_STR = TODAY.strftime('%Y-%m-%d')
YEAR = 2025

DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/pdc_downloads/"
)

pdc_contributions_file = os.path.join(DATA_FOLDER, f"pdc_contributions_{YEAR}_{TODAY_STR}.csv")
ind_exp_output_file = os.path.join(DATA_FOLDER, "pdc_ind_exp_{YEAR}_{TODAY_STR}.csv")

pdc_raw = pd.read_csv(pdc_contributions_file)
ind_exp_raw = pd.read_csv(ind_exp_output_file)