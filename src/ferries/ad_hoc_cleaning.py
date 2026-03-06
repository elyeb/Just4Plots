import pandas as pd
import os

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "../../data/ferry/ferry_merged_space_delays/"
)

merged_df = pd.read_csv(DATA_PATH + "ferry_merged_space_delays.csv")
os.listdir(DATA_PATH)

cols_to_keep = [
    "actual_vessel",
    "Departing",
    "Destination",
    "scheduled_depart",
    "actual_depart",
    "est_arrival",
    "Date",
    "day_of_week",
    "soldout_time",
    "depart_dif",
    "soldout_dif",
]
merged_df = merged_df[cols_to_keep]


## Correct times
def correct_est_arrival(row):
    if pd.isna(row["est_arrival"]) or pd.isna(row["actual_depart"]):
        return None
    est_arrival_hr = int(str(row["est_arrival"]).split(":")[0])
    actual_depart_hr = int(str(row["actual_depart"]).split(":")[0])
    if (est_arrival_hr == 12) and (actual_depart_hr == 23):
        return "00" + row["est_arrival"][2:]
    else:
        return row["est_arrival"]


def correct_actual_depart(row):
    if pd.isna(row["est_arrival"]) or pd.isna(row["actual_depart"]):
        return None
    est_arrival_hr = int(str(row["est_arrival"]).split(":")[0])
    actual_depart_hr = int(str(row["actual_depart"]).split(":")[0])
    if (est_arrival_hr == 12) and (actual_depart_hr == 23):
        return "11" + row["actual_depart"][2:]
    else:
        return row["actual_depart"]


merged_df["est_arrival"] = merged_df.apply(correct_est_arrival, axis=1)
merged_df["actual_depart"] = merged_df.apply(correct_actual_depart, axis=1)

merged_df[
    merged_df["est_arrival"].notna()
    & (merged_df["est_arrival"].str.split(":").str[0].astype(int) == 12)
]

merged_df = merged_df[merged_df["day_of_week"].notna()]


merged_df.to_csv(DATA_PATH + "ferry_merged_space_delays.csv", index=False)
merged_df.to_parquet(DATA_PATH + "ferry_merged_space_delays.parquet", index=False)
