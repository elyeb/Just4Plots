"""

Find contributor matches and roll up their IDs to a canonical ID.
This script populates the contributor_aliases table with mappings from
example call: contributor_id to canonical_id.


INSERT OR REPLACE INTO contributor_aliases(contributor_id, canonical_id)
VALUES (822, 41);
"""

import pandas as pd
import sqlite3
import os
from tqdm import tqdm

DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/intermediate_processing/"
)
os.listdir(DATA_FOLDER)

# pull in full table #######################################################################
conn = sqlite3.connect(DATA_FOLDER + "contributor_entities.db")


variants = pd.read_sql(
    """
SELECT
    c.contributor_id,
    n.contributor_name,
    a.cleaned_full_address,
    a.contributor_zip,
    a.Latitude,
    a.Longitude,
    o.contributor_occupation
FROM contributor_entities c
LEFT JOIN contributor_names n ON n.contributor_id = c.contributor_id
LEFT JOIN contributor_addresses a ON a.contributor_id = c.contributor_id
LEFT JOIN contributor_occupations o ON o.contributor_id = c.contributor_id
""",
    conn,
)

# drop duplicates across all columns
variants = variants.drop_duplicates()
# only keep first instance of contributor_id,
variants = variants.drop_duplicates(subset=["contributor_id"], keep="first")

#############################################################################################

# first pass - same contributor_name and contributor_zip ########################################


variants["latlong"] = (
    variants["Latitude"].astype(str) + "," + variants["Longitude"].astype(str)
)

m1 = variants[
    variants["contributor_zip"].notna()
    & variants.duplicated(subset=["contributor_name", "contributor_zip"], keep=False)
]

m1 = m1.sort_values(by=["contributor_name", "latlong", "contributor_id"])
m1["contributor_name"].nunique()


# test rollup - assuming all of the above are matches
cur = conn.cursor()
names = m1["contributor_name"].unique()
for name in tqdm(names):
    subset = m1[m1["contributor_name"] == name]

    canonical_id = subset.iloc[0]["contributor_id"]
    other_ids = subset.iloc[1:]["contributor_id"]

    for other_id in other_ids:
        cur.execute(
            """
            INSERT OR REPLACE INTO contributor_aliases(contributor_id, canonical_id)
            VALUES (?, ?)
            """,
            (int(other_id), int(canonical_id)),
        )
        conn.commit()

    preferred_address = subset["cleaned_full_address"].dropna()
    if len(preferred_address) > 0:
        preferred_address = preferred_address.iloc[0]

        # Update the canonical contributor to point to that preferred address
        # We need the id from contributor_addresses
        cur.execute(
            """
            SELECT id
            FROM contributor_addresses
            WHERE contributor_id = ?
            AND cleaned_full_address = ?
            """,
            (int(canonical_id), preferred_address),
        )
        addr_id = cur.fetchone()[0]

        # Update contributor_entities.preferred_address_id
        cur.execute(
            """
            UPDATE contributor_entities
            SET preferred_address_id = ?
            WHERE contributor_id = ?
            """,
            (int(addr_id), int(canonical_id)),
        )
        conn.commit()


## TEST

# Pick the first two rows in m1 to roll up
rows_to_merge = m1.iloc[:2]

# Identify which contributor_id will be the canonical ID
# Typically, we pick the first row as canonical
canonical_id = rows_to_merge.iloc[0]["contributor_id"]
other_id = rows_to_merge.iloc[1]["contributor_id"]

print(f"Rolling up {other_id} into {canonical_id}")

# 1️⃣ Add to contributor_aliases

cur.execute(
    """
    INSERT OR REPLACE INTO contributor_aliases(contributor_id, canonical_id)
    VALUES (?, ?)
    """,
    (int(other_id), int(canonical_id)),
)
conn.commit()

# 2️⃣ Select a preferred address for the canonical ID
# For simplicity, pick the first non-null cleaned_full_address among the two rows
preferred_address = rows_to_merge["cleaned_full_address"].dropna().iloc[0]

# Update the canonical contributor to point to that preferred address
# We need the id from contributor_addresses
cur.execute(
    """
    SELECT id
    FROM contributor_addresses
    WHERE contributor_id = ?
      AND cleaned_full_address = ?
    """,
    (int(canonical_id), preferred_address),
)
addr_id = cur.fetchone()[0]

# Update contributor_entities.preferred_address_id
cur.execute(
    """
    UPDATE contributor_entities
    SET preferred_address_id = ?
    WHERE contributor_id = ?
    """,
    (int(addr_id), int(canonical_id)),
)
conn.commit()

print(f"Canonical ID {canonical_id} now has preferred address id {addr_id}")
#############################################################################################
