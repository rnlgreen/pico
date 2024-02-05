"""Main routine for Pico6 (Garage door)"""
import time
from utils import door
from utils import mqtt
from utils import wifi
from utils.log import status
from utils import ruuvi

def get_status():
    """Get garage door status"""
    door.get_status()
    ruuvi.get_status()


def main():
    """pico 6 main routine"""
    while True:
        #Monitor the door status
        door.door()

        #Get RuuviTag readings, returns false if we haven't had any for a while
        if not ruuvi.get_readings():
            status("RuuviTag data missing")
            return "RuuviTag data missing"

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()
        else:
            return

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        #Wait a bit
        time.sleep(0.5)

if __name__ == "__main__":
    main()
