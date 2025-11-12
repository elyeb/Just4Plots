import pandas as pd
import os
import csv

INPUT_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/powerbi_inputs/"
)
INPUT_FILE = "pdc_contributions_2025_2025-11-05_name_cleaned_lat_long.csv"

OUTPUT_FILE = "pdc_contributions_2025_2025-11-05_name_cleaned_lat_long_sankey.csv"

df = pd.read_csv(os.path.join(INPUT_FOLDER, INPUT_FILE))

# group by donor and recipient and calc total amounts for sankey diagrams
df_sk = (
    df.groupby(["contributor_name", "contributor_employer_name", "filer_name"])[
        "amount"
    ]
    .sum()
    .reset_index()
)
df_sk = df_sk.rename(
    columns={
        "contributor_name": "donor_name",
        "contributor_employer_name": "donor_employer",
        "filer_name": "recipient_name",
        "amount": "total_amount",
    }
)
df_sk = df_sk.sort_values(
    by=["recipient_name", "total_amount"], ascending=[True, False]
)
df_sk.to_csv(
    os.path.join(INPUT_FOLDER, OUTPUT_FILE),
    index=False,
    sep=",",
    quotechar='"',
    quoting=csv.QUOTE_ALL,  # quotes text columns only
    lineterminator="\n",  # avoids \r\n issues on Windows
    encoding="utf-8",
)

# get the top 10 donors by total amount given
top_donors = df_sk.groupby("donor_name")["total_amount"].sum().reset_index()
top_donors = top_donors.sort_values(by="total_amount", ascending=False).head(10)

# return sankey info for only top 10 donors
df_sk_top_donors = df_sk[df_sk["donor_name"].isin(top_donors["donor_name"])]
df_sk_top_donors["donor_total"] = df_sk_top_donors.groupby("donor_name")[
    "total_amount"
].transform("sum")

df_sk_top_donors = df_sk_top_donors.sort_values(
    by=["donor_total", "donor_name", "total_amount"], ascending=[False, True, False]
)
df_sk_top_donors.drop(columns=["donor_total"], inplace=True)


df_sk_top_donors.to_csv(
    os.path.join(
        INPUT_FOLDER,
        "pdc_contributions_2025_2025-11-05_name_cleaned_lat_long_top_10_donors.csv",
    ),
    index=False,
    sep=",",
    quotechar='"',
    quoting=csv.QUOTE_ALL,  # quotes text columns only
    lineterminator="\n",  # avoids \r\n issues on Windows
    encoding="utf-8",
)
