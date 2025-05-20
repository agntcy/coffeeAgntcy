import streamlit as st
import asyncio
from graph.graph import ExchangeGraph
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle

node_styles = [
  NodeStyle(label='EXCHANGE', color='#005073', caption='name'),
  NodeStyle(label='FARM', color='#007CBA', caption='name')
]

edge_styles = [
  EdgeStyle("A2A over AGP", caption='label', directed=True, labeled=None,color="#00A859")
]

layout = {"name": "cose", "animate": "end", "nodeDimensionsIncludeLabels": False}

# Initialize elements with two nodes and no edges
if "elements" not in st.session_state:
  st.session_state.elements = {
    "nodes": [
      {"data": {"id": "exchange", "label": "EXCHANGE", "name": "Exchange"}},
      {"data": {"id": "farm", "label": "FARM", "name": "Farm"}}
    ],
    "edges": []
  }

# Function to add an edge after prompt submission
def add_edge():
  st.session_state.elements["edges"].append({
    "data": {"id": "a2a_agp", "label": 'A2A over AGP', "source": "exchange", "target": "farm"}
  })

def update_node_with_value(id, field_name, value):
  # Update the node with the user input
  for node in st.session_state.elements["nodes"]:
    if node["data"]["id"] == id:
      node["data"][field_name] = value
      break

# Initialize the ExchangeGraph
exchange_graph = ExchangeGraph()

async def process_prompt(prompt):
  result, _ = await exchange_graph.serve(prompt)
  return result

# Sidebar for chat input
st.sidebar.title("Chat Input")
prompt = st.sidebar.text_input("Enter your prompt:")
if st.sidebar.button("Submit"):
  if prompt:
    # Simulate processing the input
    result = asyncio.run(process_prompt(prompt))
    add_edge()
    st.sidebar.success(result)
    update_node_with_value("exchange","prompt", prompt)
    update_node_with_value("farm","response", result)
  else:
    st.sidebar.warning("Please enter some input.")

if st.sidebar.button("Clear"):
  st.session_state.elements["edges"] = []
  update_node_with_value("exchange","prompt", "")
  update_node_with_value("farm","response", "")

# Main area for graph visualization
st.title("Coffee Exchange Graph")
st_link_analysis(st.session_state.elements, layout, node_styles, edge_styles, key="xyz", height=800)