#pico3 main code
import time

def main(client = False):
    while True:
        #Check for messages
        if client != False:
            client.check_msg() 
        time.sleep(0.2)
    
if __name__ == "__main__":
    main()

