"""
Is the spread between oil and gas prices increasing?

oil prices from: https://fred.stlouisfed.org/series/DCOILWTICO#
gas prices from: https://fred.stlouisfed.org/series/APU000074714
"""
import pandas as pd
import matplotlib.pyplot as plt

## Load data
gas = pd.read_csv('../data/gas_prices.csv')
oil = pd.read_csv('../data/oil_prices.csv')

outfile = 'oil_gas_spread.png'

# merge
gas.columns = ['date','gas_price']
oil.columns = ['date','oil_price']
df = pd.merge(gas,oil,on='date',how='inner')

# get spread
df['spread'] = df['oil_price'] - df['gas_price']
df['oil_price_12mo_avg'] = df['oil_price'].rolling(window=12).mean()
df['gas_price_12mo_avg'] = df['gas_price'].rolling(window=12).mean()

# plot spread as area plot
fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor('white')  # Figure background
ax.set_facecolor('white') 
df['spread'].plot(kind='area', ax=ax, alpha=0.5, color='blue')
df['oil_price_12mo_avg'].plot(ax=ax, linestyle='dotted', color='red', label='Oil Price 12-Month Avg')
df['gas_price_12mo_avg'].plot(ax=ax, linestyle='dashed', color='green', label='Gas Price 12-Month Avg')

# Set x-axis labels to match the format in the data
# label all the januaries every 5 years
x_ticks = [i for i, d in enumerate(df['date']) if ((int(d[:4]) % 5 == 0) and (d[5:7] == '01'))]

ax.set_xticks(x_ticks)  # Set tick positions
ax.set_xticklabels([df['date'][i] for i in x_ticks], rotation=45, ha='right')  # Set labels for the chosen positions

# Add titles and labels
ax.set_title('Spread between Oil and Gas Prices',fontsize=18)
ax.set_xlabel('Date',fontsize=15)
ax.set_ylabel('Spread ($)',fontsize=15)
ax.grid(True)
ax.legend()
# plt.figtext(0.01, -0.05, "Oil prices from: https://fred.stlouisfed.org/series/DCOILWTICO#\nGas prices from: https://fred.stlouisfed.org/series/APU000074714", ha='left', fontsize=13)
ax.annotate(
    "Oil prices from: https://fred.stlouisfed.org/series/DCOILWTICO#\n"
    "Gas prices from: https://fred.stlouisfed.org/series/APU000074714",
    xy=(0, -0.3),  # Position below the plot
    xycoords='axes fraction',  # Coordinates relative to the axes
    ha='left', fontsize=12
)

plt.tight_layout()  # Adjust layout to prevent label overlap
plt.subplots_adjust(bottom=0.3)  # Increase the bottom margin

plt.savefig(f'../outputs/plots/{outfile}',dpi=300)
plt.show()