#Main routine for all picos
import time
import _thread
import machine # type: ignore

#Import my supporting code
import utils.myid as myid, utils.wifi as wifi, utils.mqtt as mqtt
from utils.blink import blink

#Get my ID
pico = myid.get_id()
print("I am {}".format(pico))

#Call wifi_connect with our hostname
wifi_connected = wifi.wlan_connect(pico)

#Send alert 
def send_mqtt(topic,message):
    print("{}: {}".format(topic,message))
    if client != False:
        mqtt.send_mqtt(client,topic,message)

def restart():
    print('Restarting {} ...'.format(pico))
    topic = 'pico/'+pico+'/status'
    message = pico + " restarting in 5 seconds..."
    send_mqtt(topic,message)
    time.sleep(5)
    machine.reset()

def reload():
    print("Fetching latest code...")
    topic = 'pico/'+pico+'/status'
    message = pico + " fetching latest code..."
    send_mqtt(topic,message)
    import utils.ftp as ftp
    topic = 'pico/'+pico+'/status'
    #Move to the root FTP folder
    ftp.cwd('pico/scripts')
    #Get all files for the root
    numfiles = ftp.get_allfiles(".")
    message = pico + ' copied ' + str(numfiles) + " files to root"
    send_mqtt(topic,message)
    #Get all files for utils (get_allfiles will deal with changing directory)
    numfiles = ftp.get_allfiles("utils")
    message = pico + ' copied ' + str(numfiles) + " files to utils"
    send_mqtt(topic,message)
    ftp.quit()

#define callback
def on_message(topic, payload):
    print("Received topic: {} message: {}".format(str(topic.decode()),str(payload.decode())))
    if str(topic.decode()) == "pico/"+pico+"/control":
        if str(payload.decode()) == "blink":
            blink(0.25,0.25)
        elif str(payload.decode()) == "reload":
            reload()
        elif str(payload.decode()) == "restart":
            restart()
        else:
            print("Unknown command: {}".format(str(payload.decode())))
    elif str(topic.decode()) == "pico/"+pico+"/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        send_mqtt(heartbeat_topic,"Yes, I'm here")

#Try and connect to MQTT
client = mqtt.mqtt_connect(client_id=pico)

if client == False:
    print("We should probably reboot now...")
else:
    #Say Hello
    topic = 'pico/'+pico+'/status'
    message = pico + ' is Alive!'

    send_mqtt(topic,message)

    #Subscribe to control and heartbeat channels
    client.set_callback(on_message) # type: ignore
    print("Subscribing to channels...")
    client.subscribe("pico/"+pico+"/control") # type: ignore
    client.subscribe("pico/"+pico+"/poll") # type: ignore

#Now load and call the specific code for this pico
main = __import__(pico)
main.main()
