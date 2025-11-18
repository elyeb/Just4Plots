"""
Create dual horizontal bar charts comparing total contributions to two candidates.

Set recipient list to include candidates and their aligned PACs. Set two candidate names.
Update candidate_map as needed.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import numpy as np


recipient_list = [
    # "DAVISON FOR COMMON SENSE",
    # "ANN DAVISON",
    # "ERIKA EVANS",
    "EDWARD C. LIN (EDDIE LIN)",
    "ADONIS E. DUCKSWORTH (ADONIS DUCKSWORTH)",
    #     "SARA FOR A BETTER SEATTLE",
    #     "SARA NELSON",
    #     "DIONNE FOSTER",
    #     "BRUCE HARRELL",
    #     "BRUCE HARRELL FOR SEATTLE'S FUTURE",
    #     "KATIE WILSON",
    #     "KATIE WILSON FOR AN AFFORDABLE SEATTLE",
]

candidate_1 = "ADONIS E. DUCKSWORTH (ADONIS DUCKSWORTH)"
candidate_2 = "EDWARD C. LIN (EDDIE LIN)"
# candidate_1 = "SARA NELSON"
# candidate_2 = "DIONNE FOSTER"
# candidate_1 = "BRUCE HARRELL"
# candidate_2 = "KATIE WILSON"

candidate_map = {
    "EDWARD C. LIN (EDDIE LIN)": "EDWARD C. LIN (EDDIE LIN)",
    "ADONIS E. DUCKSWORTH (ADONIS DUCKSWORTH)": "ADONIS E. DUCKSWORTH (ADONIS DUCKSWORTH)",
    "SARA FOR A BETTER SEATTLE": "SARA NELSON",
    "SARA NELSON": "SARA NELSON",
    "DIONNE FOSTER": "DIONNE FOSTER",
    "BRUCE HARRELL": "BRUCE HARRELL",
    "BRUCE HARRELL FOR SEATTLE'S FUTURE": "BRUCE HARRELL",
    "KATIE WILSON": "KATIE WILSON",
    "KATIE WILSON FOR AN AFFORDABLE SEATTLE": "KATIE WILSON",
    "DAVISON FOR COMMON SENSE": "ANN DAVISON",
    "ANN DAVISON": "ANN DAVISON",
    "ERIKA EVANS": "ERIKA EVANS",
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
outfile = "contributions_dual_horizontal_bar_chart_lin_ducksworth.png"
# outfile = "contributions_dual_horizontal_bar_chart_harrell_wilson.png"


df = pd.read_csv(os.path.join(DATA_DIR, data_file))

# Prep data ###########################################################################

df[df["filer_name"].str.contains("ADONIS")]["filer_name"].unique()


df.rename(columns={"filer_name": "recipient_name"}, inplace=True)
df = df[df["recipient_name"].isin(recipient_list)]

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

#######################################################################################

# prep for plotting ###################################################################
df_grouped["candidate"] = df_grouped["recipient_name"].map(candidate_map)
df_grouped = df_grouped[df_grouped["total_amount"] > 0]

bin_edges = [0, 100, 500, 2000, 5000, 10000, 50000, 100000, 1000000]
df_grouped["bin"] = pd.cut(df_grouped["total_amount"], bins=bin_edges)


df_binned = (
    df_grouped.groupby(["recipient_name", "bin"])["total_amount"].sum().reset_index()
)
df_binned = df_binned.pivot(
    index="bin", columns="recipient_name", values="total_amount"
).fillna(0)

# make index into column
df_binned = df_binned.reset_index()
df_plot = df_binned.copy()


def pretty_bin(interval):
    left = interval.left + 1 if interval.closed_right else interval.left
    right = interval.right
    return f"${left:,.0f}-{right:,.0f}"


df_plot["bin_str"] = df_plot["bin"].apply(pretty_bin)


candidate_1_cols = [
    col
    for col in df_plot.columns
    if col in recipient_list and candidate_map[col] == candidate_1
]

candidate_2_cols = [
    col
    for col in df_plot.columns
    if col in recipient_list and candidate_map[col] == candidate_2
]

# Number of stacked columns per side
# Build per-candidate color sets
blue_cmap = cm.get_cmap("Blues")
red_cmap = cm.get_cmap("Reds")
n_cand_1 = len(candidate_1_cols)
n_cand_2 = len(candidate_2_cols)
cand_1_colors = [
    blue_cmap(0.4 + 0.5 * i / (max(n_cand_1 - 1, 1))) for i in range(n_cand_1)
]
cand_2_colors = [
    red_cmap(0.4 + 0.5 * i / (max(n_cand_2 - 1, 1))) for i in range(n_cand_2)
]

#######################################################################################

# Call plot ###########################################################################
fig, ax = plt.subplots(figsize=(10, 6))

# Positive side (candidate_1)
right_accum = np.zeros(len(df_plot))
for col, color in zip(candidate_1_cols, cand_1_colors):
    ax.barh(df_plot["bin_str"], df_plot[col], left=right_accum, label=col, color=color)
    left_accum += df_plot[col]

# Negative side (candidate_2)
left_accum = np.zeros(len(df_plot))
for col, color in zip(candidate_2_cols, cand_2_colors):
    ax.barh(
        df_plot["bin_str"],
        -df_plot[col],
        left=-left_accum,
        label=col,
        color=color,
    )
    left_accum += df_plot[col]

ax.axvline(0, color="black")

# Pretty x-axis labels
ticks = ax.get_xticks()
ax.set_xticklabels([f"${abs(int(t)):,}" for t in ticks], rotation=45)


plt.tight_layout()
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
plt.xlabel(f"{candidate_2}               {candidate_1}")
plt.title(
    "Total Contributions per Donor by Size\nto Candidate Campaigns and Directly-Aligned PACs"
)
# plt.show()
plt.savefig(OUTPUT_DIR + outfile, dpi=300, bbox_inches="tight")

#######################################################################################
