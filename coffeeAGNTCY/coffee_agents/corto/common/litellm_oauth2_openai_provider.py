# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import aiohttp
import time
import json
import logging
import requests
from typing import Any, Dict, List, Optional

from litellm import CustomLLM
from litellm.utils import ModelResponse

logger = logging.getLogger(__name__)

class RefreshOAuth2OpenAIProvider(CustomLLM):
    """
    LiteLLM custom provider that:
      - gets a OAuth2 client_credentials token
      - sends chat completions to OpenAI-compatible proxy
      - returns a LiteLLM ModelResponse
    """
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        base_url_tmpl: str,
        appkey: Optional[str],
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.base_url_tmpl = base_url_tmpl

        self._cached_token: Optional[str] = None
        self._token_expiry_ts: float = 0.0

        if appkey:
            self.appkey = appkey


    # ---------- LiteLLM required methods ----------

    def completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        **kwargs,
    ) -> ModelResponse:
        """
        Called by litellm.completion() / ChatLiteLLM. Must return a ModelResponse.
        """
        logger.info(f"completion called with model={model}, messages={messages}, kwargs={kwargs}")
        token = self._get_token()

        url = self.base_url_tmpl
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "api-key": token,
        }

        # Build payload. You can pass through temperature, top_p, etc. via kwargs if desired.
        payload = {
            "messages": messages,
        }
        if self.appkey is not None:
            payload["user"] = json.dumps({"appkey": self.appkey})

        for k in kwargs:
            if 'tool_choice' in kwargs and kwargs['tool_choice'] == 'any':
                kwargs['tool_choice'] = 'auto'
            payload[k] = kwargs[k]

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Convert OpenAI-style response to LiteLLM ModelResponse
        mr = ModelResponse()
        mr.model = model
        mr.created = data.get("created")
        mr.id = data.get("id")
        mr.choices = data.get("choices", [])
        mr.usage = data.get("usage", {})
        mr._hidden_params = {}  # optional
        return mr

    async def acompletion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        **kwargs,
    ) -> ModelResponse:
        """
        Called by litellm.acompletion() / ChatLiteLLM. Must return a ModelResponse.
        """
        logger.info(f"acompletion called with model={model}, messages={messages}, kwargs={kwargs}")
        token = self._get_token()

        url = self.base_url_tmpl
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "api-key": token,
        }

        # Build payload
        payload = {"messages": messages}
        if self.appkey is not None:
            payload["user"] = json.dumps({"appkey": self.appkey})

        for k in kwargs:
            if 'tool_choice' in kwargs and kwargs['tool_choice'] == 'any':
                kwargs['tool_choice'] = 'auto'
            payload[k] = kwargs[k]
            
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()

        # Convert OpenAI-style response to LiteLLM ModelResponse
        mr = ModelResponse()
        mr.model = model
        mr.created = data.get("created")
        mr.id = data.get("id")
        mr.choices = data.get("choices", [])
        mr.usage = data.get("usage", {})
        mr._hidden_params = {}
        return mr
            

    def _get_token(self) -> str:
        now = time.time()
        if self._cached_token and now < self._token_expiry_ts:
            return self._cached_token

        # client_credentials with HTTP Basic
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {"grant_type": "client_credentials"}
        r = requests.post(self.token_url, headers=headers, data=payload, auth=auth, timeout=30)
        r.raise_for_status()
        token_data = r.json()
        access_token = token_data["access_token"]
        # Default to 55 min if expires_in not provided
        expires_in = int(token_data.get("expires_in", 3300))
        self._cached_token = access_token
        # Refresh a bit before expiry but never less than 30s
        self._token_expiry_ts = now + max(30, expires_in - 30)
        return access_token

