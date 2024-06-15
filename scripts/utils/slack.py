#Util function to send message to Slack
from secrets import webhook
import urequests # type: ignore # pylint: disable=import-error
from utils import log

#Format and send the message to Slack
def send_msg(pico,msg):
    ''' Send a message to a predefined slack channel.'''
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
        resp = urequests.post(URL, data=data, headers=headers)
    except Exception as oops: # pylint: disable=broad-except
        log.status("Failed to send message to Slack", logit=True, handling_exception=True)
        log.log_exception(oops)
    #print(resp.content)
    return resp
