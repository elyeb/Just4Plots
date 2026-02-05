"""
Get daily ferry schedules for seattle-bainbridge and edmonds-kingston routes.

"""

import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import datetime
import os

SCHEDULE_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/ferry/ferry_schedules/"
)
os.makedirs(SCHEDULE_FOLDER, exist_ok=True, mode=0o777)

TODAY = datetime.datetime.now().strftime("%Y_%m_%d")
day_of_week = datetime.date.today().strftime("%A")
day_of_week = day_of_week.lower()
outfile_root = f"ferry_schedule_{TODAY}_{day_of_week}_"

previously_downloaded_schedules = os.listdir(SCHEDULE_FOLDER)

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


def get_ferry_schedule(dock, dest, day_of_week):
    """

    dock = "Colman"
    dest = "Bainbridge"
    day_of_week = "Wednesday"
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


# DRIVER CODE
for route in ROUTES:
    dock = route[0]
    dest = route[1]
    outfile = f"{outfile_root}{dock}_to_{dest}.csv"
    if outfile not in previously_downloaded_schedules:

        print(f"Getting schedule for {dock} to {dest}...")
        schedule_times = get_ferry_schedule(dock, dest, day_of_week)
        df_schedule = pd.DataFrame(schedule_times, columns=["scheduled_depart"])
        csv_file_path = os.path.join(SCHEDULE_FOLDER, outfile)
        df_schedule.to_csv(csv_file_path, index=False)
        print(f"Saved schedule for {dock} to {dest}")
