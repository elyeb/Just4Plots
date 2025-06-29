"""
Collect data on ferry sellout times from: 
https://wsdot.com/ferries/vesselwatch/TerminalDetail.aspx?terminalid=7


"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys



# try:
URL_ROOT = "https://wsdot.com/ferries/vesselwatch/TerminalDetail.aspx?terminalid="
# DATA_FOLDER = "../data/ferry_spaces/"
DATA_FOLDER = "/Users/elyebliss/Documents/Just4Plots/data/ferry_spaces/"
# os.makedirs(DATA_FOLDER, exist_ok=True)
dock_dict = {
    "colman": 7,
    "bainbridge": 3,
    "kingston": 12,
    "edmonds": 8,
}

# Set up Selenium WebDriver (ensure you have ChromeDriver installed)
executable_path = "/usr/local/bin/geckodriver"
# Firefox options
options = Options()
options.add_argument("--headless")

# GeckoDriver service
service = Service(executable_path)
driver = webdriver.Firefox(service=service, options=options)

dock = 'colman'
terminal_id = 7
url = f"{URL_ROOT}{terminal_id}"

driver.get(url)
# time.sleep(10)
# html = driver.page_source
# # Parse the HTML with BeautifulSoup
# soup = BeautifulSoup(html, "html.parser")
# print(soup)
# # Find the table
# table = soup.find("div", {"id": "realtimecontent"}).find("table")

# # Extract table data into a DataFrame
# rows = []
# for row in table.find_all("tr"):
#     cells = row.find_all(["td", "th"])
#     rows.append([cell.get_text(strip=True) for cell in cells])

# # Convert to a DataFrame
# df = pd.DataFrame(
#     rows[1:], columns=rows[0]
# )  # Use the first row as headers

# # Convert the soup object to text
# page_text = soup.get_text()

# # Use a regular expression to find the timestamp after "Last Refresh: "
# match = re.search(r"Last Refresh:\s*(.*)", page_text)
# timestamp = match.group(1).strip()
# # Close the Selenium WebDriver
# df["timestamp"] = timestamp

# timestamp = (
#     timestamp.replace("/", "-").replace(" ", "_").replace(":", "_")
# )
# print(df)


for dock, terminal_id in dock_dict.items():
    # Construct the URL for the specific terminal
    url = f"{URL_ROOT}{terminal_id}"
    print(f"{dock} dock")
    print(f"Scraping {url}...")

    # Navigate to the URL
    keep_trying = True
    while keep_trying:

        try:
            driver.get(url)
            time.sleep(20)

            html = driver.page_source
            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Find the table
            table = soup.find("div", {"id": "realtimecontent"}).find("table")

            # Extract table data into a DataFrame
            rows = []
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                rows.append([cell.get_text(strip=True) for cell in cells])

            # Convert to a DataFrame
            df = pd.DataFrame(
                rows[1:], columns=rows[0]
            )  # Use the first row as headers

            # Convert the soup object to text
            page_text = soup.get_text()

            # Use a regular expression to find the timestamp after "Last Refresh: "
            match = re.search(r"Last Refresh:\s*(.*)", page_text)
            timestamp = match.group(1).strip()
            # Close the Selenium WebDriver
            df["timestamp"] = timestamp

            timestamp = (
                timestamp.replace("/", "-").replace(" ", "_").replace(":", "_")
            )

            file_name = f"{dock}_ferry_spaces_{timestamp}.csv"
            # Save the DataFrame to a CSV file
            csv_file_path = os.path.join(DATA_FOLDER, file_name)
            df.to_csv(csv_file_path, index=False)
            keep_trying = False
        except Exception as e:
            print(f"Error occurred: {e}")
            print("Retrying...")
            time.sleep(5)
            driver.quit()
            service = Service(executable_path)
            driver = webdriver.Firefox(service=service, options=options)
            keep_trying = True
            continue
driver.quit()
