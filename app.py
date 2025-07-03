import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="FF Graph Mapper", layout="wide")
st.title("🗜︌ Fighting Fantasy Graph Builder")

# Storage for user inputs
if "edges" not in st.session_state:
    st.session_state.edges = []
if "required_nodes" not in st.session_state:
    st.session_state.required_nodes = set()

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

        for to_page in to_pages:
            st.session_state.edges.append({
                "from": from_page,
                "to": to_page.replace("+", ""),
                "chosen": False,
                "tag": "",
                "is_secret": False
            })
            if "+" in to_page:
                st.session_state.required_nodes.add(to_page.replace("+", ""))

        chosen_clean = chosen.replace("*", "").replace("x", "").replace("t", "").replace("+", "")
        if "+" in chosen:
            st.session_state.required_nodes.add(chosen_clean)

        st.session_state.edges.append({
            "from": from_page,
            "to": chosen_clean,
            "chosen": True,
            "tag": "End" if chosen.endswith("t") else tag_input.strip(),
            "is_secret": "*" in chosen
        })
    else:
        st.warning("Please enter at least a from-page and a chosen path.")

# --- Paste in CSV-style data ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Paste Data from CSV")
pasted_data = st.sidebar.text_area("Paste rows like: 123,4,5+,6,200*,Got key")
if st.sidebar.button("Add Pasted Paths"):
    for line in pasted_data.splitlines():
        if not line.strip():
            continue

        parts = [p.strip() for p in line.split(",") if p.strip()]

        if len(parts) == 1 and (parts[0].endswith("x") or parts[0].endswith("t")):
            node = parts[0].replace("x", "").replace("t", "").replace("+", "")
            if "+" in parts[0]:
                st.session_state.required_nodes.add(node)
            st.session_state.edges.append({
                "from": node,
                "to": node,
                "chosen": True,
                "tag": "End" if parts[0].endswith("t") else "",
                "is_secret": False
            })
            continue

        if len(parts) >= 2:
            from_page = parts[0]
            tag = parts[-1] if not parts[-1][-1].isdigit() and parts[-1][-1] not in ["*", "x", "t", "+"] else ""
            dest_parts = parts[1:-1] if tag else parts[1:]

            chosen = dest_parts[-1]
            to_pages = dest_parts[:-1]

            for to_page in to_pages:
                clean_to = to_page.replace("+", "")
                st.session_state.edges.append({
                    "from": from_page,
                    "to": clean_to,
                    "chosen": False,
                    "tag": "",
                    "is_secret": False
                })
                if "+" in to_page:
                    st.session_state.required_nodes.add(clean_to)

            chosen_clean = chosen.replace("*", "").replace("x", "").replace("t", "").replace("+", "")
            if "+" in chosen:
                st.session_state.required_nodes.add(chosen_clean)

            st.session_state.edges.append({
                "from": from_page,
                "to": chosen_clean,
                "chosen": True,
                "tag": "End" if chosen.endswith("t") else tag,
                "is_secret": "*" in chosen
            })
        else:
            st.warning(f"Invalid line skipped: {line}")

# --- Shortest Path ---
shortest_path_display = ""
highlight_path_edges = set()
if st.session_state.edges:
    G = nx.DiGraph()
    for edge in st.session_state.edges:
        G.add_edge(edge["from"], edge["to"])

    start_node = st.session_state.edges[0]["from"]
    end_nodes = [e["to"] for e in st.session_state.edges if e["tag"].lower() == "end"]

    if end_nodes:
        try:
            all_paths = list(nx.all_simple_paths(G, source=start_node, target=end_nodes[0]))
            required = st.session_state.required_nodes
            valid_paths = [p for p in all_paths if required.issubset(set(p))]
            if valid_paths:
                shortest = min(valid_paths, key=len)
                shortest_path_display = " → ".join(shortest)
                highlight_path_edges = set(zip(shortest, shortest[1:]))
                st.markdown(f"**Shortest Path (including required):** {shortest_path_display}")
            else:
                st.markdown("**Shortest Path:** No valid path includes all required nodes.")
        except nx.NetworkXNoPath:
            st.markdown("**Shortest Path:** No path found between Start and End.")
    else:
        st.markdown("**Shortest Path:** End node not defined.")

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
- Add `*` to the last number to mark it as a **secret or hidden exit**.
- Add `x` to the last number to mark it as a **dead end** — the node will turn **red**.
- Add `t` to the last number to mark it as a **final target** — the node will turn **green** and say **End**.
- Add `+` to any number to mark it as a **required node** — shortest path will include it.
- You can optionally add a short **text tag** — this appears as a **tooltip** on the destination node.  
  Dashed lines indicate **secret paths**.
- Arrows show directions of travel
- Orange Nodes have not been explored further yet
- Green Node is the **first page entered**, and End is marked **green** too.
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
        edge_highlight = edge_key in highlight_path_edges

        if edge["from"] not in net.node_ids:
            if edge["from"] == first_node:
                node_color = "green"
                node_title = "Start"
            elif edge["from"] in st.session_state.required_nodes:
                node_color = "yellow"
                node_title = "Required"
            elif edge["from"] in unexplored:
                node_color = "orange"
                node_title = ""
            else:
                node_color = "#97C2FC"
                node_title = ""
            net.add_node(edge["from"], label=edge["from"], color=node_color, title=node_title)

        if edge["to"] not in net.node_ids:
            if edge["to"] in death_nodes:
                node_color = "red"
                node_title = "Dead End"
            elif edge["to"] in st.session_state.required_nodes:
                node_color = "yellow"
                node_title = "Required"
            elif edge["to"] in unexplored:
                node_color = "orange"
                node_title = edge["tag"]
            elif edge["tag"].lower() == "end":
                node_color = "green"
                node_title = "End"
            else:
                node_color = "#97C2FC"
                node_title = edge["tag"]
            net.add_node(edge["to"], label=edge["to"], title=node_title if node_title else "", color=node_color)

        net.add_edge(
            edge["from"],
            edge["to"],
            color="lime" if edge_highlight else "gray",
            width=3 if edge_highlight else 2,
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
