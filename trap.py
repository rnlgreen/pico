#Trigger script to record and report the status of the mouse trap 
#Uses the tilt switches on GPIO 15 (pin 10) and GPIO 3 (pin 5)
#Switches should be attached to the GPIO pin and to ground
#Allows for some flutter on the horizontal

from machine import Pin, RTC as rtc
from time import sleep, time
import utils.myid as myid
import urequests as requests

BEAM_PIN = 16
slack_url = "https://hooks.slack.com/services/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"

ir_last_state = "unbroken"
ir_last_sent = 0

pico = myid.get_id()

#Return formatted time string
def strftime():
    timestamp=rtc.datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

#Send alert via MQTT
def send_alert(message):
    topic = 'pico/'+pico+'/status'
    message = pico + ' is Alive!'
    payload = {
       "channel":"#home-security",
        "text":message
    }
    r = requests.post(slack_url, json=payload)

#Callback function for when the IR Beam state changes
def break_beam_callback(channel):
    global ir_last_state, ir_last_sent
    dt = strftime()
    if beam.value == 1:
        if ir_last_state == "broken":
            print("beam unbroken")
            ir_last_state = "unbroken"
        else:
            print("beam still unbroken (!?)")
    else:
        if ir_last_state == "unbroken":
            print("beam broken")
            ir_last_state = "broken"
            if time() - ir_last_sent > 5:
                ir_last_sent = time()
                sprung = False
                #Check trap status and only send alerts if the traps are both clear
                for trap in (traps):
                    if traps[trap]["sprung"]:
                        sprung =True
                if not sprung:
                    #send_alert(":mouse: infrared beam has been broken!")
                    print("Slack alert (would have been) sent")
        else:
            print("{}: beam still broken (!?)".format(dt),flush=True)

def trap():
    do_beam = True

    if do_beam:
        beam = Pin(BEAM_PIN, Pin.IN, Pin.PULL_UP)
        beam.irq(break_beam_callback, Pin.IRQ_FALLING)
        print("IR Beam enabled",flush=True)

    traps = {
                "Trap 1": {"button": Pin(15, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0},
                "Trap 2": {"button": Pin(15, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0}
    }

    while True:
        dt = strftime()
        for trap in (traps):
            if traps[trap]["button"] == 1:
                if traps[trap]["sprung"]:
                    traps[trap]["sprung"] = False
                    print  ("{}: {} is set".format(dt,trap),flush=True)
                    send_alert ("-> {} is set".format(trap))
                    traps[trap]["spring trigger"] = 0
                #else:
                #	print ("{} already set".format(trap))
            else:
                if not traps[trap]["sprung"]:
                    traps[trap]["spring trigger"] += 1
                    if (traps[trap]["spring trigger"] > 5):
                        traps[trap]["sprung"] = True
                        print  ("{}: {} is sprung".format(dt,trap),flush=True)
                        send_alert (":mouse_trap: {} sprung!!!".format(trap))
                #else:
                #	print ("{} already sprung".format(trap))
        sleep(0.2)

