"""
Create dual horizontal bar charts comparing total contributions to two candidates.

Set recipient list to include candidates and their aligned PACs. Set two candidate names.
Update candidate_map as needed.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# recipient_list = [
#     "BRUCE HARRELL",
#     "BRUCE HARRELL FOR SEATTLE'S FUTURE",
#     "KATIE WILSON",
#     "KATIE WILSON FOR AN AFFORDABLE SEATTLE",
# ]
recipient_list = [
    "SARA FOR A BETTER SEATTLE",
    "SARA NELSON",
    "WA BIKES PAC SPONSORED BY WASHINGTON BIKES",
    "DIONNE FOSTER",
    "FUSE VOTES",
]

candidate_1 = "BRUCE HARRELL"
candidate_2 = "KATIE WILSON"

candidate_map = {
    "SARA FOR A BETTER SEATTLE": "SARA NELSON",
    "SARA NELSON": "SARA NELSON",
    "NATIONAL ASSOCIATION OF REALTORS FUND": "SARA NELSON",
    "WA BIKES PAC SPONSORED BY WASHINGTON BIKES": "DIONNE FOSTER",
    "FUSE VOTES": "DIONNE FOSTER",
    "SEIU 775 QUALITY CARE COMMITTEE": "DIONNE FOSTER",
    "PROGRESSIVE PEOPLE POWER": "DIONNE FOSTER",
    "BRUCE HARRELL": "BRUCE HARRELL",
    "BRUCE HARRELL FOR SEATTLE'S FUTURE": "BRUCE HARRELL",
    "KATIE WILSON": "KATIE WILSON",
    "KATIE WILSON FOR AN AFFORDABLE SEATTLE": ("KATIE WILSON", "DIONNE FOSTER"),
}


DATA_DIR = os.path.join(
    os.path.dirname(__file__), "../", "../", "../", "data/lobbying/powerbi_inputs/"
)
os.listdir(DATA_DIR)
data_file = "pdc_contributions_2025_2025-11-05_name_cleaned_lat_long.csv"

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "../", "../", "../", "outputs/plots/lobbying/"
)
os.listdir(OUTPUT_DIR)
outfile = "contributions_dual_horizontal_bar_chart_nelson_foster.png"

df = pd.read_csv(os.path.join(DATA_DIR, data_file))

df[df["filer_name"].str.contains("REALTORS")]["filer_name"].unique()


df.rename(columns={"filer_name": "recipient_name"}, inplace=True)
df = df[df["recipient_name"].isin(recipient_list)]
df["amount"].max()

# break up grouped small contributions into individual
df["description"] = df["description"].fillna("")
df[df["description"].str.contains("Small contributions")]["description"].unique()
small_contributors = df[df["description"].str.contains("Small contributions")]
non_small_contributors = df[~df["description"].str.contains("Small contributions")]

# get number of contributors for each
small_contributors["num_contributors"] = (
    small_contributors["description"].str.extract(r"(\d+)").astype(int)
)

small_contributors["avg_contribution"] = (
    small_contributors["amount"] / small_contributors["num_contributors"]
)
small_contributors_expanded = small_contributors.loc[
    small_contributors.index.repeat(small_contributors["num_contributors"])
].copy()
small_contributors_expanded["total_amount"] = small_contributors_expanded[
    "avg_contribution"
]

# concat back together
non_small_contributors_grouped = (
    non_small_contributors.groupby(["recipient_name", "contributor_name"])["amount"]
    .sum()
    .reset_index()
)
non_small_contributors_grouped.rename(columns={"amount": "total_amount"}, inplace=True)

df_grouped = pd.concat(
    [small_contributors_expanded, non_small_contributors_grouped], ignore_index=True
)

# prep for plotting
df_grouped["candidate"] = df_grouped["recipient_name"].map(candidate_map)
df_grouped = df_grouped[df_grouped["total_amount"] > 0]

bin_edges = [0, 100, 500, 1000, 5000, 10000, 50000, 100000, 1000000]
df_grouped["bin"] = pd.cut(df_grouped["total_amount"], bins=bin_edges)

df_binned = df_grouped.groupby(["candidate", "bin"])["total_amount"].sum().reset_index()
df_binned = df_binned.pivot(
    index="bin", columns="candidate", values="total_amount"
).fillna(0)

# make index into column
df_binned = df_binned.reset_index()
df_plot = df_binned.copy()


def pretty_bin(interval):
    left = interval.left + 1 if interval.closed_right else interval.left
    right = interval.right
    return f"${left:,.0f}-{right:,.0f}"


df_plot["bin_str"] = df_plot["bin"].apply(pretty_bin)


# plot results
fig, ax = plt.subplots(figsize=(8, 5))

ax.barh(
    df_plot["bin_str"],
    df_plot[candidate_1],
    label=candidate_1,
    align="center",
)
ax.barh(df_plot["bin_str"], -df_plot[candidate_2], label=candidate_2, align="center")
ax.set_xticks(ax.get_xticks())  # ensure fixed locator
ax.set_xticklabels([f"${abs(int(x)):,}" for x in ax.get_xticks()], rotation=45)
ax.axvline(0, color="black")
plt.legend()
plt.tight_layout()
plt.xlabel("Total Contribution Amount")
plt.title("Total Contributions to Candidates and Aligned PACs by Contribution Size")
plt.savefig(os.path.join(OUTPUT_DIR, outfile), bbox_inches="tight", dpi=300)
plt.show()
