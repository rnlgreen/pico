#pico0 main code
import time
import gc
import utils.mqtt as mqtt
import utils.myid as myid
import utils.leds as leds
import utils.am2320 as am2320
from machine import I2C, Pin, ADC # type: ignore

#Pins from left to right:
#1: Voltage in, 3-5 VDC
#2: SDA: I2C data in/out 
#3: Ground
#4: SCL: I2C clock in

I2CID = 1
SDAPIN = 26 #GPIO26
SCLPIN = 27 #GPIO27
photoPIN = 28 #GPIO28, Pin 34

last_temp = -1
last_humidity = -1

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

#Send alert 
def send_measurement(what,value):
    print("Sending measurement {}: {}".format(what, value))
    topic = what+"/"+where
    if mqtt.client != False:
        mqtt.send_mqtt(topic,str(value))

#Report current status of lights and sensors etc.
def get_status():
    status("running: {}".format(leds.running))
    status("effect: {}".format(leds.effect))
    status("stop: {}".format(leds.stop))
    status("speed: {}".format(leds.speed))
    status("dyndelay: {}".format(leds.dyndelay))
    status("brightness: {}".format(leds.brightness))
    gc.collect()
    status("freemem: {}".format(gc.mem_free()))
    #i2c sensor
    i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=400000)
    devices = i2c.scan()
    if len(devices) == 0:
        status("No I2C device found")
    elif len(devices) > 1:
        status("Multiple I2C devices found -")
        for d in devices:
            status("  0x{:02X}".format(d))
    else:
        status("I2C device found at 0x{:02X}".format(devices[0]))    
    status("Latest temperature = {}".format(last_temp))
    status("Latest humidity: {}".format(last_humidity))
    status("Light level: {}".format(readLight()))

#LED control function to accept commands and launch effects
def led_control(command=""):
    leds.led_control(command)

#Measure light levels
def readLight(photoGP=photoPIN):
    photoRes = ADC(Pin(photoGP))
    light = photoRes.read_u16()
    light = round(light/65535*100,2)
    return light

#Called my main.py
def main():
    global last_temp, last_humidity

    strip_type = "GRBW"
    pixels = 16
    GPIO = 0
    leds.init_strip(strip_type,pixels,GPIO)

    try:
        i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=40000)
        sensor = am2320.AM2320(i2c)
    except Exception as e:
        status("Error setting up I2C: {}".format(e))
        time.sleep(3)
        return

    if mqtt.client != False:
        mqtt.client.subscribe("pico/lights") # type: ignore
    last_sent = time.time() - 60
    last_light = time.time() - 60

    while True:
        if time.time() - last_sent >= 60:
            last_sent = time.time()
            try:
                sensor.measure()
                send_measurement("temperature",sensor.temperature())
                send_measurement("humidity",sensor.humidity())
                last_temp = sensor.temperature()
                last_humidity = sensor.humidity()
                #status("Measurements sent")
            except Exception as e:
                status("Exception: {}".format(e))
        if time.time() - last_light >= 5:
            send_measurement("light",readLight())
            last_light = time.time()

        #Check for messages
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()

