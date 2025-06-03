"""
Make a plot that is regularly updated with today's ferry data.

"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import os

import requests
from bs4 import BeautifulSoup

def get_ferry_schedule(dock,dest):
    """
    dock = "Colman"
    dest = "Bainbridge"
    """
    # get today's ferry schedule
    dock_dict = {
        "Colman": 7,
        "Bainbridge": 3,
        "Kingston": 12,
        "Edmonds": 8,
    }


    schedule_date = datetime.date.today().strftime("%Y%m%d")
    request_url = f"https://www.wsdot.com/Ferries/Schedule/scheduledetail.aspx?tripdate={schedule_date}&departingterm={dock_dict[dock]}&arrivingterm={dock_dict[dest]}"

    response = requests.get(request_url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='schedgrid')  # Replace with your table's class or other identifier

    rows = table.find_all('tr')
    schdeule_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        schdeule_data.append(cols)
    schdeule_df = pd.DataFrame(schdeule_data)
    schdeule_df.columns = ["time","vessel","null"]
    schdeule_df = schdeule_df[~schdeule_df['time'].isnull()]
    # covert times after PM to 24-hour format
    schdeule_df = schdeule_df.reset_index(drop=True)
    schdeule_df.drop(columns=["null"], inplace=True)
    schedule_am_index = schdeule_df[schdeule_df["time"]=='AM'].index.tolist()[0]
    schedule_pm_index = schdeule_df[schdeule_df["time"]=='PM'].index.tolist()[0]
    midnight_index = schdeule_df[schdeule_df["time"].str.contains('AM ')].index.tolist()[0]
    schdeule_df = schdeule_df[schdeule_df.index <midnight_index]
    schedule_am = schdeule_df[schdeule_df.index<schedule_pm_index]
    schedule_am = schedule_am[~schedule_am["vessel"].isnull()]
    schedule_pm = schdeule_df[schdeule_df.index>schedule_pm_index]
    def convert_to_24_hour_format(time_str):
        hour = time_str.split(':')[0]
        if hour == '12':  # Handle the case for 12 AM
            return time_str  # 12 AM is already in 24-hour format
        minute = time_str.split(':')[1]
        new_hour = str(int(hour)+12)
        new_time = f"{new_hour}:{minute}"
        return new_time


    schedule_pm["time"] = schedule_pm["time"].apply(convert_to_24_hour_format)

    schdeule_df = pd.concat([schedule_am, schedule_pm], ignore_index=True)

    return schdeule_df

PLOT_DF_FOLDER = os.path.join(os.path.dirname(__file__), "../data/ferry_merged_space_delays/")

df = pd.read_parquet(PLOT_DF_FOLDER + "ferry_merged_space_delays.parquet")

today = datetime.date.today().strftime("%m/%d/%Y")




day_of_week = today.strftime("%A")

def plot_scatter_day(data, dock, dest, day_of_week,date, custom_title):
    """
    data = df.copy()
    dock = "Colman"
    dest = "Bainbridge"
    day_of_week = day_of_week
    date = today
    custom_title = day_title
    """
    df = data[data["Destination"] == dest]
    df = df[df["Departing"] == dock]

    df = df[df["day_of_week"] == day_of_week]

    df = df.sort_values(by="scheduled_depart")
    
    df["scheduled_depart"] = pd.to_datetime(df["scheduled_depart"], format="%H:%M")


    today_df = df[df["Date"] == date]
    prev_df = df[df["Date"] != date]

    depart_times = prev_df[prev_df["Date"]==prev_df["Date"].max()]["scheduled_depart"] #.dt.strftime("%H:%M")

    fig, ax = plt.subplots(figsize=(12, 6))
    # Plot depart_dif above the x-axis


    dots_1_historic = plt.plot(
        prev_df["scheduled_depart"].dt.strftime("%H:%M"),
        prev_df["depart_dif"], 
        'o',
        label="Dif btw scheduled & actual departure (historic)",
        color="blue",
        alpha=0.2,
             ) 
    dots_1_today = plt.plot(
        today_df["scheduled_depart"].dt.strftime("%H:%M"),
        today_df["depart_dif"],
         'o',
        label="Dif btw scheduled & actual departure (today)",
        color="black",
        alpha=1,
             )

    dots_2_historic = plt.plot(
        prev_df["scheduled_depart"].dt.strftime("%H:%M"),
        prev_df["soldout_dif"],
         'o',
        label="Dif btw scheduled departure & sellout time (historic)",
        color="red",
        alpha=0.2,
             )  

    dots_2_today = plt.plot(
        today_df["scheduled_depart"].dt.strftime("%H:%M"),
        today_df["soldout_dif"],
         'x',
        label="Dif btw scheduled departure & sellout time (today)",
        color="black",
        alpha=1,
             )
    
    ax.set_xticks(depart_times.dt.strftime("%H:%M"))
    ax.set_xticklabels(depart_times.dt.strftime("%H:%M"), rotation=45, fontsize=8)
   
    # Customize each subplot
    # ax.set_title(day_of_week, fontsize=12)
    # ax.axhline(
    #     0, color="black", linewidth=0.8, linestyle="--"
    # )  # Add a horizontal line at y=0

    # # ax.tick_params(axis="x", rotation=45, labelsize=8)

    # # Keep x-ticks on the y=0 line
    # ax.spines["bottom"].set_position(("data", 0))

    # ax.set_ylabel("Difference (Minutes)", fontsize=10)

    # ax.legend(loc="upper left", fontsize=10)
    # # Adjust layout
    # # fig.suptitle(custom_title)
    # fig.text(0.5, -0.05, "Scheduled Departure Time", ha="center", fontsize=12)
    plt.tight_layout()
    # fig.savefig(outfile_day, bbox_inches="tight", dpi=300, facecolor="white")
    plt.show()


# plot_scatter_day(data, dock, dest, outfile_day, day_of_week, custom_title)
plot_scatter_day(df,"Colman","Bainbridge",f"{TODAY}","colman_bainbridge_{TODAY}.png")