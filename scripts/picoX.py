"""Main routine for PicoX"""
#Initialise the traps
import time
import gc
from utils import mqtt
from utils import settings
from utils import leds
from utils import wifi
from utils.log import status,log
from utils.common import set_brightness, set_all

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
    if standalone:
        log("Running standalone")

    strip_type = "GRB"
    pixels = 50
    GPIO = 28
    settings.xstrip = True
    leds.init_strip(strip_type,pixels,GPIO)

    if standalone:
        set_brightness(60)
        effect_duration = 20
        led_control("standalone xlights","speed:90")
        while True:
            if mqtt.client is not False:
                mqtt.client.check_msg()
            settings.speed = 90
            led_control("standalone xlights",f"rainbow2:{effect_duration}")
            led_control("standalone xlights",f"statics:{effect_duration}")
            set_all(0, 0, 30)
            led_control("standalone xlights",f"twinkling:{effect_duration}")
            set_all(255, 200, 0)
            led_control("standalone xlights",f"shimmer:{effect_duration}")
            set_all(0, 30, 0)
            settings.speed = 30
            led_control("standalone xlights",f"splashing:{effect_duration}")
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
