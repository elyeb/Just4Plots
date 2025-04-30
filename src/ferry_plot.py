"""
Make plots of weekly ferry space and departure data
"""

import pandas as pd
import os
import matplotlib.pyplot as plt
import re
from datetime import datetime

SPACE_FOLDER = "/Users/elyebliss/Documents/Just4Plots/data/ferry_spaces/"
DEP_TIME_FOLDER = "/Users/elyebliss/Documents/Just4Plots/data/"

depart_data = pd.read_csv(DEP_TIME_FOLDER+"ferry_data_combined_04252025_thru_04292025.csv")

sub_strings = {
    "Bainbridge Island": "Bainbridge",
}
def format_depart(df):

    df.columns = [d.strip() for d in df.columns]
    df.rename(columns={"Arriving":"Destination","Scheduled Depart":"scheduled_depart","Actual Depart":"actual_depart","Est. Arrival":"est_arrival"}, inplace=True)
    return df

def format_space(df,dockname):
    df['Date'] = pd.to_datetime(df['timestamp']).dt.strftime('%m/%d/%Y')
    df["Departing"] =dockname
    df.rename(columns={"Depart":"scheduled_depart"},inplace=True)
    df["scheduled_depart"] = df["scheduled_depart"].apply(lambda x: datetime.strptime(x, "%I:%M %p").strftime("%H:%M"))
    df["Departing"] = df["Departing"].apply(lambda x: sub_strings[x] if x in sub_strings else x)
    df["Destination"] = df["Destination"].apply(lambda x: sub_strings[x] if x in sub_strings else x)
    return df
# merge ferry space data with ferry departure data
space_files = os.listdir(SPACE_FOLDER)
edmonds_space = [pd.read_csv(SPACE_FOLDER+f) for f in space_files if "edmonds" in f]
bainbridge_space = [pd.read_csv(SPACE_FOLDER+f) for f in space_files if "bainbridge" in f]
kingston_space = [pd.read_csv(SPACE_FOLDER+f) for f in space_files if "kingston" in f]
colman_space = [pd.read_csv(SPACE_FOLDER+f) for f in space_files if "colman" in f]
edmonds_df = pd.concat(edmonds_space, ignore_index=True)
bainbridge_df = pd.concat(bainbridge_space, ignore_index=True)
kingston_df = pd.concat(kingston_space, ignore_index=True)
colman_df = pd.concat(colman_space, ignore_index=True)

# merge on Depart, Destination, Vessel, and Date (from timestamp)

depart_data = format_depart(depart_data)
colman_df = format_space(colman_df,"Colman")

test = colman_df.merge(depart_data, how="left", on=["scheduled_depart","Departing","Destination","Vessel","Date"])

# TODO: deal with overlapping dates data