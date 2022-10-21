#Main routine for Pico1
#Initialise the traps
import time
import trap

def main(client):
    while True:
        #Check the traps
        trap.trap()
        #Check for messages
        if client != False:
            client.check_msg() # type: ignore
        #Wait a bit
        time.sleep(0.2)
