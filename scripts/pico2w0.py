"""Main routine for xbox lights"""
#Initialise the traps
import time
import gc
from machine import Pin # pylint: disable=import-error
from utils import mqtt
from utils import settings
from utils import leds
from utils import wifi
from utils.blink import blink
from utils.log import status
from utils.common import new_brightness, set_brightness, set_all, set_speed

BUTTON = 15
SWITCH = 17
effect_duration = 300

def get_status():
    status(f"running: {settings.running}")
    status(f"effect: {settings.effect}")
    status(f"stop: {settings.stop}")
    status(f"speed: {settings.speed}")
    status(f"dyndelay: {settings.dyndelay}")
    status(f"brightness: {settings.brightness}")
    status(f"colour: {settings.colour}")
    status(f"hue: {settings.hue}")
    status(f"lightsoff: {settings.lightsoff}")
    status(f"Auto control: {settings.auto}")
    status(f"Single pattern: {settings.singlepattern}")
    gc.collect()
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member

#LED control function to accept commands and launch effects
def led_control(topic,payload):
    leds.led_control(topic,payload)

def button_callback(_):
    if settings.stop_after != 1:
        blink(0.1,0,1)
        status("Skipping to next sequence")
        settings.stop_after = 1 # Specific setting to trigger time_to_go()

def switch_callback(pin):
    blink(0.1,0,1)
    if pin.value() == 1:
        status("Single pattern")
        settings.singlepattern = True
        settings.stop_after = 0 # Flag to not stop
    else:
        if settings.singlepattern:
            status("Multiple patterns")
            settings.stop_after = 2 # Not 0 or 1 but something in the past
            settings.singlepattern = False

#Called my main.py
def main(standalone = False):
    standalone = False
    if standalone:
        status("Running standalone")

    strip_type = "GRB"
    pixels = 288
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)

    button = Pin(BUTTON, Pin.IN, Pin.PULL_UP)
    button.irq(button_callback, Pin.IRQ_FALLING)
    switch = Pin(SWITCH, Pin.IN, Pin.PULL_UP)
    switch.irq(switch_callback, Pin.IRQ_FALLING | Pin.IRQ_RISING)

    #Send a message to the playroom lights to come on
    if mqtt.client is not False:
        message = "brightness:30"
        topic = 'pico/plights'
        try:
            mqtt.send_mqtt(topic,message)
        except Exception: # pylint: disable=broad-except
            mqtt.client = False # just adding this in here to try and avoid a failure loop

    if standalone:
        if switch.value() == 1:
            settings.singlepattern = True
            status("Single pattern mode")
        else:
            settings.singlepattern = False
            status("Multiple pattern mode")

        set_brightness(0) #does set_all(0,0,0) and show() so don't need to do that here as well

        while True:
            if mqtt.client is not False:
                mqtt.client.check_msg()
            set_speed(10)
            set_all(255,0,0)
            new_brightness(50)
            led_control("standalone xlights",f"rainbow:{effect_duration}")
    else:
        if mqtt.client is not False:
            mqtt.client.subscribe("pico/xlights") # type: ignore
            #mqtt.client.subscribe("pico/lights") # type: ignore

        set_speed(10)
        set_all(255,0,0)
        new_brightness(50)
        led_control("standalone xlights",f"rainbow:{effect_duration}")

        while True:
            if mqtt.client is not False:
                mqtt.client.check_msg()

            #Check WiFi status
            if not wifi.check_wifi():
                return "Wi-Fi Lost"

            time.sleep(0.2)

if __name__ == "__main__":
    main()
