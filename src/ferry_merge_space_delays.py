"""
Merge ferry space data with ferry departure data and delete extra space data.
May 30, 2025
"""

import pandas as pd
import os
import re
from datetime import datetime

SPACE_FOLDER = os.path.join(os.path.dirname(__file__), "../data/ferry/ferry_spaces/")
os.makedirs(SPACE_FOLDER, exist_ok=True, mode=0o777)
DEP_TIME_FOLDER = os.path.join(os.path.dirname(__file__), "../data/ferry/ferry_delays/")
OUTPUT_ROOT = os.path.join(
    os.path.dirname(__file__), "../data/ferry/ferry_merged_space_delays/"
)

print("Running ferry_merge_space_delays.py...")

depart_data = pd.read_csv(DEP_TIME_FOLDER + "ferry_depart_times.csv")

prev_space_db = pd.read_parquet(OUTPUT_ROOT + "ferry_space_db.parquet")
prev_merged_db = pd.read_parquet(OUTPUT_ROOT + "ferry_merged_space_delays.parquet")

sub_strings = {
    "Bainbridge Island": "Bainbridge",
}
sub_vessels = {
    "WallaWalla": "Walla Walla",
}


def format_depart(data):
    df = data.copy()
    df.columns = [d.strip() for d in df.columns]
    df.rename(
        columns={
            "Arriving": "Destination",
            "Scheduled Depart": "scheduled_depart",
            "Actual Depart": "actual_depart",
            "Est. Arrival": "est_arrival",
        },
        inplace=True,
    )
    df["Vessel"] = df["Vessel"].apply(
        lambda x: sub_vessels[x] if x in sub_vessels else x
    )
    df.rename(columns={"Vessel": "actual_vessel"}, inplace=True)

    # df['Date'] = pd.to_datetime(df['Date'])
    df["day_of_week"] = pd.to_datetime(df["Date"]).dt.day_name()
    return df


def format_space(data):
    """
    df = colman_df.copy()
    dockname = "Colman"
    """
    df = data.copy()
    df["Date"] = pd.to_datetime(df["timestamp"]).dt.strftime("%m/%d/%Y")
    df.rename(columns={"Depart": "scheduled_depart"}, inplace=True)
    df["scheduled_depart"] = df["scheduled_depart"].apply(
        lambda x: datetime.strptime(x, "%I:%M %p").strftime("%H:%M")
    )
    df["Departing"] = df["Departing"].apply(
        lambda x: sub_strings[x] if x in sub_strings else x
    )
    df["Destination"] = df["Destination"].apply(
        lambda x: sub_strings[x] if x in sub_strings else x
    )

    # space data: if the sailing sold out, get the earliest timestamp for which it's sold out
    df["timestamp_time"] = df["timestamp"].apply(lambda x: " ".join(x.split(" ")[1:]))
    df["soldout_time"] = pd.to_datetime(
        df["timestamp_time"], format="%I:%M:%S %p"
    ).dt.strftime("%H:%M:%S")

    soldout = df[df["Drive-up"] == "0 Spaces"]

    soldout_grouped = (
        soldout.groupby(["scheduled_depart", "Departing", "Destination", "Date"])
        .agg({"soldout_time": "min"})
        .reset_index()
    )
    return soldout_grouped


def calculate_depart_dif(row):
    """
    actual_depart = "23:32"
    scheduled_depart = "00:55"
    """

    actual_depart = row["actual_depart"]
    scheduled_depart = row["scheduled_depart"]

    actual_minutes = int(actual_depart.split(":")[0]) * 60 + int(
        actual_depart.split(":")[1]
    )
    scheduled_minutes = int(scheduled_depart.split(":")[0]) * 60 + int(
        scheduled_depart.split(":")[1]
    )

    schedule_b4_midnight_actual_after_midnight = (
        scheduled_depart[0] == "2" and actual_depart[0] == "0"
    )
    schedule_after_midnight_actual_b4_midnight = (
        scheduled_depart[0] == "0" and actual_depart[0] == "2"
    )  # should be rare

    if schedule_b4_midnight_actual_after_midnight:
        scheduled_dif = 24 * 60 - scheduled_minutes + actual_minutes
    elif schedule_after_midnight_actual_b4_midnight:
        scheduled_dif = 24 * 60 - actual_minutes - scheduled_minutes
    else:
        scheduled_dif = actual_minutes - scheduled_minutes
    return scheduled_dif


def calculate_soldout_dif(row):
    """
    soldout_time = "23:40"
    scheduled_depart = "23:55"
    """

    scheduled_depart = row["scheduled_depart"]
    soldout_time = row["soldout_time"]

    scheduled_minutes = int(scheduled_depart.split(":")[0]) * 60 + int(
        scheduled_depart.split(":")[1]
    )
    if pd.isna(soldout_time):
        return None
    else:
        soldout_minutes = int(soldout_time.split(":")[0]) * 60 + int(
            soldout_time.split(":")[1]
        )

        soldout_b4_midnight_scheduled_after_midnight = (
            scheduled_depart[0] == "0" and soldout_time[0] == "2"
        )
        soldout_after_midnight_scheduled_b4_midnight = (
            scheduled_depart[0] == "2" and soldout_time[0] == "0"
        )  # should be rare

        if soldout_b4_midnight_scheduled_after_midnight:
            soldout_dif = -scheduled_minutes - (24 * 60 - soldout_minutes)
        elif soldout_after_midnight_scheduled_b4_midnight:
            soldout_dif = soldout_minutes + (24 * 60 - scheduled_minutes)
        else:
            soldout_dif = soldout_minutes - scheduled_minutes
        return soldout_dif


## DRIVER CODE
# merge ferry space data with ferry departure data
space_files = os.listdir(SPACE_FOLDER)


docks = [f.split("_ferry")[0] for f in space_files if "_ferry" in f]
docks = list(set(docks))

edmonds_space_files = [
    pd.read_csv(SPACE_FOLDER + f) for f in space_files if "edmonds" in f
]
bainbridge_space_files = [
    pd.read_csv(SPACE_FOLDER + f) for f in space_files if "bainbridge" in f
]
kingston_space_files = [
    pd.read_csv(SPACE_FOLDER + f) for f in space_files if "kingston" in f
]
colman_space_files = [
    pd.read_csv(SPACE_FOLDER + f) for f in space_files if "colman" in f
]

concat_list = []
if len(edmonds_space_files) > 0:
    edmonds_df = pd.concat(edmonds_space_files, ignore_index=True)
    edmonds_df["Departing"] = "Edmonds"
    concat_list.append(edmonds_df)
if len(bainbridge_space_files) > 0:
    bainbridge_df = pd.concat(bainbridge_space_files, ignore_index=True)
    bainbridge_df["Departing"] = "Bainbridge"
    concat_list.append(bainbridge_df)
if len(kingston_space_files) > 0:
    kingston_df = pd.concat(kingston_space_files, ignore_index=True)
    kingston_df["Departing"] = "Kingston"
    concat_list.append(kingston_df)
if len(colman_space_files) > 0:
    colman_df = pd.concat(colman_space_files, ignore_index=True)
    colman_df["Departing"] = "Colman"
    concat_list.append(colman_df)

if len(concat_list) > 0:
    new_space_db = pd.concat(concat_list, ignore_index=True)

    db = pd.concat([prev_space_db, new_space_db], ignore_index=True)
    # remove duplicates
    db = db.drop_duplicates()

    db.to_parquet(OUTPUT_ROOT + "ferry_space_db.parquet", index=False)

# remove individual space files
for f in space_files:
    os.remove(SPACE_FOLDER + f)
os.makedirs(SPACE_FOLDER, exist_ok=True, mode=0o777)

## prep for merge
# format the dataframes
depart_data = format_depart(depart_data)

space_df = format_space(db)

merged = depart_data.merge(
    space_df, how="left", on=["scheduled_depart", "Departing", "Destination", "Date"]
)

merged = merged.sort_values(["Date", "scheduled_depart"], ascending=False)


merged["depart_dif"] = merged.apply(lambda x: calculate_depart_dif(x), axis=1)

merged["soldout_dif"] = merged.apply(lambda x: calculate_soldout_dif(x), axis=1)

merged = pd.concat([merged, prev_merged_db], ignore_index=True)
# remove duplicates
merged = merged.drop_duplicates()

merged.to_parquet(OUTPUT_ROOT + "ferry_merged_space_delays.parquet", index=False)
merged.to_csv(OUTPUT_ROOT + "ferry_merged_space_delays.csv", index=False)
