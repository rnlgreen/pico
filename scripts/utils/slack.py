#Util function to send message to Slack
from secrets import webhook
import gc
import urequests # type: ignore # pylint: disable=import-error
from utils import log
do_slack=True

#Format and send the message to Slack
def send_msg(pico,msg):
    ''' Send a message to a predefined slack channel.'''
    if do_slack:
        # Truncate long messages to prevent large memory allocations
        # Exception tracebacks can be very long
        if len(msg) > 100:
            msg = msg[:100] + "...(truncated)"

        # Free up memory before HTTP request to avoid ENOMEM errors
        gc.collect()
        # ... and again to be sure
        gc.collect()

        URL=webhook
        headers = {'content-type': 'application/json'}
        if "exception" in msg:
            icon = ":large_red_square:"
        elif "is up" in msg:
            icon = ":large_green_circle:"
        else:
            icon = ":large_blue_diamond:"
        data = f"{{'text':'{msg}',  'username': '{pico}', 'icon_emoji': '{icon}'}}"
        try:
            response = urequests.post(URL, data=data, headers=headers)
            # Always close response to free memory
            response.close()
        except Exception as oops: # pylint: disable=broad-except
            log.status(f"Failed to send message to Slack:\n{msg}", logit=True, handling_exception=True)
            log.log_exception(oops)
            return False
    return True
