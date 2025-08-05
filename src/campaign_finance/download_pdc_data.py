"""
Run daily. Get data downloads from the PDC website. Specifically, 
- campaign contributions: https://data.wa.gov/Politics/Contributions-to-Candidates-and-Political-Committe/kv7h-kjye/about_data
- independent expenditures: https://data.wa.gov/Politics/Independent-Campaign-Expenditures-and-Electioneeri/67cp-h962/about_data
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
import sys
import datetime
from tqdm import tqdm
import time
import click


URL_ROOT = "https://data.wa.gov/Politics/"
DATA_FOLDER = "/Users/elyebliss/Documents/Just4Plots/data/lobbying/pdc_downloads/"
os.makedirs(os.path.dirname(DATA_FOLDER), exist_ok=True, mode=0o777)






@click.command()
@click.option('--contr_type', type=click.Choice(['contributions', 'independent_expenditurers']), required=True, help='Type of contribution data to download')
def main(contr_type):
    """
    contr_type = "contributions"
    """
    website_dict = {
        "contributions": 'Contributions-to-Candidates-and-Political-Committe/kv7h-kjye/about_data',
        "independent_expenditurers": 'Independent-Campaign-Expenditures-and-Electioneeri/67cp-h962/about_data',
    }

    if contr_type not in website_dict:
        print(f"Invalid contribution type: {contr_type}")
        sys.exit(1)
    website = website_dict[contr_type]
    # Construct the URL for the specific terminal
    url = f"{URL_ROOT}{website}"
    print(f"Downloading {contr_type}")
    print(f"From {url}...")


    executable_path = "/usr/local/bin/geckodriver"
    # Firefox options
    options = Options()
    # options.add_argument("--headless")

    # GeckoDriver service
    service = Service(executable_path)
    driver = webdriver.Firefox(service=service, options=options)


    driver.get(url)
    time.sleep(20)

    export_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="export-data-button"]'))
    )
    export_button.click()

    export_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="export-download-button"]'))
    )
    export_button.click()

    time.sleep(90)  # Wait for the download to complete
    driver.quit()
