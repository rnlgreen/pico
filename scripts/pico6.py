"""Main routine for Pico6 (Garage door)"""
import time
from utils import door
from utils import mqtt
from utils import wifi
from utils.log import log
from utils.control import restart

def get_status():
    """Get garage door status"""
    door.get_status()

def main():
    """pico 6 main routine"""
    while True:
        #Monitor the door status
        door.door()
        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()
        else:
            return
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
