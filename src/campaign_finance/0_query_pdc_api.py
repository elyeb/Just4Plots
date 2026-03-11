import pandas as pd
from sodapy import Socrata
import os
import datetime

TODAY = datetime.date.today()
TODAY_STR = TODAY.strftime("%Y-%m-%d")
YEAR_START = 2024
YEAR_END = 2026
years = list(range(YEAR_START, YEAR_END + 1))

client = Socrata("data.wa.gov", None)

DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/pdc_downloads/"
)
CLEAN_DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/intermediate_processing/"
)

os.makedirs(os.path.dirname(DATA_FOLDER), exist_ok=True, mode=0o777)

# First archive existing files that end with csv in the data folder
for filename in os.listdir(DATA_FOLDER):
    if filename.endswith(".csv"):

        os.rename(
            os.path.join(DATA_FOLDER, filename),
            os.path.join(DATA_FOLDER, "ARCHIVE/", filename),
        )

# read in previous cleaned files:
prev_contributions = pd.read_csv(
    os.path.join(CLEAN_DATA_FOLDER, "pdc_contributions_cleaned_lat_long.csv")
)

prev_ies = pd.read_csv(
    os.path.join(CLEAN_DATA_FOLDER, "pdc_ind_exp_cleaned_lat_long.csv")
)

## Fetch all campaign contributions for the election year 2025
all_results = []
limit = 50000  # Use a smaller limit to avoid backend issues
offset = 0

for year in years:
    print(f"Fetching campaign contributions for the year {year}...")
    offset = 0
    while True:
        results = client.get(
            "kv7h-kjye",
            where=f"election_year={year}",
            order="receipt_date DESC",
            limit=limit,
            offset=offset,
        )
        if not results:
            break
        all_results.extend(results)
        print(f"Fetched {len(results)} rows at offset {offset}")
        if len(results) < limit:
            break  # Last page reached
        offset += limit

# Convert to DataFrame
results_df = pd.DataFrame.from_records(all_results)
print(f"Total rows fetched: {len(results_df)}")

prev_contributions["matched_address"].head()

# avoid saving previously-processed data
for col in [
    "id",
    "report_number",
    "committee_id",
    "election_year",
    "fund_id",
    "filer_id",
]:
    prev_contributions[col] = prev_contributions[col].astype(int)
    results_df[col] = results_df[col].astype(int)
for col in ["amount"]:
    prev_contributions[col] = prev_contributions[col].astype(float)
    results_df[col] = results_df[col].astype(float)


results_df = results_df.merge(
    prev_contributions[
        [
            "id",
            "report_number",
            "origin",
            "committee_id",
            "contributor_address",
            "filer_id",
            "matched_address",
        ]
    ],
    on=[
        "id",
        "report_number",
        "origin",
        "committee_id",
        "contributor_address",
        "filer_id",
    ],
    how="left",
)

rows_with_matches = len(results_df[results_df["matched_address"].notna()])
print(f"Rows with previous matches: {rows_with_matches}")

# remove previous matches, as address-matching is time-intensive
results_df = results_df[results_df["matched_address"].isna()].drop(
    columns=["matched_address"]
)

# Save to CSV
output_file = os.path.join(DATA_FOLDER, f"pdc_contributions_new.csv")
results_df.to_csv(output_file, index=False)


## Fetch all independent expenditures for the election year
all_historic = []
for year in years:
    print(f"Fetching independent expenditures for the year {year}...")
    all_results = []
    limit = 50000  # Use a smaller limit to avoid backend issues
    offset = 0

    while True:
        results = client.get(
            "67cp-h962",
            where=f"election_year={year}",
            order="report_date DESC",
            limit=limit,
            offset=offset,
        )
        if not results:
            break
        all_results.extend(results)
        print(f"Fetched {len(results)} rows at offset {offset}")
        if len(results) < limit:
            break  # Last page reached
        offset += limit

    # Convert to DataFrame
    ind_exp_results_df = pd.DataFrame.from_records(all_results)
    print(f"Total rows fetched: {len(ind_exp_results_df)}")

    # Save to CSV
    ind_exp_output_file = os.path.join(
        DATA_FOLDER, f"pdc_ind_exp_{year}_{TODAY_STR}.csv"
    )
    # ind_exp_results_df.to_csv(ind_exp_output_file, index=False)

    all_historic.append(ind_exp_results_df)

# Combine all years into a single DataFrame
combined_ind_exp_df = pd.concat(all_historic, ignore_index=True)

# Remove previously matched rows
# avoid saving previously-processed data
for col in [
    "report_number",
    "sponsor_id",
    "election_year",
]:
    prev_ies[col] = prev_ies[col].astype(int)
    combined_ind_exp_df[col] = combined_ind_exp_df[col].astype(int)

combined_ind_exp_df = combined_ind_exp_df.merge(
    prev_ies[
        [
            "id",
            "report_number",
            "sponsor_id",
            "election_year",
            "sponsor_address",
            "matched_address",
        ]
    ],
    on=["id", "report_number", "sponsor_id", "election_year", "sponsor_address"],
    how="left",
)

rows_with_matches = len(
    combined_ind_exp_df[combined_ind_exp_df["matched_address"].notna()]
)
print(f"Rows with previous matches: {rows_with_matches}")

combined_ind_exp_df = combined_ind_exp_df[
    combined_ind_exp_df["matched_address"].notna()
]

combined_ind_exp_df.drop(columns=["matched_address"], inplace=True)

# Save combined DataFrame to CSV
combined_output_file = os.path.join(DATA_FOLDER, f"pdc_ind_exp_new.csv")
combined_ind_exp_df.to_csv(combined_output_file, index=False)
