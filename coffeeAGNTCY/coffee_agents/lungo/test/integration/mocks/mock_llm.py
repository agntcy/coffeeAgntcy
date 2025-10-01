# test/integration/mocks/mock_llm_langchainish.py
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class MockAIMessage:
    content: str
    response_metadata: Dict[str, Any] = field(default_factory=dict)

class MockLangChainLLM:
    """
    A tiny stand-in for a LangChain ChatModel: supports .invoke() and .ainvoke().
    Records call history and returns canned responses by substring match.
    """
    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.model_name = model_name
        self.mock_responses: Dict[str, str] = {}
        self.call_history: List[str] = []

    def set_mock_responses(self, mapping: Dict[str, str]):
        self.mock_responses = mapping

    def _match(self, messages: Any) -> str:
        # Support both strings and LC-style message lists
        if isinstance(messages, str):
            user_text = messages
        elif isinstance(messages, list) and messages:
            # try to find last human/user content
            user_text = ""
            for m in reversed(messages):
                # LC HumanMessage/AIMessage have .content; dicts may have {"role","content"}
                user_text = getattr(m, "content", m.get("content") if isinstance(m, dict) else "")
                if (getattr(m, "type", None) == "human") or (isinstance(m, dict) and m.get("role") == "user"):
                    break
        else:
            user_text = ""

        self.call_history.append(user_text)

        for needle, reply in self.mock_responses.items():
            if needle.lower() in (user_text or "").lower():
                return reply
        return f"Mock LLM default for: {user_text}"

    # LangChain-style sync
    def invoke(self, messages: Any, **kwargs) -> MockAIMessage:
        return MockAIMessage(content=self._match(messages))

    # Async variant if your code uses it
    async def ainvoke(self, messages: Any, **kwargs) -> MockAIMessage:
        await asyncio.sleep(0)  # yield to loop
        return self.invoke(messages, **kwargs)
