#Util function to send message to Slack
from secrets import webhook
import gc
import json
import micropython # type: ignore # pylint: disable=import-error
import urequests # type: ignore # pylint: disable=import-error
from utils import log
from utils import mqtt
do_slack=True

# Slack messages are normally published to this MQTT topic and posted to Slack by
# pi/slack_relay.py running on the Pi (no TLS needed on the Pico).
# Direct HTTPS to the webhook is only used as a fallback if MQTT isn't available.
SLACK_TOPIC = "pico/slack"

# Memory diagnostics: report free and largest allocatable block around each Slack post
DEBUG_MEM = True

def largest_block():
    '''Probe for the largest bytearray we can currently allocate (to within 256 bytes).'''
    gc.collect()
    low = 0
    high = gc.mem_free() # pylint: disable=no-member
    while high - low > 256:
        mid = (low + high) // 2
        try:
            block = bytearray(mid)
            del block
            low = mid
        except MemoryError:
            high = mid
    return low

def mem_report(tag):
    '''Report heap state via MQTT status, and the full heap map on the serial console.'''
    if not DEBUG_MEM:
        return
    try:
        log.status(f"slack mem {tag}: free={gc.mem_free()} largest={largest_block()}") # pylint: disable=no-member
        micropython.mem_info(1)
    except Exception: # pylint: disable=broad-except
        pass

#Format and send the message to Slack
def send_msg(pico,msg):
    ''' Send a message to a predefined slack channel.'''
    if do_slack:
        # Truncate long messages to prevent large memory allocations
        # Exception tracebacks can be very long
        if len(msg) > 200:
            msg = msg[:200] + "...(truncated)"

        if "exception" in msg:
            icon = ":large_red_square:"
        elif "is up" in msg:
            icon = ":large_green_circle:"
        else:
            icon = ":large_blue_diamond:"

        # Preferred route: hand the message to the Pi relay via MQTT (small plain-TCP publish).
        # Publish directly rather than via mqtt.send_mqtt(), which restarts the Pico on failure.
        if mqtt.client is not False:
            try:
                # Encode to bytes: umqtt sizes str payloads by characters, which truncates non-ASCII text
                mqtt.client.publish(SLACK_TOPIC, json.dumps({"pico": pico, "text": msg, "icon": icon}).encode("utf-8"))
                return True
            except Exception: # pylint: disable=broad-except
                # Fall through to the direct HTTPS route. Don't log via MQTT here, it's what just failed.
                print("Slack: MQTT publish failed, falling back to HTTPS")

        # Fallback route: direct HTTPS. Collect garbage first to avoid ENOMEM.
        gc.collect()
        mem_report("before")

        URL=webhook
        headers = {'content-type': 'application/json'}
        data = json.dumps({"text": msg, "username": pico, "icon_emoji": icon})
        try:
            response = urequests.post(URL, data=data, headers=headers)
            # Always close response to free memory
            response.close()
        except Exception as oops: # pylint: disable=broad-except
            mem_report("FAILED")
            log.status(f"Failed to send message to Slack:\n{msg}", logit=True, handling_exception=True)
            log.log_exception(oops)
            return False
    return True
