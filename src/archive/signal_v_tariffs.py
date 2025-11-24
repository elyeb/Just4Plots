import matplotlib.pyplot as plt
import pandas as pd
import os


# Load data
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "../data/news/")

signal_df = pd.read_excel(DATA_FOLDER+"signal_chart.xlsx")
tariffs_df = pd.read_excel(DATA_FOLDER+"tariffs_chart.xlsx")

with open(DATA_FOLDER+'signal_combined.txt', 'r') as file:
    text = file.read()
text_list = text.split('\n')
text_dict_list = []
for i in range(0,len(text_list)):
    if text_list[i].startswith(" "):
        article_dict = {}

        article_dict["headline"]=text_list[i].strip()
        second_line = text_list[i+1].split(",")
        if '2025' in second_line[1]:
            date = second_line[1]
        else:
            date= second_line[2]
        article_dict["publisher"]=second_line[0]
        article_dict["Date"]=date
        text_dict_list.append(article_dict)

headlines_df = pd.DataFrame(text_dict_list)
[p for p in headlines_df.publisher.unique()]

preferred_publishers = ['The Boston Globe','Fox News: Fox News @ Night','Dow Jones Institutional News', 'WSJ Podcasts','Washington Post.com', 'USA Today Online','Forbes.com','Reuters News', 'Fox News: The Ingraham Angle', 'The Guardian','Chicago Tribune','CNN: CNN Newsroom','Al Jazeera English','CNN Wire',]

headlines_df = headlines_df[headlines_df['publisher'].isin(preferred_publishers)]
headlines_df = headlines_df.drop_duplicates('Date',keep='first')

# Format combined data
signal_df.columns = list(signal_df.iloc[3,:])
signal_df = signal_df.iloc[4:20,:]
signal_df.rename(columns={"Document Count":"signal"},inplace=True)
tariffs_df.columns = list(tariffs_df.iloc[3,:])
tariffs_df = tariffs_df.iloc[4:38,:]
tariffs_df.rename(columns={"Document Count":"tariffs"},inplace=True)

merged = tariffs_df.merge(signal_df,on="Date",how="left")
merged = merged.iloc[:len(merged)-1,:]

headlines_df['Date'] = pd.to_datetime(headlines_df['Date'].str.strip(), format='%d %B %Y')

merged['Date'] = pd.to_datetime(merged['Date'])
merged = merged.merge(headlines_df,on="Date",how="left")

# plot
merged['signal'].fillna(0,inplace=True)
merged['signal'] = merged['signal'].astype(int)
merged['tariffs'] = merged['tariffs'].astype(int)
merged['Date'] = pd.to_datetime(merged['Date'], errors='coerce')
merged['Date'] = merged['Date'].dt.strftime('%Y-%m-%d')

# Plot the data
fig, ax = plt.subplots(figsize=(10, 8))

# Plot 'tariffs' as an area plot
ax.fill_between(merged['Date'], merged['tariffs'], alpha=0.5, label='Tariffs', color='blue')

# Plot 'signal' as an area plot
ax.fill_between(merged['Date'], merged['signal'], alpha=0.5, label='Signal', color='orange')

# Add labels for 'signal'
for i, row in merged.iterrows():
    if not pd.isna(row['signal']) and not pd.isna(row['headline']):
        ax.text(row['Date'], row['signal'], f"{row['publisher']}: {row['headline']}", fontsize=8, rotation=45)

# Add labels, legend, and title
ax.xlabel('Date')
ax.ylabel('Values')
ax.title('Tariffs and Signal Over Time')
ax.legend()
plt.tight_layout()

# Show the plot
plt.show()