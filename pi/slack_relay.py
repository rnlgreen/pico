#!/usr/bin/env python3
"""Relay Slack messages from the picos (published over MQTT) to a Slack incoming webhook.

Picos publish JSON to the topic pico/slack:
    {"pico": "pico7", "text": "message", "icon": ":large_blue_diamond:"}

Configuration is via environment variables:
    SLACK_WEBHOOK  (required) Slack incoming webhook URL
    MQTT_HOST      MQTT broker host (default: localhost)
    MQTT_PORT      MQTT broker port (default: 1883)
    MQTT_USER      optional broker username
    MQTT_PASSWORD  optional broker password
    SLACK_TOPIC    topic to subscribe to (default: pico/slack)

Requires: paho-mqtt (v1 or v2) and requests.
"""
import json
import logging
import os
import queue
import sys
import threading
import time

import paho.mqtt.client as mqtt
import requests

WEBHOOK = os.environ.get("SLACK_WEBHOOK")
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
TOPIC = os.environ.get("SLACK_TOPIC", "pico/slack")

MAX_RETRIES = 5
MIN_INTERVAL = 1.1  # Slack webhooks allow roughly one message per second

log = logging.getLogger("slack_relay")
messages = queue.Queue()


def post_to_slack(item):
    """Post one message to Slack, retrying on rate limits and transient errors."""
    payload = {
        "text": item.get("text", ""),
        "username": item.get("pico", "pico"),
        "icon_emoji": item.get("icon", ":large_blue_diamond:"),
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(WEBHOOK, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            if response.status_code == 429:
                delay = float(response.headers.get("Retry-After", 2))
                log.warning("Rate limited by Slack, waiting %.1fs", delay)
                time.sleep(delay)
                continue
            log.error("Slack returned %s: %s", response.status_code, response.text[:200])
        except requests.RequestException as err:
            log.error("Slack post failed (attempt %d): %s", attempt, err)
        time.sleep(2 * attempt)
    log.error("Giving up on message from %s", payload["username"])
    return False


def worker():
    """Send queued messages one at a time so MQTT handling never blocks on Slack."""
    while True:
        item = messages.get()
        post_to_slack(item)
        time.sleep(MIN_INTERVAL)
        messages.task_done()


def on_connect(client, _userdata, _flags, reason_code, *_args):
    """Subscribe on every (re)connect so the subscription survives broker restarts."""
    # paho 2.x passes a ReasonCode object (with is_failure); paho 1.x passes an int (0 = success)
    failed = reason_code.is_failure if hasattr(reason_code, "is_failure") else reason_code != 0
    if failed:
        log.error("MQTT connect failed: %s", reason_code)
        return
    log.info("Connected to MQTT %s:%s, subscribing to %s", MQTT_HOST, MQTT_PORT, TOPIC)
    client.subscribe(TOPIC)


def on_message(_client, _userdata, msg):
    """Queue a message from a pico."""
    try:
        item = json.loads(msg.payload.decode("utf-8"))
        if not isinstance(item, dict):
            raise ValueError("payload is not a JSON object")
    except (ValueError, UnicodeDecodeError):
        # Be lenient: treat a non-JSON payload as plain text
        item = {"pico": "unknown", "text": msg.payload.decode("utf-8", "replace")}
    log.info("Queued message from %s", item.get("pico"))
    messages.put(item)


def make_client():
    """Create an MQTT client compatible with both paho-mqtt 1.x and 2.x."""
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="slack_relay")
    except AttributeError:
        client = mqtt.Client(client_id="slack_relay")
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    return client


def main():
    """Run the relay until interrupted."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not WEBHOOK:
        log.error("SLACK_WEBHOOK environment variable is not set")
        sys.exit(1)
    threading.Thread(target=worker, daemon=True).start()
    client = make_client()
    # connect_async + loop_forever retries automatically if the broker is down at startup
    client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()
