#Trigger script to record and report the status of the garage door
#Uses the magnetic switches on GPIO 14 (pin 19) and GPIO 15 (pin 20)
#Switches should be attached to the GPIO pin and to ground

from machine import Pin # type: ignore # pylint: disable=import-error
from utils import myid
from utils import mqtt
from utils.blink import blink

sensors = {
            "top":    {"button": Pin(14, Pin.IN, Pin.PULL_UP)},
            "bottom": {"button": Pin(15, Pin.IN, Pin.PULL_UP)}
}
door_open = False   #Used to flag if the door is open
door_closed = True  #Used to flag if the door is closed; assume this is true as the normal position

#Send alert
def send_alert(message):
    print(f"Sending alert {message}")
    topic = "pico/"+myid.pico+"/alerts/garage_door"
    if mqtt.client is not False:
        message = ":car: " + message
        mqtt.send_mqtt(topic,message)

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

def get_status():
    for sensor in sensors: # pylint: disable=consider-using-dict-items
        if sensors[sensor]["button"].value() == 0:
            status(f"{sensor} switch is closed")
        else:
            status(f"{sensor} switch is open")
    if door_closed:
        status("Garage closed")
    elif door_open:
        status("Garage fully open")
    else:
        status("Garage partially open")

def door():
    global door_open, door_closed #pylint: disable=global-statement
    #Check if the closed or opening
    if sensors["bottom"]["button"].value() == 0:
        if not door_closed:
            #Blink the LED - useful when testing
            blink(0.1,0.05,3)
            door_closed = True
            send_alert("Garage closed")
    else:
        if door_closed:
            #Blink the LED - useful when testing
            blink(0.1,0.05,3)
            send_alert("Garage opening")
            door_closed = False
    #Check if the fully open or closing
    if sensors["top"]["button"].value() == 0:
        if not door_open:
            #Blink the LED - useful when testing
            blink(0.1,0.05,3)
            door_open = True
            send_alert("Garage fully open")
    else:
        if door_open:
            #Blink the LED - useful when testing
            blink(0.1,0.05,3)
            send_alert("Garage closing")
            door_open = False
