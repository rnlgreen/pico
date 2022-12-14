#Main routine for all picos
import time
import gc
from machine import reset, RTC as rtc # type: ignore

#Import my supporting code
import utils.myid as myid
import utils.wifi as wifi
import utils.mqtt as mqtt
import utils.ntp as ntp
from utils.blink import blink
import secrets

testmode = False

#Send message with specific topic
def send_mqtt(topic,message):
    print("{}: {}".format(topic,message))
    if mqtt.client != False:
        mqtt.send_mqtt(topic,message)

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client != False:
        mqtt.send_mqtt(topic,message)

#Restart pico
def restart():
    status('Restarting ...')
    if mqtt.client != False:
        mqtt.client.disconnect()
    time.sleep(1)
    reset()

def reload():
    status("Fetching latest code...")
    totalfiles = 0
    import utils.ftp as ftp
    try:
        session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
        status("Comparing files...")
        if session:
            #Get all files for the root
            #Move to the root FTP folder
            ftp.cwd(session,'/pico/scripts')
            numfiles = ftp.get_changedfiles(session,".")
            totalfiles += numfiles
            message = 'Copied ' + str(numfiles) + " files to root"
            status(message)
            #Get all files for utils (get_allfiles will deal with changing directory)
            #Move back to the root FTP folder
            ftp.cwd(session,'/pico/scripts')
            numfiles = ftp.get_changedfiles(session,"utils")
            totalfiles += numfiles
            message = 'Copied ' + str(numfiles) + " files to utils"
            status(message)
            #Get all files for lib (get_allfiles will deal with changing directory)
            #Move back to the root FTP folder
            ftp.cwd(session,'/pico/scripts')
            numfiles = ftp.get_changedfiles(session,"lib")
            totalfiles += numfiles
            message = 'Copied ' + str(numfiles) + " files to lib"
            status(message)
            ftp.quit(session)
            status("Reload complete".format(pico))
        else:
            message = "FTP error occurred"
            status(message)
    except Exception as e:
        status("Exception occurred: {}".format(e))
    return totalfiles

#Return formatted time string
def strftime():
    timestamp=rtc().datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

#process incoming control commands
def on_message(topic, payload):
    topic = str(topic.decode())
    payload = str(payload.decode())
    print("Received topic: {} message: {}".format(topic,payload))
    if topic == "pico/"+pico+"/control" or topic == "pico/all/control":
        command = payload
        if command == "blink":
            status("blinking")
            blink(0.1,0.1,5)
        elif command == "reload":
            reload()
        elif command == "restart":
            restart()
        elif command == "datetime":
            thetime = strftime()
            status("Time is: {}".format(thetime))
        elif command == "status":
            main.get_status()
        else:
            status("Unknown command: {}".format(payload))
    elif topic == "pico/lights":
        main.led_control(payload)
    elif topic == "pico/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        send_mqtt(heartbeat_topic,"Yes, I'm here")

#Get my ID
pico = myid.get_id()
print("I am {}".format(pico))

#Call wifi_connect with our hostname
ipaddr = wifi.wlan_connect(pico)
if ipaddr:
    #Try and connect to MQTT
    mqtt.mqtt_connect(client_id=pico)
    status("Wi-Fi connected on {}".format(ipaddr))

    status("Attempting time sync...")
    #Sync the time up
    if not ntp.set_time():
        status("Failed to set the time")
    else:
        status("Booted at {}".format(strftime()))

    #Get latest code
    if reload() > 0:
        status("New code loaded")
        restart()

    if mqtt.client == False:
        status("MQTT Connection failed...")
    else:
        #Subscribe to control and heartbeat channels
        status("Subscribing to channels...")
        mqtt.client.set_callback(on_message) # type: ignore
        mqtt.client.subscribe("pico/"+pico+"/control") # type: ignore
        mqtt.client.subscribe("pico/all/control") # type: ignore
        mqtt.client.subscribe("pico/poll") # type: ignore

if not testmode:
    #Now load and call the specific code for this pico
    status("Loading main")
    try:
        main = __import__(pico)
        gc.collect()
        status("Free memory: {}".format(gc.mem_free()))
        main.main()
    except Exception as e:
        import io
        import sys
        output = io.StringIO()
        #status("main.py caught exception: {}".format(e))
        sys.print_exception(e, output)
        status("Main caught exception:\n{}".format(output.getvalue()))
        #Now pause a while then restart
        time.sleep(10)
        #Assume MQTT might be broken
        mqtt.client = False
        restart()