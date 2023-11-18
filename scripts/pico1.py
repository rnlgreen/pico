"""Main routine for Pico1"""
#Initialise the traps
import time
from utils import trap
from utils import mqtt

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
        #Wait a bit
        time.sleep(0.2)

if __name__ == "__main__":
    main()
