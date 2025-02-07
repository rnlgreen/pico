"""Main routine for PicoX"""
#Extractor fan lights
import time
import gc
from utils import mqtt
from utils import settings
from utils import leds
from utils import wifi
from utils.log import status,log
from utils.common import set_brightness, off

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
    gc.collect()
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member

#LED control function to accept commands and launch effects
def led_control(topic,payload):
    leds.led_control(topic,payload)

#Called by main.py
def main(standalone = False):
    standalone = True
    if standalone:
        settings.standalone = True # Set this so it can be accessed by other functions
        log("Running standalone")

    strip_type = "GRB"
    pixels = 50
    GPIO = 28
    settings.xstrip = True
    leds.init_strip(strip_type,pixels,GPIO)

    if standalone:
        brightness = 20
        set_brightness(brightness)
        settings.speed = 90
        effect_duration = 600 # Was -1, but if we want to check the time of day to turn off we need to come back
        led_control("standalone xlights","speed:90")
        mqtt.client.subscribe("pico/xlights") # type: ignore
        while True:
            if mqtt.client is not False:
                mqtt.client.check_msg()
            if not (leds.daytime() or settings.lightsoff):
                status("Turning lights off")
                off()
            else:
                if leds.daytime() and settings.lightsoff:
                    status("Turning lights on")
                    set_brightness(brightness)
                #led_control("standalone xlights",f"test:{effect_duration}")
                #led_control("standalone xlights",f"rainbow2:{effect_duration}")
                led_control("standalone xlights",f"statics:{effect_duration}")
                #set_all(0, 0, 30)
                #settings.cycle=True
                #led_control("standalone xlights",f"twinkling:{-1}")
                #set_all(255, 200, 0)
                #led_control("standalone xlights",f"shimmer:{effect_duration}")
    else:
        if mqtt.client is not False:
            mqtt.client.subscribe("pico/xlights") # type: ignore
            mqtt.client.subscribe("pico/lights") # type: ignore

        while True:
            if mqtt.client is not False:
                mqtt.client.check_msg()

            #Check WiFi status
            if not wifi.check_wifi():
                return "Wi-Fi Lost"

            time.sleep(0.2)

if __name__ == "__main__":
    main()
