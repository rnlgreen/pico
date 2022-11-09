#pico3 main code
import time
import utils.mqtt as mqtt
import utils.myid as myid
from neopixel import Neopixel

#Print and send status messages
def status(message):
    print(message)
    message = pico + ": " + message
    topic = 'pico/'+pico+'/status'
    mqtt.send_mqtt(topic,message)

def rainbow():
    global running, effect
    hue = 0
    effect = "rainbow"
    status("Running {}...".format(effect))
    running = True
    start = time.time()
    while not stop:
        elapsed = time.time()-start
        if elapsed > 5:
            if mqtt.client != False:
                mqtt.client.check_msg() 
            start = time.time()
        color = strip.colorHSV(hue, 255, 150)
        strip.fill(color)
        strip.show()
        hue += 150
        if hue > 65535:
            hue -= 65535
        time.sleep(0.01)
    status("Finished {}".format(effect))
    strip[:] = (0,0,0)
    strip.show()
    running = False
    effect = "None"

def off():
    global stop
    if running:
        status("Stopping..")
        stop = True

def led_control(command):
    undef,pattern = command.split(" ")
    try:
        led_functions[pattern]()
    except Exception as e:
        status("Exception: {}".format(e))

#Return status
def get_status():
    status("running: {}".format(running))
    status("effect: {}".format(effect))
    status("stop: {}".format(stop))

led_functions = { "rainbow": rainbow,
                 "off":    off }

#Called my main.py
def main():
    off()
    while True:
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(0.2)

pico = myid.get_id()

numpix = 60
#Create strip object
#parameters: number of LEDs, state machine ID, GPIO number and mode (RGB or RGBW)
status("Initialising strip")
strip = Neopixel(numpix, 0, 0, "GRB")
strip.brightness(20)

stop = False
running = False
effect = ""

if __name__ == "__main__":
    main()

