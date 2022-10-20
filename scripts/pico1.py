#Main routine for Pico1
#Initialise the traps
from time import sleep
import trap

while True:
    #Check the traps
    trap.trap()
    #Check for messages
    client.check_msg() # type: ignore
    #Wait a bit
    sleep(0.2)
