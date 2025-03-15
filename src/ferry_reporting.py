""" 
TODO:
- break down by day of week
"""

import pandas as pd
import matplotlib.pyplot as plt

DATA_ROOT = "/Users/elyebliss/Documents/Just4Plots/data/"
OUTPUT_ROOT = "/Users/elyebliss/Documents/Just4Plots/outputs/plots/"

# Port Townsend and (Coupeville) Keystone
data = pd.read_csv(DATA_ROOT + "Kennewick.20250305.20250311.csv", index_col=False)
# (Seattle) Colman and Bainbridge
data1 = pd.read_csv(DATA_ROOT + "Puyallup.20250301.20250313.csv", index_col=False)
data2 = pd.read_csv(DATA_ROOT + "Chimacum.20250301.20250313.csv", index_col=False)
data = pd.concat([data1, data2])

def plot_dep_arrival_times(ferry, location_1, location_2):
    """
    debug:
    ferry = data
    location_1 = "Bainbridge"
    location_2 = "Colman"
    """

    OUTFILE = f'{location_1.replace(" ","_").lower()}_{location_2.replace(" ","_").lower()}.pdf'
    # Data cleaning
    clean_cols = [c.strip() for c in ferry.columns]
    ferry.columns = clean_cols
    # Strip leading and trailing spaces from time columns
    ferry["Scheduled Depart"] = ferry["Scheduled Depart"].str.strip()
    ferry["Est. Arrival"] = ferry["Est. Arrival"].str.strip()
    ferry["Actual Depart"] = ferry["Actual Depart"].str.strip()

    # Need to get minimum, average and maximum by 'Scheduled Depart' and 'Est. Arrival'
    ferry["Scheduled Depart"] = pd.to_datetime(
        ferry["Scheduled Depart"], format="%H:%M"
    )
    ferry["Est. Arrival"] = pd.to_datetime(ferry["Est. Arrival"], format="%H:%M")
    ferry["Actual Depart"] = pd.to_datetime(ferry["Actual Depart"], format="%H:%M")

    # Group by 'Scheduled Depart' and calculate min, avg, and max for 'Actual Depart' and 'Est. Arrival'
    ferry = (
        ferry.groupby([ "Departing", "Arriving", "Scheduled Depart"])
        .agg(
            {
                "Actual Depart": ["min", "mean", "max"],
                "Est. Arrival": ["min", "mean", "max"],
            }
        )
        .reset_index()
    )

    # Rename columns for clarity
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

    # Calculate time differences in minutes

    # check for values that overflow midnight
    # Function to calculate time differences in minutes
    def calculate_time_diff(scheduled, actual):
        if actual < scheduled:
            actual += pd.Timedelta(days=1)
        return (actual - scheduled).total_seconds() / 60

    # Calculate time differences in minutes
    ferry["Earliest Actual Depart Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Earliest Actual Depart"]), axis=1)
    ferry["Avg Actual Depart Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Avg Actual Depart"]), axis=1)
    ferry["Latest Actual Depart Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Latest Actual Depart"]), axis=1)
    ferry["Earliest Est. Arrival Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Earliest Est. Arrival"]), axis=1)
    ferry["Avg Est. Arrival Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Avg Est. Arrival"]), axis=1)
    ferry["Latest Est. Arrival Diff"] = ferry.apply(lambda row: calculate_time_diff(row["Scheduled Depart"], row["Latest Est. Arrival"]), axis=1)

    
    # ferry["Earliest Actual Depart Diff"] = (
    #     ferry["Earliest Actual Depart"] - ferry["Scheduled Depart"]
    # ).dt.total_seconds() / 60
    # ferry["Avg Actual Depart Diff"] = (
    #     ferry["Avg Actual Depart"] - ferry["Scheduled Depart"]
    # ).dt.total_seconds() / 60
    # ferry["Latest Actual Depart Diff"] = (
    #     ferry["Latest Actual Depart"] - ferry["Scheduled Depart"]
    # ).dt.total_seconds() / 60
    # ferry["Earliest Est. Arrival Diff"] = (
    #     ferry["Earliest Est. Arrival"] - ferry["Scheduled Depart"]
    # ).dt.total_seconds() / 60
    # ferry["Avg Est. Arrival Diff"] = (
    #     ferry["Avg Est. Arrival"] - ferry["Scheduled Depart"]
    # ).dt.total_seconds() / 60
    # ferry["Latest Est. Arrival Diff"] = (
    #     ferry["Latest Est. Arrival"] - ferry["Scheduled Depart"]
    # ).dt.total_seconds() / 60

    # Convert 'Scheduled Depart' to string format for y-axis labels
    ferry["Scheduled Depart Str"] = ferry["Scheduled Depart"].dt.strftime("%H:%M")

    # Make 2 data frames based on departing /arriving location
    ferry_dir_1 = ferry[ferry["Departing"] == location_1]
    ferry_dir_2 = ferry[ferry["Departing"] == location_2]

    # Plotting
    fig, ax = plt.subplots(2, 1, figsize=(18, 15))

    # Function to create box and whiskers plot
    def create_box_and_whiskers(ax, data, title):
        for i, row in data.iterrows():
            # Plot lines
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
            # Plot markers
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
            # Annotate with original times
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
                color="black",
            )
            ax.annotate(
                row["Earliest Est. Arrival"].strftime("%H:%M"),
                (row["Earliest Est. Arrival Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(-20, -4),
                ha="center",
                color="black",
            )
            ax.annotate(
                row["Latest Est. Arrival"].strftime("%H:%M"),
                (row["Latest Est. Arrival Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(20, -4),
                ha="center",
                color="black",
            )
            ax.annotate(
                row["Avg Est. Arrival"].strftime("%H:%M"),
                (row["Avg Est. Arrival Diff"], row["Scheduled Depart Str"]),
                textcoords="offset points",
                xytext=(0, -15),
                ha="center",
                color="black",
            )
        ax.set_title(title)
        ax.set_xlabel("Minutes from Scheduled Departure")
        ax.set_ylabel("Scheduled Departure")
        ax.invert_yaxis()

    # Create box and whiskers plot for each direction
    create_box_and_whiskers(ax[0], ferry_dir_1, f"{location_1} to {location_2}")
    create_box_and_whiskers(ax[1], ferry_dir_2, f"{location_2} to {location_1}")

    plt.tight_layout()
    plt.show()
    plt.savefig(OUTPUT_ROOT + OUTFILE,bbox_inches="tight")


plot_dep_arrival_times(data, "Port Townsend", "Keystone")
plot_dep_arrival_times(data, "Colman","Bainbridge")
