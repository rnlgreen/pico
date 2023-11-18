"""Main routine for all picos"""
import time
import gc
import secrets
from machine import reset # pylint: disable=import-error # type: ignore

#Import my supporting code
from utils import myid
from utils import wifi
from utils import mqtt
from utils import ntp
from utils import ftp
from utils import slack
from utils.blink import blink
from utils.timeutils import strftime, uptime
import uos # pylint: disable=import-error # type: ignore

TESTMODE = False
EXCEPTION_FILE = "exception.txt"

#Send message with specific topic
def send_mqtt(topic,message):
    """Function for sending MQTT message."""
    print(f"{topic}: {message}")
    if mqtt.client is not False:
        try:
            mqtt.send_mqtt(topic,message)
        except Exception as e: # pylint: disable=broad-except
            log_exception(e)

#Print and send status messages
def status(message):
    """Function for reporting status."""
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client is not False:
        try:
            mqtt.send_mqtt(topic,message)
        except Exception as e: # pylint: disable=broad-except
            log_exception(e)

def log(message):
    """Function to write status message to exception logfile"""
    try:
        file = open(EXCEPTION_FILE,"at",encoding="utf-8")
        file.write(f"{strftime()}: {pico} {message}\n")
        file.close()
    except Exception: # pylint: disable=broad-except
        status("Unable to log message to file")

#Restart pico
def restart(reason):
    """Function to restart the pico"""
    status(f'Restarting: {reason}')
    log(f"Restarting: {reason}")
    if mqtt.client is not False:
        try:
            mqtt.client.disconnect()
        except Exception as e: # pylint: disable=broad-except
            log_exception(e)
    time.sleep(1)
    reset()

#Function to check for new code and download it from FTP site
def reload():
    """Function to reload new code if there is any"""
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
            ftp.ftpquit(session)
            if totalfiles > 0:
                status("Reload complete")
            else:
                status("No new files found")
        else:
            message = "FTP error occurred"
            status(message)
    except Exception as e: # pylint: disable=broad-except
        log_exception(e)
    return totalfiles

#Check if a local file exists
def file_exists(filename):
    """Function to test if a file exists"""
    try:
        return (uos.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False

def log_exception(e):
    """Function to log exceptions to file"""
    import io  #pylint: disable=import-outside-toplevel
    import sys #pylint: disable=import-outside-toplevel
    output = io.StringIO()
    sys.print_exception(e, output) # pylint: disable=maybe-no-member
    exception1=output.getvalue()
    #Write exception to logfile
    print("Writing exception to storage")
    try:
        file = open(EXCEPTION_FILE,"at",encoding="utf-8")
        file.write(f"{strftime()}: {pico} detected exception:\n{e}:{exception1}")
        file.close()
    except Exception as f: # pylint: disable=broad-except
        output2 = io.StringIO()
        sys.print_exception(f, output2) # pylint: disable=maybe-no-member
        print(f"Failed to write exception:\n{output2.getvalue()}")
    #Try sending the original exception to MQTT
    try:
        status(f"Caught exception:\n{exception1}")
    except Exception: # pylint: disable=broad-except
        pass
    return exception1

#Check if there is a local exception file from before and copy to FTP site
def report_exceptions():
    """Function to upload exception files via FTP"""
    print("Checking for exception file")
    if file_exists(EXCEPTION_FILE):
        status("Uploading exception file")
        #import os
        try:
            session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
            if session:
                ftp.cwd(session,'/pico/logs')
                ftp.put_binaryfile(session,".",EXCEPTION_FILE)
                ftp.ftpquit(session)
                #os.remove(EXCEPTION_FILE)
        except Exception as e: # pylint: disable=broad-except
            log_exception(e)

def clear_log():
    """Function to clear the local exception log"""
    try:
        file = open(EXCEPTION_FILE,"wt",encoding="utf-8")
        file.write(f"{strftime()}: {pico} Cleared exception log\n")
        file.close()
        report_exceptions()
    except Exception: # pylint: disable=broad-except
        pass

#Attempt NTP sync
def do_ntp_sync():
    """Function to do NTP Time Sync"""
    #Sync the time up
    if not ntp.set_time():
        status("Failed to set time")
        return False
    else:
        status(f"{strftime()}")
        return True

#process incoming control commands
def on_message(topic, payload):
    """Process incoming MQTT messages"""
    topic = str(topic.decode())
    payload = str(payload.decode())
    print(f"Received topic: {topic} message: {payload}")
    if topic == "pico/"+pico+"/control" or topic == "pico/all/control":
        command = payload
        if command == "blink":
            status("blinking")
            blink(0.1,0.1,5)
        elif command == "reload":
            reload()
        elif command == "restart":
            restart("Remote control")
        elif command == "datetime":
            thetime = strftime()
            status(f"Time is: {thetime}")
        elif command == "uptime":
            status(f"Uptime: {uptime(timeInit)}")
        elif command == "status":
            status(f"Uptime: {uptime(timeInit)}")
            main.get_status()
        elif command == "clear":
            status("Clearing exception log")
            clear_log()
        else:
            status(f"Unknown command: {payload}")
    elif topic == "pico/lights":
        main.led_control(payload)
    elif topic == "pico/lights/auto":
        main.led_control("auto",payload)
    elif topic == "pico/lights/boost":
        main.led_control("boost",payload)
    elif topic == "pico/poll":
        heartbeat_topic = "pico/"+pico+"/heartbeat"
        send_mqtt(heartbeat_topic,"Yes, I'm here")


### INITIALISATION STEPS ###
#Blink the LED to show we're starting up
blink(0.1,0.1,3)

#Get my ID (e.g. 'pico0', based on the MAC address of this device)
pico = myid.get_id()

print(f"I am {pico}")

#Call wifi_connect with our hostname; my routine tries multiple times to connect
ipaddr = wifi.wlan_connect(pico)

#If we got an IP address we can update code adn setup MQTT connection and subscriptions
if ipaddr:
    #Check for previous exceptions logged locally and report them
    report_exceptions()

    #Try and connect to MQTT
    mqtt.mqtt_connect(client_id=pico)
    status(f"Wi-Fi: {ipaddr}")

    status("Attempting time sync")
    ntp_sync = do_ntp_sync() # pylint: disable=invalid-name

    blink(0.1,0.1,4)

    #Get latest code by calling reload(); it returns the number of files updated
    if reload() > 0:
        status("New code loaded")
        slack.send_msg(pico,":repeat: Restarting to load new code")
        restart("New code")

    #If we managed to connect MQTT then subscribe to the relevant channels
    if mqtt.client is False:
        status("MQTT Connection failed")
        restart("No MQTT Connection")
    else:
        #Subscribe to control and heartbeat channels
        status("Subscribing to MQTT")
        mqtt.client.set_callback(on_message) # type: ignore
        mqtt.client.subscribe("pico/"+pico+"/control") # type: ignore
        mqtt.client.subscribe("pico/all/control") # type: ignore
        mqtt.client.subscribe("pico/poll") # type: ignore

    #Let Slack know we're up
    print("Posting to Slack")
    slack.send_msg(pico,f":up: {pico} is up")
else:
    #not sure what to do here, keep rebooting indefinitely until we get a Wi-Fi connection?
    #or attempt to run the pico code anyway regardless of having no Wi-Fi?
    #or maybe just drop out? Probably not this option
    restart("No Wifi")

if not TESTMODE:
    #Blink the LED to say we're here
    blink(0.2,0.2,5)

    #Have another go at syncing the time if that failed during initialisation
    if ipaddr and not ntp_sync:
        #Retry NTP sync
        ntp_sync = do_ntp_sync() # pylint: disable=invalid-name

    #Assuming we have the time now get the init time
    timeInit = time.time()

    #Now load and call the specific code for this pico
    status("Loading main")
    log("Loading main")

    #Upload latest log
    report_exceptions()

    try:
        main = __import__(pico)
        gc.collect()
        #status("Free memory: {}".format(gc.mem_free()))
        main.main()
    #Catch any exceptions detected by the pico specific code
    except Exception as oops: # pylint: disable=broad-except
        exception = log_exception(oops)
        #Now pause a while then restart
        time.sleep(10)
        #Assume MQTT might be broken so don't try and send the restarting message
        mqtt.client = False
        try:
            slack.send_msg(pico,f":fire: Restarting after exception:\n{exception}")
        except Exception as oops2: # pylint: disable=broad-except
            pass
        restart("Exception")
    restart("Dropped through")
