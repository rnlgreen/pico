"""pico0 main code"""
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import mqtt
from utils import myid
#from utils import leds
#from utils import am2320
#from utils import light
from utils import wifi
from utils import trap
from utils.log import log
from utils.control import restart
from machine import I2C, Pin # type: ignore # pylint: disable=import-error
from ruuvitag import RuuviTag

#Pins from left to right:
#1: Voltage in, 3-5 VDC
#2: SDA: I2C data in/out
#3: Ground
#4: SCL: I2C clock in

I2CID = 1
SDAPIN = 26 #GPIO26
SCLPIN = 27 #GPIO27
photoPIN = 18 #GPIO18

trap.traps = {
        "Trap 1": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": False, "spring trigger": 0},
}

mytags = { 'f34584d173cb': "woodstore", 'dc7eb48031b4': "garage", 'fab5c40c4095': "loft" }

last_temp = -1
last_humidity = -1
last_sent = 0
last_ruuvi = 0
no_ruuvi_since_start = True

#Callback handler that receives a tuple of data from the RuuviTag class object
#RuuviTagRAWv2(mac=b'f34584d173cb', rssi=-100, format=5, humidity=91.435, temperature=9.01,
#pressure=101617, acceleration_x=-20, acceleration_y=-40, acceleration_z=1020,
#battery_voltage=2851, power_info=4, movement_counter=122, measurement_sequence=31396)
def ruuvicb(ruuvitag):
    global last_ruuvi, no_ruuvi_since_start # pylint: disable=global-statement
    last_ruuvi = utime.ticks_ms()
    #elapsed = utime.ticks_diff(last_ruuvi,last_sent) / 1000
    #status(f"Processing data for {tagwhere} RuuviTag after {elapsed} seconds")
    tagwhere = mytags[ruuvitag.mac.decode('ascii')]
    if mqtt.client is not False:
        for thing in ["temperature", "humidity", "pressure", "battery_voltage"]:
            print(f"{thing}: {getattr(ruuvitag, thing)}")
            value = getattr(ruuvitag, thing)
            if thing == "battery_voltage":
                thing = "battery"
                value = value / 1000
            topic = thing+"/"+tagwhere
            if thing == "pressure":
                value = value / 100
            mqtt.send_mqtt(topic,str(value))
    no_ruuvi_since_start = False

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

#Report current status of lights and sensors etc.
def get_status():
    trap.get_status()
    # status(f"running: {leds.running}")
    # status(f"effect: {leds.effect}")
    # status(f"stop: {leds.stop}")
    # status(f"speed: {leds.speed}")
    # status(f"dyndelay: {leds.dyndelay}")
    # status(f"brightness: {leds.brightness}")
    gc.collect()
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    #i2c sensor
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
    #status(f"Light level: {light.readLight()}")

# #LED control function to accept commands and launch effects - called from main.py
# def led_control(command=""):
#     leds.led_control(command)

#Called my main.py
def main():
    global last_sent # pylint: disable=global-statement

    # strip_type = "GRBW"
    # pixels = 16
    # GPIO = 0
    # leds.init_strip(strip_type,pixels,GPIO)

    #Inititialise Ruuvi
    ruuvi = RuuviTag()
    ruuvi._callback_handler = ruuvicb # pylint: disable=protected-access

    # #Initialise i2c temperature/humidity sensor
    # try:
    #     i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=40000)
    #     sensor = am2320.AM2320(i2c)
    # except Exception as e: # pylint: disable=broad-exception-caught
    #     status(f"Error setting up I2C: {e}")
    #     utime.sleep(3)
    #     return

    # #Subscribe to MQTT
    # if mqtt.client is not False:
    #     mqtt.client.subscribe("pico/lights") # type: ignore

    #Main loop
    while True:
        # #Check the trap status
        # trap.trap()

        #Get and send a light reading
        if utime.ticks_diff(utime.ticks_ms(),last_sent) >= 60000:
            last_sent = utime.ticks_ms()

            # try:
            #     sensor.measure()
            #     light.send_measurement(where,"temperature",sensor.temperature())
            #     light.send_measurement(where,"humidity",sensor.humidity())
            #     last_temp = sensor.temperature()
            #     last_humidity = sensor.humidity()
            #     #status("Measurements sent")
            # except Exception as e: # pylint: disable=broad-exception-caught
            #     status(f"Exception: {e}")

            #Get Ruuvi Data
            print("Calling ruuvi.scan()")
            ruuvi.scan()

        #Check we've got an update from RuuviTag
        if utime.ticks_diff(utime.ticks_ms(),last_ruuvi) > 70000 and not no_ruuvi_since_start:
            status("RuuviTag data is missing")
            return "RuuviTag data missing"

        # if utime.time() - last_light >= 5:
        #     light.send_measurement(where,"light",light.readLight())
        #     last_light = utime.time()

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()
        else:
            print("mqtt.client is False")

        #Check WiFi status
        if wifi.wlan.isconnected() is not True or wifi.wlan.status() != 3:
            log("Wi-Fi down")
            log(f"wlan.isconnected(): {wifi.wlan.isconnected()}")
            log(f"wlan.status(): {wifi.wlan.status()}")
            restart("Wi-Fi Lost")

        utime.sleep(0.2)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
