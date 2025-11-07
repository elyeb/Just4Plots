from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import bs4, requests, sys, codecs, urllib.request, re
import urllib.parse
from urllib.parse import urljoin, urlencode
from bs4 import SoupStrainer
from bs4.element import Comment
import random
from bs4 import BeautifulSoup
import pickle
import os

# Path to the GeckoDriver executable
executable_path = '/usr/local/bin/geckodriver'
folder_path = os.path.join(os.getcwd(), 'data')

# Firefox options
options = Options()
# options.add_argument('--headless')  # Run Firefox in headless mode

# GeckoDriver service
service = Service(executable_path)

# Initialize WebDriver
driver = webdriver.Firefox(service=service, options=options)

# Step 1: Define the login URL and the target URL
driver.get('https://www.ptleader.com/login.html')

# Key sites:
# Historic:
historic_leader = "https://www.ptleader.com/browse.html?archive_search=1&content_source=archive&search_filter=&search_filter_mode=and&byline=&sub_type%5B%5D=stories&sub_type%5B%5D=photos&sub_type%5B%5D=videos&sub_type%5B%5D=eeditions&sub_type%5B%5D=specialsections&sub_type%5B%5D=legals&sub_type%5B%5D=premium&date_start_n=&date_start_j=&date_start_Y=&date_end_n=&date_end_j=&date_end_Y="
# opinions
opinion_leader = "https://www.ptleader.com/opinionletters-to-editor/"

driver.get(historic_leader)
page_source = driver.page_source
# Stems for PT Leader:
# https://www.ptleader.com/stories/

# data = []
# errors = []
data = pickle.load(open(os.path.join(folder_path, 'pt_articles.pkl'), 'rb'))
errors = pickle.load(open(os.path.join(folder_path, 'errors.pkl'), 'rb'))



driver.get(historic_leader)
continue_scraping = True
page_no = 1
title_set = set()

# page_no = 3443
while continue_scraping:

    try:
        # Save next page before navigating to child pages
        #next_link = driver.find_element(By.XPATH, '//a[contains(text(), "Next")]').get_attribute('href')
        # Print the href attribute of the next link
        stem = "https://www.ptleader.com/browse.html?content_source=archive&page_size=20&search_filter_mode=and&sub_type=stories%2Cphotos%2Cvideos%2Ceeditions%2Cspecialsections%2Clegals%2Cpremium&page="
        next_link = stem + str(page_no)
        print(next_link)
        # Navigate to the next page
        
    except:
        print("No next link")
        continue_scraping = False


    print("Page number: ", page_no)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')


    # Find all <a> tags and extract the href attributes
    links = [a.get('href') for a in soup.find_all('a', href=True)]

    # Only use stories
    links = [link for link in links if ('/stories/' in link) and ("#comments" not in link) and ("pt-leader-" not in link)]
    links = list(set(links))

    for i in range(0,len(links)):
        time.sleep(1)

        child_url = "https://www.ptleader.com"+links[i]

        

        try:
            driver.get(child_url)
            page_source = driver.page_source
            # Try a couple variations for titles and bodies of articles
            # Title
            title = re.findall(r'<title>(.*?)</title>', page_source)
            if len(title) > 0:
                title = title[0]
            else:
                title = re.findall(r'"headline": (.+?),', page_source)
                if len(title) > 0:
                    title = title[0]

            # Body
            body = re.findall(r'<p>(.*?)</p>', page_source)
            if len(body) == 0:
                body = re.findall(r'<p class="p1">(.*?)</p>', page_source)

            date = re.findall(r'<time datetime="(.*?)">', page_source)[0]
            if title not in title_set:
                title_set.add(title)
                data.append({"title": title, "body": body, "date": date,"url": child_url})
        except:
            errors.append(child_url)
            print("Error at: ", child_url)

    with open(os.path.join(folder_path, 'pt_articles.pkl'), 'wb') as f:
        pickle.dump(data, f)
    with open(os.path.join(folder_path, 'errors.pkl'), 'wb') as f:
        pickle.dump(errors, f)
    # Wait for 5 seconds
    time.sleep(5)

    driver.get(next_link)
    page_no += 1
    


# Add current data to pickle file
current_leader = "https://www.ptleader.com/news/index.html"

driver.get(current_leader)
# page_source = driver.page_source
# Stems for PT Leader:
# https://www.ptleader.com/stories/

# data = []
# errors = []
# data = pickle.load(open(os.path.join(folder_path, 'pt_articles.pkl'), 'rb'))
# errors = pickle.load(open(os.path.join(folder_path, 'errors.pkl'), 'rb'))

# driver.get(historic_leader)
continue_scraping = True
page_no = 1
# title_set = set()

# page_no = 3443
while continue_scraping:

    try:
        # Save next page before navigating to child pages
        #next_link = driver.find_element(By.XPATH, '//a[contains(text(), "Next")]').get_attribute('href')
        # Print the href attribute of the next link
        stem = "https://www.ptleader.com/news/index.html?page_size=20&category_id=7&sub_type=stories%252Cphotos%252Cvideos%252Cspecialsections%252Ceeditions%252Cpackages%252Cmaps%252Cpolls%252Ccharts%252Cpressreleases&page="
        next_link = stem + str(page_no)
        print(next_link)
        # Navigate to the next page
        
    except:
        print("No next link")
        continue_scraping = False


    print("Page number: ", page_no)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')


    # Find all <a> tags and extract the href attributes
    links = [a.get('href') for a in soup.find_all('a', href=True)]

    # Only use stories
    links = [link for link in links if ('/stories/' in link) and ("#comments" not in link) and ("pt-leader-" not in link)]
    links = list(set(links))

    for i in range(0,len(links)):
        time.sleep(1)

        child_url = "https://www.ptleader.com"+links[i]

        

        try:
            driver.get(child_url)
            page_source = driver.page_source
            # Try a couple variations for titles and bodies of articles
            # Title
            title = re.findall(r'<title>(.*?)</title>', page_source)
            if len(title) > 0:
                title = title[0]
            else:
                title = re.findall(r'"headline": (.+?),', page_source)
                if len(title) > 0:
                    title = title[0]

            # Body
            body = re.findall(r'<p>(.*?)</p>', page_source)
            if len(body) == 0:
                body = re.findall(r'<p class="p1">(.*?)</p>', page_source)

            date = re.findall(r'<time datetime="(.*?)">', page_source)[0]
            if title not in title_set:
                title_set.add(title)
                data.append({"title": title, "body": body, "date": date,"url": child_url})
        except:
            errors.append(child_url)
            print("Error at: ", child_url)

    with open(os.path.join(folder_path, 'pt_articles.pkl'), 'wb') as f:
        pickle.dump(data, f)
    with open(os.path.join(folder_path, 'errors.pkl'), 'wb') as f:
        pickle.dump(errors, f)
    # Wait for 5 seconds
    time.sleep(5)

    driver.get(next_link)
    page_no += 1

driver.quit()

#test = pickle.load(open(os.path.join(folder_path, 'pt_articles.pkl'), 'rb'))

## Scrape opinions only
# Firefox options
options = Options()
# options.add_argument('--headless')  # Run Firefox in headless mode

# GeckoDriver service
service = Service(executable_path)

# Initialize WebDriver
driver = webdriver.Firefox(service=service, options=options)

# Step 1: Define the login URL and the target URL
driver.get('https://www.ptleader.com/login.html')
# Step 1: Define the login URL and the target URL


driver.get(opinion_leader)
page_source = driver.page_source
# Stems for PT Leader:
# https://www.ptleader.com/stories/

data = []
errors = []
# data = pickle.load(open(os.path.join(folder_path, 'pt_opinion.pkl'), 'rb'))
# errors = pickle.load(open(os.path.join(folder_path, 'pt_opinion_errors.pkl'), 'rb'))

folder_path = "/Users/elyebliss/Documents/Just4Plots/data/"

stems = ["https://www.ptleader.com/opinionletters-to-editor/?page_size=20&category_id=385&sub_type=stories%2Cphotos%2Cvideos%2Cspecialsections%2Ceeditions%2Cpackages%2Cmaps%2Cpolls%2Ccharts%2Cpressreleases&page=",
         "https://www.ptleader.com/browse.html?content_source=archive&page_size=20&search_filter_mode=and&category_id=385&sub_type=stories%2Cphotos%2Cvideos%2Ceeditions%2Cspecialsections&page="]
for stem in stems:
    continue_scraping = True
    page_no = 1
    title_set = set()
    driver.get(stem + str(page_no))

    # page_no = 3443
    while continue_scraping:

        try:
            # Save next page before navigating to child pages
            #next_link = driver.find_element(By.XPATH, '//a[contains(text(), "Next")]').get_attribute('href')
            # Print the href attribute of the next link
            # stem = "https://www.ptleader.com/opinionletters-to-editor/?page_size=20&category_id=385&sub_type=stories%2Cphotos%2Cvideos%2Cspecialsections%2Ceeditions%2Cpackages%2Cmaps%2Cpolls%2Ccharts%2Cpressreleases&page="
            # stem = "https://www.ptleader.com/browse.html?content_source=archive&page_size=20&search_filter_mode=and&category_id=385&sub_type=stories%2Cphotos%2Cvideos%2Ceeditions%2Cspecialsections&page="
            page_no += 1
            next_link = stem + str(page_no)
            print(next_link)
            # Navigate to the next page
            
        except:
            print("No next link")
            continue_scraping = False


        print("Page number: ", page_no)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        if bool(re.findall(r'Nothing to display',str(soup))):
            continue_scraping = False
        else:

            # Find all <a> tags and extract the href attributes
            links = [a.get('href') for a in soup.find_all('a', href=True)]

            # Only use stories
            links = [link for link in links if ('/stories/' in link) and ("#comments" not in link) and ("pt-leader-" not in link)]
            links = list(set(links))

            for i in range(0,len(links)):
                time.sleep(1)

                child_url = "https://www.ptleader.com"+links[i]

                

                try:
                    driver.get(child_url)
                    page_source = driver.page_source
                    # Try a couple variations for titles and bodies of articles
                    # Title
                    title = re.findall(r'<title>(.*?)</title>', page_source)
                    if len(title) > 0:
                        title = title[0]
                    else:
                        title = re.findall(r'"headline": (.+?),', page_source)
                        if len(title) > 0:
                            title = title[0]

                    # Body
                    body_list = []

                    body_p = re.findall(r'<p>(.*?)</p>', page_source)
                    if len(body_p) > 0:
                        body_p = [b.replace("&nbsp;", " ") for b in body_p]
                        for item in body_p:
                            body_list.append(item)
                    for j in range(1, 10):
                        pattern = r'<p class="p' + str(j) + '">(.*?)</p>'
                        body = re.findall(pattern, page_source)
                        if len(body) > 0:
                            body = [b.replace("&nbsp;", " ") for b in body]
                            for item in body:
                                body_list.append(body)
        
                    date = re.findall(r'<time datetime="(.*?)">', page_source)
                    if len(date)>0:
                        date = date[0]
                    if title not in title_set:
                        title_set.add(title)
                        data.append({"title": title, "body": body_list, "date": date,"url": child_url})
                except:
                    errors.append(child_url)
                    print("Error at: ", child_url)

            with open(os.path.join(folder_path, 'pt_opinions.pkl'), 'wb') as f:
                pickle.dump(data, f)
            with open(os.path.join(folder_path, 'pt_opinion_errors.pkl'), 'wb') as f:
                pickle.dump(errors, f)
            # Wait for 5 seconds
            time.sleep(3)

            driver.get(next_link)
            
        
driver.quit()




# Update editorials with latest:
# Step 1: Define the login URL and the target URL
driver.get('https://www.ptleader.com/login.html')
# Step 1: Define the login URL and the target URL


driver.get(opinion_leader)
page_source = driver.page_source
# Stems for PT Leader:
# https://www.ptleader.com/stories/

folder_path = "/Users/elyebliss/Documents/Just4Plots/data/"
# data = []
# errors = []
data = pickle.load(open(os.path.join(folder_path, 'pt_opinions.pkl'), 'rb'))
errors = pickle.load(open(os.path.join(folder_path, 'pt_opinion_errors.pkl'), 'rb'))

pattern = re.compile(r"[0-9]{1,2}\s[a-zA-Z]{3}\s")
test = 'Thu, 18 Feb 2021 11:48:35 -0800'
re.findall(pattern,test)[0]
dates = [d['date'] for d in data]
dates = [re.findall(pattern,test)[0]]

stems = "https://www.ptleader.com/opinionletters-to-editor/?page_size=20&category_id=385&sub_type=stories%2Cphotos%2Cvideos%2Cspecialsections%2Ceeditions%2Cpackages%2Cmaps%2Cpolls%2Ccharts%2Cpressreleases&page="


continue_scraping = True
page_no = 1
title_set = set()
driver.get(stem + str(page_no))

# page_no = 3443
while continue_scraping:

    try:
        # Save next page before navigating to child pages
        #next_link = driver.find_element(By.XPATH, '//a[contains(text(), "Next")]').get_attribute('href')
        # Print the href attribute of the next link
        # stem = "https://www.ptleader.com/opinionletters-to-editor/?page_size=20&category_id=385&sub_type=stories%2Cphotos%2Cvideos%2Cspecialsections%2Ceeditions%2Cpackages%2Cmaps%2Cpolls%2Ccharts%2Cpressreleases&page="
        # stem = "https://www.ptleader.com/browse.html?content_source=archive&page_size=20&search_filter_mode=and&category_id=385&sub_type=stories%2Cphotos%2Cvideos%2Ceeditions%2Cspecialsections&page="
        page_no += 1
        next_link = stem + str(page_no)
        print(next_link)
        # Navigate to the next page
        
    except:
        print("No next link")
        continue_scraping = False


    print("Page number: ", page_no)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    if bool(re.findall(r'Nothing to display',str(soup))):
        continue_scraping = False
    else:

        # Find all <a> tags and extract the href attributes
        links = [a.get('href') for a in soup.find_all('a', href=True)]

        # Only use stories
        links = [link for link in links if ('/stories/' in link) and ("#comments" not in link) and ("pt-leader-" not in link)]
        links = list(set(links))

        for i in range(0,len(links)):
            time.sleep(1)

            child_url = "https://www.ptleader.com"+links[i]

            

            try:
                driver.get(child_url)
                page_source = driver.page_source
                # Try a couple variations for titles and bodies of articles
                # Title
                title = re.findall(r'<title>(.*?)</title>', page_source)
                if len(title) > 0:
                    title = title[0]
                else:
                    title = re.findall(r'"headline": (.+?),', page_source)
                    if len(title) > 0:
                        title = title[0]

                # Body
                body_list = []

                body_p = re.findall(r'<p>(.*?)</p>', page_source)
                if len(body_p) > 0:
                    body_p = [b.replace("&nbsp;", " ") for b in body_p]
                    for item in body_p:
                        body_list.append(item)
                for j in range(1, 10):
                    pattern = r'<p class="p' + str(j) + '">(.*?)</p>'
                    body = re.findall(pattern, page_source)
                    if len(body) > 0:
                        body = [b.replace("&nbsp;", " ") for b in body]
                        for item in body:
                            body_list.append(body)
    
                date = re.findall(r'<time datetime="(.*?)">', page_source)
                if len(date)>0:
                    date = date[0]
                if title not in title_set:
                    title_set.add(title)
                    data.append({"title": title, "body": body_list, "date": date,"url": child_url})
            except:
                errors.append(child_url)
                print("Error at: ", child_url)

        with open(os.path.join(folder_path, 'pt_opinions.pkl'), 'wb') as f:
            pickle.dump(data, f)
        with open(os.path.join(folder_path, 'pt_opinion_errors.pkl'), 'wb') as f:
            pickle.dump(errors, f)
        # Wait for 5 seconds
        time.sleep(3)

        driver.get(next_link)
            
        
driver.quit()