""" """

import pickle
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from tqdm import tqdm

# Load pre-scraped PT Leader data
folder_path = "/Users/elyebliss/Documents/Just4Plots/data"
raw = pickle.load(open(os.path.join(folder_path, "pt_opinions.pkl"), "rb"))



# Define keyword list
keywords = [
    "housing",
    "rent",
    "homeless",
    "homelessness",
]

all_urls = [article["url"] for article in raw]
all_url_types = [url.split("/")[3] for url in all_urls]
all_dates = [article["date"] for article in raw]
all_years = [re.findall(r"(?<=\s)\d{4}(?=\s)", date)[0] for date in all_dates]

# deduplicate using titles
all_titles = set([article["title"] for article in raw]) #378
raw_unique  = []
title_added = set()
for article in raw:
    if article["title"] not in title_added:
        raw_unique.append(article)
        title_added.add(article["title"])

# Number of articles by year is very imbalanced. I might need to rescrape some years

# Draft graphic will need to focus on % of total articles by year

# Make dictionary sorting articles into contains/not-contains
keyword_dict = {}

def flatten_list(nested_list):
    """
    Flatten a nested list if it's nested, otherwise return it as-is.
    """
    if any(isinstance(i, list) for i in nested_list):
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):
                flat_list.extend(flatten_list(item))
            else:
                flat_list.append(item)
        return flat_list
    else:
        return nested_list



for article in tqdm(raw_unique):
    text = article["title"] + "\n" + "".join(flatten_list(article["body"]))
    year = int(re.findall(r"(?<=\s)\d{4}(?=\s)", article["date"])[0])
    if year not in keyword_dict:
        keyword_dict[year] = {"contains": [], "not_contains": []}
    keyword_found = False
    for keyword in keywords:
        keyword_found = bool(re.findall(keyword, text, re.IGNORECASE))

    if keyword_found:
        keyword_dict[year]["contains"].append(article)
    else:
        keyword_dict[year]["not_contains"].append(article)

keyword_counts = {}
for year in keyword_dict:
    keyword_counts[year] = {
        "contains": len(keyword_dict[year]["contains"]),
        "not_contains": len(keyword_dict[year]["not_contains"]),
    }

keyword_percent = {}
for year in keyword_counts:
    total = keyword_counts[year]["contains"] + keyword_counts[year]["not_contains"]
    keyword_percent[year] = {
        "housing_related": round(100 * keyword_counts[year]["contains"] / total, 2)
    }

keyword_df = pd.DataFrame(keyword_percent)
keyword_df = keyword_df.transpose()
keyword_df = keyword_df.reset_index()
keyword_df.rename(columns={"index": "year"}, inplace=True)
keyword_df.sort_values("year", inplace=True)

# Plot line chart
plt.figure(figsize=(10, 5))
keyword_df.plot(x="year", y="housing_related", kind="line", marker="o", color="blue")
plt.title(
    "Percentage of PT Leader Articles and Opinions Containing Housing-Related Keywords"
)
plt.xlabel("Year")
plt.ylabel("Percentage of Articles")

"""
TODO:

- make stacked bar plot showing total articles
- put keywords checked in legend
- what other words are most prominent in the housing articles?
- what's the second most common topic?
- check data quality/rescrape
"""
