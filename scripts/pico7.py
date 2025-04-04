#Code for Pico7 - measure and report temperature and pressure, and play desk lighting
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import myid
from utils import mqtt
from utils import wifi
from utils.log import status
from utils import ruuvi
from utils import leds
from utils.common import off
from utils import settings

#Send alert
def send_mqtt(topic,message):
    print(f"{topic}: {message}")
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

#Return i2cscan to status commands
def get_status():
    gc.collect()
    status(f"latest_heartbeat: {latest_heartbeat}")
    status(f"heartbeat_check: {heartbeat_check()}")
    status(f"lightsoff: {settings.lightsoff}")
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    ruuvi.get_status()

#LED control function to accept commands and launch effects
def led_control(topic,payload):
    leds.led_control(topic,payload)

def heartbeat():
    global latest_heartbeat # pylint: disable=global-statement
    latest_heartbeat = utime.time()

def heartbeat_check():
    if latest_heartbeat < utime.time() - 300:
        status("Heartbeat not seen in 300 seconds")
        return False
    return True

def main():
    strip_type = "GRB"
    pixels = 60 #need strips to be the same length, for now...
    GPIO1 = 28
    GPIO2 = 27
    leds.init_strip(strip_type,pixels,GPIO1)
    leds.init_strip(strip_type,pixels,GPIO2,True) # True says we are setting up strip2

    if mqtt.client is not False:
        mqtt.client.subscribe("pico/plights") # control commands for the playdesk lights
        mqtt.client.subscribe("pico/pico2w0/heartbeat") # monitor heartbeat to see if power is on or not

    while True:
        #Get RuuviTag readings, returns false if we haven't had any for a while
        if not ruuvi.get_readings():
            status("RuuviTag data missing")
            return "RuuviTag data missing"

        #Check we've seen a heartbeat from pico2w0 recently, otherwise turn the lights off
        if not settings.lightsoff and not heartbeat_check():
            status("Turning lights off")
            off()

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        utime.sleep(0.5)

pico = myid.get_id()
where = myid.where[pico]
latest_heartbeat = utime.time()

if __name__ == "__main__":
    main()
