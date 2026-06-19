#Code for Pico7
#Playroom console under lighting (2 strips)
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import myid
from utils import mqtt
from utils import wifi
from utils.log import status, debug
from utils import ruuvi
from utils import leds
from utils.common import off, new_brightness
from utils import settings
from utils.uping import ping
from utils.control import restart

def get_status():
    wifi.wifi_status()
    gc.collect()
    status(f"latest_heartbeat: {latest_heartbeat}")
    status(f"heartbeat_check: {heartbeat_check()}")
    status(f"xbox: {check_xbox()}")
    status(f"lightsoff: {settings.lightsoff}")
    status(f"brightness: {settings.brightness}")
    status(f"colour: {settings.colour}")
    status(f"hue: {settings.hue}")
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    ruuvi.get_status()

#LED control function to accept commands and launch effects
def led_control(topic,payload):
    global latest_heartbeat # pylint: disable=global-statement
    latest_heartbeat = utime.time()
    leds.led_control(topic,payload)

#Called by main.py when it receives heartbeat topic from pico2w0
def heartbeat():
    global latest_heartbeat # pylint: disable=global-statement
    latest_heartbeat = utime.time()

def heartbeat_check():
    if latest_heartbeat < utime.time() - 305:
        #status("Heartbeat not seen in 300 seconds")
        return False
    return True

def check_xbox():
    try:
        _, recv = ping('10.0.2.195')
        #status(f"Ping sent: {sent}, received: {recv}")
        if recv > 0:
            return True
        else:
#            sent, recv = ping('xantus2')
#            if recv > 0:
#                return True
            return False
    except Exception as e: # pylint: disable=broad-except
        status(f"Ping exception in check_xbox: {e}", logit=True)
        restart("Ping exception in check_xbox")
        return False

def xlights(on_or_off):
    if mqtt.client is not False:
        topic = 'pico/xlights' # xlights are the backlights on the playdesk managed by pico2w0
        if on_or_off == "on":
            message = "brightness:50"
            status("Turning xbox lights on", logit=True)
        else:
            message = "off"
            status("Turning xbox lights off", logit=True)
        mqtt.send_mqtt(topic,message)
    else:
        status("MQTT client not connected, can't send xlights command", logit=True)

def debug_logging():
    debug(f"lightsoff: {settings.lightsoff}")
    debug(f"pico2w0 heartbeat: {heartbeat_check()}")
    debug(f"xbox on: {check_xbox()}")
    debug(f"time since on: {utime.time() - settings.time_on}")

def main():
    standalone = False
    #debug_logging()
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
        #debug_logging()

        #Get RuuviTag readings, returns false if we haven't had any for a while
        if not ruuvi.get_readings():
            status("RuuviTag data missing")
            return "RuuviTag data missing"

        if not standalone:
            #Check we've seen a heartbeat from pico2w0 recently, otherwise turn the lights off
            if not settings.lightsoff and not heartbeat_check():
                status("Turning lights off, pico2w0 heartbeat not seen in 300 seconds", logit=True)
                off()

            #Check for Xbox Off if the lights are on and we've been up for 90 seconds
            if not settings.lightsoff and (utime.time() - settings.time_on) > 90 and not check_xbox():
                status("Xbox is off, turning lights off!", logit=True)
                led_control("plights","off")
                xlights("off")

            #Check for Xbox On
            if check_xbox():
                if settings.lightsoff: #If the lights were off then set the brightness and make sure the rear lights are on
                    status("Xbox is on, turning lights on!", logit=True)
                    new_brightness(30)
                    xlights("on") # turns on the background lights on the playdesk via pico2w0
                    xlights("brightness:50") # sets the brightness of the background lights on the playdesk via pico2w0
                    xlights("rainbow") # run the rainbow effect on the background lights
                    led_control("plights","playdesk") # turns on the playdesk lights via pico7 (me)

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        utime.sleep(1)

pico = myid.get_id()
where = myid.where[pico]
latest_heartbeat = utime.time()

if __name__ == "__main__":
    main()
