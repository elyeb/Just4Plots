import pandas as pd
from sodapy import Socrata
import os
import datetime

TODAY = datetime.date.today()
TODAY_STR = TODAY.strftime("%Y-%m-%d")
YEAR = 2025

client = Socrata("data.wa.gov", None)

DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/pdc_downloads/"
)

os.makedirs(os.path.dirname(DATA_FOLDER), exist_ok=True, mode=0o777)


## Fetch all campaign contributions for the election year 2025
all_results = []
limit = 50000  # Use a smaller limit to avoid backend issues
offset = 0

while True:
    results = client.get(
        "kv7h-kjye",
        where="election_year=2025",
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

# Save to CSV
output_file = os.path.join(DATA_FOLDER, f"pdc_contributions_{YEAR}_{TODAY_STR}.csv")
results_df.to_csv(output_file, index=False)


## Fetch all independent expenditures for the election year
all_historic = []
for year in range(2008, 2025):
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
        DATA_FOLDER, f"pdc_ind_exp_{YEAR}_{TODAY_STR}.csv"
    )
    ind_exp_results_df.to_csv(ind_exp_output_file, index=False)

    all_historic.append(ind_exp_results_df)

# Combine all years into a single DataFrame
combined_ind_exp_df = pd.concat(all_historic, ignore_index=True)
# Save combined DataFrame to CSV
combined_output_file = os.path.join(
    DATA_FOLDER, f"pdc_ind_exp_all_time_{TODAY_STR}.csv"
)
combined_ind_exp_df.to_csv(combined_output_file, index=False)
