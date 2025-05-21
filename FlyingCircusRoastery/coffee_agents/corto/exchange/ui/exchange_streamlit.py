import time
import asyncio
import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout
from graph.graph import ExchangeGraph

# Set the page configuration
st.set_page_config(layout="wide")

# Utility function to add line breaks in the Streamlit app
def add_line_breaks(count: int = 1):
  """Adds the specified number of line breaks in the Streamlit app."""
  for _ in range(count):
    st.write("")


# Sidebar setup
def setup_sidebar():
  """Sets up the sidebar with a logo and input field."""
  with st.sidebar:
    st.image("exchange/ui/assets/agntcy_logo.png", width=150)
    add_line_breaks(2)


# Initialize the ExchangeGraph
def initialize_exchange_graph():
  """Initializes the ExchangeGraph instance."""
  return ExchangeGraph()


# Streamed response emulator
def response_generator(response):
  """Yields the response word by word with a delay."""
  for word in response.split():
    yield word + " "
    time.sleep(0.05)


# Asynchronous function to process user input
async def process_prompt(exchange_graph, prompt):
  """Processes the user input asynchronously using ExchangeGraph."""
  result, _ = await exchange_graph.serve(prompt)
  return result


# Handle user input and display responses
def handle_user_input(exchange_graph):
  """Handles user input from the sidebar and displays responses."""
  if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []  # Initialize chat history

  prompt = st.sidebar.chat_input("Enter your message here...")
  if prompt:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Process the prompt and get the bot response
    bot_response = asyncio.run(process_prompt(exchange_graph, prompt))
    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})

  # Display chat history
  for message in st.session_state.chat_history:
    if message["role"] == "user":
      with st.sidebar.chat_message("user", avatar='👤'):
        st.write(message["content"])
    elif message["role"] == "assistant":
      with st.sidebar.chat_message("assistant", avatar='☕'):
        st.write(message["content"])


# Define a common style for blue opaque rectangular nodes
def get_blue_node_style():
  """Returns the style dictionary for blue opaque rectangular nodes."""
  return {
    "backgroundColor": "rgba(74, 144, 226, 0.2)",  # Low opacity background
    "border": "2px solid #4a90e2",  # Fully opaque blue border
    "borderRadius": "10px",  # Rounded corners
    "padding": "0px 25px",  # Padding inside the node
    "color": "#000000",  # Fully opaque black text
    "fontSize": "14px",  # Font size
    "boxShadow": "2px 2px 5px rgba(0, 0, 0, 0.1)",  # Subtle shadow
  }


# Define nodes for the graph
def define_nodes():
  """Defines the nodes for the graph."""
  blue_node_style = get_blue_node_style()
  return [
    StreamlitFlowNode(id='1', pos=(0, 0), data={'content': 'Supervisor'}, node_type='input', source_position='bottom', style=blue_node_style),
    StreamlitFlowNode(id='2', pos=(0, 150), data={'content': 'Sommelier'}, node_type='default', source_position='bottom', target_position='top', style=blue_node_style),
  ]


# Define edges for the graph
def define_edges():
  """Defines the edges for the graph."""
  return [
    StreamlitFlowEdge(
      id='1-2',
      source='1',
      target='2',
      edge_type='default',
      label="SLIM",
      marker_end={"type": "arrowclosed", "color": "#4a90e2"},
      style={"stroke": "#4a90e2", "strokeWidth": 1.5},
    ),
  ]


# Initialize the graph state
def initialize_graph_state():
  """Initializes the graph state in Streamlit session state."""
  if 'flow_state' not in st.session_state:
    nodes = define_nodes()
    edges = define_edges()
    st.session_state.flow_state = StreamlitFlowState(nodes, edges)


# Render the graph
def render_graph():
  """Renders the graph using Streamlit Flow."""
  streamlit_flow(
    key='simple_graph',
    state=st.session_state.flow_state,
    layout=TreeLayout(direction='down'),  # Align along the y-axis
    fit_view=True,
    style={
      "width": "100%",
      "height": "1000px",
      # "background": "linear-gradient(to bottom, #ffffff, #e6f7ff)"  # Gradient background
    },
    hide_watermark=True,
  )


# Main function to run the Streamlit app
def main():
  """Main function to run the Streamlit app."""
  setup_sidebar()
  exchange_graph = initialize_exchange_graph()
  handle_user_input(exchange_graph)
  initialize_graph_state()
  add_line_breaks(10)
  render_graph()


# Run the app
if __name__ == "__main__":
  main()