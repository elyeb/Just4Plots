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

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "../../data/ferry/ferry_merged_space_delays/"
)


df_hist = pd.read_csv(DATA_PATH + "ferry_merged_space_delays.csv")
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
            df["Date"] = TODAY

            df.rename(
                columns={
                    "sched_depart": "scheduled_depart",
                    "eta": "estimated_arrival",
                    "departing": "Departing",
                    "arriving": "Destination",
                    "vessel": "actual_vessel",
                },
                inplace=True,
            )
            df = df[
                [
                    "estimated_arrival",
                    "actual_depart",
                    "scheduled_depart",
                    "Destination",
                    "Departing",
                    "actual_vessel",
                    "Date",
                ]
            ]

            # Change names where applicable
            df.loc[df["Departing"].isin(dock_dict_names_remap.keys()), "Departing"] = (
                df.loc[
                    df["Departing"].isin(dock_dict_names_remap.keys()), "Departing"
                ].map(dock_dict_names_remap)
            )
            df.loc[
                df["Destination"].isin(dock_dict_names_remap.keys()), "Destination"
            ] = df.loc[
                df["Destination"].isin(dock_dict_names_remap.keys()), "Destination"
            ].map(
                dock_dict_names_remap
            )

            # replace data in df_hist with df when empty values in df_hist
            df_hist["version"] = "historical"
            df = df.merge(
                df_hist[["Date", "Departing", "Destination", "version"]],
                on=["Date", "Departing", "Destination"],
                how="left",
            )
            df = df[df["version"].notna()]
            if len(df) > 0:

                df_hist = pd.concat([df, df_hist], ignore_index=True)
                df_hist = df_hist.drop(columns=["version"])

                df_hist.to_parquet(
                    DATA_PATH + "ferry_merged_space_delays.parquet", index=False
                )
                df_hist.to_csv(DATA_PATH + "ferry_merged_space_delays.csv", index=False)

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
