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
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--width=1920')
options.add_argument('--height=1080')
options.set_preference("network.http.connection-timeout", 300)  # 5 minutes

# GeckoDriver service
service = Service(
    executable_path=executable_path,
    service_args=['--connect-timeout', '300']  # 5 minutes
)

# Update the WebDriver initialization with explicit timeouts
driver = webdriver.Firefox(
    service=service, 
    options=options
)
driver.set_page_load_timeout(300)  # 5 minutes
driver.implicitly_wait(30)  # 30 seconds wait for elements

for dock, terminal_id in dock_dict.items():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            url = f"{URL_ROOT}{terminal_id}"
            print(f"Attempting {dock} dock (try {retry_count + 1}/{max_retries})")
            
            driver.get(url)
            # Use explicit wait instead of sleep
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located((By.ID, "realtimecontent")))
            
            html = driver.page_source
            # ...rest of your scraping code...
            
            break  # Success, exit retry loop
            
        except Exception as e:
            retry_count += 1
            print(f"Error on try {retry_count}: {str(e)}")
            
            if retry_count >= max_retries:
                print(f"Failed to scrape {dock} after {max_retries} attempts")
                continue
                
            print(f"Waiting 30 seconds before retry...")
            time.sleep(30)
            
            # Restart the driver
            try:
                driver.quit()
            except:
                pass
            driver = webdriver.Firefox(service=service, options=options)
            driver.set_page_load_timeout(300)
            driver.implicitly_wait(30)

try:
    driver.quit()
except:
    pass