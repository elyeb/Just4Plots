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

####################################################################################

# Initialize contributor database  #################################################

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

####################################################################################
