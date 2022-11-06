#pico3 main code
import time
import utils.mqtt as mqtt
import utils.myid as myid

#Print and send status messages
def status(message):
    print(message)
    message = pico + ": " + message
    topic = 'pico/'+pico+'/status'
    mqtt.send_mqtt(topic,message)

#Called my main.py
def main():
    while True:
        #Check for messages
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(0.2)

#Return status
def get_status():
    status("I'm here")

pico = myid.get_id()

if __name__ == "__main__":
    main()

