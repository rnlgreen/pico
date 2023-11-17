#Utility functions for light sensor
from machine import Pin, ADC # type: ignore # pylint: disable=import-error
from utils import mqtt

photoPIN = 26 #GPIO26, Pin 31 # pylint: disable=invalid-name
MIN_BRIGHTNESS = 15
MAX_BRIGHTNESS = 80

#Measure light levels
def readLight(photoGP=photoPIN):
    photoRes = ADC(Pin(photoGP))
    light = photoRes.read_u16()
    light = round(light/65535*100,2)
    return light

#Calculate how close the new brightness is to a threshold
def check_hysteresis(lightlevel):
    l = lightlevel / 2.5
    h = 0.5 - abs(l - round(l,0))
    #debug("Hysteresis {} -> {}".format(lightlevel,h))
    return(h)

readings = [readLight()] * 10
#Returns the rolling average for light readings
def rolling_average():
    global readings
    readings.pop(0)
    latest = readLight()
    readings += [latest]
    avg = sum(readings)/len(readings)
    #debug("Latest: {} Average: {} Hysteresis: {}".format(latest,avg))
    return(avg)

#Returns new brightness level
def get_brightness(lightlevel,boost=False):
    if boost:
        b = min(MAX_BRIGHTNESS,max(MIN_BRIGHTNESS,(round((lightlevel * 2)/5) * 5) + 10))
    else:
        b = min(MAX_BRIGHTNESS,max(MIN_BRIGHTNESS,(round((lightlevel * 2)/5) * 5) - 10))
    return b

#Send measurement
def send_measurement(where,what,value):
    print("Sending measurement {}: {}".format(what, value))
    topic = what+"/"+where
    if mqtt.client != False:
        mqtt.send_mqtt(topic,str(value))

last_reading = 0
