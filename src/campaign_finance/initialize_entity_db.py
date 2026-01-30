"""
entities
-entity type (sponsor, contributor, candidate)
-
names
addresses


Notes:
- Only PACs and Candidates have IDs in the PDC data.
- For PACs, use their sponsor_id, and record their sponsor_name, including all variations,
    as well as their addresses as attributes.
- For Candidates, use their filer_id, and record their filer_name, including all variations,
    as well as election years and positions run for as attributes.
"""

import pandas as pd
import sqlite3
import os
from tqdm import tqdm
import numpy as np

# load downloaded data sets
DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/intermediate_processing/"
)
os.listdir(DATA_FOLDER)
ie_df = pd.read_csv(
    os.path.join(DATA_FOLDER, "pdc_ind_exp_all_time_2026-01-02_cleaned_lat_long.csv")
)
contr_df = pd.read_csv(
    os.path.join(DATA_FOLDER, "pdc_contributions_2025_2026-01-02_cleaned_lat_long.csv")
)

unique_ids = ie_df["sponsor_id"].nunique()
unique_names = ie_df["sponsor_name"].nunique()
print(f"IE Unique IDs: {unique_ids}, Unique Names: {unique_names}")


# Initialize IE database  ##########################################################
conn = sqlite3.connect(DATA_FOLDER + "ie_entities.db")

cur = conn.cursor()

cur.executescript(
    """
CREATE TABLE IF NOT EXISTS ie_entities (
    sponsor_id INTEGER PRIMARY KEY,
    preferred_name_id INTEGER,
    preferred_address_id INTEGER
);

CREATE TABLE IF NOT EXISTS names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    sponsor_name TEXT,
    UNIQUE(sponsor_id, sponsor_name)
);
                  
CREATE TABLE IF NOT EXISTS cleaned_full_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    cleaned_full_address TEXT,
    UNIQUE(sponsor_id, cleaned_full_address)
);

CREATE TABLE IF NOT EXISTS cleaned_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    cleaned_address TEXT,
    UNIQUE(sponsor_id, cleaned_address)
);                
                  
CREATE TABLE IF NOT EXISTS sponsor_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    sponsor_address TEXT,
    UNIQUE(sponsor_id, sponsor_address)
);      
                  
CREATE TABLE IF NOT EXISTS sponsor_city (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    sponsor_city TEXT,
    UNIQUE(sponsor_id, sponsor_city)
);         

CREATE TABLE IF NOT EXISTS sponsor_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    sponsor_state TEXT,
    UNIQUE(sponsor_id, sponsor_state)
);        

CREATE TABLE IF NOT EXISTS sponsor_zip (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    sponsor_zip INTEGER,
    UNIQUE(sponsor_id, sponsor_zip)
);                                              

                  
CREATE TABLE IF NOT EXISTS sponsor_email (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    sponsor_email TEXT,
    UNIQUE(sponsor_id, sponsor_email)
);     

CREATE TABLE IF NOT EXISTS sponsor_latitude (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    Latitude REAL,
    UNIQUE(sponsor_id, Latitude)
);   

CREATE TABLE IF NOT EXISTS sponsor_longitude (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sponsor_id INTEGER,
    Longitude REAL,
    UNIQUE(sponsor_id, Longitude)
);                                                    
"""
)

conn.commit()


def add_entity(sponsor_id):
    cur.execute(
        "INSERT OR IGNORE INTO ie_entities(sponsor_id) VALUES (?)", (sponsor_id,)
    )


def add_name(sponsor_id, sponsor_name):
    cur.execute(
        """
        INSERT OR IGNORE INTO names(sponsor_id, sponsor_name)
        VALUES (?, ?)
    """,
        (sponsor_id, sponsor_name),
    )


def add_full_address(sponsor_id, address):
    cur.execute(
        """
        INSERT OR IGNORE INTO cleaned_full_addresses(sponsor_id, cleaned_full_address)
        VALUES (?, ?)
    """,
        (sponsor_id, address),
    )


def add_cleaned_address(sponsor_id, address):
    cur.execute(
        """
        INSERT OR IGNORE INTO cleaned_addresses(sponsor_id, cleaned_address)
        VALUES (?, ?)
    """,
        (sponsor_id, address),
    )


def add_sponsor_address(sponsor_id, address):
    cur.execute(
        """
        INSERT OR IGNORE INTO sponsor_addresses(sponsor_id, sponsor_address)
        VALUES (?, ?)
    """,
        (sponsor_id, address),
    )


def add_sponsor_city(sponsor_id, city):
    cur.execute(
        """
        INSERT OR IGNORE INTO sponsor_city(sponsor_id, sponsor_city)
        VALUES (?, ?)
    """,
        (sponsor_id, city),
    )


def add_sponsor_state(sponsor_id, state):
    cur.execute(
        """
        INSERT OR IGNORE INTO sponsor_state(sponsor_id, sponsor_state)
        VALUES (?, ?)
    """,
        (sponsor_id, state),
    )


def add_sponsor_zip(sponsor_id, zip_code):
    cur.execute(
        """
        INSERT OR IGNORE INTO sponsor_zip(sponsor_id, sponsor_zip)
        VALUES (?, ?)
    """,
        (sponsor_id, zip_code),
    )


def add_sponsor_email(sponsor_id, email):
    cur.execute(
        """
        INSERT OR IGNORE INTO sponsor_email(sponsor_id, sponsor_email)
        VALUES (?, ?)
    """,
        (sponsor_id, email),
    )


def add_sponsor_latitude(sponsor_id, latitude):
    cur.execute(
        """
        INSERT OR IGNORE INTO sponsor_latitude(sponsor_id, Latitude)
        VALUES (?, ?)
    """,
        (sponsor_id, latitude),
    )


def add_sponsor_longitude(sponsor_id, longitude):
    cur.execute(
        """
        INSERT OR IGNORE INTO sponsor_longitude(sponsor_id, Longitude)
        VALUES (?, ?)
    """,
        (sponsor_id, longitude),
    )


def set_preferred_name(sponsor_id, sponsor_name):
    cur.execute(
        """
        SELECT id FROM names
        WHERE sponsor_id = ? AND sponsor_name = ?
    """,
        (sponsor_id, sponsor_name),
    )
    name_id = cur.fetchone()[0]

    cur.execute(
        """
        UPDATE ie_entities
        SET preferred_name_id = ?
        WHERE sponsor_id = ?
    """,
        (name_id, sponsor_id),
    )


def get_entity(sponsor_id):
    cur.execute(
        """
        SELECT n.sponsor_name, a.cleaned_full_address
        FROM ie_entities e
        LEFT JOIN names n ON e.preferred_name_id = n.id
        LEFT JOIN cleaned_full_addresses a ON e.preferred_address_id = a.id
        WHERE e.sponsor_id = ?
    """,
        (sponsor_id,),
    )
    return cur.fetchone()


conn.execute("BEGIN")
for index, row in tqdm(ie_df.iterrows()):
    sponsor_id = row["sponsor_id"]
    sponsor_name = row["sponsor_name"]
    sponsor_address = row["sponsor_address"]
    cleaned_full_address = row["cleaned_full_address"]
    cleaned_address = row["cleaned_address"]
    sponsor_city = row["sponsor_city"]
    sponsor_state = row["sponsor_state"]
    sponsor_zip = row["sponsor_zip"]
    sponsor_email = row["sponsor_email"]
    latitude = row["Latitude"]
    longitude = row["Longitude"]

    add_entity(sponsor_id)
    add_name(sponsor_id, sponsor_name)
    add_full_address(sponsor_id, cleaned_full_address)
    add_cleaned_address(sponsor_id, cleaned_address)
    add_sponsor_address(sponsor_id, sponsor_address)
    add_sponsor_city(sponsor_id, sponsor_city)
    add_sponsor_state(sponsor_id, sponsor_state)
    add_sponsor_zip(sponsor_id, sponsor_zip)
    add_sponsor_email(sponsor_id, sponsor_email)
    add_sponsor_latitude(sponsor_id, latitude)
    add_sponsor_longitude(sponsor_id, longitude)

    # Optionally set preferred name and address
    set_preferred_name(sponsor_id, sponsor_name)

conn.commit()

####################################################################################


# Initialize candidate database  ###################################################

conn2 = sqlite3.connect(DATA_FOLDER + "candidate_entities.db")

cur2 = conn2.cursor()

cur2.executescript(
    """
CREATE TABLE IF NOT EXISTS candidate_entities (
    filer_id TEXT PRIMARY KEY,
    preferred_name_id INTEGER);

CREATE TABLE IF NOT EXISTS names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filer_id TEXT,
    filer_name TEXT,
    UNIQUE(filer_id, filer_name)
);
                  
CREATE TABLE IF NOT EXISTS committee_ids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filer_id TEXT,
    committee_id TEXT,
    UNIQUE(filer_id, committee_id)
);

CREATE TABLE IF NOT EXISTS fund_ids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filer_id TEXT,
    fund_id TEXT,
    UNIQUE(filer_id, fund_id)
);

CREATE TABLE IF NOT EXISTS election_contributor_source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filer_id TEXT,
    type TEXT,
    election_year INTEGER,
    party TEXT,
    office TEXT,
    position TEXT,
    jurisdiction TEXT,
    jurisdiction_county TEXT,
    juristiction_type TEXT,
    legislative_district TEXT,
    primary_general TEXT,
    UNIQUE(filer_id, type, election_year, party, office, position, jurisdiction, jurisdiction_county, juristiction_type, legislative_district, primary_general)
);

CREATE TABLE IF NOT EXISTS election_ie_source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filer_id TEXT,
    candidate_entity_id INTEGER,
    candidate_candidacy_id INTEGER,
    candidate_committee_id TEXT,
    candidate_name TEXT,
    candidate_last_name TEXT,
    candidate_first_name TEXT,
    candidate_office TEXT,
    candidate_jurisdiction TEXT,
    candidate_party TEXT,
    UNIQUE(filer_id, candidate_entity_id, candidate_candidacy_id, candidate_committee_id, candidate_name, candidate_last_name, candidate_first_name, candidate_office, candidate_jurisdiction, candidate_party)
);
"""
)

conn2.commit()


def add_candidate(filer_id):
    cur2.execute(
        "INSERT OR IGNORE INTO candidate_entities(filer_id) VALUES (?)", (filer_id,)
    )


def add_candidate_name(filer_id, candidate_name):
    cur2.execute(
        """
        INSERT OR IGNORE INTO names(filer_id, filer_name)
        VALUES (?, ?)
    """,
        (filer_id, candidate_name),
    )


def add_committee_id(filer_id, committee_id):
    cur2.execute(
        """
        INSERT OR IGNORE INTO committee_ids(filer_id, committee_id)
        VALUES (?, ?)
    """,
        (filer_id, committee_id),
    )


def add_fund_id(filer_id, fund_id):
    cur2.execute(
        """
        INSERT OR IGNORE INTO fund_ids(filer_id, fund_id)
        VALUES (?, ?)
    """,
        (filer_id, fund_id),
    )


def add_election_contributor_source(
    filer_id,
    type,
    election_year,
    party,
    office,
    position,
    jurisdiction,
    jurisdiction_county,
    juristiction_type,
    legislative_district,
    primary_general,
):
    cur2.execute(
        """
        INSERT OR IGNORE INTO election_contributor_source(
            filer_id, type, election_year, party, office, position, jurisdiction, jurisdiction_county, juristiction_type, legislative_district, primary_general
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            filer_id,
            type,
            election_year,
            party,
            office,
            position,
            jurisdiction,
            jurisdiction_county,
            juristiction_type,
            legislative_district,
            primary_general,
        ),
    )


def add_election_ie_source(
    filer_id,
    candidate_entity_id,
    candidate_candidacy_id,
    candidate_committee_id,
    candidate_name,
    candidate_last_name,
    candidate_first_name,
    candidate_office,
    candidate_jurisdiction,
    candidate_party,
):
    cur2.execute(
        """
        INSERT OR IGNORE INTO election_ie_source(
            filer_id, candidate_entity_id, candidate_candidacy_id, candidate_committee_id, candidate_name, candidate_last_name, candidate_first_name, candidate_office, candidate_jurisdiction, candidate_party
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            filer_id,
            candidate_entity_id,
            candidate_candidacy_id,
            candidate_committee_id,
            candidate_name,
            candidate_last_name,
            candidate_first_name,
            candidate_office,
            candidate_jurisdiction,
            candidate_party,
        ),
    )


def set_preferred_candidate_name(filer_id, filer_name):
    cur2.execute(
        """
        SELECT id FROM names
        WHERE filer_id = ? AND filer_name = ?
    """,
        (filer_id, filer_name),
    )
    name_id = cur2.fetchone()[0]

    cur2.execute(
        """
        UPDATE candidate_entities
        SET preferred_name_id = ?
        WHERE filer_id = ?
    """,
        (name_id, filer_id),
    )


def get_candidate(filer_id):
    cur2.execute(
        """
        SELECT n.filer_name, a.cleaned_full_address
        FROM candidate_entities e
        LEFT JOIN names n ON e.preferred_name_id = n.id
        LEFT JOIN cleaned_full_addresses a ON e.preferred_address_id = a.id
        WHERE e.filer_id = ?
    """,
        (filer_id,),
    )
    return cur2.fetchone()


conn2.execute("BEGIN")
for index, row in contr_df.iterrows():
    filer_id = row["filer_id"]
    filer_name = row["filer_name"]

    add_candidate(filer_id)
    add_candidate_name(filer_id, filer_name)

    add_election_contributor_source(
        filer_id,
        row["type"],
        row["election_year"],
        row["party"],
        row["office"],
        row["position"],
        row["jurisdiction"],
        row["jurisdiction_county"],
        row["jurisdiction_type"],
        row["legislative_district"],
        row["primary_general"],
    )

    # Optionally set preferred name and address
    set_preferred_candidate_name(filer_id, filer_name)

conn2.commit()


conn2.execute("BEGIN")
for index, row in ie_df.iterrows():
    filer_id = row["candidate_filer_id"]

    add_candidate(filer_id)

    add_election_ie_source(
        filer_id,
        row["candidate_candidacy_id"],
        row["candidate_candidacy_id"],
        row["candidate_committee_id"],
        row["candidate_name"],
        row["candidate_last_name"],
        row["candidate_first_name"],
        row["candidate_office"],
        row["candidate_jurisdiction"],
        row["candidate_party"],
    )

conn2.commit()

####################################################################################


import pandas as pd
import sqlite3
import os
from tqdm import tqdm
import numpy as np

# load downloaded data sets
DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/intermediate_processing/"
)
os.listdir(DATA_FOLDER)
ie_df = pd.read_csv(
    os.path.join(DATA_FOLDER, "pdc_ind_exp_all_time_2026-01-02_cleaned_lat_long.csv")
)
contr_df = pd.read_csv(
    os.path.join(DATA_FOLDER, "pdc_contributions_2025_2026-01-02_cleaned_lat_long.csv")
)

unique_ids = ie_df["sponsor_id"].nunique()
unique_names = ie_df["sponsor_name"].nunique()
print(f"IE Unique IDs: {unique_ids}, Unique Names: {unique_names}")

# Initialize contributor database  #################################################
"""
Now I am looking to make a similar database for contributors, who have names, addresses and occupations, sometimes inconsistently-entered in the raw data. I have the following algorithm in mind for creating a data base for contributors:
1. Each new unique entry from the raw data gets it's own unique indentifying number.
2. A sub-algorithm (to be written later) shows likely duplicates based on fuzzy matches of names, addresses (especially if their coordinates are found), and occupation. Let's not work on this right away, but ideally it will identify possible matches in a ranked list for each.
3. Once entries are manually determined to be the same person, I want to simply be able to add later entries under the entry number of when the unique entry was first recorded. But these matched entries should still be searchable to see if future entries match them.

Database schema:
contributors   (the person)
names          (all name variants)
addresses      (all known addresses)
occupations    (all known employment records)


contributor_category
contributor_name
contributor_address
cleaned_address
contributor_city
contributor_state
contributor_zip
cleaned_full_address
matched_address
Latitude
Longitude
contributor_longitude_given
contributor_latitude_given
contributor_location
contributor_occupation
contributor_employer_name
contributor_employer_city
contributor_employer_state
"""

conn3 = sqlite3.connect(DATA_FOLDER + "contributor_entities.db")

cur3 = conn3.cursor()

cur3.executescript(
    """
CREATE TABLE contributor_entities (
    contributor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    preferred_name_id INTEGER,
    preferred_address_id INTEGER,
    preferred_occupation_id INTEGER
);

CREATE TABLE IF NOT EXISTS contributor_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER,
    contributor_name TEXT,
    UNIQUE(contributor_id, contributor_name)
);
                  
CREATE TABLE IF NOT EXISTS contributor_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER,

    contributor_address TEXT,
    cleaned_address TEXT,
    contributor_city TEXT,
    contributor_state TEXT,
    contributor_zip INTEGER,
    cleaned_full_address TEXT,
    matched_address TEXT,

    Latitude REAL,
    Longitude REAL,
    contributor_latitude_given REAL,
    contributor_longitude_given REAL,

    UNIQUE(
        contributor_id,
        cleaned_full_address,
        Latitude,
        Longitude
    )
);

CREATE TABLE IF NOT EXISTS contributor_occupations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER,

    contributor_occupation TEXT,
    contributor_employer_name TEXT,
    contributor_employer_city TEXT,
    contributor_employer_state TEXT,
    contributor_category TEXT,

    UNIQUE(
        contributor_id,
        contributor_occupation,
        contributor_employer_name,
        contributor_employer_city,
        contributor_employer_state
    )
);

-- =========================
-- Indexes (Suggestion #1)
-- =========================

CREATE INDEX IF NOT EXISTS idx_contributor_names_name
    ON contributor_names(contributor_name);

CREATE INDEX IF NOT EXISTS idx_contributor_names_contributor
    ON contributor_names(contributor_id);

CREATE INDEX IF NOT EXISTS idx_contributor_addresses_cleaned
    ON contributor_addresses(cleaned_full_address);

CREATE INDEX IF NOT EXISTS idx_contributor_addresses_latlon
    ON contributor_addresses(Latitude, Longitude);

CREATE INDEX IF NOT EXISTS idx_contributor_addresses_contributor
    ON contributor_addresses(contributor_id);
"""
)

conn3.commit()

cur3.execute(
    """
CREATE TABLE IF NOT EXISTS contributor_aliases (
    contributor_id INTEGER PRIMARY KEY,
    canonical_id INTEGER
);
"""
)
conn3.commit()

cur3.execute(
    """
CREATE VIEW canonical_contributors AS
SELECT
    c.contributor_id,
    COALESCE(a.canonical_id, c.contributor_id) AS canonical_id
FROM contributor_entities c
LEFT JOIN contributor_aliases a
  ON c.contributor_id = a.contributor_id;
"""
)
conn3.commit()


def normalize(s):
    if s is not np.nan:
        return s.strip().upper()
    return s


def find_existing_contributor(row):
    # Normalize values
    name = normalize(row["contributor_name"])
    addr = normalize(row["cleaned_full_address"])
    lat = row["Latitude"]
    lon = row["Longitude"]

    # If any key field is missing, return None immediately
    if not name or not addr or pd.isna(lat) or pd.isna(lon):
        return None

    # Try exact name + (address OR coordinates)
    cur3.execute(
        """
        SELECT cc.canonical_id
        FROM contributor_names n
        JOIN contributor_addresses a
          ON n.contributor_id = a.contributor_id
        JOIN canonical_contributors cc
          ON n.contributor_id = cc.contributor_id
        WHERE n.contributor_name = ?
          AND (a.cleaned_full_address = ? OR (a.Latitude = ? AND a.Longitude = ?))
        LIMIT 1
        """,
        (name, addr, lat, lon),
    )

    r = cur3.fetchone()
    if r:
        return r[0]

    # Fallback: match by coordinates alone
    cur3.execute(
        """
        SELECT cc.canonical_id
        FROM contributor_addresses a
        JOIN canonical_contributors cc
          ON a.contributor_id = cc.contributor_id
        WHERE a.Latitude = ? AND a.Longitude = ?
        LIMIT 1
        """,
        (lat, lon),
    )

    r = cur3.fetchone()
    if r:
        return r[0]

    # No match found
    return None


def create_contributor():
    cur3.execute("INSERT INTO contributor_entities DEFAULT VALUES")
    return cur3.lastrowid


def add_contributor_name(contributor_id, name):
    cur3.execute(
        """
        INSERT OR IGNORE INTO contributor_names(contributor_id, contributor_name)
        VALUES (?, ?)
    """,
        (contributor_id, normalize(name)),
    )


def add_contributor_address(contributor_id, row):
    cur3.execute(
        """
        INSERT OR IGNORE INTO contributor_addresses(
            contributor_id,
            contributor_address,
            cleaned_address,
            contributor_city,
            contributor_state,
            contributor_zip,
            cleaned_full_address,
            matched_address,
            Latitude,
            Longitude,
            contributor_latitude_given,
            contributor_longitude_given
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            contributor_id,
            row["contributor_address"],
            row["cleaned_address"],
            row["contributor_city"],
            row["contributor_state"],
            row["contributor_zip"],
            normalize(row["cleaned_full_address"]),
            row["matched_address"],
            row["Latitude"],
            row["Longitude"],
            row["contributor_latitude_given"],
            row["contributor_longitude_given"],
        ),
    )


def add_contributor_occupation(contributor_id, row):
    cur3.execute(
        """
        INSERT OR IGNORE INTO contributor_occupations (
            contributor_id,
            contributor_occupation,
            contributor_employer_name,
            contributor_employer_city,
            contributor_employer_state,
            contributor_category
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            contributor_id,
            normalize(row["contributor_occupation"]),
            normalize(row["contributor_employer_name"]),
            normalize(row["contributor_employer_city"]),
            normalize(row["contributor_employer_state"]),
            normalize(row["contributor_category"]),
        ),
    )


conn3.execute("BEGIN")

for i in tqdm(range(len(contr_df))):
    row = contr_df.iloc[i]

    contributor_id = find_existing_contributor(row)

    if contributor_id is None:
        contributor_id = create_contributor()

    add_contributor_name(contributor_id, row["contributor_name"])
    add_contributor_address(contributor_id, row)
    add_contributor_occupation(contributor_id, row)

conn3.commit()


####################################################################################

# Initialize vendor database  ######################################################

####################################################################################


# Tests ############################################################################

df = pd.read_sql_query(
    """
    SELECT
        e.sponsor_id,
        n.sponsor_name
    FROM ie_entities e
    JOIN names n
        ON e.sponsor_id = n.sponsor_id
    ORDER BY e.sponsor_id
""",
    conn,
)

# find duplicate names
df[df["sponsor_name"].duplicated(keep=False)].sort_values("sponsor_name")

# find duplicate IDs
df[df["sponsor_id"].duplicated(keep=False)].sort_values("sponsor_id")

# find candidate ID
c_ids = contr_df[
    ["committee_id", "fund_id", "filer_id", "election_year"]
].drop_duplicates()
c_ids[c_ids["filer_id"].duplicated(keep=False)]

# load contributors
df2 = pd.read_sql_query(
    """
    SELECT
        c.contributor_id,
        n.contributor_name,
        a.cleaned_full_address,
        o.contributor_occupation
    FROM contributor_entities c
    JOIN contributor_names n
        ON c.contributor_id = n.contributor_id
    JOIN contributor_addresses a
        ON c.contributor_id = a.contributor_id
    JOIN contributor_occupations o
        ON c.contributor_id = o.contributor_id
    ORDER BY c.contributor_id
""",
    conn3,
)
# examine duplicates
df2_dups = df2[df2["contributor_name"].duplicated(keep=False)].sort_values(
    "contributor_name"
)

df3 = pd.read_sql_query(
    """
    SELECT *
    FROM contributor_entities c
    JOIN contributor_names n
        ON c.contributor_id = n.contributor_id
    JOIN contributor_addresses a
        ON c.contributor_id = a.contributor_id
    JOIN contributor_occupations o
        ON c.contributor_id = o.contributor_id
    ORDER BY c.contributor_id
""",
    conn3,
)


# deduplicate
# 1️⃣ Deduplicate contributor_names
cur3.execute(
    """
DELETE FROM contributor_names
WHERE id NOT IN (
    SELECT MIN(id)
    FROM contributor_names
    GROUP BY contributor_id, contributor_name
)
"""
)

# 2️⃣ Deduplicate contributor_addresses
cur3.execute(
    """
DELETE FROM contributor_addresses
WHERE id NOT IN (
    SELECT MIN(id)
    FROM contributor_addresses
    GROUP BY contributor_id, cleaned_full_address, Latitude, Longitude
)
"""
)

# 3️⃣ Deduplicate contributor_occupations
cur3.execute(
    """
DELETE FROM contributor_occupations
WHERE id NOT IN (
    SELECT MIN(id)
    FROM contributor_occupations
    GROUP BY contributor_id, contributor_occupation, contributor_employer_name, contributor_employer_city, contributor_employer_state
)
"""
)

conn3.commit()

# 4️⃣ Reclaim database space
cur3.execute("VACUUM")
conn3.commit()
####################################################################################
