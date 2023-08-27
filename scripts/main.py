#Main routine for all picos
import time
import gc
from machine import reset, RTC as rtc # type: ignore

#Import my supporting code
import utils.myid as myid
import utils.wifi as wifi
import utils.mqtt as mqtt
import utils.ntp as ntp
import utils.ftp as ftp
import utils.slack as slack
from utils.blink import blink
import secrets
import uos # type: ignore

testmode = False
EXCEPTION_FILE = "exception.txt"

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
    status('Restarting ')
    if mqtt.client != False:
        mqtt.client.disconnect()
    time.sleep(1)
    reset()

#Function to check for new code and download it from FTP site
def reload():
    status("Checking for new code")
    totalfiles = 0
    try:
        session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
        #status("Comparing files")
        if session:
            #Check all the folders for new files
            for source in (".", "utils", "lib"):
                ftp.cwd(session,'/pico/scripts')
                numfiles = ftp.get_changedfiles(session,source)
                totalfiles += numfiles
                #message = 'Copied ' + str(numfiles) + " files to " + source
                #if numfiles > 0:
                #    status(message)
            ftp.quit(session)
            if totalfiles > 0:
                status("Reload complete".format(pico))
            else:
                status("No new files found")
        else:
            message = "FTP error occurred"
            status(message)
    except Exception as e:
        status("Exception occurred: {}".format(e))
    return totalfiles

#Check if a local file exists
def file_exists(filename):
    try:
        return (uos.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False

#Check if there is a local exception file from before and copy to FTP site
def report_exceptions():
    print("Checking for exception file")
    if file_exists(EXCEPTION_FILE):
        status("Uploading exception file")
        import os
        try:
            session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
            if session:
                ftp.cwd(session,'/pico/logs')
                ftp.put_binaryfile(session,".",EXCEPTION_FILE)
                ftp.quit(session)
                os.remove(EXCEPTION_FILE)
        except Exception as e:
            status("Exception occurred: {}".format(e))

#Return formatted time string
def strftime():
    timestamp=rtc().datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

#Attempt NTP sync
def do_ntp_sync():
    #Sync the time up
    if not ntp.set_time():
        status("Failed to set time")
        return False
    else:
        status("{}".format(strftime()))
        return True

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
    elif topic == "pico/lights/auto":
        main.led_control("auto",payload)
    elif topic == "pico/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        send_mqtt(heartbeat_topic,"Yes, I'm here")


### INITIALISATION STEPS ###
#Blink the LED to show we're starting up
blink(0.1,0.1,3)

#Get my ID (e.g. 'pico0', based on the MAC address of this device)
pico = myid.get_id()

print("I am {}".format(pico))

#Call wifi_connect with our hostname; my routine tries multiple times to connect 
ipaddr = wifi.wlan_connect(pico)

#If we got an IP address we can update code adn setup MQTT connection and subscriptions
if ipaddr:
    #Try and connect to MQTT
    mqtt.mqtt_connect(client_id=pico)
    status("Wi-Fi: {}".format(ipaddr))

    status("Attempting time sync")
    ntp_sync = do_ntp_sync()

    blink(0.1,0.1,4)

    #Get latest code by calling reload(); it returns the number of files updated
    if reload() > 0:
        status("New code loaded")
        slack.send_msg(pico,":repeat: Restarting to load new code")
        restart()

    #If we managed to connect MQTT then subscribe to the relevant channels
    if mqtt.client == False:
        status("MQTT Connection failed")
    else:
        #Subscribe to control and heartbeat channels
        status("Subscribing to MQTT")
        mqtt.client.set_callback(on_message) # type: ignore
        mqtt.client.subscribe("pico/"+pico+"/control") # type: ignore
        mqtt.client.subscribe("pico/all/control") # type: ignore
        mqtt.client.subscribe("pico/poll") # type: ignore

    #Check for previous exceptions logged locally and report them
    report_exceptions()

    #Let Slack know we're up
    print("Posting to Slack")
    slack.send_msg(pico,f":up: {pico} is up")
else:
    #not sure what to do here, keep rebooting indefinitely until we get a Wi-Fi connection? 
    #or attempt to run the pico code anyway regardless of having no Wi-Fi?
    #or maybe just drop out? Probably not this option
    pass

if not testmode:
    #Blink the LED to say we're here
    blink(0.2,0.2,5)

    #Have another go at syncing the time if that failed during initialisation
    if ipaddr and not ntp_sync:
        #Retry NTP sync
        ntp_sync = do_ntp_sync()

    #Now load and call the specific code for this pico
    status("Loading main")
    try:
        main = __import__(pico)
        gc.collect()
        #status("Free memory: {}".format(gc.mem_free()))
        main.main()
    #Catch any exceptions detected by the pico specific code
    except Exception as e:
        import io
        import sys
        output = io.StringIO()
        sys.print_exception(e, output)
        exception1=output.getvalue()
        #Write exception to logfile
        print("Writing exception to storage")
        try:
            file = open(EXCEPTION_FILE,"w")
            file.write(f"{strftime()}: {pico} detected exception:\n{e}:{exception1}")
            file.close()
        except Exception as f:
            output2 = io.StringIO()
            sys.print_exception(f, output2)
            print("Failed to write exception:\n{}".format(output2.getvalue()))
        #Try sending the original exception to MQTT
        try:
            status("Main caught exception:\n{}".format(exception1))
        except:
            pass
        #Now pause a while then restart
        time.sleep(10)
        #Assume MQTT might be broken so don't try and send the restarting message
        mqtt.client = False
        try:
            slack.send_msg(pico,f":fire: Restarting after exception {output}")
        except:
            pass
        restart()
