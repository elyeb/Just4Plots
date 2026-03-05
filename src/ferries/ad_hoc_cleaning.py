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
merged_df.to_csv(DATA_PATH + "ferry_merged_space_delays.csv", index=False)
merged_df.to_parquet(DATA_PATH + "ferry_merged_space_delays.parquet", index=False)
