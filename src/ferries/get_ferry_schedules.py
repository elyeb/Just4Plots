"""
Get daily ferry schedules for seattle-bainbridge and edmonds-kingston routes.

Landing page: https://wsdot.com/ferries/schedule/scheduledetailbyroute.aspx?

Issues can arrise when conflicting schedules posted on same page, for example,
Seattle-Bainbridge has tables for:
- Feb 16, 2026 - Mar 21, 2026
- Feb 9, 2026 - Mar 21, 2026

The first table is for Leave Seattle M-F, followed by Leave Bainbridge M-F and
then the weekend table. The second date-range is for Leave Seattle S-S.
"""

import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

now_pacific = datetime.now(PACIFIC)
today_pacific = now_pacific.date()

TODAY = today_pacific.strftime("%Y_%m_%d")
day_of_week = today_pacific.strftime("%A").lower()


SCHEDULE_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/ferry/ferry_schedules/"
)
os.makedirs(SCHEDULE_FOLDER, exist_ok=True, mode=0o777)

previously_downloaded_schedules = os.listdir(SCHEDULE_FOLDER)

print(f"Getting schedule for {day_of_week} {TODAY}...")

dock_dict_names = {
    "Colman": "Seattle",
    "Bainbridge": "Bainbridge",
    "Kingston": "Kingston",
    "Edmonds": "Edmonds",
}

ROUTES = [
    ("Colman", "Bainbridge"),
    ("Bainbridge", "Colman"),
    ("Edmonds", "Kingston"),
    ("Kingston", "Edmonds"),
]


# helper functions:
def replace_time_str(time_str):
    if time_str is None:
        return ""
    time_str = str(time_str)
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


def get_ferry_schedule(dock, dest, day_of_week):
    """

    dock = "Edmonds"
    dest = "Kingston"
    day_of_week = "thursday"
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
    tables = soup.find_all("table", class_="schedgridbyroute")

    schdeule_data = []

    for table in tables:
        rows = table.find_all("tr")
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
                    cols.append(td.text.strip())
            schdeule_data.append(cols)
    schdeule_df = pd.DataFrame(schdeule_data)

    # check if schedule is split into weekdays/weekend, or if it's all daily
    departures_rows = schdeule_df[schdeule_df[0].str.contains(dock_dict_names[dock])]
    non_data_rows = schdeule_df[
        schdeule_df[0].str.contains(dock_dict_names[dock])
        | schdeule_df[0].str.contains(dock_dict_names[dest])
    ].index.tolist()
    non_data_rows += [len(schdeule_df)]
    subtables = []
    for i in range(len(non_data_rows) - 1):
        subtable = schdeule_df.iloc[non_data_rows[i] : non_data_rows[i + 1]]
        if dock_dict_names[dock] in subtable[0].iloc[0]:
            subtables.append(subtable)

    if len(departures_rows) == 1:
        # schedule is daily, not split into weekday/weekend
        schedule = subtables[0]
        schedule[1] = schedule[1].apply(replace_time_str)
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
        todays_schedule = [t for t in todays_schedule if ("AM" in t) or ("PM" in t)]
        todays_schedule = [
            convert_to_24_hour_format(time_str) for time_str in todays_schedule
        ]
        return todays_schedule
    elif len(departures_rows) == 2:
        # schedule is split into weekday/weekend
        if "Monday" in subtables[0][0].iloc[0]:
            weekday_schedule = subtables[0]
            weekend_schedule = subtables[1]
        else:
            weekday_schedule = subtables[1]
            weekend_schedule = subtables[0]
        weekday_schedule[1] = weekday_schedule[1].apply(replace_time_str)
        weekday_schedule[2] = weekday_schedule[2].apply(replace_time_str)
        weekday_schedule[3] = weekday_schedule[3].apply(replace_time_str)
        weekend_schedule[1] = weekend_schedule[1].apply(replace_time_str)
        weekend_schedule[2] = weekend_schedule[2].apply(replace_time_str)
        weekend_schedule[3] = weekend_schedule[3].apply(replace_time_str)

        # deal with Monday bleeding over into weekend schedule, and Sunday bleeding over into weekday schedule
        if day_of_week in ["saturday", "sunday"]:
            if day_of_week == "saturday":
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
                    t for t in todays_schedule if ("AM" in t) or ("PM" in t)
                ]
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
                    t for t in todays_schedule if ("AM" in t) or ("PM" in t)
                ]
                todays_schedule = [
                    convert_to_24_hour_format(time_str) for time_str in todays_schedule
                ]
        else:
            if day_of_week == "monday":
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
                    t for t in todays_schedule if ("AM" in t) or ("PM" in t)
                ]
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
                    t for t in todays_schedule if ("AM" in t) or ("PM" in t)
                ]
                todays_schedule = [
                    convert_to_24_hour_format(time_str) for time_str in todays_schedule
                ]
        return todays_schedule
    else:
        print(
            f"Unexpected schedule format for {dock} to {dest}. Check the webpage and update the code if needed."
        )
        return []


# DRIVER CODE
outfile_root = f"ferry_schedule_{TODAY}_{day_of_week}_"
outfile_today = (
    "ferry_schedule_today_"  # make second version that is name-constant for today
)
for route in ROUTES:
    dock = route[0]
    dest = route[1]
    outfile = f"{outfile_root}{dock}_to_{dest}.csv"
    outfile_2 = f"{outfile_today}{dock}_to_{dest}.csv"
    if outfile not in previously_downloaded_schedules:

        print(f"Getting schedule for {dock} to {dest}...")
        schedule_times = get_ferry_schedule(dock, dest, day_of_week)
        df_schedule = pd.DataFrame(schedule_times, columns=["scheduled_depart"])
        csv_file_path = os.path.join(SCHEDULE_FOLDER, outfile)
        csv_file_path_2 = os.path.join(SCHEDULE_FOLDER, outfile_2)
        df_schedule.to_csv(csv_file_path, index=False)
        df_schedule.to_csv(csv_file_path_2, index=False)
        print(f"Saved schedule for {dock} to {dest}")
