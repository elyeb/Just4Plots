"""
Download all ferry real-time map history
"""

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
import os
import datetime
from tqdm import tqdm
import time

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

START_DATE = "01/01/2025"
END_DATE = datetime.datetime.now().strftime("%m/%d/%Y")
# left off 03/21/2025

# Path to the GeckoDriver executable
executable_path = "/usr/local/bin/geckodriver"
folder_path = os.path.join(os.getcwd(), "data")

# Firefox options
options = Options()
# options.add_argument('--headless')  # Run Firefox in headless mode

# GeckoDriver service
service = Service(executable_path)

# Initialize WebDriver
driver = webdriver.Firefox(service=service, options=options)

URL = "https://wsdot.com/ferries/vesselwatch/VesselWatchHis.aspx"
# Open the website
driver.get(URL)

for ferry in tqdm(ferries):

    ferry_place = ferries.index(ferry)+1
    print(f"Gathering data for {ferry}, ferry {ferry_place} out of fleet of {len(ferries)}")
    # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    # Example: Select an option from a drop-down menu
    ID_OF_DROPDOWN = "RightContentPlaceHolder_ddlVessels"

    dropdown = wait.until(EC.presence_of_element_located((By.ID, ID_OF_DROPDOWN)))
    select = Select(dropdown)
    select.select_by_visible_text(ferry)

    # set start date
    ID_OF_START_DATE_PICKER = "RightContentPlaceHolder_txtDateFrom"
    date_picker = wait.until(EC.presence_of_element_located((By.ID, ID_OF_START_DATE_PICKER)))
    date_picker.clear()
    date_picker.send_keys(START_DATE)  

    # set end date
    ID_OF_START_END_PICKER = "RightContentPlaceHolder_txtDateThru"
    date_picker = wait.until(EC.presence_of_element_located((By.ID, ID_OF_START_END_PICKER)))
    date_picker.clear()
    date_picker.send_keys(END_DATE)  

    # select csv
    ID_OF_CSV = "RightContentPlaceHolder_radCsv"
    csv_button = wait.until(
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
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ui-button') and text()='Yes']"))
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
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ui-button') and text()='Ok']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", popup_complete_button)
            time.sleep(5)
            popup_complete_button.click()
            success = True
        except (ElementClickInterceptedException, TimeoutException):
            print(f"Retrying to find and click 'Ok' button for ferry {ferry}")
            time.sleep(5)

# Close the browser
driver.quit()


# Concat results of downloads
import pandas as pd
DOWNLOAD_FOLDER = "/Users/elyebliss/Downloads/"
OUTPUT_FOLDER = "/Users/elyebliss/Documents/Just4Plots/data/"
START_DATE_MODIFIED = START_DATE.replace("/","")
END_DATE_MODIFIED = END_DATE.replace("/","")
OUTFILE = f"ferry_data_combined_{START_DATE_MODIFIED}_thru_{END_DATE_MODIFIED}.csv"

df_list = []
for f in os.listdir(DOWNLOAD_FOLDER):
    if f.endswith("csv"):
        df_list.append(pd.read_csv(DOWNLOAD_FOLDER+f,index_col=False)) 
df = pd.concat(df_list,ignore_index=True)

df.to_csv(OUTPUT_FOLDER+OUTFILE,index=False)
os.chmod(OUTPUT_FOLDER+OUTFILE,0o777)