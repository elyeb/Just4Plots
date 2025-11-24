import matplotlib.pyplot as plt

# Timeline data with start year and label to show
events = [
    (1907, "1907", "Alexandrine/ Mamaman est née"),
    (1914, "1914–18", "Jacky, fils aîné de Léonie, est décédé"),
    (1926, "1926–27", "Mamaman retourne à Mulhouse, rencontre André Heyberg"),
    (1928, "1928", "Jacqueline est née"),
    (1934, "1934", "Léonie, grand-mère de Jacqueline est décédée à 63 ans"),
    (1944, "1944–45", "Mamaman tombe malade de schizophrénie à 37 ans et entre à Rouffach"),
    (1948, "1948", "Jacques Thule, grand-père de Jacqueline, est décédé"),
    (1949, "1949–50", "Vente du magasin"),
    (1953, "1953–54", "Jacqueline rencontre Pauli"),
    (1956, "1956", "Mamaman sort de Rouffach"),
    (1975, "1975", "Mariage avec Pauli"),
    (1983, "1983", "Mère de Paul est décédée"),
]

# Sort events by the numeric year
events.sort(reverse=False)

# Extract start years and normalized positions
start_years = [event[0] for event in events]
labels = [event[1] for event in events]
descriptions = [event[2] for event in events]

# Normalize years for vertical placement (min year = 0)
min_year = min(start_years)
norm_years = [year - min_year for year in start_years]

# Create figure and axis
fig, ax = plt.subplots(figsize=(6, 12))
ax.set_ylim(-1, max(norm_years) + 1)
ax.set_xlim(-1, 1)
ax.axis('off')

# Plot the timeline with labels as ranges
for y, label, desc in zip(norm_years, labels, descriptions):
    ax.plot([0], [y], 'o', color='black')
    ax.text(-0.05, y, label, ha='right', va='center', fontsize=10, color='black')
    ax.text(0.05, y, desc, ha='left', va='center', fontsize=10, color='black')

# Draw vertical line
ax.plot([0, 0], [min(norm_years), max(norm_years)], color='black', linewidth=1)

plt.tight_layout()
plt.show()
