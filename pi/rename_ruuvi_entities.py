#!/usr/bin/env python3
"""Rename the RuuviTag entities in Home Assistant to e.g. sensor.ruuvitag_kitchen_temperature.

Uses the HA WebSocket API (the same one the UI uses). Dry run by default; add --apply to rename.

Usage:
    export HA_URL=ws://homeassistant.local:8123/api/websocket
    export HA_TOKEN=<long-lived access token>   # HA profile page -> Security -> Long-lived access tokens
    python3 rename_ruuvi_entities.py            # show what would change
    python3 rename_ruuvi_entities.py --apply    # do it

Requires: websocket-client (pip install websocket-client)
"""
import json
import os
import sys

import websocket

HA_URL = "ws://condor:8123/api/websocket"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhNWYyMjNlNTRiMjY0ZDcxYmRjY2U0MTYzYzgxNDM1YyIsImlhdCI6MTc4ODUyMzAxNSwiZXhwIjoyMTAzODgzMDE1fQ.e_GuNYLxw-Sq8z-ImBsG9--Atu-1oh0YRP5TwEGkz8M"

# Keep in step with mytags in scripts/utils/ruuvi.py
MYTAGS = {
    "f34584d173cb": "lounge",
    "dc7eb48031b4": "kitchen",
    "fab5c40c4095": "orangery",
    "f9a8d010746c": "utility",
}

_next_id = 0


def call(ws, message):
    """Send one command and return its result message."""
    global _next_id # pylint: disable=global-statement
    _next_id += 1
    message["id"] = _next_id
    ws.send(json.dumps(message))
    while True:
        reply = json.loads(ws.recv())
        if reply.get("id") == _next_id:
            return reply


def main():
    """Work out the new entity IDs and optionally apply them."""
    apply = "--apply" in sys.argv
    if not HA_TOKEN:
        sys.exit("HA_TOKEN environment variable is not set")

    ws = websocket.create_connection(HA_URL, timeout=30)
    json.loads(ws.recv())  # auth_required
    ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
    if json.loads(ws.recv()).get("type") != "auth_ok":
        sys.exit("Authentication failed")

    entities = call(ws, {"type": "config/entity_registry/list"})["result"]
    taken = {e["entity_id"] for e in entities}
    changes = 0

    for entity in entities:
        unique_id = entity.get("unique_id") or ""
        if entity.get("platform") != "mqtt" or not unique_id.startswith("ruuvi_"):
            continue
        parts = unique_id.split("_", 2)  # ruuvi, <mac>, <key>
        if len(parts) != 3 or parts[1] not in MYTAGS:
            print(f"SKIP   {entity['entity_id']} (unknown tag in {unique_id})")
            continue
        new_id = f"sensor.ruuvitag_{MYTAGS[parts[1]]}_{parts[2]}"
        old_id = entity["entity_id"]
        if old_id == new_id:
            continue
        if new_id in taken:
            print(f"CLASH  {old_id} -> {new_id} (target already exists, skipped)")
            continue
        changes += 1
        if not apply:
            print(f"WOULD  {old_id} -> {new_id}")
            continue
        result = call(ws, {"type": "config/entity_registry/update",
                           "entity_id": old_id, "new_entity_id": new_id})
        if result.get("success"):
            taken.add(new_id)
            print(f"OK     {old_id} -> {new_id}")
        else:
            print(f"FAILED {old_id} -> {new_id}: {result.get('error')}")

    ws.close()
    if not changes:
        print("Nothing to rename")
    elif not apply:
        print("Dry run only; re-run with --apply to rename")


if __name__ == "__main__":
    main()
