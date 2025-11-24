"""
Is the spread between oil and gas prices increasing?

oil prices from: https://fred.stlouisfed.org/series/DCOILWTICO#
gas prices from: https://fred.stlouisfed.org/series/APU000074714
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import numpy as np

## Load data
gas = pd.read_csv('../data/gas_prices.csv')
oil = pd.read_csv('../data/oil_prices.csv')

outfile = 'oil_gas_scatter.png'

# merge
gas.columns = ['date','gas_price']
oil.columns = ['date','oil_price']
df = pd.merge(gas,oil,on='date',how='inner')

# Fit a linear model
coefficients = np.polyfit(df['oil_price'], df['gas_price'], 1)  # Linear regression (degree=1)
slope, intercept = coefficients
df['predicted_gas_price'] = slope * df['oil_price'] + intercept  # Predicted gas prices
df['residual'] = abs(df['gas_price'] - df['predicted_gas_price'])  # Residuals

# Identify top 5 outliers based on residuals
top_outliers = df.nlargest(10, 'residual')
# keep max 1 outlier per year
top_outliers = top_outliers.sort_values('date')
top_outliers['year'] = pd.to_datetime(top_outliers['date']).dt.year
top_outliers = top_outliers.drop_duplicates(subset=['year'], keep='last')


# Ensure the 'date' column is in datetime format
df['date'] = pd.to_datetime(df['date'])

# Normalize the dates to a range between 0 and 1 for the colormap
norm = mcolors.Normalize(vmin=df['date'].min().toordinal(), vmax=df['date'].max().toordinal())

# Create a colormap that transitions from blue to red
cmap = cm.get_cmap('coolwarm')

# Map each date to a color
colors = [cmap(norm(date.toordinal())) for date in df['date']]

# Plot scatter plot with color-coded points
fig, ax = plt.subplots(figsize=(11, 8))
fig.patch.set_facecolor('white')  # Figure background
ax.set_facecolor('white')

scatter = ax.scatter(df['oil_price'], df['gas_price'], c=colors, alpha=0.5, edgecolor='gray', s=50)

# Add a colorbar to show the date range
sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

# Create the colorbar
cbar = plt.colorbar(sm, ax=ax)
cbar.set_label('Date', fontsize=12, labelpad=10)  # Add padding to move the label away from the ticks

# Format the colorbar ticks to show dates
date_ticks = np.linspace(df['date'].min().toordinal(), df['date'].max().toordinal(), num=5)  # Generate 5 evenly spaced ticks
cbar.set_ticks(date_ticks)  # Set the ticks on the colorbar
cbar.set_ticklabels([pd.Timestamp.fromordinal(int(ordinal)).strftime('%Y-%m-%d') for ordinal in date_ticks])  # Format ticks as dates

# Plot the regression line as a light gray dotted line
x_vals = np.linspace(df['oil_price'].min(), df['oil_price'].max(), 100)
y_vals = slope * x_vals + intercept
ax.plot(x_vals, y_vals, color='gray', linestyle='dotted', linewidth=1.5, label='Linear Fit')

# Annotate top outliers, avoiding overlap
min_distance = 0.5  # Minimum distance between annotations
annotated_points = []

# for _, row in top_outliers.iterrows():
#     # Check if the point is too close to an already annotated point
#     too_close = any(
#         abs(row['oil_price'] - x) < min_distance and abs(row['gas_price'] - y) < min_distance
#         for x, y in annotated_points
#     )
#     if not too_close:
#         ax.text(
#             row['oil_price'], row['gas_price'], 
#             f"{row['date']}", fontsize=11, color='black', ha='right', va='bottom',
#             bbox=dict(facecolor='white', alpha=0, edgecolor='none')
#         )
#         annotated_points.append((row['oil_price'], row['gas_price']))

# Add labels, grid, and legend
ax.set_title("Average Gas vs Crude Oil Prices", pad=15, size=20, fontweight="bold")
ax.set_xlabel('Oil $', fontsize=15)
ax.set_ylabel('Gas $', fontsize=15)
ax.grid(True)

# Add text below the plot for data source
fig.text(
    0.05, -0.05,
   "Crude Oil Prices: West Texas Intermediate: https://fred.stlouisfed.org/series/DCOILWTICO#\nAverage Price: Gasoline, Unleaded Regular in U.S. City: https://fred.stlouisfed.org/series/APU000074714",
    ha="left",
    fontsize=10,
    color="black"
)

plt.tight_layout()  # Adjust layout to prevent label overlap

plt.savefig(f'../outputs/plots/{outfile}',dpi=300, bbox_inches="tight", facecolor="white")

# Show the plot
plt.show()