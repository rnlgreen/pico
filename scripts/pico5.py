#pico0 main code
import time, utime # type: ignore
import gc
import utils.mqtt as mqtt
import utils.myid as myid
import utils.leds as leds
from machine import Pin, ADC # type: ignore

photoPIN = 26 #GPIO26, Pin 31
debug = False

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

#Print and send status messages
def debug(message):
    print(message)
    if debug:
        message = myid.pico + ": " + message
        topic = 'pico/'+myid.pico+'/debug'
        mqtt.send_mqtt(topic,message)

def send_control(payload):
    topic = 'pico/lights'
    mqtt.send_mqtt(topic,payload)

def get_status():
    status("hour: {}".format(utime.localtime()[3]))
    status("running: {}".format(leds.running))
    status("effect: {}".format(leds.effect))
    status("stop: {}".format(leds.stop))
    status("speed: {}".format(leds.speed))
    status("dyndelay: {}".format(leds.dyndelay))
    status("brightness: {}".format(leds.brightness))
    status("colour: {}".format(leds.colour))
    status("lightsoff: {}".format(leds.lightsoff))
    status("Light level: {}".format(readLight()))
    status("Auto control: {}".format(leds.auto))
    gc.collect()
    status("freemem: {}".format(gc.mem_free()))

#Send measurement
def send_measurement(what,value):
    print("Sending measurement {}: {}".format(what, value))
    topic = what+"/"+where
    if mqtt.client != False:
        mqtt.send_mqtt(topic,str(value))

#LED control function to accept commands and launch effects
def led_control(command="",arg=""):
    leds.led_control(command,arg)

#Measure light levels
def readLight(photoGP=photoPIN):
    photoRes = ADC(Pin(photoGP))
    light = photoRes.read_u16()
    light = round(light/65535*100,2)
    return light

readings = [readLight()] * 10
#Returns the rolling average for light readings
def rolling_average():
    global readings
    readings.pop(0)
    latest = readLight()
    readings += [latest]
    avg = sum(readings)/len(readings)
    debug("Latest: {} Average: {}".format(latest,avg))
    return(avg)

#Control LEDs based on light and time of day
#Returns True if lights were updated so we can slow the rate of changes
def manage_lights():
    lightlevel = rolling_average()
    #Check time of day first
    hour = utime.localtime()[3]
    updated = False
    #Turn on or adjust brightness for low light level, unless it is late
    if 6 <= hour <= 21: #from 06:00 to 21:59 (or 07:00 to 22:59 in Summer as pico runs in GMT)
        if lightlevel < 45:
            if leds.lightsoff:
                status("Turning lights on")
                if leds.colour == [0, 0, 0]:
                    send_control("rgb(0, 255, 255)")
                    updated = True
                #Set brightness to 50% of target, we'll see if we need brighter as the rolling average catches up
                new_brightness = min(80,max(10,(round((lightlevel)/5) * 5) - 10))
            else:
                #New brightness something between 10 and 80 step 5
                new_brightness = min(80,max(10,(round((lightlevel*2)/5) * 5) - 10))
            if leds.brightness != new_brightness:
                debug("Old brightness: {} -> New brightness: {}".format(leds.brightness,new_brightness))
                status("Brightness {} -> {}".format(leds.brightness,new_brightness))
                send_control("brightness:{}".format(new_brightness))
                updated = True
    #Turn off for high light levels
    if lightlevel > 55 and not leds.lightsoff:
        status("Turning lights off")
        send_control("off")
        updated = True
    return updated

#Called my main.py
def main():
    strip_type = "GRB"
    pixels = 72
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)

    if mqtt.client != False:
        mqtt.client.subscribe("pico/lights") 
        mqtt.client.subscribe("pico/lights/+") 
    last_reading = time.time()
    last_lights = time.time()
    updated = False #Flag to limit lighting auto updates to every other second
    while True:
        if mqtt.client != False:
            mqtt.client.check_msg() 
        #Publish light level every 5 seconds
        if time.time() - last_reading >= 5:
            lightlevel = readLight()
            send_measurement("light",lightlevel)
            last_reading = time.time()
        #Manage light level every second
        if time.time() - last_lights >= 1:
            last_lights = time.time()
            if leds.auto:
                if not updated: #If we updated last time the lights won't have finished fading yet
                    #Manage LEDs based on light level and time of day
                    updated = manage_lights()
                else:
                    debug("Skipping lighting update this time")
                    updated = False
                    rolling_average()
            else:
                rolling_average()
        time.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
