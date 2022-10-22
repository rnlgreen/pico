#Main routine for all picos
import time
import machine # type: ignore

#Import my supporting code
import utils.myid as myid, utils.wifi as wifi, utils.mqtt as mqtt
from utils.blink import blink
import secrets

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

#Print and send status messages
def status(message):
    print(message)
    topic = 'pico/'+pico+'/status'
    send_mqtt(topic,message)

#Restart pico
def restart():
    status('Restarting {} ...'.format(pico))
    time.sleep(1)
    machine.reset()

def reload():
    status("Fetching latest code...")
    import utils.ftp as ftp
    session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
    status("Established FTP session, copying files...")
    if session:
        #Move to the root FTP folder
        ftp.cwd(session,'/pico/scripts')
        #Get all files for the root
        numfiles = ftp.get_allfiles(session,".")
        message = pico + ' copied ' + str(numfiles) + " files to root"
        status(message)
        #Get all files for utils (get_allfiles will deal with changing directory)
        numfiles = ftp.get_allfiles(session,"utils")
        message = pico + ' copied ' + str(numfiles) + " files to utils"
        status(message)
        ftp.quit(session)
    else:
        message = pico + " FTP error occurred"
        status(message)

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
            status("Unknown command: {}".format(str(payload.decode())))
    elif str(topic.decode()) == "pico/"+pico+"/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        send_mqtt(heartbeat_topic,"Yes, I'm here")

#Try and connect to MQTT
client = mqtt.mqtt_connect(client_id=pico)

if client == False:
    status("We should probably reboot now...")
else:
    #Say Hello
    message = pico + ' is Alive!'
    status(message)
    #Subscribe to control and heartbeat channels
    client.set_callback(on_message) # type: ignore
    status("Subscribing to channels...")
    client.subscribe("pico/"+pico+"/control") # type: ignore
    client.subscribe("pico/"+pico+"/poll") # type: ignore

#Now load and call the specific code for this pico
status("Loading main for {}".format(pico))
main = __import__(pico)
main.main(client)
