import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import to_rgba
import pandas as pd
import datetime
import sys
import math
import matplotlib.dates as mdates
import os
import streamlit as st

# Page Config  #####################################################
st.set_page_config(page_title="Ferry Tracker", layout="wide")

# Set variables #####################################################
DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/ferry/ferry_merged_space_delays/"
)


@st.cache_data(ttl=600)
def load_data(data_folder):
    dataset = pd.read_parquet(
        os.path.join(data_folder, "ferry_merged_space_delays.parquet")
    )
    return dataset


today = datetime.date.today().strftime("%m/%d/%Y")
day_of_week = datetime.date.today().strftime("%A")


depart_dock = "Colman"
arrive_dock = "Bainbridge"

## Constants
dock_dict_names = {
    "Colman": "Seattle",
    "Bainbridge": "Bainbridge",
    "Kingston": "Kingston",
    "Edmonds": "Edmonds",
}

# Filter data and format #####################################################

df = load_data(DATA_FOLDER)
df = df[df["Departing"] == depart_dock]
df = df[df["Destination"] == arrive_dock]
df = df[df["day_of_week"] == day_of_week]

df["scheduled_depart"] = pd.to_datetime(df["scheduled_depart"]).dt.time
df["scheduled_depart"] = df["scheduled_depart"].apply(lambda t: t.strftime("%H:%M"))
df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%m/%d/%Y")

todays_schedules = df[df["Date"] == today]["scheduled_depart"]
todays_schedules = pd.to_datetime(todays_schedules).dt.time
todays_schedules = todays_schedules.apply(lambda t: t.strftime("%H:%M"))
todays_schedules = todays_schedules.unique().astype(str).tolist()

df = df[~df["actual_depart"].isna()]
time_cols = ["actual_depart", "est_arrival"]
for col in time_cols:
    df[col] = pd.to_datetime(df[col]).dt.time
    df[col] = df[col].apply(lambda t: t.strftime("%H:%M"))

st.title("Seattle to Bainbridge")


def plot_scatter_day(data, dock, dest, day_of_week, date, schedule):
    """
    Troubleshooting:
    data = df.copy()
    dock, dest, day_of_week, date, schedule = depart_dock, arrive_dock, day_of_week, today, todays_schedules
    """

    graph_title = (
        f"{dock_dict_names[dock]} to {dock_dict_names[dest]}\n{day_of_week}, {date}"
    )

    df = data.copy()
    df = df.sort_values(by="scheduled_depart")

    # format times as datetime (NOT strings)
    df["scheduled_depart"] = pd.to_datetime(df["scheduled_depart"], format="%H:%M")

    today_df = df[df["Date"] == date]
    prev_df = df[df["Date"] != date]

    # scale alpha by recency
    prev_df["days_ago"] = (
        pd.to_datetime(date) - pd.to_datetime(prev_df["Date"])
    ).dt.days
    prev_df["inverse_days_ago"] = (365 - prev_df["days_ago"]) / 365
    prev_df["inverse_days_ago"] = prev_df["inverse_days_ago"] / 3

    prev_df["departure_color"] = prev_df["inverse_days_ago"].apply(
        lambda a: to_rgba("blue", alpha=a)
    )
    prev_df["sellout_color"] = prev_df["inverse_days_ago"].apply(
        lambda a: to_rgba("red", alpha=a)
    )

    y_upper = 60  # math.ceil(df["depart_dif"].max() / 5) * 5 + 5
    y_lower = -60  # math.floor(df["soldout_dif"].min() / 5) * 5 - 5

    # schedule ticks as datetime
    depart_times = pd.to_datetime(schedule, format="%H:%M")

    fig, ax = plt.subplots(figsize=(16, 9))

    # TODAY departures
    ax.scatter(
        today_df["scheduled_depart"],
        today_df["depart_dif"],
        label="Actual departure (today)",
        c="black",
        edgecolors="white",
        s=500,
        zorder=5,
    )

    # HISTORIC departures
    ax.scatter(
        prev_df["scheduled_depart"],
        prev_df["depart_dif"],
        label="Actual departure (historic, scaled by recency)",
        c=prev_df["departure_color"].tolist(),
        edgecolors="none",
        s=196,
    )

    # TODAY sellouts
    ax.plot(
        today_df["scheduled_depart"],
        today_df["soldout_dif"],
        "X",
        label="Sellout time (today)",
        color="black",
        alpha=1,
        markersize=20,
        zorder=10,
    )

    # HISTORIC sellouts
    ax.scatter(
        prev_df["scheduled_depart"],
        prev_df["soldout_dif"],
        label="Sellout time (historic, scaled by recency)",
        c=prev_df["sellout_color"].tolist(),
        marker="X",
        edgecolors="none",
        s=196,
    )

    # Move x-axis to y=0
    ax.spines["bottom"].set_position(("data", 0))

    # Proportional datetime axis formatting
    ax.set_xticks(depart_times)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.tick_params(axis="x", which="major", pad=20)
    plt.setp(ax.get_xticklabels(), rotation=60, fontsize=18)

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

    ax.set_ylabel("Difference (Minutes)", fontsize=18)
    plt.setp(ax.get_yticklabels(), fontsize=18)
    ax.set_ylim(ymin=y_lower, ymax=y_upper)

    leg = ax.legend(loc="lower left", fontsize=18)
    for handle in leg.legend_handles:
        handle.set_alpha(1)

    fig.suptitle(graph_title, fontsize=30)
    fig.text(0.5, 0.05, "Scheduled Departure Time", ha="center", fontsize=14)

    plt.show()


plot_scatter_day(df, depart_dock, arrive_dock, day_of_week, today, todays_schedules)
