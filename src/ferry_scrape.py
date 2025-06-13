"""
Collect data on ferry sellout times from: 
https://wsdot.com/ferries/vesselwatch/TerminalDetail.aspx?terminalid=7
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

def create_webdriver(max_retries=3, retry_interval=5):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Set Firefox preferences through options
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", os.path.abspath(DATA_FOLDER))
    
    for attempt in range(max_retries):
        try:
            selenium_host = os.getenv('SELENIUM_HOST', 'localhost')
            selenium_url = f'http://{selenium_host}:4444/wd/hub'
            print(f"Attempt {attempt + 1} connecting to Selenium at: {selenium_url}")
            
            driver = webdriver.Remote(
                command_executor=selenium_url,
                options=options
            )
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

# Ensure data directory exists
os.makedirs(DATA_FOLDER, exist_ok=True)

try:
    # Initialize WebDriver
    driver = create_webdriver()
    
    for dock, terminal_id in dock_dict.items():
        url = f"{URL_ROOT}{terminal_id}"
        print(f"Scraping {dock} dock at {url}...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 20)
                wait.until(EC.presence_of_element_located((By.ID, "realtimecontent")))
                
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                
                content_div = soup.find("div", {"id": "realtimecontent"})
                if not content_div:
                    print(f"No 'realtimecontent' div found for {dock}")
                    break
                    
                table = content_div.find("table")
                if not table:
                    print(f"No table found for {dock}")
                    break
                
                # Extract table data
                rows = []
                for row in table.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    rows.append([cell.get_text(strip=True) for cell in cells])
                
                # Create DataFrame
                df = pd.DataFrame(rows[1:], columns=rows[0])
                
                # Get timestamp
                match = re.search(r"Last Refresh:\s*(.*)", soup.get_text())
                if not match:
                    print(f"No timestamp found for {dock}")
                    continue
                    
                timestamp = match.group(1).strip()
                df["timestamp"] = timestamp
                timestamp = timestamp.replace("/", "-").replace(" ", "_").replace(":", "_")
                
                # Save data
                file_name = f"{dock}_ferry_spaces_{timestamp}.csv"
                csv_file_path = os.path.join(DATA_FOLDER, file_name)
                df.to_csv(csv_file_path, index=False)
                print(f"Successfully saved data for {dock}")
                break
                
            except Exception as e:
                print(f"Error scraping {dock} (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    print("Waiting 5 seconds before retry...")
                    time.sleep(5)
                    driver = create_webdriver()
                else:
                    print(f"Failed to scrape {dock} after {max_retries} attempts")

finally:
    if 'driver' in locals():
        driver.quit()