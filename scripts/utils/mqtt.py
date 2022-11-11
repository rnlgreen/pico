#MQTT specific functions
from umqtt.simple import MQTTClient # type: ignore
import secrets

client = False

def mqtt_connect(client_id, mqtt_server=secrets.mqtt_server):
    global client
    print("Connecting to MQTT...")
    try:
        print("Connecting as {} to {}".format(client_id, mqtt_server))
        client = MQTTClient(client_id, mqtt_server, keepalive=3600)
        client.connect()
        print('Connected to MQTT Broker {}'.format(mqtt_server))
        return client
    except:
        print("Failed to connect to MQTT")
        return False

#send a message
def send_mqtt(topic, payload):
    #print("Sending message '{}' to '{}'".format(topic,payload))
    client.publish(topic,payload)
