#Code for Pico2 - measure and report temperature and pressure
import time
import utils.am2320 as am2320
from machine import I2C, Pin # type: ignore
import utils.myid as myid
import utils.mqtt as mqtt

#Pins from left to right:
#1: Voltage in, 3-5 VDC
#2: SDA: I2C data in/out 
#3: Ground
#4: SCL: I2C clock in

I2CID = 1
SDAPIN = 26 #GPIO26
SCLPIN = 27 #GPIO27

#Print and send status messages
def status(message):
    print(message)
    message = pico + ": " + message
    topic = 'pico/'+pico+'/status'
    send_mqtt(topic,message)

#Send alert 
def send_mqtt(topic,message):
    print("{}: {}".format(topic,message))
    if mqtt.client != False:
        mqtt.send_mqtt(topic,message)

#Send alert 
def send_measurement(what,value):
    print("Sending measurement {}: {}".format(what, value))
    topic = what+"/"+where
    if mqtt.client != False:
        mqtt.send_mqtt(topic,str(value))

def main():
    try:
        i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=40000)
        sensor = am2320.AM2320(i2c)
    except Exception as e:
        status("Error setting up I2C: {}".format(e))
        time.sleep(3)
        return

    last_sent = time.time() - 60

    while True:
        if time.time() - last_sent >= 60:
            last_sent = time.time()
            try:
                sensor.measure()
                send_measurement("temperature",sensor.temperature())
                send_measurement("humidity",sensor.humidity())
                status("Measurements sent")
            except Exception as e:
                status("Exception: {}".format(e))
        #Check for messages
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
