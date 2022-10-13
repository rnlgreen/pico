#MQTT specific functions
from umqtt.simple import MQTTClient

#NOTE: ".local" seems to use mdns, but raw "condor" uses DNS
mqtt_server = 'condor'

def mqtt_connect(client_id, mqtt_server=mqtt_server):
    print("Connecting to MQTT...")
    client = MQTTClient(client_id, mqtt_server, keepalive=3600)
    client.connect()
    print('Connected to MQTT Broker {}'.format(mqtt_server))
    return client

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()

#send a message
def send_mqtt(client, topic, payload):
    print("Sending message '{}' to '{}'".format(topic,payload))
    client.publish(topic,payload)