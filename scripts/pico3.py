#pico0 main code
import time
import gc
from utils import mqtt
from utils import leds
from utils import wifi
from utils import settings
from utils.log import status

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
def main():
    strip_type = "GRB"
    pixels = 72
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)

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
