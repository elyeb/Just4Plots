"""
Download all ferry real-time map history from https://wsdot.com/ferries/vesselwatch/
"""

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
import os
import datetime
from tqdm import tqdm
import time
import pandas as pd

# Ferry list
ferries = [
    # "Cathlamet",
    # "Chelan",
    # "Chetzemoka",
    "Chimacum",
    "Issaquah",
    "Kaleetan",
    "Kennewick",
    "Kitsap",
    "Kittitas",
    "Puyallup",
    "Salish",
    "Samish",
    "Sealth",
    "Spokane",
    "Suquamish",
    "Tacoma",
    "Tillikum",
    "Tokitae",
    "WallaWalla",
    "Wenatchee",
    "Yakima",
]

START_DATE = datetime.datetime.now().strftime("%m/%d/%Y")
END_DATE = datetime.datetime.now().strftime("%m/%d/%Y")
# left off 03/21/2025

# Path to the GeckoDriver executable
# executable_path = "/usr/local/bin/geckodriver"
executable_path = r"C:\Tools\geckodriver.exe"
firefox_binary_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"

folder_path = os.path.join(os.getcwd(), "data")

# Firefox options
options = Options()
options.add_argument("--headless")  # Run Firefox in headless mode
options.binary_location = firefox_binary_path

# GeckoDriver service
service = Service(executable_path)

# Initialize WebDriver
driver = webdriver.Firefox(service=service, options=options)

URL = "https://wsdot.com/ferries/vesselwatch/VesselWatchHis.aspx"
# Open the website
driver.get(URL)

for ferry in tqdm(ferries):

    ferry_place = ferries.index(ferry) + 1
    print(
        f"Gathering data for {ferry}, ferry {ferry_place} out of fleet of {len(ferries)}"
    )
    # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    # Example: Select an option from a drop-down menu
    ID_OF_DROPDOWN = "RightContentPlaceHolder_ddlVessels"

    dropdown = wait.until(EC.presence_of_element_located((By.ID, ID_OF_DROPDOWN)))
    select = Select(dropdown)
    select.select_by_visible_text(ferry)

    # set start date
    ID_OF_START_DATE_PICKER = "RightContentPlaceHolder_txtDateFrom"
    date_picker = wait.until(
        EC.presence_of_element_located((By.ID, ID_OF_START_DATE_PICKER))
    )
    date_picker.clear()
    date_picker.send_keys(START_DATE)

    # set end date
    ID_OF_START_END_PICKER = "RightContentPlaceHolder_txtDateThru"
    date_picker = wait.until(
        EC.presence_of_element_located((By.ID, ID_OF_START_END_PICKER))
    )
    date_picker.clear()
    date_picker.send_keys(END_DATE)

    # select csv
    ID_OF_CSV = "RightContentPlaceHolder_radCsv"
    csv_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, ID_OF_CSV))
    )
    csv_button.click()

    # Example: Click a button to download data
    ID_OF_DOWNLOAD_BUTTON = "RightContentPlaceHolder_btnDownload"
    download_button = wait.until(
        EC.element_to_be_clickable((By.ID, ID_OF_DOWNLOAD_BUTTON))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
    success = False
    while not success:
        time.sleep(5)
        try:
            download_button.click()
            success = True
        except ElementClickInterceptedException:
            download_button.click()

    # Wait for the popup to appear and click the "Yes" button
    popup_yes_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'ui-button') and text()='Yes']")
        )
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", popup_yes_button)
    success = False
    while not success:
        time.sleep(5)
        try:
            popup_yes_button.click()
            success = True
        except ElementClickInterceptedException:
            popup_yes_button.click()

    # close the complete window
    success = False
    while not success:
        try:
            popup_complete_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'ui-button') and text()='Ok']",
                    )
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", popup_complete_button
            )
            time.sleep(5)
            popup_complete_button.click()
            success = True
        except (ElementClickInterceptedException, TimeoutException):
            print(f"Retrying to find and click 'Ok' button for ferry {ferry}")
            time.sleep(5)

# Close the browser
driver.quit()


# Concat results of downloads

DOWNLOAD_FOLDER = "C:/Users/Elye/Downloads/"

OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../data/ferry/ferry_delays/")

START_DATE_MODIFIED = START_DATE.replace("/", "")
END_DATE_MODIFIED = END_DATE.replace("/", "")
OUTFILE = f"ferry_depart_times.csv"

df_current = pd.read_csv(OUTPUT_FOLDER + OUTFILE, index_col=False)

downloads_csvs = os.listdir(DOWNLOAD_FOLDER)
downloads_csvs = [f for f in downloads_csvs if f.endswith("csv")]
downloads_csvs = [f for f in downloads_csvs if f.split(".")[0] in ferries]
df_list = []
for f in downloads_csvs:
    df_list.append(pd.read_csv(DOWNLOAD_FOLDER + f, index_col=False))
    os.remove(DOWNLOAD_FOLDER + f)
df_updates = pd.concat(df_list, ignore_index=True)
columns = [c.strip() for c in df_updates.columns]
df_updates.columns = columns

# Combine with current data
df = pd.concat([df_current, df_updates], ignore_index=True)
df = df.drop_duplicates()
df = df.sort_values(by=["Date", "Scheduled Depart"], ascending=False)

df.to_csv(OUTPUT_FOLDER + OUTFILE, index=False)
os.chmod(OUTPUT_FOLDER + OUTFILE, 0o777)
