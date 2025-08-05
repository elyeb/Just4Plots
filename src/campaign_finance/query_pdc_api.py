import pandas as pd
from sodapy import Socrata
import os

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
        offset=offset
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
output_file = os.path.join(DATA_FOLDER, "pdc_contributions_2025.csv")
results_df.to_csv(output_file, index=False)

## Fetch all independent expenditures for the election year 2025
all_results = []
limit = 50000  # Use a smaller limit to avoid backend issues
offset = 0

while True:
    results = client.get(
        "67cp-h962",
        where="election_year=2025",
        order="report_date DESC",
        limit=limit,
        offset=offset
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
ind_exp_output_file = os.path.join(DATA_FOLDER, "pdc_ind_exp_2025.csv")
ind_exp_results_df.to_csv(ind_exp_output_file, index=False)