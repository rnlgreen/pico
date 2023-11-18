"""MQTT specific functions"""
import secrets
from umqtt.simple import MQTTClient # type: ignore # pylint: disable=import-error

client = False # pylint: disable=invalid-name

def mqtt_connect(client_id, mqtt_server=secrets.mqtt_server):
    """Connect to MQTT server, returns client object or False"""
    global client #pylint: disable=global-statement
    print("Connecting to MQTT")
    try:
        print(f"Connecting as {client_id} to {mqtt_server}")
        client = MQTTClient(client_id, mqtt_server, keepalive=3600)
        client.connect()
        print(f'Connected to MQTT Broker {mqtt_server}')
        return client
    except Exception: # pylint: disable=broad-except
        print("Failed to connect to MQTT")
        client = False
        return client

#send a message
def send_mqtt(topic, payload):
    """Publish message"""
    #print("Sending message '{}' to '{}'".format(topic,payload))
    if not client is False:
        client.publish(topic,payload)
