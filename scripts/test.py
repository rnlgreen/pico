import time
from utils import myid
from utils import wifi
from utils import mqtt

#Send message with specific topic
def send_mqtt(topic,message):
    """Function for sending MQTT message."""
    print(f"{topic}: {message}")
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)
        return True

#process incoming control commands
def on_message(topic, payload):
    """Process incoming MQTT messages"""
    topic = str(topic.decode())
    payload = str(payload.decode())
    print(f"Received topic: {topic} message: {payload}")

pico = myid.get_id()
ipaddr = wifi.wlan_connect(pico)

mqtt.mqtt_connect(client_id=pico)
mqtt.client.set_callback(on_message) # type: ignore
mqtt.client.subscribe("#") # type: ignore

print("Sending 'test1'")
mqtt.send_mqtt("test","test1")
time.sleep(2)
print(mqtt.client.ping())
print("Checking for messages")
mqtt.client.ping()
mqtt.client.check_msg()

print("Sending 'test2°'")
mqtt.send_mqtt("test","test2°")
time.sleep(2)
print(mqtt.client.ping())
print("Checking for messages")
mqtt.client.check_msg()

print("Sending 'test3'")
mqtt.send_mqtt("test","test3")
time.sleep(1)
print(mqtt.client.ping())
print("Checking for messages")
mqtt.client.check_msg()

mqtt.client.disconnect()
