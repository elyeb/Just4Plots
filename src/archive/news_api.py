"""

Instructions: https://newsapi.org/docs/get-started#search
"""

import configparser
import requests
import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import random

# Load Google trends data
trends = pd.read_csv('../data/signal_vs_tariffs.csv')
trends.columns = ['date','tariffs','signal']

# Load the config file
config = configparser.ConfigParser()
config.read('config')

# set variables
api_key = config['MEDIASTACK']['mediastack_key']
endpoint = 'top-headlines?'# 'everything?'
start_date = '2025-03-15'
keyword_1 = "signal"
keyword_2 = "tariffs"

# form request


# url = (f'https://newsapi.org/v2/{endpoint}'
#        #f'q={keyword}&'
#        f'from={start_date}&'
#        'sortBy=popularity&'
#        'page=1&'
#        'pageSize=100&'
#        'country=us&'
#        f'apiKey={api_key}')

    ? access_key = YOUR_ACCESS_KEY
url = ('http://api.mediastack.com/v1/news'
       '& countries = us,'


response = requests.get(url)

# headlines only



headlines  = response.json()
articles = headlines['articles']
len(articles)



def plot_by_day(df):
    """
    df = signal_everything['articles']

    """
    for article in df:
        date = article['publishedAt']
        


# Extract and format dates
data = [{'date': article['publishedAt'][:10], 'title': article['title'], 'source':article['source']['name']} for article in articles]
df = pd.DataFrame(data)

# Group by date and count articles
df['date'] = pd.to_datetime(df['date'])  # Convert to datetime
df[keyword_1] = df['title'].apply(lambda x: x if keyword_1 in x else None)
df[keyword_2] = df['title'].apply(lambda x: x if keyword_2 in x else None)

article_counts = df.groupby('date').size().reset_index(name='count')

# Sample one title per day for labeling
grouped = df.groupby('date')['title']
sampled_titles = []
for date, group in grouped:
    sampled_titles.append({date:random.choice(group.tolist())})  # Randomly sample one title

# Merge counts and sampled titles
article_counts = article_counts.merge(sampled_titles, on='date')

# Plot the line chart
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(article_counts['date'], article_counts['count'], marker='o', label='Articles per Day')

# Add labels to points
for i, row in article_counts.iterrows():
    ax.annotate(
        row['title'],  # The sampled title
        (row['date'], row['count']),  # The data point
        textcoords="offset points",  # Offset the text
        xytext=(0, 10),  # Offset position (x, y)
        ha='center',  # Horizontal alignment
        fontsize=8,  # Font size
        arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)  # Optional arrow
    )

# Format the x-axis
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)

# Add labels and title
ax.set_xlabel('Date')
ax.set_ylabel('Number of Articles')
ax.set_title('Articles per Day with Sample Titles')

# Show the plot
plt.tight_layout()
plt.show()