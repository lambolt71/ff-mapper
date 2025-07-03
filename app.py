import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="FF Graph Mapper", layout="wide")
st.title("🕜Ｚ Fighting Fantasy Graph Builder")

# ✅ Storage for user inputs must be initialized FIRST
if "edges" not in st.session_state:
    st.session_state.edges = []

# Find shortest path from Start to End if both exist
shortest_path_display = ""
if st.session_state.edges:
    G = nx.DiGraph()
    for edge in st.session_state.edges:
        if edge["to"] is not None:
            G.add_edge(edge["from"], edge["to"])

    start_node = next((e["from"] for e in st.session_state.edges if e["to"] is not None), None)
    end_nodes = [e["to"] for e in st.session_state.edges if e["to"] is not None and e["tag"].lower() == "end"]

    if end_nodes:
        try:
            path = nx.shortest_path(G, source=start_node, target=end_nodes[0])
            shortest_path_display = " → ".join(path)
            st.markdown(f"**Shortest Path:** {shortest_path_display}")
        except nx.NetworkXNoPath:
            st.markdown("**Shortest Path:** No path found between Start and End.")
    else:
        st.markdown("**Shortest Path:** End node not defined.")

# --- Sidebar: Add New Path ---
st.sidebar.header("Add Path")
path_input = st.sidebar.text_input("Enter path (e.g. 123,4,10,200,400*)")
tag_input = st.sidebar.text_input("Optional tag/comment (e.g. got potion from wizard)")

if st.sidebar.button("Add Path"):
    parts = [p.strip() for p in path_input.split(",") if p.strip()]

    if len(parts) >= 2:
        from_page_raw = parts[0]
        from_page = from_page_raw.rstrip("*xt+s")
        from_tag = ""
        if "+" in from_page_raw:
            from_tag = "Required"
        elif "t" in from_page_raw:
            from_tag = "End"
        elif "x" in from_page_raw:
            from_tag = "Dead"
        elif "s" in from_page_raw:
            from_tag = "Start"
        if from_tag:
            st.session_state.edges.append({
                "from": from_page,
                "to": None,
                "chosen": False,
                "tag": from_tag,
                "is_secret": "*" in from_page_raw
            })

        for to_page in parts[1:]:
            clean_to = to_page.rstrip("*xt+s")
            edge_tag = ""
            if "+" in to_page:
                edge_tag = "Required"
            elif "t" in to_page:
                edge_tag = "End"
            elif "x" in to_page:
                edge_tag = "Dead"
            elif "s" in to_page:
                edge_tag = "Start"

            st.session_state.edges.append({
                "from": from_page,
                "to": clean_to,
                "chosen": True,
                "tag": edge_tag,
                "is_secret": "*" in to_page
            })
    else:
        st.warning("Please enter at least a from-page and one destination.")

# --- Paste in CSV-style data ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📜 Paste Data from CSV")
pasted_data = st.sidebar.text_area("Paste rows like: 123,4,5,6,200*,Got key")
if st.sidebar.button("Add Pasted Paths"):
    for line in pasted_data.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) < 2:
            continue
        from_page_raw = parts[0]
        from_page = from_page_raw.rstrip("*xt+s")
        from_tag = ""
        if "+" in from_page_raw:
            from_tag = "Required"
        elif "t" in from_page_raw:
            from_tag = "End"
        elif "x" in from_page_raw:
            from_tag = "Dead"
        elif "s" in from_page_raw:
            from_tag = "Start"
        if from_tag:
            st.session_state.edges.append({
                "from": from_page,
                "to": None,
                "chosen": False,
                "tag": from_tag,
                "is_secret": "*" in from_page_raw
            })

        for to_page in parts[1:]:
            clean_to = to_page.rstrip("*xt+s")
            edge_tag = ""
            if "+" in to_page:
                edge_tag = "Required"
            elif "t" in to_page:
                edge_tag = "End"
            elif "x" in to_page:
                edge_tag = "Dead"
            elif "s" in to_page:
                edge_tag = "Start"
            st.session_state.edges.append({
                "from": from_page,
                "to": clean_to,
                "chosen": True,
                "tag": edge_tag,
                "is_secret": "*" in to_page
            })

# --- Export ---
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

# --- Help ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Input Format Help")
st.sidebar.markdown("""
- First number = source node.
- Following numbers = all destination nodes from the source.
- Add * to mark a **secret** path (dashed line).
- Add x to mark a **dead end** (node will be **red**).
- Add t to mark an **End** node (light green).
- Add + to mark a **Required** node (yellow).
- Add s to mark a **Start** node (dark green).
""")

# --- Build Graph ---
net = Network(height="1000px", width="100%", bgcolor="#111", font_color="white", directed=True)
added_edges = set()
all_from = set(edge["from"] for edge in st.session_state.edges if edge["to"] is not None)
all_to = set(edge["to"] for edge in st.session_state.edges if edge["to"] is not None)
unexplored = all_to - all_from
first_node = next((e["from"] for e in st.session_state.edges if e["to"] is not None), None)

node_tags = {}
for edge in st.session_state.edges:
    for node in [edge["from"], edge["to"]]:
        if node is not None:
            if node not in node_tags:
                node_tags[node] = set()
            if edge["tag"]:
                node_tags[node].add(edge["tag"])

for edge in st.session_state.edges:
    edge_key = (edge["from"], edge["to"])
    if edge["to"] is not None and edge_key not in added_edges:
        for node in [edge["from"], edge["to"]]:
            if node not in net.node_ids:
                color = "#97C2FC"
                title = ""
                tags = node_tags.get(node, set())
                if "Dead" in tags:
                    color = "red"
                    title = "Dead End"
                elif "End" in tags:
                    color = "#00cc88"
                    title = "End"
                elif "Required" in tags:
                    color = "yellow"
                    title = "Required"
                elif "Start" in tags or node == first_node:
                    color = "#007733"
                    title = "Start"
                elif node in unexplored:
                    color = "orange"

                net.add_node(node, label=node, color=color, title=title)

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
st.components.v1.html(html_string, height=1000, scrolling=True)

st.markdown("---")
st.markdown("### 📷 Static Image Export")

if st.button("Export Static Graph as PNG"):
    G = nx.DiGraph()
    for edge in st.session_state.edges:
        if edge["to"] is not None:
            G.add_edge(edge["from"], edge["to"])

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(30, 30))
    nx.draw(
        G, pos, with_labels=True,
        node_size=700, node_color="white",
        edge_color="black", font_color="black", font_size=10,
        arrows=True
    )
    plt.axis("off")
    export_path = "static_ff_graph.png"
    plt.savefig(export_path, dpi=300, bbox_inches='tight', facecolor="white")
    st.image(export_path, caption="Static Graph Export (matplotlib)")
    with open(export_path, "rb") as f:
        st.download_button("⬇️ Download Static Image", f.read(), file_name="ff_graph.png", mime="image/png")
