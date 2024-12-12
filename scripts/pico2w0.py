"""Main routine for PicoX"""
#Initialise the traps
import time
import gc
from utils import mqtt
from utils import more_leds as leds
from utils import wifi
from utils.log import status, log

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
def main(standalone = True):
    if standalone:
        log("Running standalone")

    strip_type = "GRB"
    pixels = 50
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)
    leds.xstrip = True
    leds.xsync = False

    if standalone:
        effect_duration = 15
        sequence = ["rainbow", "train", "statics", "shimmer", "splashing"]
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
