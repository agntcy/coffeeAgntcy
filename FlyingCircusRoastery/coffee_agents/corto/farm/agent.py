from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


# Define the state structure
class State(TypedDict):
    messages: Annotated[list, add_messages]

class FarmAgent:
    def __init__(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("MessageNode", self.message_node)
        graph_builder.add_edge(START, "MessageNode")
        graph_builder.add_edge("MessageNode", END)
        self._agent = graph_builder.compile()

    async def message_node(self, state: State):
        user_input = state['messages'][-1].content
        print(f"Received user input: {user_input}")
        response = "This is a response from the farm agent." # TODO Put farm response here
        return {"messages": [response]}

    async def ainvoke(self, inputs):
        return await self._agent.ainvoke(inputs)