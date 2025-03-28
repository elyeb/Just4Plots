""" 
Use the WSF-provided format to graph vehicle ridership for the main routes
"""

import pandas as pd
import matplotlib.pyplot as plt
import re
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MultipleLocator
# Load the data
edmonds_kingston = pd.read_excel('/Users/elyebliss/Documents/Just4Plots/data/edmonds_kingston_west_2024.xlsx')
kingston_edmonds = pd.read_excel('/Users/elyebliss/Documents/Just4Plots/data/kingston_edmonds_east_2024.xlsx')
seattle_bainbridge = pd.read_excel('/Users/elyebliss/Documents/Just4Plots/data/seattle_bainbridge_west_2024.xlsx')
bainbridge_seattle = pd.read_excel('/Users/elyebliss/Documents/Just4Plots/data/seattle_bainbridge_east_2024.xlsx')

OUTPUT_ROOT = "/Users/elyebliss/Documents/Just4Plots/outputs/plots/"
# Reformat

def reformat_data(df):
    """
    df = seattle_bainbridge.copy()
    """

    df.rename(columns={'Unnamed: 0': 'sailing','Unnamed: 1':'Actual Vessel Name'}, inplace=True)
    df = df[df['sailing']!= 'Grand Total']


    # start by concatenating the first 3 rows
    new_cols = []

    for i in range(0, df.shape[1]):
        if df.columns[i] in (['sailing', 'Actual Vessel Name']):
            new_cols.append(df.columns[i])
        else:
            new_cols.append(df.columns[i] +"," + df.iloc[0,i] +","+ df.iloc[1,i] )

    df.columns = new_cols
    df = df.iloc[2:,:]
    df_long = df.melt(id_vars=['sailing', 'Actual Vessel Name'], var_name='Date', value_name='Ridership')
    df_long['Date']  = df_long['Date'].str.split(',')
    df_long['ridership_type'] = df_long['Date'].apply(lambda x: x[1])
    df_long['vehicle_type'] = df_long['Date'].apply(lambda x: x[2])
    df_long['Date'] = df_long['Date'].apply(lambda x: x[0])

    pattern = re.compile(r'\.\d{1}')

    df_long['Date'] = df_long['Date'].apply(lambda x: re.sub(pattern,'',x))
    df_long.rename(columns={'Actual Vessel Name': 'vessel_name'}, inplace=True)
    df_long['vessel_name'] = df_long['vessel_name'].str.upper()

    return df_long



def make_plot_df(df):
    """
    df = seattle_bainbridge_long.copy()
    """

    df = df[~df['Ridership'].isna()]
    df["vessel_name"].value_counts()

    # agg to avg number of vehicles by sailing time
    df_plt = df[df['ridership_type'] == 'Vehicles']
    # sum across vehicle types
    df_plt = df_plt.groupby(['sailing', 'Date'])['Ridership'].sum().reset_index()

    df_plt['Date'] = pd.to_datetime(df_plt['Date'])
    df_plt['Day of Week'] = df_plt['Date'].dt.day_name()

    # get average per sailing/day of week
    df_plt = df_plt.groupby(['sailing', 'Day of Week'])['Ridership'].mean().reset_index()

    return df_plt

def plot_hist_by_day(ferry, dep, dest):
    """
    ferry = df_plt_e_k.copy()
    dep = 'Edmonds'
    dest = 'Kingston'
    """
    OUTFILE = f'{dep.replace(" ","_").lower()}_{dest.replace(" ","_").lower()}_vehicles_by_day.pdf'

    # Formatter function to convert numeric sailing_time back to time format
    def time_formatter(x, pos):
        hours = int(x)
        minutes = int((x - hours) * 60)
        return f'{hours:02d}:{minutes:02d}'

    # Convert sailing times to datetime and then to numeric (e.g., hours)
    ferry['sailing_time'] = pd.to_datetime(ferry['sailing'], format='%H:%M:%S', errors='coerce').dt.hour + pd.to_datetime(ferry['sailing'], format='%H:%M:%S', errors='coerce').dt.minute / 60

    x_min = ferry['sailing_time'].min()
    x_max = ferry['sailing_time'].max()
    y_max = ferry['Ridership'].max()+25

    num_rows = 7
    fig, ax = plt.subplots(num_rows, 1, figsize=(18, num_rows * 8)) #, dpi=300

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    row_counter = 0
    for day in days:
        day_df = ferry[ferry["Day of Week"] == day]

        ax[row_counter].bar(day_df['sailing_time'], height=day_df['Ridership'])
        ax[row_counter].xaxis.set_major_formatter(FuncFormatter(time_formatter))
        ax[row_counter].xaxis.set_major_locator(MultipleLocator(2)) 
        ax[row_counter].set_xlim(x_min, x_max)
        ax[row_counter].set_ylim(0, y_max)
        ax[row_counter].tick_params(axis='both', which='major', labelsize=12)
        if day=="Monday":
            ax[row_counter].set_title(f"{dep} to {dest}: {day}s", fontsize=30)
        else:
            ax[row_counter].set_title(day, fontsize=20)
        if day=="Sunday":
            ax[row_counter].set_xlabel("Scheduled Departure", fontsize=15)
        ax[row_counter].set_ylabel(f"Avg. Num. Vehicles", fontsize=15)
            
        row_counter += 1

    plt.tight_layout()
    plt.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.95, hspace=0.4, wspace=0.4)
    plt.show()
    fig.savefig(OUTPUT_ROOT + OUTFILE, bbox_inches="tight", dpi=300)
    plt.show()


edmonds_kingston_long = reformat_data(edmonds_kingston)
kingston_edmonds_long = reformat_data(kingston_edmonds)
seattle_bainbridge_long = reformat_data(seattle_bainbridge)
bainbridge_seattle_long = reformat_data(bainbridge_seattle)


# Only keep non-empty ferries
df_plt_e_k = make_plot_df(edmonds_kingston_long)
df_plt_k_e = make_plot_df(kingston_edmonds_long)
df_plt_s_b = make_plot_df(seattle_bainbridge_long)
df_plt_b_s = make_plot_df(bainbridge_seattle_long)

# plot and save
plot_hist_by_day(df_plt_e_k, 'Edmonds', 'Kingston')
plot_hist_by_day(df_plt_k_e, 'Kingston', 'Edmonds')
plot_hist_by_day(df_plt_s_b, 'Seattle', 'Bainbridge')
plot_hist_by_day(df_plt_b_s, 'Bainbridge', 'Seattle')

