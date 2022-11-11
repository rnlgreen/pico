#pico3 main code
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

#LED control function to accept commands and launch effects
def led_control(command=""):
    if command.startswith("rgb"):
        #rgb(219, 132, 56)
        r, g, b = [int(x) for x in command[4:-1].split(", ")]
        leds.set_all(r, g, b)
    elif command.startswith("brightness:"):
        _, b = command.split(":")
        leds.strip.brightness(int(b))
        if not leds.running:
            r, g, b = leds.list_to_rgb(leds.colour)
            leds.set_all(r, g, b)
    elif command.startswith("saturation:"):
        _, s = command.split(":")
        leds.saturation = int(s)
    else:
        try:
            leds.effects[command]()
        except Exception as e:
            status("Exception: {}".format(e))

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

