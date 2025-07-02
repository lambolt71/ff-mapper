import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import os

st.set_page_config(page_title="FF Graph Mapper", layout="wide")
st.title("🗺️ Fighting Fantasy Graph Builder")

# Storage for user inputs
if "edges" not in st.session_state:
    st.session_state.edges = []

# --- Sidebar: Add New Path ---
st.sidebar.header("Add Path")
path_input = st.sidebar.text_input("Enter path (e.g. 123,4,10,200,400*)")
tag_input = st.sidebar.text_input("Optional tag/comment (e.g. got potion from wizard)")
if st.sidebar.button("Add Path"):
    parts = [p.strip() for p in path_input.split(",") if p.strip()]

    if len(parts) >= 2:
        from_page = parts[0]
        to_and_chosen = parts[1:]

        chosen = to_and_chosen[-1]
        to_pages = to_and_chosen[:-1]

        # Save all other links as non-chosen (optional, not drawn)
        for to_page in to_pages:
            st.session_state.edges.append({
                "from": from_page,
                "to": to_page,
                "chosen": False,
                "tag": ""
            })

        # Save chosen path
        st.session_state.edges.append({
            "from": from_page,
            "to": chosen.replace("*", ""),
            "chosen": True,
            "tag": tag_input.strip()
        })
    else:
        st.warning("Please enter at least a from-page and a chosen path.")

# --- Export/Import ---
st.sidebar.markdown("---")
if st.sidebar.button("Export as CSV"):
    df = pd.DataFrame(st.session_state.edges)
    df.to_csv("graph_data.csv", index=False)
    st.sidebar.success("Saved as graph_data.csv")

uploaded = st.sidebar.file_uploader("Import CSV", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    st.session_state.edges = df.to_dict(orient="records")
    st.sidebar.success("Imported successfully")

# --- Build Graph ---
G = nx.DiGraph()
for edge in st.session_state.edges:
    G.add_edge(edge["from"], edge["to"])

# --- Display Graph ---
net = Network(height="700px", width="100%", bgcolor="#111", font_color="white")
net.from_nx(G)

# Add extra info to edges (color, label)
for edge in st.session_state.edges:
    e = net.get_edge(edge["from"], edge["to"])
    if e:
        e["color"] = "lime" if edge["chosen"] else "gray"
        e["width"] = 3 if edge["chosen"] else 1
        if edge["tag"]:
            e["title"] = edge["tag"]

# Save HTML and render
net_path = "graph.html"
net.write_html(net_path)
with open(net_path, 'r', encoding='utf-8') as f:
    html_string = f.read()
st.components.v1.html(html_string, height=600, scrolling=True)

