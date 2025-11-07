"""
Try making a Sankey diagram with donation data.
"""

import pandas as pd
import plotly.graph_objects as go
import os

# Load the data
DATA_FOLDER = "/Users/elyebliss/Documents/Just4Plots/data/lobbying/pdc_downloads/subsets"
os.listdir(DATA_FOLDER)

contr_pac = pd.read_csv(os.path.join(DATA_FOLDER, "relevant_pacs_grouped.csv"))
contr_cand = pd.read_csv(os.path.join(DATA_FOLDER, "direct_contributors_grouped.csv"))
pac_spend = pd.read_csv(os.path.join(DATA_FOLDER, "sea_mayor_25.csv"))

# Color map for contribution sizes
color_map = {
    'SMALL (<=$150)': 'rgba(173, 216, 230, 0.8)',  # light blue
    'MEDIUM (<=$1000)': 'rgba(64, 224, 208, 0.8)', # medium turquoise
    'BIG (>$1000)': 'rgba(0, 76, 153, 0.8)'        # dark blue
}

# Build all unique nodes
contr_pac = contr_pac.sort_values(['sponsor_name','total_contributed'], ascending=False)
contr_cand = contr_cand.sort_values(['candidate_name','total_contributed'], ascending=False)
pac_spend = pac_spend.sort_values(['candidate_name','total_spent'], ascending=False)

contr_pac_cand1 = contr_pac[contr_pac['sponsor_name']=="BRUCE HARRELL FOR SEATTLE'S FUTURE"]
contr_pac_cand2 = contr_pac[contr_pac['sponsor_name']=='FUSE VOTES']
contr_cand_cand1 = contr_cand[contr_cand['candidate_name']=='BRUCE HARRELL']
contr_cand_cand2 = contr_cand[contr_cand['candidate_name']=='KATIE WILSON']

contributor_names = contr_cand_cand2['contributor_name'].tolist() + contr_cand_cand1['contributor_name'].tolist()+ contr_pac_cand1['contributor_name'].tolist()+contr_pac_cand2['contributor_name'].tolist() 
sponsor_names = contr_pac['sponsor_name'].tolist() + pac_spend['sponsor_name'].tolist()
candidate_names = pac_spend['candidate_name'].tolist() + contr_cand['candidate_name'].tolist()



all_nodes = pd.Series(contributor_names + sponsor_names + candidate_names).unique().tolist()

# Build node labels
node_labels = []
for n in all_nodes:
    if n in sponsor_names or n in candidate_names:
        node_labels.append(n)
    else:
        node_labels.append("")  # blank for contributors

# Build links and link_colors as before
links = []
link_colors = []

# Start from top-right corner in paper coords
legend_x = 1.1
legend_y_start = 0.80
box_height = 0.03
gap = 0.05

# sponsor_name -> candidate_name (pac_spend)
for _, row in pac_spend.iterrows():
    links.append(dict(
        source=all_nodes.index(row['sponsor_name']),
        target=all_nodes.index(row['candidate_name']),
        value=row['total_spent']
    ))
    link_colors.append(color_map.get(row['contribution_size'], 'rgba(0,0,0,0.3)'))
    
# contributor_name -> sponsor_name (contr_pac)
for _, row in contr_pac.iterrows():
    links.append(dict(
        source=all_nodes.index(row['contributor_name']),
        target=all_nodes.index(row['sponsor_name']),
        value=row['total_contributed']
    ))
    link_colors.append(color_map.get(row['contribution_size'], 'rgba(0,0,0,0.3)'))


# contributor_name -> candidate_name (contr_cand)
for _, row in contr_cand.iterrows():
    links.append(dict(
        source=all_nodes.index(row['contributor_name']),
        target=all_nodes.index(row['candidate_name']),
        value=row['total_contributed']
    ))
    link_colors.append(color_map.get(row['contribution_size'], 'rgba(0,0,0,0.3)'))



# Sankey diagram
fig = go.Figure(go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=node_labels,
    ),
    link=dict(
        source=[l['source'] for l in links],
        target=[l['target'] for l in links],
        value=[l['value'] for l in links],
        color=link_colors
    )
))

# Add legend title
fig.add_annotation(
    x=legend_x,  # centered over boxes
    y=legend_y_start + 0.05,
    xref="paper", yref="paper",
    text="<b>Contribution Size</b>",
    showarrow=False,
    font=dict(size=16, color="black"),
    align="center",
    xanchor="center",
    yanchor="bottom"
)

# Custom legend inside the plot area
legend_items = [
    ('SMALL (<=$150)', color_map['SMALL (<=$150)']),
    ('MEDIUM (<=$1000)', color_map['MEDIUM (<=$1000)']),
    ('BIG (>$1000)', color_map['BIG (>$1000)'])
]

for i, (label, col) in enumerate(legend_items):
    y0 = legend_y_start - i * gap
    y1 = y0 + box_height
    fig.add_shape(
        type="rect",
        x0=legend_x, x1=legend_x + 0.03,
        y0=y0, y1=y1,
        xref="paper", yref="paper",
        line=dict(color="black", width=0.5),
        fillcolor=col
    )
    fig.add_annotation(
        x=legend_x - 0.01,
        y=y1,#y=y0 + box_height / 2,
        xref="paper", yref="paper",
        text=label,
        showarrow=False,
        font=dict(size=14, color="black"),
        align="left"
    )
fig.update_layout(
    title_text="Flows of Contributions and PAC Spending for Candidates' Campaigns",
    font_size=30,
    width=2200,
    height=1000,
    margin=dict(l=50, r=300, t=100, b=50),
    annotations=list(fig.layout.annotations) + [
        dict(x=0.01, y=1.05, xref='paper', yref='paper',
             text='Contributors', showarrow=False,
             font=dict(size=24, color='black')),
        dict(x=0.5, y=1.05, xref='paper', yref='paper',
             text='PACs', showarrow=False,
             font=dict(size=24, color='black')),
        dict(x=0.99, y=1.05, xref='paper', yref='paper',
             text='Candidates', showarrow=False,
             font=dict(size=24, color='black'))
    ]
)

fig.show()