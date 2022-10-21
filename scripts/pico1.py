#Main routine for Pico1
#Initialise the traps
import time
import trap

def main(client = False):
    while True:
        #Check the traps
        trap.trap()
        #Check for messages
        if client != False:
            client.check_msg() 
        #Wait a bit
        time.sleep(0.2)

if __name__ == "__main__":
    main()
