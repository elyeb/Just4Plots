"""
entities
-entity type (sponsor, contributor, candidate)
-
names
addresses

CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    preferred_name_id INTEGER,
    preferred_address_id INTEGER
);

CREATE TABLE names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,
    name TEXT,
    UNIQUE(entity_id, name),
    FOREIGN KEY(entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,
    address TEXT,
    UNIQUE(entity_id, address),
    FOREIGN KEY(entity_id) REFERENCES entities(entity_id)
);


import sqlite3

conn = sqlite3.connect("entities.db")
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    preferred_name_id INTEGER,
    preferred_address_id INTEGER
);

CREATE TABLE IF NOT EXISTS names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,
    name TEXT,
    UNIQUE(entity_id, name)
);

CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,
    address TEXT,
    UNIQUE(entity_id, address)
);
""")

conn.commit()

def add_entity(entity_id):
    cur.execute("INSERT OR IGNORE INTO entities(entity_id) VALUES (?)", (entity_id,))
    conn.commit()

    
def add_name(entity_id, name):
    cur.execute("""
        INSERT OR IGNORE INTO names(entity_id, name)
        VALUES (?, ?)
    """, (entity_id, name))
    conn.commit()

def add_address(entity_id, address):
    cur.execute("""
        INSERT OR IGNORE INTO addresses(entity_id, address)
        VALUES (?, ?)
    """, (entity_id, address))
    conn.commit()

    
def set_preferred_name(entity_id, name):
    cur.execute("""
        SELECT id FROM names
        WHERE entity_id = ? AND name = ?
    """, (entity_id, name))
    name_id = cur.fetchone()[0]

    cur.execute("""
        UPDATE entities
        SET preferred_name_id = ?
        WHERE entity_id = ?
    """, (name_id, entity_id))
    conn.commit()

    
def get_entity(entity_id):
    cur.execute("""
        SELECT n.name, a.address
        FROM entities e
        LEFT JOIN names n ON e.preferred_name_id = n.id
        LEFT JOIN addresses a ON e.preferred_address_id = a.id
        WHERE e.entity_id = ?
    """, (entity_id,))

    return cur.fetchone()

"""

import pandas as pd
import sqlite3
import os

# load downloaded data sets
DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/intermediate_processing/"
)
ie_df = pd.read_csv(os.path.join(DATA_FOLDER,"pdc_contributions_2025_2026-01-02_cleaned_lat_long.csv"))
        
unique_ids = ie_df["sponsor_id"].nunique()
unique_names = ie_df["sponsor_name"].nunique()
print(f"Unique IDs: {unique_ids}, Unique Names: {unique_names}")

# initialize database
conn = sqlite3.connect("ie_entities.db")