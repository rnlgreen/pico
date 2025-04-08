#Code for Pico7 - measure and report temperature and pressure, and play desk lighting
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import myid
from utils import mqtt
from utils import wifi
from utils.log import status
from utils import ruuvi
from utils import leds
from utils.common import off, new_brightness
from utils import settings
from utils.uping import ping

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
    status(f"brightness: {settings.brightness}")
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    ruuvi.get_status()

#LED control function to accept commands and launch effects
def led_control(topic,payload):
    global latest_heartbeat # pylint: disable=global-statement
    latest_heartbeat = utime.time()
    leds.led_control(topic,payload)

def heartbeat():
    global latest_heartbeat # pylint: disable=global-statement
    latest_heartbeat = utime.time()

def heartbeat_check():
    if latest_heartbeat < utime.time() - 305:
        status("Heartbeat not seen in 300 seconds")
        return False
    return True

def check_xbox():
    sent, recv = ping('xantus')
    if recv > 0:
        return True
    else:
        return False

def xlights(on_or_off):
    if mqtt.client is not False:
        topic = 'pico/xlights'
        if on_or_off == "on":
            message = "brightness:50"
            status("Turning xbox lights on")
        else:
            message = "brightness:0"
            status("Turning xbox lights off")
        try:
            mqtt.send_mqtt(topic,message)
        except Exception: # pylint: disable=broad-except
            mqtt.client = False # just adding this in here to try and avoid a failure loop

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

        #Check for Xbox Off
        if not settings.lightsoff and (utime.time() - settings.time_on) > 90 and not check_xbox():
            status("Xbox not on")
            off()
            xlights("off")

        #Check for Xbox On
        if settings.lightsoff and check_xbox():
            status("Xbox is on!")
            new_brightness(30)
            xlights("on")

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        utime.sleep(5)

pico = myid.get_id()
where = myid.where[pico]
latest_heartbeat = utime.time()

if __name__ == "__main__":
    main()
