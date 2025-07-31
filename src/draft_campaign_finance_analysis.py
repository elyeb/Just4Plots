"""
Exploratory script to see differences in campaign contributions by candidates
for the King County Executive position in 2025.

Data from https://www.pdc.wa.gov/political-disclosure-reporting-data/browse-search-data/candidates/567407#contributions

Date: July 2025
Author: Elye Bliss
"""

import pandas as pd
import os
from rapidfuzz.distance import JaroWinkler
import matplotlib.pyplot as plt
import numpy as np

data_dir = os.path.join(os.path.dirname(__file__), "../data/lobbying/")
plots_dir = os.path.join(os.path.dirname(__file__), "../outputs/plots/lobbying/")
os.listdir(data_dir)
os.makedirs(plots_dir, exist_ok=True, mode=0o777)

balducci = pd.read_csv(
    os.path.join(data_dir, "campaign_contributions_balducci_king_county.csv")
)
zahilay = pd.read_csv(
    os.path.join(data_dir, "campaign_contributions_zahilay_king_county.csv")
)
constatine = pd.read_csv(
    os.path.join(data_dir, "campaign_contributions_constatine_king_county.csv")
)

"""
Specific cases:
- This must be the same person: Annie Pierre Hurd and Annie-Pierre Hurd
"""


def find_similar_names(df):
    # make a matrix of JaroWinkler distances between names, and determine if matches are above a threshold
    similarities = []
    threshold = 0.97  # Define a similarity threshold. This is very conservative. Some duplicates will fall through the cracks.
    name1s = set()

    names = df[
        "contributor_name"
    ].tolist()  # Convert column to a list for easier iteration

    for i in range(len(names)):
        for j in range(i + 1, len(names)):  # Avoid self-comparison and duplicate pairs
            name1 = names[i]
            name2 = names[j]

            if (name1 not in name1s) and (name2 not in name1s):

                if name1 != name2:
                    # Calculate Jaro-Winkler similarity
                    similarity_score = JaroWinkler.similarity(name1, name2)

                    if similarity_score >= threshold:
                        # only append once per pair
                        similarities.append(
                            {
                                "contributor_name": name1,
                                "contributor_name_standard": name2,
                                "Similarity": similarity_score,
                            }
                        )
                        name1s.add(name1)
                        name1s.add(name2)

    # Convert results to a DataFrame for better viewing
    similar_pairs_df = pd.DataFrame(similarities)
    return similar_pairs_df


def clean_0(df):
    """
    df = balducci.copy()
    """
    df["contributor_name"] = df["contributor_name"].str.strip()

    similar_names_df = find_similar_names(df)

    df = df.merge(
        similar_names_df[["contributor_name", "contributor_name_standard"]],
        on="contributor_name",
        how="left",
    )
    df["contributor_name"] = df["contributor_name_standard"].fillna(
        df["contributor_name"]
    )

    df = df.drop(columns=["contributor_name_standard"])
    return df


def clean_1(df):
    """
    df = balducci.copy()
    """
    # drop in-kind contributions
    df = df[df.cash_or_in_kind == "Cash"]

    # drop negative or $0 contributions
    df = df[df.contributor_amount > 0]

    # agg by contributor across primary/general, year and date

    df = df[
        [
            "contributor_name",
            "contributor_city",
            "contributor_state",
            "contributor_employer_name",
            "contributor_occupation",
            "contributor_amount",
        ]
    ]

    df["contributor_amount"] = df["contributor_amount"].astype(float)

    # also notice that several individuals who own multiple similar business donate
    # multiple times, so we'll aggregate those in a comma-separated string.
    df["contributor_employer_name"] = df["contributor_employer_name"].fillna("")
    df["contributor_occupation"] = df["contributor_occupation"].fillna("")
    df = (
        df.groupby(["contributor_name", "contributor_city", "contributor_state"])
        .agg(
            {
                "contributor_employer_name": lambda x: ", ".join(x.unique()),
                "contributor_occupation": lambda x: ", ".join(x.unique()),
                "contributor_amount": "sum",
            }
        )
        .reset_index()
    )

    return df


def get_overlapping_donors(df1, cand_1, df2, cand_2):
    """
    Find overlapping donors between two DataFrames.
    df1 = balducci_df.copy()
    df2 = zahilay_df.copy()
    cand_1 = 'balducci'
    cand_2 = 'zahilay'
    """
    df1 = df1.copy().rename(
        columns={
            "contributor_employer_name": "contributor_employer_name_" + cand_1,
            "contributor_occupation": "contributor_occupation_" + cand_1,
            "contributor_amount": "contributor_amount_" + cand_1,
        }
    )
    df2 = df2.copy().rename(
        columns={
            "contributor_employer_name": "contributor_employer_name_" + cand_2,
            "contributor_occupation": "contributor_occupation_" + cand_2,
            "contributor_amount": "contributor_amount_" + cand_2,
        }
    )

    # Merge on contributor_name , contributor_city, contributor_state

    overlapping_donors = pd.merge(
        df1,
        df2,
        on=["contributor_name", "contributor_city", "contributor_state"],
        how="inner",
    )
    overlapping_donors["total_contribution"] = (
        overlapping_donors["contributor_amount_" + cand_1]
        + overlapping_donors["contributor_amount_" + cand_2]
    )
    overlapping_donors = overlapping_donors.sort_values(
        by="total_contribution", ascending=False
    )
    return overlapping_donors


balducci_df = clean_0(balducci)
zahilay_df = clean_0(zahilay)
constatine_df = clean_0(constatine)

balducci_df = clean_1(balducci_df)
zahilay_df = clean_1(zahilay_df)
constatine_df = clean_1(constatine_df)



# Get overlapping donors
overlapping_donors = get_overlapping_donors(
    balducci_df, "balducci", zahilay_df, "zahilay"
)

# what percent of each candidate's donors are overlapping?
balducci_overlap_pct = len(overlapping_donors) / len(balducci_df) * 100
zahilay_overlap_pct = len(overlapping_donors) / len(zahilay_df) * 100

# what percent of their money is from overlapping donors?
balducci_overlap_money_pct = (
    overlapping_donors["contributor_amount_balducci"].sum()
    / balducci_df["contributor_amount"].sum()
    * 100
)
zahilay_overlap_money_pct = (
    overlapping_donors["contributor_amount_zahilay"].sum()
    / zahilay_df["contributor_amount"].sum()
    * 100
)

print(
    f"Balducci overlapping donors: {len(overlapping_donors)} ({balducci_overlap_pct:.2f}%)"
)
print(
    f"Zahilay overlapping donors: {len(overlapping_donors)} ({zahilay_overlap_pct:.2f}%)"
)
print(
    f"Balducci overlapping money: ${overlapping_donors['contributor_amount_balducci'].sum():,.2f} ({balducci_overlap_money_pct:.2f}%)"
)
print(
    f"Zahilay overlapping money: ${overlapping_donors['contributor_amount_zahilay'].sum():,.2f} ({zahilay_overlap_money_pct:.2f}%)"
)

# Make distrubution plots of their contribution amounts that can be overlayed


def plot_histograms(column, *dfs, labels=None, colors=None, bins=15):
    """
    column = 'contributor_amount'
    dfs = [balducci_df, zahilay_df]
    labels = ['Balducci', 'Zahilay']
    colors = ['blue', 'red']
    bins = 15
    """
    plt.figure(figsize=(10, 6))
    if labels is None:
        labels = [f"DF{i+1}" for i in range(len(dfs))]
    # Combine all data for bin calculation
    all_data = np.hstack([df[column].dropna().values for df in dfs])
    min_val, max_val = np.min(all_data), np.max(all_data)
    bin_edges = np.linspace(min_val, max_val, bins + 1)
    for df, label, colour in zip(dfs, labels, colors if colors else "blue"):
        plt.hist(
            df[column],
            bins=bin_edges,
            alpha=0.2,
            label=label,
            color=colour,
            edgecolor="black",
        )
        # Find max contributor
        idx_max = df[column].idxmax()
        max_value = df[column].max()
        max_contributor = df.loc[idx_max, "contributor_name"]
        plt.annotate(
            f"Highest donor to {label}:\n{max_contributor}",
            xy=(max_value, 0),
            xytext=(max_value, plt.ylim()[1] * 0.1),
            arrowprops=dict(arrowstyle="->", color="black"),
            fontsize=12,
            color="black",
            ha="center",
        )
    plt.xlabel(column)
    plt.ylabel("Frequency")
    plt.legend()
    plt.title(f"Distribution of Donor Amounts")

    figure_name = "_".join(labels)
    plt.savefig(
        os.path.join(plots_dir, f"donors_hist_{figure_name}.png"),
        bbox_inches="tight",
        dpi=300,
        facecolor="white",
    )
    plt.show()


plot_histograms(
    "contributor_amount",
    balducci_df,
    zahilay_df,
    constatine_df,
    labels=["Balducci", "Zahilay"],
    colors=[
        "blue",
        "red",
    ],
)
