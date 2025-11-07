import streamlit as st
from PIL import Image
import os

# Streamlit app
st.title("2024 Average Ferry Ridership by Day Visualization")

# Display the saved graphs
OUTPUT_ROOT = os.path.join(os.path.dirname(__file__), "../outputs/plots/")
graph_files = [
    "seattle_bainbridge_vehicles_by_day.png",
    "bainbridge_seattle_vehicles_by_day.png",
    "edmonds_kingston_vehicles_by_day.png",
    "kingston_edmonds_vehicles_by_day.png",
]

if graph_files:
    for graph_file in graph_files:
        st.subheader(graph_file.replace("_", " ").replace(".png", "").title())
        image = Image.open(os.path.join(OUTPUT_ROOT, graph_file))
        st.image(image, caption=graph_file, use_container_width=True)
