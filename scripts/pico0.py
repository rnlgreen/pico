#pico0 main code
import time
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

#LED control function to accept commands and launch effects
def led_control(command=""):
    leds.led_control(command)

#Called my main.py
def main():
    leds.off()
    if mqtt.client != False:
        mqtt.client.subscribe("pico/"+myid.pico+"/lights") # type: ignore
    while True:
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(0.2)

if __name__ == "__main__":
    main()

