"""
Make plots of weekly ferry space and departure data
"""

import pandas as pd
import os
import matplotlib.pyplot as plt
import re
from datetime import datetime, timedelta

SPACE_FOLDER = "../data/ferry_spaces/"
DEP_TIME_FOLDER = "../data/"
OUTPUT_ROOT = "../outputs/plots/"
outfile_week = f"{OUTPUT_ROOT}ferry_04252025_thru_04302025.png"

depart_data = pd.read_csv(
    DEP_TIME_FOLDER + "ferry_data_combined_04252025_thru_04302025.csv"
)

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


def format_space(data, dockname):
    """
    df = colman_df.copy()
    dockname = "Colman"
    """
    df = data.copy()
    df["Date"] = pd.to_datetime(df["timestamp"]).dt.strftime("%m/%d/%Y")
    df["Departing"] = dockname
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
        scheduled_depart[0] != "0" and actual_depart[0] == "0"
    )
    schedule_after_midnight_actual_b4_midnight = (
        scheduled_depart[0] == "0" and actual_depart[0] != "0"
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
    soldout_minutes = int(soldout_time.split(":")[0]) * 60 + int(
        soldout_time.split(":")[1]
    )

    soldout_b4_midnight_scheduled_after_midnight = (
        scheduled_depart[0] == "0" and soldout_time[0] != "0"
    )
    soldout_after_midnight_scheduled_b4_midnight = (
        scheduled_depart[0] != "0" and soldout_time[0] == "0"
    )  # should be rare

    if soldout_b4_midnight_scheduled_after_midnight:
        soldout_dif = -scheduled_minutes - (24 * 60 - soldout_minutes)
    elif soldout_after_midnight_scheduled_b4_midnight:
        soldout_dif = soldout_minutes + (24 * 60 - scheduled_minutes)
    else:
        soldout_dif = soldout_minutes - scheduled_minutes
    return soldout_dif


def create_plot_df(data, dock):
    """
    data = merged.copy()
    dock = "Colman"
    """
    df = data[data["Departing"] == dock].copy()

    df["depart_dif"] = df.apply(lambda x: calculate_depart_dif(x), axis=1)

    df["soldout_time"] = pd.to_datetime(
        df["soldout_time"], format="%H:%M:%S"
    ).dt.strftime("%H:%M")
    df["soldout_time"].fillna(df["scheduled_depart"], inplace=True)
    df["soldout_dif"] = df.apply(lambda x: calculate_soldout_dif(x), axis=1)

    return df


def plot_week(data, dock, dest, outfile_week):
    """
    data = merged.copy()
    dock = "Colman"
    """
    df = create_plot_df(data, dock)
    df = df[df["Destination"] == dest]

    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    df["day_of_week"] = pd.Categorical(
        df["day_of_week"], categories=days_order, ordered=True
    )

    df["scheduled_depart"] = pd.to_datetime(df["scheduled_depart"], format="%H:%M")

    # Create subplots for each day of the week
    fig, axes = plt.subplots(
        1, 7, figsize=(60, 6), sharey=True
    )  # 7 subplots horizontally, shared y-axis

    for i, day in enumerate(days_order):
        ax = axes[i]
        day_data = df[df["day_of_week"] == day].sort_values(
            by="scheduled_depart"
        )  # Sort by scheduled_depart

        # Plot depart_dif above the x-axis
        ax.bar(
            day_data["scheduled_depart"].dt.strftime("%H:%M"),
            day_data["depart_dif"],
            label="Dif btw scheduled & actual departure",
            color="blue",
            alpha=0.3,
        )

        # Plot soldout_dif below the x-axis
        ax.bar(
            day_data["scheduled_depart"].dt.strftime("%H:%M"),
            day_data["soldout_dif"],
            label="Dif btw sellout time & scheduled departure",
            color="red",
            alpha=0.3,
        )

        # Customize each subplot
        ax.set_title(day, fontsize=12)
        ax.axhline(
            0, color="black", linewidth=0.8, linestyle="--"
        )  # Add a horizontal line at y=0

        ax.tick_params(axis="x", rotation=45, labelsize=8)

        # Keep x-ticks on the y=0 line
        ax.spines["bottom"].set_position(("data", 0))

        if i == 0:  # Add y-axis label only to the first subplot
            ax.set_ylabel("Difference (Minutes)", fontsize=10)

    # Adjust layout
    fig.suptitle(f"{dock} to {dest}")
    fig.text(0.5, 0.02, "Scheduled Depart Time", ha="center", fontsize=12)
    plt.tight_layout()
    plt.legend(
        ["depart_dif", "soldout_dif"],
        loc="upper left",
        fontsize=8,
        bbox_to_anchor=(1.05, 1),
    )
    fig.savefig(outfile_week, bbox_inches="tight", dpi=300, facecolor="white")
    plt.show()


def plot_day(data, dock, dest, outfile_day, day_of_week, custom_title):
    """
    data = merged.copy()
    dock = "Colman"
    dest = "Bainbridge"
    day_of_week = "Saturday"
    custom_title = day_title
    """
    df = data[data["Destination"] == dest]
    df = create_plot_df(df, dock)

    df = df[df["day_of_week"] == day_of_week]

    df["scheduled_depart"] = pd.to_datetime(df["scheduled_depart"], format="%H:%M")

    fig, ax = plt.subplots(figsize=(12, 6))

    day_data = df.sort_values(by="scheduled_depart")

    # Plot depart_dif above the x-axis
    bar1 = ax.bar(
        day_data["scheduled_depart"].dt.strftime("%H:%M"),
        day_data["depart_dif"],
        label="Dif btw scheduled & actual departure",
        color="blue",
        alpha=0.3,
    )

    # Plot soldout_dif below the x-axis
    bar2 = ax.bar(
        day_data["scheduled_depart"].dt.strftime("%H:%M"),
        day_data["soldout_dif"],
        label="Dif btw scheduled departure & sellout time",
        color="red",
        alpha=0.3,
    )
    # Annotate negative soldout_dif values
    for i, row in day_data.iterrows():
        if row["soldout_dif"] < 0:
            if row["soldout_dif"] > -25:
                offset_below_val = -25
            else:
                offset_below_val = -10
            ax.annotate(
                f'{row["soldout_time"]}', 
                xy=(row["scheduled_depart"].strftime("%H:%M"), row["soldout_dif"]), 
                xytext=(0, offset_below_val),  # Offset annotation below the bar
                textcoords="offset points",
                ha='center', 
                va='top', 
                fontsize=8, 
                color='red'
            )
    # annotate departure time if more than 15 delayed
    for i, row in day_data.iterrows():
        if row["depart_dif"] >= 15:
            ax.annotate(
                f'{row["actual_depart"]}', 
                xy=(row["scheduled_depart"].strftime("%H:%M"), row["depart_dif"]), 
                xytext=(0, 10),  # Offset annotation below the bar
                textcoords="offset points",
                ha='center', 
                va='top', 
                fontsize=8, 
                color='blue'
            )
    # Customize each subplot
    ax.set_title(day_of_week, fontsize=12)
    ax.axhline(
        0, color="black", linewidth=0.8, linestyle="--"
    )  # Add a horizontal line at y=0

    ax.tick_params(axis="x", rotation=45, labelsize=8)

    # Keep x-ticks on the y=0 line
    ax.spines["bottom"].set_position(("data", 0))

    ax.set_ylabel("Difference (Minutes)", fontsize=10)

    ax.legend(loc="lower right", fontsize=10)
    # Adjust layout
    fig.suptitle(custom_title)
    fig.text(0.5, -0.05, "Scheduled Departure Time", ha="center", fontsize=12)
    plt.tight_layout()
    # plt.legend(['depar#t_dif', 'soldout_dif'], loc='upper left', fontsize=8, bbox_to_anchor=(1.05, 1))
    fig.savefig(outfile_day, bbox_inches="tight", dpi=300, facecolor="white")
    plt.show()


## DRIVER CODE
# merge ferry space data with ferry departure data
space_files = os.listdir(SPACE_FOLDER)
edmonds_space = [pd.read_csv(SPACE_FOLDER + f) for f in space_files if "edmonds" in f]
bainbridge_space = [
    pd.read_csv(SPACE_FOLDER + f) for f in space_files if "bainbridge" in f
]
kingston_space = [pd.read_csv(SPACE_FOLDER + f) for f in space_files if "kingston" in f]
colman_space = [pd.read_csv(SPACE_FOLDER + f) for f in space_files if "colman" in f]
edmonds_df = pd.concat(edmonds_space, ignore_index=True)
bainbridge_df = pd.concat(bainbridge_space, ignore_index=True)
kingston_df = pd.concat(kingston_space, ignore_index=True)
colman_df = pd.concat(colman_space, ignore_index=True)

# format the dataframes
depart_data = format_depart(depart_data)

# Plot Seattle to Bainbridge Saturdays
space_df = format_space(colman_df, "Colman")
# merge on Depart, Destination, Vessel, and Date (from timestamp)
merged = depart_data.merge(
    space_df, how="left", on=["scheduled_depart", "Departing", "Destination", "Date"]
)
outfile_day = f"{OUTPUT_ROOT}colman_ferry_saturday.png"
day_title = f"Seattle to Bainbridge Ferry, April 26"
# plot_week(merged, "Colman", "Bainbridge", outfile_week)
plot_day(merged, "Colman", "Bainbridge", outfile_day, "Saturday", day_title)


# Plot Edmonds to Kingston Saturdays
space_df = format_space(edmonds_df, "Edmonds")
# merge on Depart, Destination, Vessel, and Date (from timestamp)
merged = depart_data.merge(
    space_df, how="left", on=["scheduled_depart", "Departing", "Destination", "Date"]
)
outfile_day = f"{OUTPUT_ROOT}edmonds_ferry_saturday.png"
day_title = f"Edmonds to Kingston Ferry, April 26"
# plot_week(merged, "Edmonds", "Kingston", outfile_week)
plot_day(merged, "Edmonds", "Kingston", outfile_day, "Saturday", day_title)



# Plot Bainbridge to Seattle Sundays
space_df = format_space(bainbridge_df, "Bainbridge")
# merge on Depart, Destination, Vessel, and Date (from timestamp)
merged = depart_data.merge(
    space_df, how="left", on=["scheduled_depart", "Departing", "Destination", "Date"]
)
outfile_day = f"{OUTPUT_ROOT}bainbridge_ferry_sunday.png"
day_title = f"Bainbridge to Seattle Ferry, April 27"
# plot_week(merged, "Colman", "Bainbridge", outfile_week)
plot_day(merged,"Bainbridge",  "Colman", outfile_day, "Sunday", day_title)


# Plot Kingston to Edmonds Sundays
space_df = format_space(kingston_df, "Kingston")
# merge on Depart, Destination, Vessel, and Date (from timestamp)
merged = depart_data.merge(
    space_df, how="left", on=["scheduled_depart", "Departing", "Destination", "Date"]
)
outfile_day = f"{OUTPUT_ROOT}kingston_ferry_sunday.png"
day_title = f"Kingston to Edmonds Ferry, April 27"
# plot_week(merged, "Edmonds", "Kingston", outfile_week)
plot_day(merged,  "Kingston","Edmonds", outfile_day, "Sunday", day_title)
