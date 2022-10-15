#MQTT specific functions
from umqtt.simple import MQTTClient # type: ignore

#NOTE: ".local" seems to use mdns, but raw "condor" uses DNS
mqtt_server = 'condor'

def mqtt_connect(client_id, mqtt_server=mqtt_server):
    print("Connecting to MQTT...")
    try:
        client = MQTTClient(client_id, mqtt_server, keepalive=3600)
        client.connect()
        print('Connected to MQTT Broker {}'.format(mqtt_server))
        return client
    except:
        print("Failed to connec to MQTT")
        return False

#send a message
def send_mqtt(client, topic, payload):
    print("Sending message '{}' to '{}'".format(topic,payload))
    client.publish(topic,payload)