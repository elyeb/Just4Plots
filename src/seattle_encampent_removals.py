"""

Data source:
https://www.seattle.gov/human-services/reports-and-data/addressing-homelessness/encampments
News articles: 
https://www.seattletimes.com/seattle-news/homeless/seattle-breaks-records-on-homeless-tents-removed-encampments-cleared/
https://www.kuow.org/stories/seattle-cleared-2-500-homeless-encampments-last-year-is-it-helping

"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os
import re
import requests
from bs4 import BeautifulSoup

url_root = "https://www.seattle.gov/human-services/reports-and-data/addressing-homelessness/encampments"

YEAR = 2024
QUARTERS = ["q1", "q2", "q3", "q4"]


def parse_table_manually(table):
    """
    Parses an HTML table manually using BeautifulSoup and converts it into a DataFrame.
    
    Args:
        table (bs4.element.Tag): The <table> element to parse.
    
    Returns:
        DataFrame: The parsed table as a Pandas DataFrame.
    """
    rows = []
    for row in table.find_all('tr'):  # Find all rows in the table
        cells = row.find_all(['td', 'th'])  # Find all cells (both <td> and <th>)
        rows.append([cell.get_text(strip=True) for cell in cells])  # Extract text from each cell

    # Convert the rows into a DataFrame
    df = pd.DataFrame(rows)

    # Handle cases where the first row is the header
    if not df.empty and len(df.columns) > 1:  # Ensure the table is not empty
        df.columns = df.iloc[0]  # Set the first row as the header
        df = df[1:]  # Drop the first row from the data

    if df.iloc[0, 0] == "Date":
        df.columns = ["Date", "Location", "Materials Stored?"]
        df = df[1:]

    return df

def get_table_for_quarter(year, quarter):
    """
    Finds and extracts the table corresponding to the specified quarter.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content.
        quarter (str): The quarter to search for (e.g., "q12024").
    
    Returns:
        DataFrame: The extracted table as a Pandas DataFrame.

    year = 2017
    quarter = "q1"
    """
    quarterstring = f"{quarter}{year}"

    url = f"https://www.seattle.gov/human-services/reports-and-data/addressing-homelessness/encampments#{quarterstring}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the <h2> element with the specified quarter name
    header = soup.find('h2', {'class': 'accordion-toggle', 'name': quarterstring})
    if not header:
        raise ValueError(f"No section found for quarter: {quarterstring}")

    # Navigate to the corresponding <div> and find the <table>
    accordion_wrapper = header.find_next_sibling('div', {'class': 'accordionWrapper'})
    table = accordion_wrapper.find('table', {'class': 'table table-bordered'})
    if not table:
        raise ValueError(f"No table found for quarter: {quarterstring}")

    df = parse_table_manually(table)
    # Convert the table to a DataFrame
    # df = pd.read_html(str(table), header=None)[0]
    if "Date" not in df.columns:
        row_0 = list(df.columns)
        new_cols = ["Date","Location","Materials Stored?"]
        row_0 = pd.DataFrame([row_0], columns=new_cols)
        df.columns = new_cols
        df = pd.concat([row_0, df], ignore_index=True)
    elif "Storage (Y/N)?" in df.columns:
        df.rename(columns={"Storage (Y/N)?": "Materials Stored?"}, inplace=True)
    return df

# Make mayor dataframe from dictionary
mayors_dict = {}
mayors_dict["Mayor"] = {}
mayors_dict["Mayor"]["Ed Murray"] 
mayors_dict["Mayor"]["Bruce Harrell"] 
mayors_dict["Mayor"]["Tim Burgess"] 
mayors_dict["Mayor"]["Jenny Durkan"] 


# Specify the quarter you want to extract
all_dfs = []
for year in range(2017,2026):
    # year = 2024
    for quarter in QUARTERS:
        try:
            df = get_table_for_quarter(year, quarter)
            all_dfs.append(df)
        except ValueError as e:
            print(e)
            continue

for d in all_dfs:
    print(d.columns)
all_dfs = pd.concat(all_dfs, ignore_index=True)
# all_2024 = pd.concat(all_dfs, ignore_index=True)

# df = all_2024.copy()
df = all_dfs.copy()

df.dropna(inplace=True)
# Ensure the Date column is in datetime format
# standardize dates


df['Date'] = df['Date'].str.replace("5/16-25/2017","5/25/2017")
df['Date'] = df['Date'].str.replace("10/9&10/2017","10/10/2017")
df['Date'] = df['Date'].str.replace("10/31-11/1/2017","11/1/2017")
df['Date'] = df['Date'].str.replace("11/15&16/2017","11/16/2017")

df['Date'] = df['Date'].str.replace("11/30&12/1/2017","12/1/2017")
df['Date'] = df['Date'].str.replace("3/7&8/2018","3/8/2018")
df['Date'] = df['Date'].str.replace("1/16/20198","1/16/2019")

# find patterns to bulk replace
df[df['Date'].str.contains("&")]
df[df['Date'].str.contains("\d+/\d+-\d+/\d+",regex=True)]
df[df['Date'].str.contains("\d+/\d+\/\d+/\d+",regex=True)]
df[df['Date'].str.contains("^\/",regex=True)]

df['Date'] = df['Date'].str.replace(r'(\d+/\d+)-(\d+/\d+)', r'\1/\2', regex=True)
df['Date'] = df['Date'].str.replace(r'^(\d+)/\d+/(\d+)/(\d+)$', r'\1/\2/\3', regex=True)
df['Date'] = df['Date'].str.replace('^\/', '', regex=True)



df['Date'] = df['Date'].str.replace("-","/")
df['Date'] = pd.to_datetime(df['Date'])


# PLot quarters only
# Create a complete range of year-quarter combinations
quarter_range = pd.date_range(start="2017-01-01", end="2025-12-31", freq="Q")
all_quarters = pd.DataFrame({'YearQuarter': quarter_range.to_period('Q').astype(str)})

# Extract year and quarter from the Date column
df['YearQuarter'] = df['Date'].dt.to_period('Q').astype(str)

# Count occurrences for each year-quarter
quarter_counts = df['YearQuarter'].value_counts().sort_index()
quarter_counts = quarter_counts.rename_axis('YearQuarter').reset_index(name='Count')

# Split YearQuarter into Year and Quarter
all_quarters['Year'] = all_quarters['YearQuarter'].str[:4]
all_quarters['Quarter'] = all_quarters['YearQuarter'].str[4:]
all_quarters = all_quarters.merge(quarter_counts, on='YearQuarter', how='left')
all_quarters['Count'] = all_quarters['Count'].fillna(0).astype(int)

# Plot the histogram for quarters
fig, ax = plt.subplots(figsize=(12, 6))

# Bar plot
ax.bar(all_quarters['YearQuarter'], all_quarters['Count'], color='skyblue', edgecolor='black')

# Set x-axis ticks and labels
ax.set_xticks(range(len(all_quarters)))
ax.set_xticklabels(all_quarters['Quarter'], fontsize=10, rotation=0)

# Add year labels below the quarters
for i, year in enumerate(all_quarters['Year'].unique()):
    year_start = all_quarters[all_quarters['Year'] == year].index[0]
    year_end = all_quarters[all_quarters['Year'] == year].index[-1]
    ax.text((year_start + year_end) / 2, -0.1, year, ha='center', va='top', fontsize=12, transform=ax.get_xaxis_transform())

# Label and grid
ax.set_xlabel('Year-Quarter', fontsize=12)
ax.set_ylabel('Number of Completed Site Journals', fontsize=12)
ax.set_title('Seattle Encampment Inspections & Cleanups', fontsize=16)
ax.grid(axis='y', linestyle='--', alpha=0.7)
fig.text(0.07, -0.04, "Data from https://www.seattle.gov/human-services/reports-and-data/addressing-homelessness/encampments", ha="left", fontsize=12, color="black")

plt.tight_layout()
plt.show()


import PyPDF2
import tabula
pdf_url = "https://www.seattle.gov/documents/Departments/Homelessness/cleanups/2025/Q2%202025/04-01-25%209th%20Ave%20NW%20from%20NW%2046th%20St%20to%20NW%2045th%20St_OB_N.pdf"
# Download the PDF (if needed)
pdf_path = "local_file.pdf"
response = requests.get(pdf_url)
with open(pdf_path, "wb") as f:
    f.write(response.content)

# Extract text from the first page using PyPDF2
with open(pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    first_page_text = reader.pages[0].extract_text()

# Find the "Date of Clean-Up" in the first page text
import re
date_match = re.search(r"Date of Clean-Up:\s*(\d+/\d+/\d+)", first_page_text)
if date_match:
    date_of_cleanup = date_match.group(1)
    print(f"Date of Clean-Up: {date_of_cleanup}")
else:
    print("Date of Clean-Up not found.")

# Extract the table from the second page using tabula
tables = tabula.read_pdf(pdf_path, pages=2, multiple_tables=True)

# Check if tables were found
if tables:
    second_page_table = tables[0]  # Assuming the first table on the second page is needed
    print(second_page_table)
else:
    print("No tables found on the second page.")