"""
Collect the live data on ferry departure times from:
https://wsdot.com/ferries/vesselwatch/default.aspx

This is more recent and does not include historic data, but is more useful for recent departures
than the historic data collected in get_departure_times.py.

Fill in top rows of ferry_depart_times.csv with data from this script.
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import time
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
now_pacific = datetime.now(PACIFIC)
today_pacific = now_pacific.date()
TODAY = today_pacific.strftime("%m/%d/%Y")

URL = "https://wsdot.com/ferries/vesselwatch/default.aspx"

# DATA_PATH = os.path.join(
#     os.path.dirname(__file__), "../../data/ferry/ferry_merged_space_delays/"
# )

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/ferry/ferry_delays/")
# df_hist = pd.read_csv(DATA_PATH + "ferry_merged_space_delays.csv")
df_hist = pd.read_csv(DATA_PATH + "ferry_depart_times.csv")

## Constants
dock_dict_names_remap = {
    "Seattle": "Colman",
    "Bainbridge Island": "Bainbridge",
}


def create_webdriver(max_retries=1, retry_interval=5):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Set Firefox preferences through options
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    # options.set_preference("browser.download.dir", os.path.abspath(DATA_FOLDER))

    for attempt in range(max_retries):
        try:
            selenium_host = os.getenv("SELENIUM_HOST", "localhost")
            selenium_url = f"http://{selenium_host}:4444/wd/hub"
            print(f"Attempt {attempt + 1} connecting to Selenium at: {selenium_url}")

            driver = webdriver.Remote(command_executor=selenium_url, options=options)
            print("Successfully connected to Selenium")
            return driver
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Waiting {retry_interval} seconds before retry...")
                time.sleep(retry_interval)
            else:
                print("Max retries reached, raising error")
                raise


def create_local_webdriver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Set Firefox preferences through options
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    driver = webdriver.Firefox(options=options)
    return driver


# Driver code #########################################################################
try:
    # Initialize WebDriver
    driver = create_webdriver()
    # driver = create_local_webdriver()

    max_retries = 1
    for attempt in range(max_retries):
        try:
            driver.get(URL)
            wait = WebDriverWait(driver, 5)

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            container = soup.find("div", id="vesselListDiv")
            rows = container.find_all("div", class_="vslLstRow")

            data = []

            for row in rows:

                def get_text(cls):
                    tag = row.find("div", class_=cls)
                    return tag.get_text(strip=True) if tag else None

                date = get_text("vslLstDate")
                pos = get_text("vslLstPos")
                route = get_text("vslLstRoute")
                eta = get_text("vslLstETA")
                depart = get_text("vslLstDepart")
                sched_depart = get_text("vslLstSchedDepart")

                arriving_tag = row.select_one("div.vslLstAterm.termfull")
                arriving = arriving_tag.get_text(strip=True) if arriving_tag else None

                departing_tag = row.select_one("div.vslLstLastdock.termfull")
                departing = (
                    departing_tag.get_text(strip=True) if departing_tag else None
                )

                speed = get_text("vslLstSpeed")

                vessel_links = row.find_all("a")
                vessel_name = (
                    vessel_links[-1].get_text(strip=True) if vessel_links else None
                )

                data.append(
                    [
                        date,
                        pos,
                        route,
                        eta,
                        depart,
                        sched_depart,
                        arriving,
                        departing,
                        speed,
                        vessel_name,
                    ]
                )

            columns = [
                "date",
                "pos",
                "route",
                "eta",
                "actual_depart",
                "sched_depart",
                "arriving",
                "departing",
                "speed",
                "vessel",
            ]

            df = pd.DataFrame(data, columns=columns)

            print("Successfully scraped live ferry departure data")

            # merge with historic data and save
            # format df
            df = df[df["date"].notna()]
            hour = int(df["date"].iloc[0].split()[1].split(":")[0])
            df["Date"] = TODAY

            df.rename(
                columns={
                    "sched_depart": "Scheduled Depart",
                    "eta": "Est. Arrival",
                    "actual_depart": "Actual Depart",
                    "departing": "Departing",
                    "arriving": "Arriving",
                    "vessel": "Vessel",
                },
                inplace=True,
            )
            df = df[
                [
                    "Est. Arrival",
                    "Actual Depart",
                    "Scheduled Depart",
                    "Arriving",
                    "Departing",
                    "Vessel",
                    "Date",
                ]
            ]

            df = df[df["Est. Arrival"] != "At Dock"]
            df = df[df["Est. Arrival"] != ""]

            def convert_to_24h_afternoon(timestr):
                time_hr = int(timestr.split(":")[0])
                time_min = timestr.split(":")[1]

                if time_hr in [11, 12]:
                    return timestr

                time_hr += 12
                return_str = f"{time_hr}:{time_min}"
                return return_str

            def convert_to_24h_night(timestr):
                time_hr = int(timestr.split(":")[0])
                time_min = timestr.split(":")[1]

                if time_hr == 12:
                    return f"00:{time_min}"

                time_hr += 12
                return_str = f"{time_hr}:{time_min}"
                return return_str

            """
            Issue 1: hour is after 12, but some depart times are still before 11. This
            makes the depart times 23:xx but the est arrive 12:xx

            Issue 2: hour is around 23, and so some of the est arrival times are 12:
            """
            if (hour >= 12) & (hour < 23):
                """
                Times after 12 pm will include some 1 pm departure times,
                requiring conversion. 11 am times will not have any 1 pm times,
                and 12 is already in 24 hour format.
                """
                for col in ["Est. Arrival", "Actual Depart", "Scheduled Depart"]:
                    df[col] = df[col].apply(convert_to_24h_afternoon)
            elif (hour >= 23) & (hour < 1):
                for col in ["Est. Arrival", "Actual Depart", "Scheduled Depart"]:
                    df[col] = df[col].apply(convert_to_24h_night)

            # Change names where applicable
            df.loc[df["Departing"].isin(dock_dict_names_remap.keys()), "Departing"] = (
                df.loc[
                    df["Departing"].isin(dock_dict_names_remap.keys()), "Departing"
                ].map(dock_dict_names_remap)
            )
            df.loc[df["Arriving"].isin(dock_dict_names_remap.keys()), "Arriving"] = (
                df.loc[
                    df["Arriving"].isin(dock_dict_names_remap.keys()), "Arriving"
                ].map(dock_dict_names_remap)
            )

            if len(df) > 0:

                df_hist = pd.concat([df, df_hist], ignore_index=True)
                df_hist = df_hist.drop_duplicates()
                df_hist["year"] = df_hist["Date"].str.split("/").str[2].astype(int)
                df_hist["month"] = df_hist["Date"].str.split("/").str[0].astype(int)
                df_hist["day"] = df_hist["Date"].str.split("/").str[1].astype(int)
                df_hist = df_hist.sort_values(
                    by=["year", "month", "day", "Scheduled Depart"], ascending=False
                )
                df_hist = df_hist.drop(columns=["year", "month", "day"])

                df_hist.to_csv(DATA_PATH + "ferry_depart_times.csv", index=False)

                print(f"Updated {len(df)} rows of historic data")
                print(df.head())
            break

        except Exception as e:
            print(f"Error scraping live ferry departure data: {str(e)}")
            # if attempt < max_retries - 1:
            #     print("Waiting 5 seconds before retry...")
            #     time.sleep(5)
            #     driver = create_webdriver()
            # else:
            #     print(
            #         f"Failed to scrape data after {max_retries} attempts, raising error"
            #     )

finally:
    if "driver" in locals():
        driver.quit()
