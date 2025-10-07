# test/integration/mocks/mock_llm_langchainish.py
from typing import Any, Callable, Dict, List, Optional, AsyncGenerator

# Import necessary types from langchain_core
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage # Import AIMessage here
from langchain_core.outputs import ChatGeneration, LLMResult

ToolSpec = Dict[str, Any]  # {"name": str, "description": str, "args_schema": pydantic.BaseModel, ...}

class MockLangChainLLM(BaseChatModel): # Inherit from BaseChatModel
    """
    A tiny stand-in for a LangChain ChatModel: supports .invoke() and .ainvoke()
    (via BaseChatModel's implementations). Records call history and returns canned
    responses by substring match.
    """
    def __init__(self, response_text: str = "Mock LLM response.", **kwargs: Any):
        super().__init__(**kwargs) # Call parent constructor
        self.response_text = response_text
        self.mock_responses: Dict[str, str] = {}
        self.call_history: List[str] = []

        # tool-call support
        self._bound_tools: Optional[List[str]] = None
        self._strict_tools: bool = False
        self._tool_call_rules: Optional[Callable[[str, List[ToolSpec]], Optional[Dict[str, Any]]]] = None
        # Return shape from _tool_call_rules:
        #   {"name": "get_all_farms_yield_inventory", "args": {}, "id": "call_1"}
        # Return None to produce a normal text answer.

    @property
    def _llm_type(self) -> str:
        return "mock_langchain_chat_model"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    def set_mock_responses(self, mapping: Dict[str, str]):
        self.mock_responses = mapping

    def set_tool_call_rules(
            self,
            fn: Callable[[str, List[ToolSpec]], Optional[Dict[str, Any]]]
    ) -> None:
        """Install your custom 'router' deciding which tool to call."""
        self._tool_call_rules = fn
    
    # Tool binding (mirros the idea of .bind_tools in LangChain)
    def bind_tools(self, tools: List[ToolSpec], strict: bool = True):
        self._bound_tools = tools
        self._strict_tools = strict
        return self

    def _generate(
        self,
        messages: List[BaseMessage],  # BaseChatModel expects a single conversation
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> LLMResult:
        # Find last human text
        user_text = ""
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                user_text = m.content
                break
            user_text = getattr(m, "content", "")

        self.call_history.append(user_text)

        # 1) If caller configured canned substring matches, use those
        response_content = next(
            (reply for needle, reply in self.mock_responses.items()
             if needle.lower() in (user_text or "").lower()),
            f"Mock LLM default for: {user_text}" if user_text else self.response_text
        )

        # 2) If tools are bound, optionally emit a tool call
        tool_calls_payload = None
        if self._bound_tools:
            tool_call = None
            if self._tool_call_rules:
                tool_call = self._tool_call_rules(user_text, self._bound_tools)
            else:
                # Very small built-in heuristic useful for your inventory node
                text = (user_text or "").lower()

                def find_tool(name: str):
                    if not self._bound_tools: return None
                    for t in self._bound_tools:
                        # tools can be passed as callables or dicts—accept both
                        tname = getattr(t, "name", None) or t.get("name") if isinstance(t, dict) else None
                        if tname == name:
                            return t
                    return None

                if "all farms" in text or "total" in text or "how much coffee we have" in text:
                    if find_tool("get_all_farms_yield_inventory"):
                        tool_call = {"name": "get_all_farms_yield_inventory", "args": {}, "id": "call_all_1"}
                elif "farm" in text:
                    # Try to extract a farm name (“Kona”, “Yirgacheffe”, etc.)
                    m = re.search(r"(?:at|for|on|in)\s+the?\s*([A-Za-z0-9_\- ]+?)\s+farm", text) \
                        or re.search(r"\b([A-Za-z0-9_\- ]+)\s+farm\b", text)
                    farm_name = (m.group(1).strip() if m else "Kona")
                    if find_tool("get_farm_yield_inventory"):
                        tool_call = {"name": "get_farm_yield_inventory", "args": {"farm_name": farm_name}, "id": "call_farm_1"}

            if tool_call:
                # IMPORTANT: LangChain's AIMessage supports a top-level `tool_calls` field.
                tool_calls_payload = [tool_call]
                # Be nice and narrate what we're “doing”
                if not response_content:
                    response_content = f"Calling tool {tool_call['name']} with {json.dumps(tool_call['args'])}."

        # Build message & generation
        ai_msg = AIMessage(content=response_content, tool_calls=tool_calls_payload)
        generations = [[ChatGeneration(message=ai_msg)]]
        return LLMResult(generations=generations)

    # ---- Optional streaming impl (returns a single full chunk) ----
    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[ChatGeneration, None]:
        gen = self._generate(messages=messages, stop=stop, run_manager=run_manager, **kwargs).generations[0][0]
        yield gen
