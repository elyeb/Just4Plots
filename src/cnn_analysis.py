"""

data source: https://transcripts.cnn.com/date/2025-04-12
"""

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import requests
from bs4 import BeautifulSoup
import nltk
# nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.util import ngrams

# Function to generate n-grams
def generate_ngrams(words, n):
    return [' '.join(gram) for gram in ngrams(words, n)]


url = "https://transcripts.cnn.com/date/2025-03-25"

# Define stop words
stop_words = set(stopwords.words('english'))


response = requests.get(url)

soup = BeautifulSoup(response.content, 'html.parser')
    
text = soup.get_text(separator=' ', strip=True)

# get show names
# Extract all <a> tags
links = soup.find_all('a', href=True)

# Get the text content of each <a> tag
link_texts = [link.text for link in links]

headlines = []
all_words = []
all_bigrams = []
all_trigrams = []
documents = []
sentences = []
for text in link_texts:
    text_split = text.split(";")
    if isinstance(text_split,list):
    # if len(text_split) > 1:
        for line in text_split:
            raw_line = line.strip().lower()
            raw_line = re.sub(r'aired.*et', '', raw_line)
            headlines.append(raw_line)
            words = re.findall(r'\b[\w.]+\b', raw_line)
            words = [word for word in words if word not in stop_words]
            all_words.extend(words)
            bigrams = generate_ngrams(words, 2)  # Generate bigrams
            all_bigrams.extend(bigrams)
            trigrams = generate_ngrams(words, 3)  # Generate trigrams
            all_trigrams.extend(trigrams)
            documents.append(words)
            sentences.append(" ".join(words))

    elif isinstance(text_split,str):
        raw_line = text_split.strip().lower()
        raw_line = re.sub(r'aired.*et', '', raw_line)
        headlines.append(raw_line)
        words = re.findall(r'\b[\w.]+\b', raw_line)
        words = [word.strip() for word in words if word not in stop_words]
        all_words.extend(words)
        bigrams = generate_ngrams(words, 2)  # Generate bigrams
        all_bigrams.extend(bigrams)
        trigrams = generate_ngrams(words, 3)  # Generate trigrams
        all_trigrams.extend(trigrams)
        documents.append(words)
        sentences.append(" ".join(words))




# Combine all n-grams into a single list
# all_ngrams = all_words + all_bigrams + all_trigrams
# all_ngrams = all_bigrams 
all_ngrams =  all_bigrams + all_trigrams

# Count n-gram frequencies
ngram_counts = Counter(all_ngrams)

# Generate the word cloud from n-gram frequencies
wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(ngram_counts)

# Display the word cloud
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title("Word Cloud with N-grams", fontsize=16)
plt.show()

# Print the top 10 n-grams
print("Top 10 N-grams:")
for rank, (ngram, count) in enumerate(ngram_counts.most_common(10), start=1):
    print(f"{rank}. {ngram} ({count} occurrences)")



import networkx as nx

# Example n-grams and their counts
ngrams = [
    ("trump", 40),
    ("chat", 36),
    ("war", 31),
    ("u.s", 27),
    ("officials", 24),
    ("group", 21),
    ("group chat", 21),
    ("plans", 17),
    ("intel", 16),
    ("war plans", 16),
]

# Create a graph
G = nx.Graph()

# Add nodes (n-grams)
for ngram, count in ngrams:
    G.add_node(ngram, weight=count)

# Add edges if n-grams share overlapping words
for i, (ngram1, _) in enumerate(ngrams):
    for j, (ngram2, _) in enumerate(ngrams):
        if i < j and set(ngram1.split()).intersection(set(ngram2.split())):
            G.add_edge(ngram1, ngram2)

# Find connected components (clusters)
clusters = list(nx.connected_components(G))

# Print clusters
print("Clusters:")
for cluster in clusters:
    print(cluster)