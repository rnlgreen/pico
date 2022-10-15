#Main routine for pico1
import time
import _thread
import machine

#Import my supporting code
import utils.myid as myid, utils.wifi as wifi, utils.mqtt as mqtt
from utils.blink import blink

#Get my ID
pico = myid.get_id()
print("I am {}".format(pico))

#Call wifi_connect with our hostname
wifi_connected = wifi.wlan_connect(pico)

def restart():
    print('Restarting {} ...'.format(pico))
    time.sleep(5)
    machine.reset()

#define callback
def on_message(topic, payload):
    print("topic: {} received message = {}".format(str(topic.decode()),str(payload.decode())))
    if str(topic.decode()) == "pico/"+pico+"/control":
        if str(payload.decode()) == "blink":
            blink(0.25,0.25)
        elif str(payload.decode()) == "restart":
            restart()
        else:
            print("Unknown command: {}".format(str(payload.decode())))
    elif str(topic.decode()) == "pico/"+pico+"/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        mqtt.send_mqtt(client,heartbeat_topic,"Yes, I'm here")

try:
    client = mqtt.mqtt_connect(client_id=pico)
except OSError as e:
    print("Failed to connect to MQ")
    #reconnect()

#Say Hello
topic = 'pico/'+pico+'/status'
message = pico + ' is Alive!'
mqtt.send_mqtt(client,topic,message)

#Initialise the traps
import trap

#Subscribe to control and heartbeat channels
client.set_callback(on_message)
print("Subscribing to channels...")
client.subscribe("pico/"+pico+"/control")
client.subscribe("pico/"+pico+"/poll")

while True:
    #Check the traps
    trap.trap()
    #Check for messages
    client.check_msg()
    #Wait a bit
    time.sleep(1)

