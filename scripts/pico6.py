#Main routine for Pico6 (Garage door)
import time
import utils.door as door
import utils.mqtt as mqtt

def get_status():
    door.get_status()

def main():
    while True:
        #Monitor the door status
        door.door()
        #Check for messages
        if mqtt.client != False:
            mqtt.client.check_msg() 
        #Wait a bit
        time.sleep(0.2)

if __name__ == "__main__":
    main()
