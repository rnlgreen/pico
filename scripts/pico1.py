"""Main routine for Pico1"""
#Initialise the traps
import time
from utils import trap
from utils import mqtt
from utils import wifi
from utils.log import log
from utils.control import restart

def get_status():
    """get trap status"""
    trap.get_status()

def main():
    """Main loop for pico1 - mouse trap"""
    while True:
        #Check the traps
        trap.trap()
        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()
        #Check WiFi status
        if wifi.wlan.isconnected() is not True or wifi.wlan.status() != 3:
            log("Wi-Fi down")
            log(f"wlan.isconnected(): {wifi.wlan.isconnected()}")
            log(f"wlan.status(): {wifi.wlan.status()}")
            restart("Wi-Fi Lost")

        #Wait a bit
        time.sleep(0.2)

if __name__ == "__main__":
    main()
