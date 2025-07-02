import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd

st.set_page_config(page_title="FF Graph Mapper", layout="wide")
st.title("🗺️ Fighting Fantasy Graph Builder")

# --- Session Init ---
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
        to_pages = parts[1:-1]
        chosen = parts[-1]

        for to_page in to_pages:
            st.session_state.edges.append({
                "from": from_page,
                "to": to_page,
                "chosen": False,
                "tag": "",
                "is_secret": False
            })

        st.session_state.edges.append({
            "from": from_page,
            "to": chosen.replace("*", ""),
            "chosen": True,
            "tag": tag_input.strip(),
            "is_secret": chosen.endswith("*")
        })
    else:
        st.warning("Please enter at least a from-page and a chosen path.")

# --- Export CSV ---
st.sidebar.markdown("---")
if st.sidebar.button("Export as CSV"):
    df = pd.DataFrame(st.session_state.edges)
    df["from"] = df["from"].astype(str)
    df["to"] = df["to"].astype(str)
    df["chosen"] = df["chosen"].astype(bool)
    df["tag"] = df["tag"].fillna("").astype(str)
    df["is_secret"] = df["is_secret"].fillna(False).astype(bool)
    csv = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("⬇️ Download CSV", csv, "graph_data.csv", "text/csv")

# --- Import CSV ---
uploaded = st.sidebar.file_uploader("Import CSV", type="csv")
if uploaded and "csv_loaded" not in st.session_state:
    df = pd.read_csv(uploaded)
    expected = {"from", "to", "chosen", "tag", "is_secret"}
    for col in expected:
        if col not in df.columns:
            df[col] = "" if col == "tag" else False
    df["from"] = df["from"].astype(str)
    df["to"] = df["to"].astype(str)
    df["chosen"] = df["chosen"].astype(bool)
    df["tag"] = df["tag"].fillna("").astype(str)
    df["is_secret"] = df["is_secret"].fillna(False).astype(bool)
    st.session_state.edges = df.to_dict(orient="records")
    st.session_state.csv_loaded = True
    st.rerun()

# --- Clear rerun flag ---
if "csv_loaded" in st.session_state:
    del st.session_state.csv_loaded

# --- Help Text ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Input Format Help")
st.sidebar.markdown("""
- Enter a **sequence of page numbers** separated by commas.
- The **first number** is your current page.
- The **last number** is your **chosen destination**.
- Pages in between are skipped choices.
- Use `*` on the last number to mark it as **secret**.
- Tags show up as **tooltips**.
- Green lines = chosen path, dashed = secret.
- Orange nodes = not yet visited.
""")

# --- Build Graph ---
net = Network(height="700px", width="100%", bgcolor="#111", font_color="white", directed=True)
added_edges = set()

# Compute explored pages (those that are a "from")
explored_pages = {edge["from"] for edge in st.session_state.edges}

for edge in st.session_state.edges:
    edge_key = (edge["from"], edge["to"])
    if edge_key not in added_edges:
        # From-node
        if edge["from"] not in net.node_ids:
            net.add_node(edge["from"], label=edge["from"], color="white")

        # To-node color: orange if not explored yet
        node_color = "orange" if edge["to"] not in explored_pages else "white"
        if edge["to"] not in net.node_ids:
            net.add_node(
                edge["to"],
                label=edge["to"],
                title=edge["tag"] if edge["tag"] else "",
                color=node_color
            )

        # Edge styling
        net.add_edge(
            edge["from"],
            edge["to"],
            color="lime" if edge["chosen"] else "gray",
            width=3 if edge["chosen"] else 1,
            title=edge["tag"],
            dashes=edge.get("is_secret", False)
        )
        added_edges.add(edge_key)

# --- Render Graph ---
net_path = "graph.html"
net.write_html(net_path)
with open(net_path, "r", encoding="utf-8") as f:
    html_string = f.read()
st.components.v1.html(html_string, height=600, scrolling=True)
