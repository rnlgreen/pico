"""MQTT utility functions"""
import secrets
from utils import log
from utils.control import restart
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
        client = False
        log.status("Failed to connect to MQTT", logit=True)
        return False

#send a message
def send_mqtt(topic, payload):
    """Publish message"""
    global client #pylint: disable=global-statement
    if not client is False:
        try:
            client.publish(topic,payload)
            return True
        except Exception as e: # pylint: disable=broad-except
            client = False # Adding this here to avoid repeatedly trying to use MQTT
            log.status("Error sending to mqtt", logit=True, handling_exception=True)
            log.log_exception(e)
            restart("MQTT Failure detected")
            return False
