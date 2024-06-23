"""Main routine for Pico9"""
#Initialise the traps
import time
from utils import mqtt
from utils import wifi

def get_status():
    return

def main():
    while True:
        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        #Wait a bit
        time.sleep(0.5)

if __name__ == "__main__":
    main()
