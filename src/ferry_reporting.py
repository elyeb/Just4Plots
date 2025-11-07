""" 
TODO:
- break down by day of week
- scrape https://wsdot.com/ferries/vesselwatch/terminals.aspx to get sold out times
"""

import pandas as pd
import matplotlib.pyplot as plt
import datetime

DATA_ROOT = "/Users/elyebliss/Documents/Just4Plots/data/"
OUTPUT_ROOT = "/Users/elyebliss/Documents/Just4Plots/outputs/plots/"

# Port Townsend and (Coupeville) Keystone
# data = pd.read_csv(DATA_ROOT + "Kennewick.20250305.20250311.csv", index_col=False)
# (Seattle) Colman and Bainbridge
# data1 = pd.read_csv(DATA_ROOT + "Puyallup.20250301.20250313.csv", index_col=False)
# data2 = pd.read_csv(DATA_ROOT + "Chimacum.20250301.20250313.csv", index_col=False)
# data = pd.concat([data1, data2])
# (Seattle) Colman and Bainbridge, 2-17 to 3-17
data1 = pd.read_csv(DATA_ROOT + "Puyallup.20250217.20250317.csv", index_col=False)
data2 = pd.read_csv(DATA_ROOT + "Chimacum.20250217.20250317.csv", index_col=False)
data3 = pd.read_csv(DATA_ROOT + "Kaleetan.20250217.20250317.csv", index_col=False)


data = pd.concat([data1, data2, data3])
clean_cols = [c.strip() for c in data.columns]
data.columns = clean_cols
ports = ["Colman","Bainbridge"]
data = data[data.Departing.isin(ports)]

def prep_for_range_plot(df):
    ferry = df.copy()
    ferry["Scheduled Depart"] = ferry["Scheduled Depart"].str.strip()
    ferry["Est. Arrival"] = ferry["Est. Arrival"].str.strip()
    ferry["Actual Depart"] = ferry["Actual Depart"].str.strip()

    ferry["Scheduled Depart"] = pd.to_datetime(ferry["Scheduled Depart"], format="%H:%M")
    ferry["Est. Arrival"] = pd.to_datetime(ferry["Est. Arrival"], format="%H:%M")
    ferry["Actual Depart"] = pd.to_datetime(ferry["Actual Depart"], format="%H:%M")

    def after_midnights(scheduled, actual):
        elevenpm = pd.to_datetime("23:00", format="%H:%M")
        if (actual < scheduled) and (scheduled > elevenpm):
            actual += pd.Timedelta(days=1)
        return actual

    ferry["Actual Depart"] = ferry.apply(lambda row: after_midnights(row["Scheduled Depart"], row["Actual Depart"]), axis=1)
    ferry["Est. Arrival"] = ferry.apply(lambda row: after_midnights(row["Scheduled Depart"], row["Est. Arrival"]), axis=1)

    ferry = (
        ferry.groupby(["Departing", "Arriving", "Scheduled Depart"])
        .agg(
            {
                "Actual Depart": ["min", "mean", "max"],
                "Est. Arrival": ["min", "mean", "max"],
            }
        )
        .reset_index()
    )

    ferry.columns = [
        "Departing",
        "Arriving",
        "Scheduled Depart",
        "Earliest Actual Depart",
        "Avg Actual Depart",
        "Latest Actual Depart",
        "Earliest Est. Arrival",
        "Avg Est. Arrival",
        "Latest Est. Arrival",
    ]

    def calculate_time_diff(scheduled, actual):
        return (actual - scheduled).total_seconds() / 60

    ferry["Earliest Actual Depart Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Earliest Actual Depart"]), axis=1)
    ferry["Avg Actual Depart Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Avg Actual Depart"]), axis=1)
    ferry["Latest Actual Depart Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Latest Actual Depart"]), axis=1)
    ferry["Earliest Est. Arrival Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Earliest Est. Arrival"]), axis=1)
    ferry["Avg Est. Arrival Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Avg Est. Arrival"]), axis=1)
    ferry["Latest Est. Arrival Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Latest Est. Arrival"]), axis=1)

    ferry["Scheduled Depart Str"] = ferry["Scheduled Depart"].dt.strftime("%H:%M")

    return ferry


def plot_dep_arrival_times_range(ferry, location_1, location_2):
    OUTFILE = f'{location_1.replace(" ","_").lower()}_{location_2.replace(" ","_").lower()}.pdf'


    ferry["Date"] = pd.to_datetime(ferry["Date"])
    ferry["Day of Week"] = ferry["Date"].dt.day_name()

    weekend = ["Saturday", "Sunday"]
    ferry_dir_1_week = ferry[(ferry["Departing"] == location_1) & (~ferry["Day of Week"].isin(weekend))]
    ferry_dir_2_week = ferry[(ferry["Departing"] == location_2) & (~ferry["Day of Week"].isin(weekend))]
    ferry_dir_1_weekend = ferry[(ferry["Departing"] == location_1) & (ferry["Day of Week"].isin(weekend))]
    ferry_dir_2_weekend = ferry[(ferry["Departing"] == location_2) & (ferry["Day of Week"].isin(weekend))]

    ferry_dir_1_week = prep_for_range_plot(ferry_dir_1_week)
    ferry_dir_2_week = prep_for_range_plot(ferry_dir_2_week)
    ferry_dir_1_weekend = prep_for_range_plot(ferry_dir_1_weekend)
    ferry_dir_2_weekend = prep_for_range_plot(ferry_dir_2_weekend)

    fig, ax = plt.subplots(2, 2, figsize=(18, 22), dpi=300)

    # Calculate the x-axis limits
    all_data = pd.concat([ferry_dir_1_week, ferry_dir_2_week, ferry_dir_1_weekend, ferry_dir_2_weekend])
    x_min = all_data[["Earliest Actual Depart Diff", "Earliest Est. Arrival Diff"]].min().min()
    x_max = all_data[["Latest Actual Depart Diff", "Latest Est. Arrival Diff"]].max().max()

    def create_box_and_whiskers(ax, data, title):
        for i, row in data.iterrows():
            ax.plot(
                [row["Earliest Actual Depart Diff"], row["Latest Actual Depart Diff"]],
                [row["Scheduled Depart Str"], row["Scheduled Depart Str"]],
                color="black",
            )
            ax.plot(
                [row["Earliest Est. Arrival Diff"], row["Latest Est. Arrival Diff"]],
                [row["Scheduled Depart Str"], row["Scheduled Depart Str"]],
                color="blue",
            )
            ax.plot(
                [row["Earliest Actual Depart Diff"]],
                [row["Scheduled Depart Str"]],
                marker="*",
                color="black",
            )
            ax.plot(
                [row["Latest Actual Depart Diff"]],
                [row["Scheduled Depart Str"]],
                marker="D",
                color="black",
            )
            ax.plot(
                [row["Avg Actual Depart Diff"]],
                [row["Scheduled Depart Str"]],
                marker="o",
                color="black",
            )
            ax.plot(
                [row["Earliest Est. Arrival Diff"]],
                [row["Scheduled Depart Str"]],
                marker="*",
                color="blue",
            )
            ax.plot(
                [row["Latest Est. Arrival Diff"]],
                [row["Scheduled Depart Str"]],
                marker="D",
                color="blue",
            )
            ax.plot(
                [row["Avg Est. Arrival Diff"]],
                [row["Scheduled Depart Str"]],
                marker="o",
                color="blue",
            )
            ax.annotate(
                row["Earliest Actual Depart"].strftime("%H:%M"),
                (row["Earliest Actual Depart Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(-20, -4),
                ha="center",
            )
            ax.annotate(
                row["Latest Actual Depart"].strftime("%H:%M"),
                (row["Latest Actual Depart Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(20, -4),
                ha="center",
            )
            ax.annotate(
                row["Avg Actual Depart"].strftime("%H:%M"),
                (row["Avg Actual Depart Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(0, -15),
                ha="center",
            )
            ax.annotate(
                row["Earliest Est. Arrival"].strftime("%H:%M"),
                (row["Earliest Est. Arrival Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(-20, -4),
                ha="center",
            )
            ax.annotate(
                row["Latest Est. Arrival"].strftime("%H:%M"),
                (row["Latest Est. Arrival Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(20, -4),
                ha="center",
            )
            ax.annotate(
                row["Avg Est. Arrival"].strftime("%H:%M"),
                (row["Avg Est. Arrival Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(0, -15),
                ha="center",
            )
            ax.set_xlim(x_min, x_max)
            ax.set_title(title)
            ax.set_xlabel("Minutes from Scheduled Departure")
            ax.set_ylabel("Scheduled Departure")
            ax.invert_yaxis()

    create_box_and_whiskers(ax[0, 0], ferry_dir_1_week, f"{location_1} to {location_2}, weekdays")
    create_box_and_whiskers(ax[1, 0], ferry_dir_2_week, f"{location_2} to {location_1}, weekdays")
    create_box_and_whiskers(ax[0, 1], ferry_dir_1_weekend, f"{location_1} to {location_2}, weekend")
    create_box_and_whiskers(ax[1, 1], ferry_dir_2_weekend, f"{location_2} to {location_1}, weekend")

    # plt.tight_layout()
    fig.savefig(OUTPUT_ROOT + 'colman_bainbridge.png', bbox_inches="tight", dpi=300)
    fig.savefig(OUTPUT_ROOT + OUTFILE, bbox_inches="tight", dpi=300)
    plt.show()


def prep_for_hist_plot(df):
    ferry = df.copy()
    ferry["Scheduled Depart"] = ferry["Scheduled Depart"].str.strip()
    ferry["Est. Arrival"] = ferry["Est. Arrival"].str.strip()
    ferry["Actual Depart"] = ferry["Actual Depart"].str.strip()

    ferry["Scheduled Depart"] = pd.to_datetime(ferry["Scheduled Depart"], format="%H:%M")
    ferry["Est. Arrival"] = pd.to_datetime(ferry["Est. Arrival"], format="%H:%M")
    ferry["Actual Depart"] = pd.to_datetime(ferry["Actual Depart"], format="%H:%M")

    def after_midnights(scheduled, actual):
        midnight = pd.to_datetime("00:00", format="%H:%M")
        if actual < scheduled:
            if ((actual - scheduled).total_seconds() / 60)>60:
                actual += pd.Timedelta(days=1)
        return actual

    ferry["Actual Depart"] = ferry.apply(lambda row: after_midnights(row["Scheduled Depart"], row["Actual Depart"]), axis=1)
    ferry["Est. Arrival"] = ferry.apply(lambda row: after_midnights(row["Scheduled Depart"], row["Est. Arrival"]), axis=1)

    

    def calculate_time_diff(scheduled, actual):
        return (actual - scheduled).total_seconds() / 60

    ferry["Actual Depart Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Actual Depart"]), axis=1)
    ferry["Est. Arrival Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Est. Arrival"]), axis=1)

    ferry["Scheduled Depart Str"] = ferry["Scheduled Depart"].dt.strftime("%H:%M")

    return ferry

def plot_hist_by_day(ferry, location_1, location_2):
    """
    ferry = data.copy()
    """
    OUTFILE = f'{location_1.replace(" ","_").lower()}_{location_2.replace(" ","_").lower()}_by_day.pdf'

    ferry["Date"] = pd.to_datetime(ferry["Date"])
    ferry["Day of Week"] = ferry["Date"].dt.day_name()

    ferry_dir_1 = ferry[ferry["Departing"] == location_1]
    # ferry_dir_2 = ferry[ferry["Departing"] == location_2]

    # Calculate the x-axis limits
    ferry_dir_1 = prep_for_hist_plot(ferry_dir_1)
    # ferry_dir_2 = prep_for_hist_plot(ferry_dir_2)
    # all_data = pd.concat([ferry_dir_1, ferry_dir_2])
    x_min = ferry_dir_1[['Actual Depart Diff','Est. Arrival Diff']].min().min()
    x_max = ferry_dir_1[['Actual Depart Diff','Est. Arrival Diff']].max().max()

    day_times = list(set(ferry_dir_1["Day of Week"]+ferry_dir_1["Scheduled Depart Str"]))
    
    num_rows = len(day_times)
    fig, ax = plt.subplots(num_rows, 1, figsize=(18, num_rows * 3)) #, dpi=300

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    row_counter = 0
    for day in days:
        dir_1_day = ferry_dir_1[ferry_dir_1["Day of Week"] == day]
        unique_scheduled_depart = sorted(dir_1_day["Scheduled Depart Str"].unique())

        for sched_depart in unique_scheduled_depart:
            dir_1_sched = dir_1_day[dir_1_day["Scheduled Depart Str"] == sched_depart]

            ax[row_counter].hist(dir_1_sched["Actual Depart Diff"], bins=range(int(x_min), int(x_max) + 5, 5), color="black", alpha=0.7, label="Actual Depart")
            ax[row_counter].hist(dir_1_sched["Est. Arrival Diff"], bins=range(int(x_min), int(x_max) + 5, 5), color="blue", alpha=0.7, label="Est. Arrival")
            ax[row_counter].set_xlim(x_min, x_max)
            ax[row_counter].set_title(f"{location_1} to {location_2} on {day} at {sched_depart}")
            ax[row_counter].set_xlabel("Minutes from Scheduled Departure")
            ax[row_counter].set_ylabel(f"{sched_depart} Frequency")
            
            row_counter += 1
    ax[row_counter-1].legend()

    plt.tight_layout()
    plt.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.95, hspace=0.4, wspace=0.4)
    fig.savefig(OUTPUT_ROOT + OUTFILE, bbox_inches="tight", dpi=300)
    plt.show()

# plot_dep_arrival_times_range(data, "Port Townsend", "Keystone")
# plot_dep_arrival_times_range(data, "Colman", "Bainbridge")
plot_hist_by_day(data, "Bainbridge","Colman" )