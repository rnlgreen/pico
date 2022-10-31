#pico3 main code
import time
import utils.mqtt as mqtt

def main():
    while True:
        #Check for messages
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(0.2)
    
if __name__ == "__main__":
    main()

