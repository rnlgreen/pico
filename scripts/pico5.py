#pico5 main code
import time 
import gc
import utils.mqtt as mqtt
import utils.myid as myid
import utils.leds as leds
import utils.light as light

debugging = True

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

#Print and send status messages
def debug(message):
    print(message)
    if debugging:
        message = myid.pico + ": " + message
        topic = 'pico/'+myid.pico+'/debug'
        mqtt.send_mqtt(topic,message)

def send_control(payload):
    topic = 'pico/lights'
    mqtt.send_mqtt(topic,payload)

def get_status():
    status("running: {}".format(leds.running))
    status("effect: {}".format(leds.effect))
    status("stop: {}".format(leds.stop))
    status("speed: {}".format(leds.speed))
    status("dyndelay: {}".format(leds.dyndelay))
    status("brightness: {}".format(leds.brightness))
    status("colour: {}".format(leds.colour))
    status("lightsoff: {}".format(leds.lightsoff))
    status("Light level: {}".format(light.readLight()))
    status("Auto control: {}".format(leds.auto))
    gc.collect()
    status("freemem: {}".format(gc.mem_free()))

#LED control function to accept commands and launch effects
def led_control(command="",arg=""):
    leds.led_control(command,arg)

#Called my main.py
def main():
    strip_type = "GRB"
    pixels = 72
    GPIO = 28
    leds.init_strip(strip_type,pixels,GPIO)

    if mqtt.client != False:
        mqtt.client.subscribe("pico/lights") 
        mqtt.client.subscribe("pico/lights/+") 
    light.last_reading = time.time()
    leds.last_lights = time.time()
    updated = False #Flag to limit lighting auto updates to every other second
    while True:
        if mqtt.client != False:
            mqtt.client.check_msg() 
        #Publish light level every 5 seconds
        if time.time() - light.last_reading >= 5:
            lightlevel = light.readLight()
            light.send_measurement(where,"light",lightlevel)
            light.last_reading = time.time()
        #Manage light level every second
        if time.time() - leds.last_lights >= 1:
            leds.last_lights = time.time()
            if leds.auto:
                if not updated: #If we updated last time the lights won't have finished fading yet
                    #Manage LEDs based on light level and time of day
                    updated = leds.manage_lights()
                else:
                    debug("Waiting for lights to fade")
                    updated = False
                    light.rolling_average()
            else:
                light.rolling_average()
        time.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
