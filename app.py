import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd

st.set_page_config(page_title="FF Graph Mapper", layout="wide")
st.title("🗘️ Fighting Fantasy Graph Builder")

# --- Session State Storage ---
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

# --- Sidebar: Paste CSV Rows ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🖋️ Paste CSV Rows")
pasted_rows = st.sidebar.text_area("Paste rows from graph_data.csv (no header)")
if st.sidebar.button("Import Pasted Rows") and pasted_rows.strip():
    for line in pasted_rows.strip().splitlines():
        fields = [x.strip() for x in line.split(",")]
        if len(fields) >= 5:
            st.session_state.edges.append({
                "from": fields[0],
                "to": fields[1],
                "chosen": fields[2].lower() == "true",
                "tag": fields[3],
                "is_secret": fields[4].lower() == "true"
            })
        else:
            st.warning(f"Skipped malformed line: {line}")

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

# --- Input Format Help ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Input Format Help")
st.sidebar.markdown("""
- Use `Add Path` for new journeys.
- Paste rows like: `1,2,False,,False`
- `from`, `to`, `chosen`, `tag`, `is_secret`
- Green = chosen path, dashed = secret path
""")

# --- Build Graph ---
net = Network(height="700px", width="100%", bgcolor="#111", font_color="white", directed=True)
added_edges = set()
from_nodes = {edge["from"] for edge in st.session_state.edges}
to_nodes = {edge["to"] for edge in st.session_state.edges}
unexplored = to_nodes - from_nodes

for edge in st.session_state.edges:
    edge_key = (edge["from"], edge["to"])
    if edge_key not in added_edges:
        for node in [edge["from"], edge["to"]]:
            if node not in net.node_ids:
                color = "orange" if node in unexplored else None
                net.add_node(node, label=node, title=node, color=color)

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
