"""
Make a plot that is regularly updated with today's ferry data.

"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import os
import re
import requests
from bs4 import BeautifulSoup
from matplotlib.backends.backend_pdf import PdfPages
import math

DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../data/ferry/ferry_merged_space_delays/"
)
PLOT_FOLDER = os.path.join(os.path.dirname(__file__), "../docs/")
MAIN_FOLDER = os.path.join(os.path.dirname(__file__), "..")

df_full = pd.read_parquet(DATA_FOLDER + "ferry_merged_space_delays.parquet")

today = datetime.date.today().strftime("%m/%d/%Y")

day_of_week = datetime.date.today().strftime("%A")

# get y-lims for day of week
y_lims = df_full[df_full["Departing"].isin(["Colman", "Bainbridge", "Edmonds", "Kingston"])]
y_lims = y_lims[y_lims["day_of_week"] == day_of_week]
y_upper = math.ceil(y_lims["depart_dif"].max() / 5) * 5 + 5
y_lower = math.floor(y_lims["soldout_dif"].min()/5)*5 - 5



## Constants
dock_dict_names = {
    "Colman": "Seattle",
    "Bainbridge": "Bainbridge",
    "Kingston": "Kingston",
    "Edmonds": "Edmonds",
}

def combine_pngs_2x2(png_files, output_path):
    """Combine 4 PNG files into a 2x2 grid PDF."""

    title = f"{day_of_week}, {today}"
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    axs = axs.flatten()
    
    for ax, png_file in zip(axs, png_files):
        # Read and display the image
        img = plt.imread(png_file)
        ax.imshow(img)
        ax.axis('off')  # Hide axes
    
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.95)
    plt.tight_layout()
    
    # Save as PDF and PNG
    fig.savefig(output_path, bbox_inches='tight', dpi=300, facecolor='white')
    fig.savefig(output_path.replace('.pdf', '.png'), bbox_inches='tight', dpi=300, facecolor='white')
    plt.close(fig)

def get_ferry_schedule(dock, dest, day_of_week):
    """

    dock = "Edmonds"
    dest = "Kingston"
    """

    dock_dict_route = {
        "Colman": "sea-bi",
        "Bainbridge": "sea-bi",
        "Kingston": "ed-king",
        "Edmonds": "ed-king",
    }

    # get yesterday's bleeding over schedule
    request_url = f"https://wsdot.com/ferries/schedule/scheduledetailbyroute.aspx?route={dock_dict_route[dock]}"

    response = requests.get(request_url)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find(
        "table", class_="schedgridbyroute"
    )  # Replace with your table's class or other identifier

    rows = tables.find_all("tr")
    schdeule_data = []
    for row in rows:
        cols = []
        tds = row.find_all("td")
        for td in tds:
            # Find divs with class 'am' or 'pm' inside each td
            div = td.find("div", class_=["am", "pm"])
            if div:
                ampm = div.get("class")[0].upper()  # 'AM' or 'PM'
                time_str = f"{div.text.strip()} {ampm}"
                cols.append(time_str)
            else:
                # Fallback: just get the stripped text of the td
                cols.append(td.text.strip())
        schdeule_data.append(cols)
    schdeule_df = pd.DataFrame(schdeule_data)

    # depart and return shown on same page
    depart_index_range = schdeule_df[
        schdeule_df[0].str.contains(dock_dict_names[dock])
    ].index.tolist()
    return_index_range = schdeule_df[
        schdeule_df[0].str.contains(dock_dict_names[dest])
    ].index.tolist()

    # helper functions:
    def replace_time_str(time_str):
        time_str = time_str.replace("12:", "00:")
        time_str = time_str.replace("Midnight", "00:00")
        return time_str

    def convert_to_24_hour_format(time_str):
        pattern = re.compile(r" AM| PM")
        hour = time_str.split(":")[0]
        if hour == "12":  # Handle the case for 12 AM
            time_str = re.sub(pattern, "", time_str)  # Remove AM/PM
            return time_str  # 12 AM is already in 24-hour format
        if "PM" in time_str:

            minute = time_str.split(":")[1]
            new_hour = str(int(hour) + 12)
            new_time = f"{new_hour}:{minute}"
            time_str = re.sub(pattern, "", new_time)
        else:
            time_str = re.sub(pattern, "", time_str)
        return time_str

    if len(depart_index_range) == 1:
        # Weekday and weekend schedule are the same
        if depart_index_range[0] == 0:
            schedule = schdeule_df.iloc[
                (depart_index_range[0] + 1) : return_index_range[0]
            ]
        else:
            schedule = schdeule_df.iloc[(depart_index_range[0] + 1) : len(schdeule_df)]

        schedule[2] = schedule[2].apply(replace_time_str)
        schedule[3] = schedule[3].apply(replace_time_str)

        previous_overlap = (
            schedule[schedule[2].str.contains("AM")][2].to_list()
            + schedule[(schedule[3].str.contains("AM")) & (schedule[3] != "")][
                3
            ].to_list()
        )
        todays_schedule = (
            schedule[0].to_list()
            + schedule[1].to_list()
            + schedule[~schedule[2].str.contains("AM")][2].to_list()
            + schedule[(~schedule[3].str.contains("AM")) & (schedule[3] != "")][
                3
            ].to_list()
        )
        todays_schedule = previous_overlap + todays_schedule
        todays_schedule = [
            convert_to_24_hour_format(time_str) for time_str in todays_schedule
        ]

    else:
        if depart_index_range[0] == 0:
            weekday_schedule = schdeule_df.iloc[
                (depart_index_range[0] + 1) : return_index_range[0]
            ]
            weekend_schedule = schdeule_df.iloc[
                (depart_index_range[1] + 1) : return_index_range[1]
            ]
        else:
            weekday_schedule = schdeule_df.iloc[
                (depart_index_range[0] + 1) : return_index_range[1]
            ]
            weekend_schedule = schdeule_df.iloc[
                (depart_index_range[1] + 1) : len(schdeule_df)
            ]

        weekday_schedule[2] = weekday_schedule[2].apply(replace_time_str)
        weekday_schedule[3] = weekday_schedule[3].apply(replace_time_str)
        weekend_schedule[2] = weekend_schedule[2].apply(replace_time_str)
        weekend_schedule[3] = weekend_schedule[3].apply(replace_time_str)

        if day_of_week in ["Saturday", "Sunday"]:
            if day_of_week == "Saturday":
                previous_overlap = (
                    weekday_schedule[weekday_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekday_schedule[
                        (weekday_schedule[3].str.contains("AM"))
                        & (weekday_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = (
                    weekend_schedule[0].to_list()
                    + weekend_schedule[1].to_list()
                    + weekend_schedule[~weekend_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekend_schedule[
                        (~weekend_schedule[3].str.contains("AM"))
                        & (weekend_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = previous_overlap + todays_schedule
                todays_schedule = [
                    convert_to_24_hour_format(time_str) for time_str in todays_schedule
                ]
            else:
                previous_overlap = (
                    weekend_schedule[weekend_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekend_schedule[
                        (weekend_schedule[3].str.contains("AM"))
                        & (weekend_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = (
                    weekend_schedule[0].to_list()
                    + weekend_schedule[1].to_list()
                    + weekend_schedule[~weekend_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekend_schedule[
                        (~weekend_schedule[3].str.contains("AM"))
                        & (weekend_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = previous_overlap + todays_schedule
                todays_schedule = [
                    convert_to_24_hour_format(time_str) for time_str in todays_schedule
                ]
        else:
            if day_of_week == "Monday":
                previous_overlap = (
                    weekend_schedule[weekend_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekend_schedule[
                        (weekend_schedule[3].str.contains("AM"))
                        & (weekend_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = (
                    weekday_schedule[0].to_list()
                    + weekday_schedule[1].to_list()
                    + weekday_schedule[~weekday_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekday_schedule[
                        (~weekday_schedule[3].str.contains("AM"))
                        & (weekday_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = previous_overlap + todays_schedule
                todays_schedule = [
                    convert_to_24_hour_format(time_str) for time_str in todays_schedule
                ]
            else:
                previous_overlap = (
                    weekday_schedule[weekday_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekday_schedule[
                        (weekday_schedule[3].str.contains("AM"))
                        & (weekday_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = (
                    weekday_schedule[0].to_list()
                    + weekday_schedule[1].to_list()
                    + weekday_schedule[~weekday_schedule[2].str.contains("AM")][
                        2
                    ].to_list()
                    + weekday_schedule[
                        (~weekday_schedule[3].str.contains("AM"))
                        & (weekday_schedule[3] != "")
                    ][3].to_list()
                )
                todays_schedule = previous_overlap + todays_schedule
                todays_schedule = [
                    convert_to_24_hour_format(time_str) for time_str in todays_schedule
                ]

    # previous method also shows which vessels are planned. Good to keep for modeling stage

    # get today's ferry schedule
    # dock_dict_nums = {
    #     "Colman": 7,
    #     "Bainbridge": 3,
    #     "Kingston": 12,
    #     "Edmonds": 8,
    # }
    # schedule_date = datetime.date.today().strftime("%Y%m%d")
    # previous_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")

    # get today's schedule
    # request_url = f"https://www.wsdot.com/Ferries/Schedule/scheduledetail.aspx?tripdate={schedule_date}&departingterm={dock_dict[dock]}&arrivingterm={dock_dict[dest]}"

    # response = requests.get(request_url)
    # html_content = response.text
    # soup = BeautifulSoup(html_content, 'html.parser')
    # table = soup.find('table', class_='schedgrid')  # Replace with your table's class or other identifier

    # rows = table.find_all('tr')
    # schdeule_data = []
    # for row in rows:
    #     cols = row.find_all('td')
    #     cols = [ele.text.strip() for ele in cols]
    #     schdeule_data.append(cols)
    # schdeule_df = pd.DataFrame(schdeule_data)
    # schdeule_df.columns = ["time","vessel","null"]
    # schdeule_df = schdeule_df[~schdeule_df['time'].isnull()]
    # # covert times after PM to 24-hour format
    # schdeule_df = schdeule_df.reset_index(drop=True)
    # schdeule_df.drop(columns=["null"], inplace=True)
    # schedule_am_index = schdeule_df[schdeule_df["time"]=='AM'].index.tolist()[0]
    # schedule_pm_index = schdeule_df[schdeule_df["time"]=='PM'].index.tolist()[0]
    # midnight_index = schdeule_df[schdeule_df["time"].str.contains('AM ')].index.tolist()[0]
    # schdeule_df = schdeule_df[schdeule_df.index <midnight_index]
    # schedule_am = schdeule_df[schdeule_df.index<schedule_pm_index]
    # schedule_am = schedule_am[~schedule_am["vessel"].isnull()]
    # schedule_pm = schdeule_df[schdeule_df.index>schedule_pm_index]

    # def convert_to_24_hour_format(time_str):
    #     hour = time_str.split(':')[0]
    #     if hour == '12':  # Handle the case for 12 AM
    #         return time_str  # 12 AM is already in 24-hour format
    #     minute = time_str.split(':')[1]
    #     new_hour = str(int(hour)+12)
    #     new_time = f"{new_hour}:{minute}"
    #     return new_time

    # schedule_pm["time"] = schedule_pm["time"].apply(convert_to_24_hour_format)

    # schdeule_df = pd.concat([schedule_am, schedule_pm], ignore_index=True)

    return todays_schedule


def plot_scatter_day(data, dock, dest, day_of_week, date):
    """
    data = df_full.copy()
    dock = "Bainbridge"
    dest = "Colman"
    day_of_week = day_of_week
    date = today

    """
    graph_title = (
        f"{dock_dict_names[dock]} to {dock_dict_names[dest]}"
    )
    filename_date = date.replace("/", "-")
    filename = f"{dock_dict_names[dock]}_to_{dock_dict_names[dest]}_{day_of_week}_{filename_date}.png"
    # filter
    df = data[data["Destination"] == dest]
    df = df[df["Departing"] == dock]
    df = df[df["day_of_week"] == day_of_week]
    df = df.sort_values(by="scheduled_depart")

    # format
    df["scheduled_depart"] = pd.to_datetime(df["scheduled_depart"], format="%H:%M")

    today_df = df[df["Date"] == date]
    prev_df = df[df["Date"] != date]

    depart_times = get_ferry_schedule(dock, dest, day_of_week)
    depart_times = pd.to_datetime(depart_times, format="%H:%M")

    fig, ax = plt.subplots(figsize=(12, 6))
    # Plot depart_dif above the x-axis

    dots_1_historic = plt.plot(
        prev_df["scheduled_depart"].dt.strftime("%H:%M"),
        prev_df["depart_dif"],
        "o",
        label="Actual departure (historic)",
        color="blue",
        markeredgecolor="none",
        alpha=0.2,
        markersize=14
    )
    dots_1_today = plt.plot(
        today_df["scheduled_depart"].dt.strftime("%H:%M"),
        today_df["depart_dif"],
        "o",
        label="Actual departure (today)",
        color="black",
        alpha=1,
        markersize=14
    )

    dots_2_historic = plt.plot(
        prev_df["scheduled_depart"].dt.strftime("%H:%M"),
        prev_df["soldout_dif"],
        "o",
        label="Sellout time (historic)",
        color="red",
        markeredgecolor="none",
        alpha=0.2,
        markersize=14
    )

    dots_2_today = plt.plot(
        today_df["scheduled_depart"].dt.strftime("%H:%M"),
        today_df["soldout_dif"],
        "x",
        label="Sellout time (today)",
        color="black",
        alpha=1,
        markersize=14
    )

    ax.spines["bottom"].set_position(("data", 0))
    ax.set_xticks(depart_times.strftime("%H:%M"))
    ax.set_xticklabels(depart_times.strftime("%H:%M"), rotation=45, fontsize=12)

    # Customize each subplot
    # ax.set_title(day_of_week, fontsize=12)
    ax.axhline(
        0, color="black", linewidth=0.8, linestyle="--"
    )  # Add a horizontal line at y=0

    ax.set_ylabel("Difference (Minutes)", fontsize=12)
    ax.set_ylim(ymin=y_lower, ymax=y_upper)
    ax.legend(loc="upper left", fontsize=12)
    # # Adjust layout
    fig.suptitle(graph_title)
    fig.text(0.5, -0.05, "Scheduled Departure Time", ha="center", fontsize=14)
    plt.tight_layout()
    fig.savefig(PLOT_FOLDER + filename, bbox_inches="tight", dpi=300, facecolor="white")
    # plt.show()

    return fig


fig_1 = plot_scatter_day(df_full, "Colman", "Bainbridge", day_of_week, today)
fig_2 = plot_scatter_day(df_full, "Bainbridge", "Colman", day_of_week, today)
fig_3 = plot_scatter_day(df_full, "Edmonds", "Kingston", day_of_week, today)
fig_4 = plot_scatter_day(df_full, "Kingston", "Edmonds", day_of_week, today)


png_files = [
    os.path.join(PLOT_FOLDER, f"Seattle_to_Bainbridge_{day_of_week}_{today.replace('/', '-')}.png"),
    os.path.join(PLOT_FOLDER, f"Bainbridge_to_Seattle_{day_of_week}_{today.replace('/', '-')}.png"),
    os.path.join(PLOT_FOLDER, f"Edmonds_to_Kingston_{day_of_week}_{today.replace('/', '-')}.png"),
    os.path.join(PLOT_FOLDER, f"Kingston_to_Edmonds_{day_of_week}_{today.replace('/', '-')}.png")
]

output_path = os.path.join(MAIN_FOLDER, f"all_routes_today.pdf")
combine_pngs_2x2(png_files, output_path)