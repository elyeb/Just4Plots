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

# lock_file = "/tmp/ferry_scrape.lock"

# if os.path.exists(lock_file):
#     print("Script is already running. Exiting.")
#     sys.exit()

# open(lock_file, "w").close()

# try:
URL_ROOT = "https://wsdot.com/ferries/vesselwatch/TerminalDetail.aspx?terminalid="

DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../data/ferry/ferry_spaces/"
)

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
# fix jun 6
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

try:
    # Connect to Selenium standalone service
    selenium_host = os.getenv('SELENIUM_HOST', 'localhost')
    selenium_url = f'http://{selenium_host}:4444/wd/hub'
    print(f"Connecting to Selenium at: {selenium_url}")
    
    driver = webdriver.Remote(
        command_executor=selenium_url,
        options=options
    )
    print("Successfully connected to Selenium")

except Exception as e:
    print(f"Failed to connect to Selenium: {e}")
    raise

# GeckoDriver service
service = Service(
    executable_path=executable_path,
)

# Update the WebDriver initialization with explicit timeouts
# driver = webdriver.Firefox(
#     service=service, 
#     options=options
# )
def create_webdriver(max_retries=3, retry_interval=5):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    for attempt in range(max_retries):
        try:
            selenium_host = os.getenv('SELENIUM_HOST', 'localhost')
            selenium_url = f'http://{selenium_host}:4444/wd/hub'
            print(f"Attempt {attempt + 1} connecting to Selenium at: {selenium_url}")
            
            driver = webdriver.Remote(
                command_executor=selenium_url,
                options=options
            )
            return driver
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                raise


for dock, terminal_id in dock_dict.items():
    # Construct the URL for the specific terminal
    url = f"{URL_ROOT}{terminal_id}"
    print(f"{dock} dock")
    print(f"Scraping {url}...")

    # Navigate to the URL
    keep_trying = True
    while keep_trying:
        error_count = 0
        try:
            driver.get(url)
            time.sleep(10)
            # WebDriverWait(driver, 20).until(
            #     EC.presence_of_element_located((By.ID, "realtimecontent"))
            # )
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
            error_count += 1
            print(f"Error occurred: {e}")
            print("Retrying...")
            time.sleep(5)
            driver.quit()
            service = Service(executable_path)
            driver = webdriver.Firefox(service=service, options=options)
            keep_trying = True
            if error_count >5:
                print("Too many errors, exiting.")
                keep_trying = False

            continue

driver.quit()