"""Main routine for PicoX"""
#Initialise the traps
import time
import gc
from utils import mqtt
from utils import leds
from utils import wifi
from utils.log import status

def get_status():
    status(f"running: {leds.running}")
    status(f"effect: {leds.effect}")
    status(f"stop: {leds.stop}")
    status(f"speed: {leds.speed}")
    status(f"dyndelay: {leds.dyndelay}")
    status(f"brightness: {leds.brightness}")
    status(f"colour: {leds.colour}")
    status(f"hue: {leds.hue}")
    status(f"lightsoff: {leds.lightsoff}")
    status(f"Auto control: {leds.auto}")
    gc.collect()
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member

#LED control function to accept commands and launch effects
def led_control(topic,payload):
    leds.led_control(topic,payload)

#Called my main.py
def main():
    strip_type = "GRB"
    pixels = 50
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)
    leds.xstrip = True

    if mqtt.client is not False:
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
