import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import os

st.set_page_config(page_title="FF Graph Mapper", layout="wide")
st.title("🗌️ Fighting Fantasy Graph Builder")

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
            "to": chosen.replace("*", "").replace("x", ""),
            "chosen": True,
            "tag": tag_input.strip(),
            "is_secret": chosen.endswith("*")
        })
    else:
        st.warning("Please enter at least a from-page and a chosen path.")

# --- Paste in CSV-style data ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Paste Data from CSV")
pasted_data = st.sidebar.text_area("Paste rows like: 123,4,5,6,200*,Got key")
if st.sidebar.button("Add Pasted Paths"):
    for line in pasted_data.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]

        if len(parts) == 1:
            # Single-node dead end, e.g. "161x"
            end = parts[0].replace("*", "").replace("x", "")
            st.session_state.edges.append({
                "from": end,
                "to": end,
                "chosen": True,
                "tag": "",
                "is_secret": False
            })

        elif len(parts) >= 2:
            from_page = parts[0]
            tag = parts[-1] if not parts[-1].isdigit() and not parts[-1].endswith("*") and not parts[-1].endswith("x") else ""
            dest_parts = parts[1:-1] if tag else parts[1:]

            chosen = dest_parts[-1]
            to_pages = dest_parts[:-1]

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
                "to": chosen.replace("*", "").replace("x", ""),
                "chosen": True,
                "tag": tag,
                "is_secret": chosen.endswith("*")
            })
        else:
            st.warning(f"Invalid line skipped: {line}")

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

# --- Help ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Input Format Help")
st.sidebar.markdown("""
- Enter a **sequence of page numbers** separated by commas.
- The **first number** is the current page you're on.
- The **last number** is the **chosen destination page**.
- All numbers **in between** are unchosen options from that page.
- Add `*` to the last number to mark it as a **secret or hidden exit**.
- Add `x` to the last number to mark it as a **dead end** — the node will turn **red**.
- You can optionally add a short **text tag** — this appears as a **tooltip** on the destination node.  
  Dashed lines indicate **secret paths**.
- Arrows show directions of travel
- Orange Nodes have not been explored further yet
""")

# --- Build Graph ---
net = Network(height="700px", width="100%", bgcolor="#111", font_color="white", directed=True)
added_edges = set()

# Determine which nodes are unexplored
all_from = set(edge["from"] for edge in st.session_state.edges)
all_to = set(edge["to"] for edge in st.session_state.edges)
unexplored = all_to - all_from

# Re-detect death nodes as nodes that only point to themselves
death_nodes = {
    edge["to"]
    for edge in st.session_state.edges
    if edge["from"] == edge["to"]
}

for edge in st.session_state.edges:
    edge_key = (edge["from"], edge["to"])
    if edge_key not in added_edges:
        # From node
        if edge["from"] not in net.node_ids:
            net.add_node(edge["from"], label=edge["from"], color="orange" if edge["from"] in unexplored else "#97C2FC")

        # To node
        node_color = "red" if edge["to"] in death_nodes else ("orange" if edge["to"] in unexplored else "#97C2FC")
        if edge["to"] not in net.node_ids:
            net.add_node(edge["to"], label=edge["to"], title=edge["tag"] if edge["tag"] else "", color=node_color)

        net.add_edge(
            edge["from"],
            edge["to"],
            color="gray",
            width=2,
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
