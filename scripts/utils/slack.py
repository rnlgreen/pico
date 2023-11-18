#Util function to send message to Slack
from secrets import webhook
import urequests # type: ignore # pylint: disable=import-error

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
    resp = urequests.post(URL, data=data, headers=headers)
    print(resp.content)
    return resp
