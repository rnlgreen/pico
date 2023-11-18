#Code for Pico2 - measure and report temperature and pressure
import time
from machine import I2C, Pin # type: ignore # pylint: disable=import-error
from utils import am2320
from utils import myid
from utils import mqtt

#Pins from left to right:
#1: Voltage in, 3-5 VDC
#2: SDA: I2C data in/out
#3: Ground
#4: SCL: I2C clock in

I2CID = 1
SDAPIN = 26 #GPIO26
SCLPIN = 27 #GPIO27

last_temp = -1
last_humidity = -1

#Print and send status messages
def status(message):
    print(message)
    message = pico + ": " + message
    topic = 'pico/'+pico+'/status'
    send_mqtt(topic,message)

#Send alert
def send_mqtt(topic,message):
    print(f"{topic}: {message}")
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

#Send alert
def send_measurement(what,value):
    print(f"Sending measurement {what}: {value}")
    topic = what+"/"+where
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,str(value))

#Return i2cscan to status commands
def get_status():
    i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=400000)
    devices = i2c.scan()
    if len(devices) == 0:
        status("No I2C device found")
    elif len(devices) > 1:
        status("Multiple I2C devices found -")
        for d in devices:
            status(f"  0x{d:02X}")
    else:
        status(f"I2C device found at 0x{devices[0]:02X}")
    status(f"Latest temperature = {last_temp}")
    status(f"Latest humidity: {last_humidity}")

def main():
    global last_temp, last_humidity # pylint: disable=global-statement
    try:
        i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=40000)
        sensor = am2320.AM2320(i2c)
    except Exception as e: # pylint: disable=broad-exception-caught
        status(f"Error setting up I2C: {e}")
        time.sleep(3)
        return

    last_sent = time.time() - 60

    while True:
        if time.time() - last_sent >= 60:
            last_sent = time.time()
            got_reading = False
            try:
                sensor.measure()
                got_reading = True
            except Exception as e: # pylint: disable=broad-exception-caught
                status(f"Exception: {e}")
            if got_reading:
                send_measurement("temperature",sensor.temperature())
                send_measurement("humidity",sensor.humidity())
                last_temp = sensor.temperature()
                last_humidity = sensor.humidity()
        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()
        time.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
