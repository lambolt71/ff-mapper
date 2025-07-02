import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os

st.set_page_config(page_title="FF Gamebook Graph", layout="wide")
st.title("📘 Fighting Fantasy Playthrough Visualizer")

st.markdown("""
Enter your playthrough transitions below.  
Use format: `start,rejected1,...,rejectedN,chosen`  
Mark secret paths with `*`, e.g., `123,400*`  
Each line must begin with a unique paragraph number.
""")

data_input = st.text_area("Enter transitions (one per line)", height=200)

if st.button("Generate Graph") and data_input.strip():
    lines = data_input.strip().split("\n")
    G = nx.DiGraph()

    for line in lines:
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if not parts or len(parts) < 2:
            continue

        source = parts[0]
        targets = parts[1:]

        chosen_raw = targets[-1]
        is_secret = chosen_raw.endswith("*")
        chosen = chosen_raw.rstrip("*")

        # Add chosen path
        G.add_edge(source, chosen, type="chosen", secret=is_secret)

        # Add rejected options
        for opt in targets[:-1]:
            if opt == source:
                continue
            G.add_edge(source, opt, type="rejected", secret=False)

    # Create Pyvis network
    net = Network(height="700px", width="100%", directed=True, notebook=False, bgcolor="#222222", font_color="white")
    net.barnes_hut()

    for node in G.nodes:
        net.add_node(node, label=f"{node}")

    for source, target, data in G.edges(data=True):
        if data["type"] == "chosen":
            if data.get("secret", False):
                color = "red"
                dashes = True
            else:
                color = "green"
                dashes = False
        else:
            color = "gray"
            dashes = True

        net.add_edge(source, target, color=color, arrows="to", dashes=dashes)

    # Generate and display HTML
    with tempfile.TemporaryDirectory() as tmpdirname:
        path = os.path.join(tmpdirname, "graph.html")
        net.write_html(path, notebook=False)

        with open(path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        st.components.v1.html(html_content, height=600, scrolling=True)
