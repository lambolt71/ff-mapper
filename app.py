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
                "tag": "",
                "is_secret": False  # NEW
            })

        # Save chosen path
        st.session_state.edges.append({
            "from": from_page,
            "to": chosen.replace("*", ""),
            "chosen": True,
            "tag": tag_input.strip(),
            "is_secret": chosen.endswith("*")  # ✅ Add this line
        })
    else:
        st.warning("Please enter at least a from-page and a chosen path.")

# --- Export/Import ---
st.sidebar.markdown("---")
if st.sidebar.button("Export as CSV"):
    df = pd.DataFrame(st.session_state.edges)
    df.to_csv("graph_data.csv", index=False)
    st.sidebar.success("Saved as graph_data.csv")

    # ✅ Add download button for user to get the file
    with open("graph_data.csv", "rb") as f:
        st.sidebar.download_button(
            label="⬇️ Download CSV",
            data=f,
            file_name="graph_data.csv",
            mime="text/csv"
        )
        

uploaded = st.sidebar.file_uploader("Import CSV", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    st.session_state.edges = df.to_dict(orient="records")
    st.sidebar.success("Imported successfully")

# --- Input Format Help ---
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
""")

# --- Build Graph ---
net = Network(height="700px", width="100%", bgcolor="#111", font_color="white")
added_edges = set()

for edge in st.session_state.edges:
    edge_key = (edge["from"], edge["to"])
    if edge_key not in added_edges:
        # Add from-node if not already added
        if edge["from"] not in net.node_ids:
            net.add_node(edge["from"], label=edge["from"])

        # Add to-node with optional tooltip
        if edge["to"] not in net.node_ids:
            net.add_node(
                edge["to"],
                label=edge["to"],
                title=edge["tag"] if edge["tag"] else ""
            )

        # Add the edge
        edge_style = "dash" if edge.get("is_secret", False) else "solid"
        net.add_edge(
            edge["from"],
            edge["to"],
            color="lime" if edge["chosen"] else "gray",
            width=3 if edge["chosen"] else 1,
            title=edge["tag"] if edge["tag"] else "",
             dashes=(edge_style == "dash")  # pyvis supports `dashes=True`
        )

        added_edges.add(edge_key)

# Save HTML and render
net_path = "graph.html"
net.write_html(net_path)
with open(net_path, 'r', encoding='utf-8') as f:
    html_string = f.read()
st.components.v1.html(html_string, height=600, scrolling=True)
