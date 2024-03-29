#Code for Pico2 - measure and report temperature and pressure
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from machine import I2C, Pin # type: ignore # pylint: disable=import-error
from utils import am2320
from utils import myid
from utils import mqtt
from utils import wifi
from utils.log import status
from utils import ruuvi
from utils import trap

do_I2C = False

if do_I2C:
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
    last_sent = 0

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
    ruuvi.get_status()
    trap.get_status()
    if do_I2C:
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
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member


def main():
    global last_temp, last_humidity, last_sent # pylint: disable=global-statement
    if do_I2C:
        try:
            i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=40000)
            sensor = am2320.AM2320(i2c)
        except Exception as e: # pylint: disable=broad-exception-caught
            status(f"Error setting up I2C: {e}")
            utime.sleep(3)
            return

    trap.traps = {
            "Trap 2": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0},
    }

    if do_I2C:
        last_sent = utime.ticks_add(utime.ticks_ms(),-60000)

    while True:
        trap.trap()
        if do_I2C:
            elapsed = utime.ticks_diff(utime.ticks_ms(),last_sent)
            if elapsed >= 60000:
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
                last_sent = utime.ticks_ms()

        #Get RuuviTag readings, returns false if we haven't had any for a while
        if not ruuvi.get_readings():
            status("RuuviTag data missing")
            return "RuuviTag data missing"

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        utime.sleep(0.5)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
