"""Main routine for Pico1"""
#Initialise the traps
import time
from utils import trap
from utils import mqtt
from utils import wifi
from machine import Pin # type: ignore # pylint: disable=import-error

def get_status():
    """get trap status"""
    trap.get_status()

def main():
    """Main loop for pico1 - mouse trap"""
    trap.traps = {
            "Trap 2": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0},
    }
    while True:
        #Check the traps
        trap.trap()

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        #Wait a bit
        time.sleep(0.2)

if __name__ == "__main__":
    main()
