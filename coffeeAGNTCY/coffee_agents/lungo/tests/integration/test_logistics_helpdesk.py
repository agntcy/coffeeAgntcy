# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import time
import json
import logging
import pytest
import httpx

logger = logging.getLogger(__name__)

TRANSPORT_MATRIX = [
  pytest.param(
    {
      "DEFAULT_MESSAGE_TRANSPORT": "SLIM",
      "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357",
    },
    id="SLIM",
  )
]

def collect_sse_for_seconds(
        base_url: str = "http://127.0.0.1:9094",
        seconds: float = 3.0,
        endpoint: str = "/agent/chat-logs",
) -> list[dict]:
  """
    Use real httpx.Client so streaming yields incremental chunks (TestClient buffers).
  """
  deadline = time.monotonic() + seconds
  events: list[dict] = []
  timeout = httpx.Timeout(connect=5.0, read=0.5, write=5.0, pool=5.0)
  with httpx.Client(base_url=base_url, timeout=timeout) as client:
    try:
      with client.stream(
              "GET", endpoint, headers={"Accept": "text/event-stream"}
      ) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_text():
          if time.monotonic() >= deadline:
            break
          if not chunk:
            continue
          for raw_line in chunk.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(":"):
              continue
            if line.startswith("data:"):
              line = line[5:].strip()
            if line == "[DONE]":
              return events
            try:
              events.append(json.loads(line))
            except json.JSONDecodeError:
              pass
          if time.monotonic() >= deadline:
            break
    except httpx.ReadTimeout:
      pass
  return events

def assert_states_present(
        events: list[dict],
        required: set[str] | None = None,
) -> None:
  assert events, "No events captured"
  order_ids = {e.get("order_id") for e in events}
  assert len(order_ids) == 1, f"Multiple order_ids found: {order_ids}"
  states = {e.get("state") for e in events if e.get("state")}
  if required is None:
    required = {
      "RECEIVED_ORDER",
      "HANDOVER_TO_SHIPPER",
      "CUSTOMS_CLEARANCE",
      "PAYMENT_COMPLETE",
    }
  missing = required - states
  assert not missing, f"Missing states: {missing}. Got: {states}"

@pytest.mark.parametrize("transport_config", TRANSPORT_MATRIX, indirect=True)
class TestHelpdeskFlows:
  @pytest.mark.agents(["logistics-farm", "accountant", "shipper", "helpdesk"])
  @pytest.mark.usefixtures("agents_up")
  def test_helpdesk_health(
          self,
          helpdesk_client,
          logistics_supervisor_client,
          transport_config,
  ):
    logger.info(
      f"--- Test: test_helpdesk_health with transport {transport_config} ---"
    )

    order_resp = logistics_supervisor_client.post(
      "/agent/prompt",
      json={
        "prompt": (
          "I want to order coffee $3.50 per pound for 500 lbs of coffee "
          "from the Tatooine farm"
        )
      },
    )
    assert order_resp.status_code == 200
    order_data = order_resp.json()
    assert "response" in order_data
    assert "successfully delivered" in order_data["response"].lower()

    # test helpdesk health endpoint
    health_resp = helpdesk_client.get("/v1/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data.get("status") == "alive", "Helpdesk health check failed"

    # test chat-logs SSE endpoint
    logs = collect_sse_for_seconds()
    logger.info(f"Collected events from helpdesk:\n{logs}")
    assert_states_present(logs)