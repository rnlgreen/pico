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
    status("running: {}".format(leds.running))
    status("effect: {}".format(leds.effect))
    status("stop: {}".format(leds.stop))
    status("speed: {}".format(leds.speed))
    status("dyndelay: {}".format(leds.dyndelay))
    status("brightness: {}".format(leds.brightness))
    status("colour: {}".format(leds.colour))
    status("hue: {}".format(leds.hue))
    status("lightsoff: {}".format(leds.lightsoff))
    status("Auto control: {}".format(leds.auto))
    gc.collect()
    status("freemem: {}".format(gc.mem_free()))

#LED control function to accept commands and launch effects
def led_control(command=""):
    leds.led_control(command)

#Called my main.py
def main():
    strip_type = "GRB"
    pixels = 72
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)

    if mqtt.client != False:
        mqtt.client.subscribe("pico/lights") # type: ignore
    while True:
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(0.2)

if __name__ == "__main__":
    main()

