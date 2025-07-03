import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="FF Graph Mapper", layout="wide")
st.title("🕜ﾜ Fighting Fantasy Graph Builder")

# ✅ Storage for user inputs must be initialized FIRST
if "edges" not in st.session_state:
    st.session_state.edges = []

# Find shortest path from Start to End if both exist
shortest_path_display = ""
if st.session_state.edges:
    G = nx.DiGraph()
    for edge in st.session_state.edges:
        G.add_edge(edge["from"], edge["to"])

    start_node = st.session_state.edges[0]["from"]
    end_nodes = [e["to"] for e in st.session_state.edges if e["tag"].lower() == "end"]

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
        from_page = from_page_raw.replace("+", "")
        to_and_chosen = parts[1:]

        if len(to_and_chosen) == 1:
            chosen = to_and_chosen[0]
            to_pages = []
        else:
            chosen = to_and_chosen[-1]
            to_pages = to_and_chosen[:-1]

        is_required = chosen.endswith("+") or from_page_raw.endswith("+")
        chosen_clean = chosen.replace("*", "").replace("x", "").replace("t", "").replace("+", "")

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
            "to": chosen_clean,
            "chosen": True,
            "tag": "End" if chosen.endswith("t") else ("Required" if is_required else tag_input.strip()),
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

        if len(parts) == 1 and (parts[0].endswith("x") or parts[0].endswith("t") or parts[0].endswith("+")):
            node = parts[0].replace("x", "").replace("t", "").replace("+", "")
            tag = "End" if parts[0].endswith("t") else ("Required" if parts[0].endswith("+") else "")
            st.session_state.edges.append({
                "from": node,
                "to": node,
                "chosen": True,
                "tag": tag,
                "is_secret": False
            })
            continue

        if len(parts) >= 2:
            from_page_raw = parts[0]
            from_page = from_page_raw.replace("+", "")
            tag = parts[-1] if not parts[-1].isdigit() and not any(parts[-1].endswith(suffix) for suffix in ["*", "x", "t", "+"]) else ""
            dest_parts = parts[1:-1] if tag else parts[1:]

            chosen = dest_parts[-1] if dest_parts else ""
            is_required = chosen.endswith("+") or from_page_raw.endswith("+")
            chosen_clean = chosen.replace("*", "").replace("x", "").replace("t", "").replace("+", "")
            to_pages = dest_parts[:-1] if dest_parts else []

            for to_page in to_pages:
                st.session_state.edges.append({
                    "from": from_page,
                    "to": to_page,
                    "chosen": False,
                    "tag": "",
                    "is_secret": False
                })

            if chosen_clean:
                st.session_state.edges.append({
                    "from": from_page,
                    "to": chosen_clean,
                    "chosen": True,
                    "tag": "End" if chosen.endswith("t") else ("Required" if is_required else tag),
                    "is_secret": chosen.endswith("*")
                })
        else:
            st.warning(f"Invalid line skipped: {line}")

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
- Enter a **sequence of page numbers** separated by commas.
- The **first number** is the current page you're on.
- The **last number** is the **chosen destination page**.
- All numbers **in between** are unchosen options from that page.
- Add * to the last number to mark it as a **secret or hidden exit**.
- Add x to the last number to mark it as a **dead end** — the node will turn **red**.
- Add t to the last number to mark it as a **final target** — the node will turn **light green** and say **End**.
- Add + to the last number to mark it as a **required location** — the node will turn **yellow**.
- You can optionally add a short **text tag** — this appears as a **tooltip** on the destination node.
- Arrows show directions of travel
- Orange Nodes have not been explored further yet
- Green Node is the **first page entered**, and End is marked **light green** too.
""")

# --- Build Graph ---
net = Network(height="1000px", width="100%", bgcolor="#111", font_color="white", directed=True)
added_edges = set()
all_from = set(edge["from"] for edge in st.session_state.edges)
all_to = set(edge["to"] for edge in st.session_state.edges)
unexplored = all_to - all_from
death_nodes = {edge["to"] for edge in st.session_state.edges if edge["from"] == edge["to"]}
first_node = st.session_state.edges[0]["from"] if st.session_state.edges else None

for edge in st.session_state.edges:
    if edge["from"] == edge["to"]:
        continue

    edge_key = (edge["from"], edge["to"])
    if edge_key not in added_edges:
        if edge["from"] not in net.node_ids:
            if edge["from"] == first_node:
                node_color = "#007733"
                node_title = "Start"
            elif edge["from"] in unexplored:
                node_color = "orange"
                node_title = ""
            else:
                node_color = "#97C2FC"
                node_title = ""
            net.add_node(edge["from"], label=edge["from"], color=node_color, title=node_title)

        if edge["to"] in death_nodes:
            node_color = "red"
            node_title = "Dead End"
        elif edge["tag"].lower() == "end":
            node_color = "#00cc88"
            node_title = "End"
        elif edge["tag"].lower() == "required":
            node_color = "yellow"
            node_title = "Required"
        elif edge["to"] in unexplored:
            node_color = "orange"
            node_title = edge["tag"]
        else:
            node_color = "#97C2FC"
            node_title = edge["tag"]

        if edge["to"] not in net.node_ids:
            net.add_node(edge["to"], label=edge["to"], title=node_title if node_title else "", color=node_color)

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
