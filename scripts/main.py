#Main routine for pico1
import time
from machine import Pin

#Import my supporting code
import utils.myid as myid, utils.wifi as wifi, utils.mqtt as mqtt
from utils.blink import blink

#Get my ID
pico = myid.get_id()
print("I am {}".format(pico))

#Call wifi_connect with our hostname
wifi_connected = wifi.wlan_connect(pico)

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()

#define callback
def on_message(topic, payload):
    print("topic: {} received message = {}".format(str(topic.decode()),str(payload.decode())))
    if str(topic.decode()) == "pico/"+pico+"/control":
        if str(payload.decode()) == "blink":
            blink(0.25,0.25)
        else:
            print("Unknown command: {}".format(str(payload.decode())))
    elif str(topic.decode()) == "pico/"+pico+"/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        mqtt.send_mqtt(client,heartbeat_topic,"Yes, I'm here")

try:
    client = mqtt.mqtt_connect(client_id=pico)
    topic = 'pico/'+pico+'/status'
    message = pico + ' is Alive!'
    mqtt.send_mqtt(client,topic,message)
    #Bind function to callback
    client.set_callback(on_message)
    #sub_topic = "pico/"+pico+"/#"
    print("Subscribing to channels...")
    client.subscribe("pico/"+pico+"/control")
    client.subscribe("pico/"+pico+"/poll")
    while True:
        client.check_msg()
        time.sleep(0.1)

except OSError as e:
    print("Failed to connect to MQ")
    #reconnect()

