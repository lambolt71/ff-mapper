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

        # Save skipped options
        for to_page in to_pages:
            st.session_state.edges.append({
                "from": from_page,
                "to": to_page,
                "chosen": False,
                "tag": "",
                "is_secret": False
            })

        # Save chosen path
        st.session_state.edges.append({
            "from": from_page,
            "to": chosen.replace("*", ""),
            "chosen": True,
            "tag": tag_input.strip(),
            "is_secret": chosen.endswith("*")
        })
    else:
        st.warning("Please enter at least a from-page and a chosen path.")

# --- Export ---
st.sidebar.markdown("---")
if st.sidebar.button("Export as CSV"):
    df = pd.DataFrame(st.session_state.edges)

    # Clean and ensure types
    df["from"] = df["from"].astype(str)
    df["to"] = df["to"].astype(str)
    df["chosen"] = df["chosen"].astype(bool)
    df["tag"] = df["tag"].fillna("").astype(str)
    df["is_secret"] = df["is_secret"].fillna(False).astype(bool)

    csv = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("⬇️ Download CSV", csv, "graph_data.csv", "text/csv")

# --- Import ---
uploaded = st.sidebar.file_uploader("Import CSV", type="csv")
if uploaded and "csv_loaded" not in st.session_state:
    df = pd.read_csv(uploaded)

    # Säkerställ kolumner och typer
    expected_cols = {"from", "to", "chosen", "tag", "is_secret"}
    for col in expected_cols:
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

# Efter omstart: rensa flagga
if "csv_loaded" in st.session_state:
    del st.session_state.csv_loaded

# --- Help ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Input Format Help")
st.sidebar.markdown("""
- Enter a **sequence of page numbers** separated by commas.
- The **first number** is the current page you're on.
- The **last number** is the **chosen destination page**.
- All numbers **in between** are unchosen options from that page.
- Add `*` to the last number to mark it as a **secret or hidden exit**.
- You can optionally add a short **text tag** — this appears as a **tooltip** on the destination node.
- Green lines show your **chosen path**.  
  Dashed green lines indicate **secret paths**.
- Arrows show directions of travel
- Orange Nodes have not been explored further yet
""")

# --- Build Graph ---
net = Network(height="700px", width="100%", bgcolor="#111", font_color="white", directed=True)
added_edges = set()

for edge in st.session_state.edges:
    edge_key = (edge["from"], edge["to"])
    if edge_key not in added_edges:
        # Add from-node
        if edge["from"] not in net.node_ids:
            net.add_node(edge["from"], label=edge["from"])

        # Add to-node with tooltip
        if edge["to"] not in net.node_ids:
            net.add_node(
                edge["to"],
                label=edge["to"],
                title=edge["tag"] if edge["tag"] else ""
            )

        # Add edge
        net.add_edge(
            edge["from"],
            edge["to"],
            color="lime" if edge["chosen"] else "gray",
            width=3 if edge["chosen"] else 1,
            title=edge["tag"] if edge["tag"] else "",
            dashes=edge.get("is_secret", False)
        )
        added_edges.add(edge_key)

# --- Render Graph ---
net_path = "graph.html"
net.write_html(net_path)
with open(net_path, "r", encoding="utf-8") as f:
    html_string = f.read()
st.components.v1.html(html_string, height=600, scrolling=True)
