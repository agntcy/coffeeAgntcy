from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing_extensions import TypedDict, Annotated
import operator
import dotenv

dotenv.load_dotenv()

# Step 2: Define state schema for LangGraph
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    prompt: str
    llm_calls: int


# --8<-- [start:HelloWorldAgent]
class HelloWorldAgent:
    """Hello World Agent."""

    def __init__(self):
        # Initialize model
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self._agent = self.build_graph()

    def build_graph(self) -> StateGraph:
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("agent", self.llm_node)
        graph_builder.add_edge(START, "agent")
        graph_builder.add_edge("agent", END)
        return graph_builder.compile() # type: ignore

    # Define the LLM node
    def llm_node(self, state: AgentState):
        user_prompt = state.get("prompt")
        messages = [
            SystemMessage("You are a helpful customer support agent for an e-commerce platform. "
    "Assist customers with their questions about orders, returns, and products."),
            HumanMessage(content=user_prompt),
        ]
        response = self.model.invoke(messages)
        return {
            "messages": [response],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    async def ainvoke(self, input: str) -> str:
        result = self._agent.invoke({"prompt": input, "messages": [], "llm_calls": 0}) # type: ignore
        return result["messages"][-1].content


# Example dataset for testing the HelloWorldAgent
dataset = [
    {
        "inputs": {"query": "Where is my order #12345?"},
        "expectations": {
            "expected_response": "I'd be happy to help you track your order #12345. "
            "Please check your email for a tracking link, or I can look it up for you if you provide your email address."
        },
    },
    {
        "inputs": {"query": "How do I return a defective product?"},
        "expectations": {
            "expected_response": "I'm sorry to hear your product is defective. You can initiate a return "
            "through your account's order history within 30 days of purchase. We'll send you a prepaid shipping label."
        },
    },
    {
        "inputs": {"query": "Do you have this item in blue?"},
        "expectations": {
            "expected_response": "I'd be happy to check product availability for you. "
            "Could you please provide the product name or SKU so I can verify if it's available in blue?"
        },
    },
    # more data...
]
