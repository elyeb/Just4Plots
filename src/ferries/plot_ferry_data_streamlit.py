import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import to_rgba
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
import requests
import io
import matplotlib.dates as mdates
import os
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Page Config  #####################################################
PACIFIC = ZoneInfo("America/Los_Angeles")
now_pacific = datetime.datetime.now(PACIFIC)
today_pacific = now_pacific.date()

today = today_pacific.strftime("%m/%d/%Y")
day_of_week = today_pacific.strftime("%A")

# Refresh the whole app every 5 minutes
st_autorefresh(interval=300000, key="datarefresh")
st.caption(f"Last refresh: {datetime.datetime.now(PACIFIC).strftime('%H:%M:%S')}")

st.set_page_config(page_title="Ferry Tracker", layout="wide")

# Set variables #####################################################
DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/ferry/ferry_merged_space_delays/"
)
DATA_URL = "https://raw.githubusercontent.com/elyeb/Just4Plots/refs/heads/main/data/ferry/ferry_merged_space_delays/ferry_merged_space_delays.parquet"
STATIC_PLOT_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../outputs/plots/ferries/"
)


# st.cache_data.clear()
@st.cache_data(ttl=300)
def load_data(url):
    response = requests.get(url)
    response.raise_for_status()  # fail loudly if download fails

    buffer = io.BytesIO(response.content)
    df = pd.read_parquet(buffer)

    return df


# def load_data(data_folder):
#     dataset = pd.read_parquet(
#         os.path.join(data_folder, "ferry_merged_space_delays.parquet")
#     )
#     return dataset


## Constants
dock_dict_names = {
    "Colman": "Seattle",
    "Bainbridge": "Bainbridge",
    "Kingston": "Kingston",
    "Edmonds": "Edmonds",
}

# Load full data and define plot function #####################################################

# data = load_data(DATA_FOLDER)
data = load_data(DATA_URL)


# @st.fragment(run_every="5m")
def plot_scatter_day(data, dock, dest, day_of_week, date):
    """
    Troubleshooting:
    data = df.copy()
    dock, dest, day_of_week, date = depart_dock, arrive_dock, day_of_week, today
    """

    graph_title = f"{day_of_week}, {date}"

    df = data.copy()

    ## FORMAT DATA
    df = data.copy()
    df = df[df["Departing"] == dock]
    df = df[df["Destination"] == dest]
    df = df[df["day_of_week"] == day_of_week]

    df["scheduled_depart"] = pd.to_datetime(
        df["scheduled_depart"], format="%H:%M"
    ).dt.time
    df["scheduled_depart"] = df["scheduled_depart"].apply(lambda t: t.strftime("%H:%M"))
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%m/%d/%Y")

    todays_schedules = df[df["Date"] == today]["scheduled_depart"]
    todays_schedules = pd.to_datetime(todays_schedules, format="%H:%M").dt.time
    todays_schedules = todays_schedules.apply(lambda t: t.strftime("%H:%M"))
    todays_schedules = todays_schedules.unique().astype(str).tolist()

    df = df[~df["actual_depart"].isna()]
    time_cols = ["actual_depart", "est_arrival"]
    for col in time_cols:
        df[col] = pd.to_datetime(df[col], format="%H:%M").dt.time
        df[col] = df[col].apply(lambda t: t.strftime("%H:%M"))

    df = df.sort_values(by="scheduled_depart")

    # format times as datetime (NOT strings)
    df["scheduled_depart"] = pd.to_datetime(df["scheduled_depart"], format="%H:%M")

    today_df = df[df["Date"] == date]
    prev_df = df[df["Date"] != date]

    # scale alpha by recency
    prev_df["days_ago"] = (
        pd.to_datetime(date) - pd.to_datetime(prev_df["Date"])
    ).dt.days
    prev_df["inverse_days_ago"] = max(
        (365 - prev_df["days_ago"]) / 365, 0.001
    )  # prevent negatives
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
    depart_times = pd.to_datetime(todays_schedules, format="%H:%M")

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

    # save static version of plot
    save_path = os.path.join(STATIC_PLOT_FOLDER, f"{dock}_to_{dest}.png")
    fig.savefig(save_path, bbox_inches="tight")
    st.pyplot(fig)


# Plot 2x2 layout #####################################################

col1, col2 = st.columns(2)
with col1:
    st.subheader("Seattle to Bainbridge")
    depart_dock = "Colman"
    arrive_dock = "Bainbridge"
    plot_scatter_day(data, depart_dock, arrive_dock, day_of_week, today)

with col2:
    st.subheader("Bainbridge to Seattle")
    depart_dock = "Bainbridge"
    arrive_dock = "Colman"
    plot_scatter_day(data, depart_dock, arrive_dock, day_of_week, today)

# Row 2
col3, col4 = st.columns(2)
with col3:
    st.subheader("Edmonds to Kingston")
    depart_dock = "Edmonds"
    arrive_dock = "Kingston"
    plot_scatter_day(data, depart_dock, arrive_dock, day_of_week, today)

with col4:
    st.subheader("Kingston to Edmonds")
    depart_dock = "Kingston"
    arrive_dock = "Edmonds"
    plot_scatter_day(data, depart_dock, arrive_dock, day_of_week, today)
