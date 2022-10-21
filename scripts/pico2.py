#Code for Pico2 - measure and report temperature and pressure
import time
import utils.am2320 as am2320
from machine import I2C, Pin # type: ignore
import utils.myid as myid
import utils.mqtt as mqtt

#Send alert 
def send_measurement(what,value):
    print("Sending measurement {}: {}".format(what, value))
    topic = what+"/"+where
    if client != False:
        mqtt.send_mqtt(client,topic,value)

def main(client = False):
    i2c = I2C(id=0, scl=Pin(5), sda=Pin(4))
    sensor = am2320.AM2320(i2c)

    last_sent = time.time() - 60

    while True:
        if time.time() - last_sent >= 60:
            last_sent = time.time()
            try:
                sensor.measure()
                send_measurement("temperature",sensor.temperature())
                send_measurement("humiditiy",sensor.humidity())
            except:
                print("Unable to access I2C")
        #Check for messages
        if client != False:
            client.check_msg() 
        time.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

#Try and connect to MQTT (so we get a global variable for client)
client = mqtt.mqtt_connect(client_id=pico+'-sensor')

if __name__ == "__main__":
    main()
