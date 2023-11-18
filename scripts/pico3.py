#pico0 main code
import time
import gc
import utils.mqtt as mqtt
import utils.myid as myid
import utils.leds as leds

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

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
def led_control(command=""):
    leds.led_control(command)

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
        time.sleep(0.2)

if __name__ == "__main__":
    main()
