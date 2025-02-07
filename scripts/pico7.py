#Code for Pico2 - measure and report temperature and pressure
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import myid
from utils import mqtt
from utils import wifi
from utils.log import status
from utils import ruuvi
from utils import leds

#Send alert
def send_mqtt(topic,message):
    print(f"{topic}: {message}")
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

#Return i2cscan to status commands
def get_status():
    gc.collect()
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    ruuvi.get_status()

#LED control function to accept commands and launch effects
def led_control(topic,payload):
    leds.led_control(topic,payload)

def main():
    strip_type = "GRB"
    pixels = 60 #need strips to be the same length, for now...
    GPIO1 = 28
    GPIO2 = 27
    leds.init_strip(strip_type,pixels,GPIO1)
    leds.init_strip(strip_type,pixels,GPIO2,True) # True says we are setting up strip2

    if mqtt.client is not False:
        mqtt.client.subscribe("pico/plights") # type: ignore

    while True:
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
