import tabula
import pandas as pd
import os
import re

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "../data/dui_raw_pdfs/")

# PAGES_DICT = {
#     1998: 

# }

all_pdfs = sorted(os.listdir(DATA_FOLDER))

# table_98 = tabula.read_pdf(DATA_FOLDER+all_pdfs[0], pages="24-37", multiple_tables=True)
table_24 = tabula.read_pdf(DATA_FOLDER+'2024.pdf', pages="105-119", multiple_tables=False)



def clean_table(df,year):
    """
    df = table_24.copy()
    year = 2024
    """
    df = pd.DataFrame(df[0])
    df.columns
    df.rename(columns={'Unnamed: 0':"Location"},inplace=True)
    df.dropna(subset=["Location"],inplace=True)
    start_index = df[(df["Location"]=="Adams County")&df['Filings'].isna()].index[0]
    df = df[df.index>=start_index]
    county_list = list(df[df['Filings'].isna()].Location)

    # deal with county rows
    df['County'] =''
    
    df = df.reset_index(drop=True)
    for i in range(0,len(df)):
        if df['Location'].iloc[i] in county_list:
            county = df['Location'].iloc[i]
            df['County'].iat[i] =county
        else:
            df['County'].iat[i] =county

    df.dropna(subset=['Filings'],inplace=True)

    # add extra variables
    df['Year'] = year
    df['State'] = 'WA'

    # only keep Counties and Metropolitan areas
    pattern_M = re.compile(r'\..*\sM')
    df_M = df[df["Location"].str.contains(pattern_M,regex=True)]

    df_county = df[df["Location"].str.contains('County')]

    return df

