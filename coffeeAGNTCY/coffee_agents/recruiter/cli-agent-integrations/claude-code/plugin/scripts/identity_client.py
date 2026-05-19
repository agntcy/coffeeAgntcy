#!/usr/bin/env python3
# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
"""
Stdlib-only client for the AGNTCY identity service.

Mirrors the consumer-side methods of
coffee_agents/lungo/services/identity_service_impl.py — minus create_badge.

Subcommands:
  apps                          List all registered apps.
  badge    --app-id <id>        Fetch the badge for an app.
  verify   --app-id <id>        Fetch the badge and POST it to /badges/verify.
  policies [--app-id <id>]      List policies (optionally filter to those that
                                target a specific app via rules[].tasks[].appId
                                or assignedTo containing the app id).

Each subcommand prints JSON to stdout. On failure, exit 1 and print
{"error": "..."} to stderr.

Environment:
  IDENTITY_SERVICE_BASE_URL   Required. e.g. http://0.0.0.0:4000
  IDENTITY_SERVICE_API_KEY    Required. Sent as the x-id-api-key header.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def _fail(msg: str, code: int = 1) -> None:
    sys.stderr.write(json.dumps({"error": msg}) + "\n")
    sys.exit(code)


def _config() -> tuple[str, str]:
    # Accept either IDENTITY_API_* (Outshift / hosted naming) or
    # IDENTITY_SERVICE_* (lungo / local naming).
    base = os.environ.get("IDENTITY_API_SERVER_URL") or os.environ.get("IDENTITY_SERVICE_BASE_URL")
    key = os.environ.get("IDENTITY_API_KEY") or os.environ.get("IDENTITY_SERVICE_API_KEY")
    if not base:
        _fail("IDENTITY_API_SERVER_URL (or IDENTITY_SERVICE_BASE_URL) is not set")
    if not key:
        _fail("IDENTITY_API_KEY (or IDENTITY_SERVICE_API_KEY) is not set")
    return base.rstrip("/"), key  # type: ignore[return-value]


def _request(method: str, url: str, api_key: str, body: Any = None, timeout: float = 15.0) -> Any:
    data = None
    headers = {"x-id-api-key": api_key, "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        _fail(f"HTTP {e.code} {method} {url}: {detail}")
    except urllib.error.URLError as e:
        _fail(f"Connection error {method} {url}: {e.reason}")
    except json.JSONDecodeError as e:
        _fail(f"Invalid JSON from {url}: {e}")


# --- API calls ---------------------------------------------------------------


def get_all_apps(base: str, key: str) -> Any:
    return _request("GET", f"{base}/v1alpha1/apps", key)


def get_badge_for_app(base: str, key: str, app_id: str) -> Any:
    return _request("GET", f"{base}/v1alpha1/apps/{app_id}/badge", key)


def verify_badge(base: str, key: str, badge: dict) -> Any:
    try:
        proof_value = badge["verifiableCredential"]["proof"]["proofValue"]
    except (KeyError, TypeError):
        _fail("Badge missing verifiableCredential.proof.proofValue")
    return _request("POST", f"{base}/v1alpha1/badges/verify", key, body={"badge": proof_value})


def list_policies(base: str, key: str) -> Any:
    return _request("GET", f"{base}/v1alpha1/policies", key)


# --- Filtering helpers -------------------------------------------------------


def _policy_targets_app(policy: dict, app_id: str) -> bool:
    assigned = policy.get("assignedTo")
    if isinstance(assigned, str) and assigned == app_id:
        return True
    if isinstance(assigned, list) and app_id in assigned:
        return True
    for rule in policy.get("rules") or []:
        for task in rule.get("tasks") or []:
            if task.get("appId") == app_id:
                return True
    return False


# --- CLI ---------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AGNTCY identity service client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("apps", help="List all apps")

    p_badge = sub.add_parser("badge", help="Fetch the badge for an app")
    p_badge.add_argument("--app-id", required=True)

    p_verify = sub.add_parser("verify", help="Fetch + verify badge for an app")
    p_verify.add_argument("--app-id", required=True)

    p_pol = sub.add_parser("policies", help="List policies (optionally filtered by app)")
    p_pol.add_argument("--app-id", default=None)

    args = parser.parse_args(argv)
    base, key = _config()

    if args.cmd == "apps":
        out = get_all_apps(base, key)

    elif args.cmd == "badge":
        out = get_badge_for_app(base, key, args.app_id)

    elif args.cmd == "verify":
        badge = get_badge_for_app(base, key, args.app_id)
        result = verify_badge(base, key, badge)
        out = {"app_id": args.app_id, "badge": badge, "verification": result}

    elif args.cmd == "policies":
        data = list_policies(base, key)
        policies = data.get("policies", []) if isinstance(data, dict) else []
        if args.app_id:
            policies = [p for p in policies if _policy_targets_app(p, args.app_id)]
        out = {"policies": policies}

    else:
        _fail(f"Unknown command: {args.cmd}")

    sys.stdout.write(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
