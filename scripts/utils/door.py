#Trigger script to record and report the status of the garage door 
#Uses the magnetic switches on GPIO 14 (pin 19) and GPIO 15 (pin 20)
#Switches should be attached to the GPIO pin and to ground

from machine import Pin, RTC as rtc, PWM # type: ignore
import time
import utils.myid as myid
import utils.mqtt as mqtt
from utils.blink import blink

sensors = {
            "top":    {"button": Pin(14, Pin.IN, Pin.PULL_UP)},
            "bottom":    {"button": Pin(15, Pin.IN, Pin.PULL_UP)}
}
door_open = False   #Might use later if we put a top sensor in to confirm open status
door_closed = False #Used to flag if the closed or not

#Return formatted time string
def strftime():
    timestamp=rtc().datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

#Send alert 
def send_alert(message):
    print("Sending alert {}".format(message))
    topic = "pico/"+myid.pico+"/alerts/garage_door"
    if mqtt.client != False:
        message = ":car: " + message
        mqtt.send_mqtt(topic,message)

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client != False:
        mqtt.send_mqtt(topic,message)

def get_status():
    for sensor in sensors:
        if sensors[sensor]["button"].value() == 0:
            status("{} switch is closed".format(sensor))
        else:
            status("{} switch is open".format(sensor))
    if door_closed:
        status("Garage closed")
    elif door_open:
        status("Garage fully open")
    else:
        status("Garage partially open") 

def door():
    global door_open, door_closed
    dt = strftime()
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

if __name__ == "__main__":
    while True:
        door()
        time.sleep(0.25)