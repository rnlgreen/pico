#pico5 main code
import time
import gc
from utils import mqtt
from utils import myid
from utils import leds
from utils import light
from utils import wifi
from utils import settings
from utils.log import status, debug

def send_control(payload):
    topic = 'pico/lights'
    mqtt.send_mqtt(topic,payload)

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
    status(f"Light level: {light.readLight()}")
    status(f"Auto control: {settings.auto}")
    status(f"Boost control: {settings.boost}")
    status(f"previously_running: {settings.previously_running}")
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
    settings.master = True
    leds.init_strip(strip_type,pixels,GPIO)
    leds.send_control(leds.INITIAL_COLOUR_COMMAND)

    if mqtt.client is not False:
        mqtt.client.subscribe("pico/lights")
        mqtt.client.subscribe("pico/lights/+")
    light.last_reading = time.time()
    settings.last_lights = time.time()
    updated = False #Flag to limit lighting auto updates to every other second
    while True:
        if mqtt.client is not False:
            mqtt.client.check_msg()
        #Publish light level every 5 seconds
        if time.time() - light.last_reading >= 5:
            lightlevel = light.readLight()
            light.send_measurement(where,"light",lightlevel)
            light.last_reading = time.time()
        #Manage light level every second
        if time.time() - settings.last_lights >= 1:
            settings.last_lights = time.time()
            if settings.auto:
                if not updated: #If we updated last time the lights won't have finished fading yet
                    #Manage LEDs based on light level and time of day
                    updated = leds.manage_lights()
                else:
                    debug("Waiting for lights to fade")
                    updated = False
                    light.rolling_average()
            else:
                light.rolling_average()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        time.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
