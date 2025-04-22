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
from tqdm import tqdm
import matplotlib as mpl

# Set global font to Arial for a clean look
mpl.rcParams['font.family'] = 'Arial'

# Constants
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../outputs/plots/")
STOP_WORDS = set()  # Define stop words if needed

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
start_date = "2025-03-22"
end_date = "2025-04-22"
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