#Main routine for Pico1
#Initialise the traps
import time
import trap
import utils.mqtt as mqtt

def get_status():
    trap.get_status()

def main():
    while True:
        #Check the traps
        trap.trap()
        #Check for messages
        if mqtt.client != False:
            mqtt.client.check_msg() 
        #Wait a bit
        time.sleep(0.2)

if __name__ == "__main__":
    main()
