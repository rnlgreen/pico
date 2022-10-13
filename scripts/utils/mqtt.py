#MQTT specific functions
from umqtt.simple import MQTTClient

#NOTE: ".local" seems to use mdns, but raw "condor" uses DNS
mqtt_server = 'condor'

def mqtt_connect(client_id, mqtt_server=mqtt_server):
    print("Connecting to MQTT...")
    client = MQTTClient(client_id, mqtt_server, keepalive=3600)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()

#define callback
def on_message(topic, payload):
    print("topic: {} received message = {}".format(str(topic.decode()),str(payload.decode())))
