"""Main routine for PicoX"""
#Initialise the traps
import time
import gc
from utils import mqtt
from utils import settings
from utils import leds
from utils import wifi
from utils.log import status, log

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

#Called my main.py
def main(standalone = True):
    if standalone:
        log("Running standalone")

    strip_type = "GRB"
    pixels = 50
    GPIO = 28
    xstrip = True
    leds.init_strip(strip_type,pixels,GPIO,xstrip)

    if standalone:
        effect_duration = 15
        sequence = ["rainbow", "statics", "shimmer", "splashing", "twinkling"]
        sequence_no = 0
        led_control("standalone xlights","brightness:30")
        while True:
            if mqtt.client is not False:
                mqtt.client.check_msg()
            led_control("standalone xlights",f"{sequence[sequence_no]}:{effect_duration}")
            sequence_no += 1
            if sequence_no == len(sequence):
                sequence_no = 0
    else:
        if mqtt.client is not False:
            mqtt.client.subscribe("pico/xlights") # type: ignore
            mqtt.client.subscribe("pico/lights") # type: ignore

        while True:
            if mqtt.client is not False:
                mqtt.client.check_msg()

            #Check WiFi status
            if not standalone and not wifi.check_wifi():
                return "Wi-Fi Lost"

            time.sleep(0.2)

if __name__ == "__main__":
    main()
