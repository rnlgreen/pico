#Main routine for all picos
import time
import machine # type: ignore

#Import my supporting code
import utils.myid as myid, utils.wifi as wifi, utils.mqtt as mqtt
from utils.blink import blink
import secrets

testmode = False

#Send alert 
def send_mqtt(topic,message):
    print("{}: {}".format(topic,message))
    if client != False:
        mqtt.send_mqtt(client,topic,message)

#Print and send status messages
def status(message):
    print(message)
    message = pico + ": " + message
    topic = 'pico/'+pico+'/status'
    send_mqtt(topic,message)

#Restart pico
def restart():
    status('Restarting ...')
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
#        numfiles = ftp.get_allfiles(session,".")
        numfiles = ftp.get_changedfiles(session,".")
        message = 'Copied ' + str(numfiles) + " files to root"
        status(message)
        #Get all files for utils (get_allfiles will deal with changing directory)
#        numfiles = ftp.get_allfiles(session,"utils")
        numfiles = ftp.get_changedfiles(session,"utils")
        message = 'Copied ' + str(numfiles) + " files to utils"
        status(message)
        ftp.quit(session)
        status("Reload complete".format(pico))
    else:
        message = "FTP error occurred"
        status(message)

#process incoming control commands
def on_message(topic, payload):
    print("Received topic: {} message: {}".format(str(topic.decode()),str(payload.decode())))
    if str(topic.decode()) == "pico/"+pico+"/control":
        if str(payload.decode()) == "blink":
            status("blinking")
            blink(0.1,0.1,5)
        elif str(payload.decode()) == "reload":
            reload()
        elif str(payload.decode()) == "restart":
            restart()
        else:
            status("Unknown command: {}".format(str(payload.decode())))
    elif str(topic.decode()) == "pico/"+pico+"/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        send_mqtt(heartbeat_topic,"Yes, I'm here")

#Get my ID
pico = myid.get_id()
print("I am {}".format(pico))

#Call wifi_connect with our hostname
ipaddr = wifi.wlan_connect(pico)
if ipaddr:
    #Try and connect to MQTT
    client = mqtt.mqtt_connect(client_id=pico)

    if client == False:
        status("We should probably reboot now...")
    else:
        #Say Hello
        status("connected on {}".format(ipaddr))
        #Subscribe to control and heartbeat channels
        client.set_callback(on_message) # type: ignore
        status("Subscribing to channels...")
        client.subscribe("pico/"+pico+"/control") # type: ignore
        client.subscribe("pico/"+pico+"/poll") # type: ignore

if not testmode:
    #Now load and call the specific code for this pico
    status("Loading main")
    main = __import__(pico)
    main.main(client)
