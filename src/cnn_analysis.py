"""
Visualize competing coverage of tariffs and signalgate on CNN by tracking 
occurrences of search terms over time. 

data source: https://transcripts.cnn.com/date/2025-04-12

Author: Elye Bliss
Date: April 2025
"""

import os
import re
from collections import Counter
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from nltk.util import ngrams
from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize
from nltk.tokenize import sent_tokenize

from tqdm import tqdm
import matplotlib as mpl

# Set global font to Arial for a clean look
mpl.rcParams['font.family'] = 'Arial'

# Constants
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../outputs/plots/")
STOP_WORDS = set(stopwords.words('english'))

# Utility Functions
def generate_ngrams(words, n):
    """Generate n-grams from a list of words."""
    return [' '.join(gram) for gram in ngrams(words, n)]

def get_date_range(start_date, end_date):
    """Generate a list of dates between start_date and end_date (inclusive)."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = timedelta(days=1)

    return [(start + delta * i).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]

def process_text(text):
    """Clean and tokenize text, removing stop words and generating n-grams."""
    raw_line = text.strip().lower()
    raw_line = re.sub(r'aired.*et', '', raw_line)
    words = re.findall(r'\b[\w.]+\b', raw_line)
    words = [word for word in words if word not in STOP_WORDS]
    bigrams = generate_ngrams(words, 2)
    trigrams = generate_ngrams(words, 3)
    return words, bigrams, trigrams

def fetch_sentences(date):
    url = f"https://transcripts.cnn.com/date/{date}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    link_texts = [link.text for link in soup.find_all('a', href=True)]
    hyperlinks = [link.get('href') for link in soup.find_all('a', href=True)]
    hyperlinks = ["https://transcripts.cnn.com/"+link for link in hyperlinks if "/date/" in link]

    sents = []    
    for link in hyperlinks:

        response = requests.get(link)
        soup = BeautifulSoup(response.content, 'html.parser')
        body_paragraphs = soup.find_all('p', class_='cnnBodyText')
        body_paragraphs = [b for b in body_paragraphs if "Aired" not in str(b)]
        body_paragraphs = [b for b in body_paragraphs if "RUSH TRANSCRIPT" not in str(b)]

        body_texts = [paragraph.get_text(strip=True) for paragraph in body_paragraphs]
        full_body_text = " ".join(body_texts)
        sentences = sent_tokenize(full_body_text)
        # remove throwaway sentences:
        sentences = [s for s in sentences if "COMMERCIAL BREAK" not in s]
        sentences = [re.sub("VIDEO CLIP","",s) for s in sentences ]
        sentences = [re.sub("\[[0-9]{2}:[0-9]{2}:[0-9]{2}\]","",s) for s in sentences ]
        sentences = [re.sub("CNN ANCHOR","",s) for s in sentences ]
        sentences = [re.sub(r"cnn", "", s, flags=re.IGNORECASE) for s in sentences]
        sentences = [re.sub(r'aired.*et', '', s, flags=re.IGNORECASE) for s in sentences]

        for text in sentences:
            raw_line = text.strip().lower()
            
            words = re.findall(r'\b[\w]+\b', raw_line)
            words = [word for word in words if word not in STOP_WORDS]
        sents.append(words)
    return sents

def fetch_headlines(date):
    url = f"https://transcripts.cnn.com/date/{date}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract text from links
    link_texts = [link.text for link in soup.find_all('a', href=True)]

    all_words = []
    for text in link_texts:
        sentences = sent_tokenize(text)
        for sent in sentences:
            words = word_tokenize(sent)
            words = [word.lower() for word in words if ((word not in STOP_WORDS) and (bool(re.findall('[a-z]',word))))]
            if len(words)>1:
                if ("transcript" not in words) and \
                ("transcripts" not in words) and \
                ("aired" not in words):
                    all_words.append(words)
    return all_words

def fetch_and_process_data(date):
    """Fetch and process data for a specific date."""
    url = f"https://transcripts.cnn.com/date/{date}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract text from links
    link_texts = [link.text for link in soup.find_all('a', href=True)]
    all_words, all_bigrams, all_trigrams = [], [], []

    for text in link_texts:
        words, bigrams, trigrams = process_text(text)
        all_words.extend(words)
        all_bigrams.extend(bigrams)
        all_trigrams.extend(trigrams)

    single_doc = " ".join(all_words)
    return single_doc, all_words, all_bigrams, all_trigrams

def count_search_terms(single_doc, search_terms):
    """Count occurrences of search terms in the document."""
    return {term: len(re.findall(term, single_doc)) for term in search_terms}

def plot_results(df):
    """Plot the results and save the figure."""
    # Format the 'date' column for plotting
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%m-%d')

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(df['date'], df['tariff'], alpha=1, label='Search terms: "tariff"', color='blue')
    ax.plot(df['date'], df['group chat|signal|signalgate'], alpha=1, label='Search terms: "group chat"|"signal"|"signalgate"', color='red')

    # Add labels, legend, and title
    ax.set_xlabel('Date', fontsize=12, fontweight="bold")
    ax.set_ylabel('No. of Occurrences', fontsize=12, fontweight="bold")
    ax.set_title('CNN Coverage: Tariffs vs Signalgate', fontsize=18, fontweight="bold")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Add text below the plot for data source
    fig.text(0.07, -0.04, "Data from https://transcripts.cnn.com", ha="left", fontsize=12, color="black")

    # Save the plot
    fig.savefig(f"{OUTPUT_FOLDER}cnn_tariffs_signal.png", bbox_inches="tight", facecolor="white", dpi=300)

    # Show the plot
    plt.show()


# Driver code
# Define date range and search terms
start_date = "2015-05-01"
end_date = "2025-05-01"
dates = get_date_range(start_date, end_date)

search_terms = ["tariff", "group chat|signal|signalgate"]

# Initialize data structures
search_results = {term: {} for term in search_terms}
top_ngrams = {}

# Process data for each date
for date in tqdm(dates):
    single_doc, all_words, all_bigrams, all_trigrams = fetch_and_process_data(date)
    term_counts = count_search_terms(single_doc, search_terms)

    # Store results
    for term, count in term_counts.items():
        search_results[term][date] = count

    # Count n-grams
    all_ngrams = all_words + all_bigrams + all_trigrams
    ngram_counts = Counter(all_ngrams)
    top_ngrams[date] = ngram_counts.most_common(10)

# Convert results to DataFrame
df = pd.DataFrame(search_results).reset_index().rename(columns={"index": "date"})

# Plot the results
plot_results(df)


## Second analysis:
# find percent of all headlines that contain trump by day
texts_by_date = {}
for date in tqdm(dates):
    sentences = fetch_headlines(date)
    texts_by_date[date] = sentences
keyword = "trump"

# get months only:
months_by_date = set([date[0:7] for date in dates if date[0:7]!= '2025-05'])

percent_keyword_by_month = {}
for month in months_by_date:
    percent_keyword_by_month[month]= {}
    percent_keyword_by_month[month]["total"] = 0
    percent_keyword_by_month[month]["keyword"] = 0

for date in texts_by_date:
    month = date[0:7]
    if month != '2025-05':
        for sent in texts_by_date[date]:
            if keyword in sent:
                percent_keyword_by_month[month]["keyword"] += 1
            percent_keyword_by_month[month]["total"] +=1
    


# plot results:
df = pd.DataFrame.from_dict(percent_keyword_by_month, orient='index').reset_index()

df = df.rename(columns={'index': 'Date', 'total': 'Total', 'keyword': 'Keyword'})
df["Keyword_percent"] = 100*df["Keyword"]/df["Total"]

df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values("Date")
df['Date'] = df['Date'].dt.strftime('%Y-%b')

# Find the maximum value and its corresponding date
max_value = df["Keyword_percent"].max()
max_date = df[df["Keyword_percent"] == max_value]["Date"].iloc[0]
recent_value = df["Keyword_percent"].iloc[len(df)-1]
recent_date = df["Date"].iloc[len(df)-1]

# Create the plot
fig, ax = plt.subplots(figsize=(10, 8))
ax.plot(df['Date'], df['Keyword_percent'], alpha=1, label='Headline contains "Trump"', color='blue')

# Add a label for the maximum value
ax.annotate(f'All-time high of {max_value:.1f}% in {max_date}', xy=(max_date, max_value), xytext=(max_date, max_value + 5),
            arrowprops=dict(facecolor='black', arrowstyle='->'), fontsize=10, color='black')

# Add a label for the recent value
ax.annotate(
    f'{recent_value:.1f}% in {recent_date}', 
    xy=(recent_date, recent_value), 
    xytext=(recent_date, recent_value +5),  # Position the label to the left
    arrowprops=dict(facecolor='black', arrowstyle='->'), 
    fontsize=10, 
    color='black',
    ha='right'  # Align the text to the right
)

# Add labels, legend, and title
ax.set_title('CNN Coverage: Percent of Headlines that contain "Trump"', fontsize=18, fontweight="bold")

# Set y-axis limits
ax.set_ylim(0, 100)

# Format x-axis ticks to show every 6 months
ax.set_xticks(df['Date'][::6])  # Select every 6th date
ax.set_xlabel("Year-Month", fontsize=12, fontweight="bold") 
ax.set_ylabel("Percent (based on monthly totals)", fontsize=12, fontweight="bold") 
plt.xticks(rotation=45)

plt.tight_layout()

# Add text below the plot for data source
fig.text(0.07, -0.04, "Data from https://transcripts.cnn.com", ha="left", fontsize=12, color="black")

# Save the plot
fig.savefig(f"{OUTPUT_FOLDER}cnn_keyword_search.png", bbox_inches="tight", facecolor="white", dpi=300)

# Show the plot
plt.show()