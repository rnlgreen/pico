"""Main routine for study lights"""
#Initialise the traps
import time
import gc
from utils import mqtt
from utils import settings
from utils import leds
from utils import wifi
from utils.log import status
from utils.common import new_brightness, set_speed, set_all, show

BUTTON = 15
SWITCH = 17
effect_duration = -1

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

#Called my main.py
def main(standalone = False):
    standalone = True
    if standalone:
        status("Running standalone")

    strip_type = "GRB"
    pixels = 150
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)

    if standalone:
        set_all(255,255,200,255)
        new_brightness(200)
        show()

    while True:
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        time.sleep(0.2)

if __name__ == "__main__":
    main()
