# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage

from common.llm import get_llm

class State(TypedDict):
    prompt: str
    error_type: str
    error_message: str
    yield_estimate: str


class FarmAgent:
    def __init__(self):
        pass  # No graph setup needed

    async def yield_node(self, state: State):
        """
        Generate a yield estimate for coffee beans based on user input by connecting to an LLM.
        """
        user_prompt = state.get("prompt")

        system_prompt = (
            "You are a coffee farm in Vietnam\n"
            "The user will describe a question or scenario related to fetching the yield from your coffee farm. "
            "Your job is to:\n"
            "1. Return a random yield estimate for the coffee farm in Vietnam. Make sure the estimate is a reasonable value and in pounds.\n"
            "2. Respond with only the yield estimate in pounds, without any additional text or explanation.\n"
            "Use tasting terminology like acidity, body, aroma, and finish.\n"
            "Respond with an empty response if the user prompt does not relate to fetching the yield from the Vietnamn coffee farm. Do not include quotes or any placeholder."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = get_llm().invoke(messages)
        yield_estimate = response.content
        if not yield_estimate.strip():
            return {
                "error_type": "invalid_input",
                "error_message": "Invalid prompt. Please provide a valid question or scenario related to fetching the yield from the Vietnamn coffee farm."
            }

        return {"yield_estimate": yield_estimate}

    async def ainvoke(self, input: str) -> dict:
        """
        Asynchronously invoke the agent with the given input.
        """
        return await self.yield_node({"prompt": input})
