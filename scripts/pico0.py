"""pico0 main code"""
import gc # Garbage Collector
import time # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import mqtt
from utils import myid
#from utils import leds
#from utils import am2320
from utils import light
from utils import wifi
#from utils import trap
from utils.log import status
# from machine import I2C, Pin # type: ignore # pylint: disable=import-error
from utils import ruuvi

#Pins from left to right:
#1: Voltage in, 3-5 VDC
#2: SDA: I2C data in/out
#3: Ground
#4: SCL: I2C clock in

I2CID = 1
SDAPIN = 26 #GPIO26
SCLPIN = 27 #GPIO27
photoPIN = 28 #GPIO28 - has to be one of the ADC pins - defined in light module

# trap.traps = {
#         "Trap 1": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": False, "spring trigger": 0},
# }

last_temp = -1
last_humidity = -1
last_sent = 0

#Report current status of lights and sensors etc.
def get_status():
    # trap.get_status()
    # status(f"running: {leds.running}")
    # status(f"effect: {leds.effect}")
    # status(f"stop: {leds.stop}")
    # status(f"speed: {leds.speed}")
    # status(f"dyndelay: {leds.dyndelay}")
    # status(f"brightness: {leds.brightness}")
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    gc.collect()
    ruuvi.get_status()

    # #i2c sensor
    # i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=400000)
    # devices = i2c.scan()
    # if len(devices) == 0:
    #     status("No I2C device found")
    # elif len(devices) > 1:
    #     status("Multiple I2C devices found -")
    #     for d in devices:
    #         status(f"  0x{d:02X}")
    # else:
    #     status(f"I2C device found at 0x{devices[0]:02X}")
    # status(f"Latest temperature = {last_temp}")
    # status(f"Latest humidity: {last_humidity}")
    status(f"Light level: {light.readLight(photoPIN)}")

# #LED control function to accept commands and launch effects - called from main.py
# def led_control(command=""):
#     leds.led_control(command)

#Called my main.py
def main():
    # strip_type = "GRBW"
    # pixels = 16
    # GPIO = 0
    # leds.init_strip(strip_type,pixels,GPIO)

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

    last_light = time.time()

    #Main loop
    while True:
        # #Check the trap status
        # trap.trap()

        #Get and send a light reading
        # if utime.ticks_diff(utime.ticks_ms(),last_sent) >= 60000:
            # last_sent = utime.ticks_ms()
            # try:
            #     sensor.measure()
            #     light.send_measurement(where,"temperature",sensor.temperature())
            #     light.send_measurement(where,"humidity",sensor.humidity())
            #     last_temp = sensor.temperature()
            #     last_humidity = sensor.humidity()
            #     #status("Measurements sent")
            # except Exception as e: # pylint: disable=broad-exception-caught
            #     status(f"Exception: {e}")

        #Get RuuviTag readings, returns false if we haven't had any for a while
        #if not ruuvi.get_readings():
        #    status("RuuviTag data missing")
        #    return "RuuviTag data missing"

        if time.time() - last_light >= 0:
            lightlevel = light.readLight(photoPIN)
            light.send_measurement(where,"light",lightlevel)
            last_light = time.time()

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()
        else:
            print("mqtt.client is False")

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        time.sleep(0.5)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
