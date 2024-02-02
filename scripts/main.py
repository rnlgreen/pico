"""Main routine for all picos"""
import time
import gc
import secrets

#Import my supporting code
from utils import myid
from utils import wifi
from utils import mqtt
from utils import ntp
from utils import ftp
from utils import slack
from utils.blink import blink
from utils.timeutils import strftime, uptime
from utils import log
from utils.control import restart
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
            log.log_exception(e)

#Check if a local file exists
def file_exists(filename):
    """Function to test if a file exists"""
    try:
        return (uos.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False

#Check if a local folder exists
def dir_exists(foldername):
    """Function to test if a file exists"""
    try:
        return (uos.stat(foldername)[0] & 0x8000) == 0
    except OSError:
        return False

#Function to check for new code and download it from FTP site
def reload():
    """Function to reload new code if there is any"""
    # log.status("Checking for new code")
    totalfiles = 0
    try:
        session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
        if session:
            #Check all the folders for new files
            folders = ["."]
            ftp.cwd(session,'/pico/scripts')
            folders += ftp.list_folders(session)
            print(f"Got list of folders: {folders}")
            for source in (folders):
                ftp.cwd(session,'/pico/scripts')
                if not dir_exists(source):
                    log.status(f"Creating new folder {source}", True)
                    uos.mkdir(source)
                numfiles = ftp.get_changedfiles(session,source)
                totalfiles += numfiles
            ftp.ftpquit(session)
            if totalfiles > 0:
                log.status(f"Updated {totalfiles} files")
            else:
                pass
                #log.status("No new files found")
        else:
            message = "FTP error occurred"
            log.status(message)
    except Exception as e: # pylint: disable=broad-except
        log.log_exception(e)
    return totalfiles

#Check if there is a local exception file from before and copy to FTP site
def report_exceptions():
    """Function to upload exception files via FTP"""
    print("Checking for exception file")
    if file_exists(EXCEPTION_FILE):
        # log.status("Uploading exception file")
        #import os
        try:
            session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
            if session:
                ftp.cwd(session,'/pico/logs')
                ftp.put_binaryfile(session,".",EXCEPTION_FILE)
                ftp.ftpquit(session)
                #os.remove(EXCEPTION_FILE)
        except Exception as e: # pylint: disable=broad-except
            log.log_exception(e)

def clear_log():
    """Function to clear the local exception log"""
    try:
        with open(EXCEPTION_FILE,"wt",encoding="utf-8") as file:
            file.write(f"{strftime()}: {pico} Cleared exception log\n")
            file.close()
        #Load the cleared file up to FTP site
        report_exceptions()
    except Exception: # pylint: disable=broad-except
        log.log("Failed to create new exception file {EXCEPTION_FILE}")

#Attempt NTP sync
def do_ntp_sync():
    """Function to do NTP Time Sync"""
    #Sync the time up
    if not ntp.set_time():
        log.status("Failed to set time", logit=True)
        return False
    else:
        log.status(f"{strftime()}")
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
            log.status("blinking")
            blink(0.1,0.1,5)
        elif command == "reload":
            reload()
        elif command == "restart":
            restart("mqtt command")
        elif command == "datetime":
            thetime = strftime()
            log.status(f"Time is: {thetime}")
        elif command == "uptime":
            log.status(f"Uptime: {uptime(timeInit)}")
        elif command == "status":
            log.status(f"Uptime: {uptime(timeInit)}")
            main.get_status()
        elif command == "clear":
            log.status("Clearing exception log")
            clear_log()
        else:
            log.status(f"Unknown command: {payload}")
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
    log.status(f"Wi-Fi: {ipaddr}")

    log.status("Attempting time sync")
    ntp_sync = do_ntp_sync() # pylint: disable=invalid-name

    #Try MQTT connect here so we get reload log events
    if mqtt.mqtt_connect(client_id=pico) is False:
        restart("No MQTT connection")

    log.status("------------------------")
    log.status("Initialising")

    #Get latest code by calling reload(); it returns the number of files updated
    if reload() > 0:
        slack.send_msg(pico,":repeat: Restarting to load new code")
        restart("new code")

    #Subscribe to the relevant channels
    if mqtt.client is not False:
        #Subscribe to control and heartbeat channels
        #log.status("Subscribing to MQTT")
        mqtt.client.set_callback(on_message) # type: ignore
        mqtt.client.subscribe("pico/"+pico+"/control") # type: ignore
        mqtt.client.subscribe("pico/all/control") # type: ignore
        mqtt.client.subscribe("pico/poll") # type: ignore
else: #No WiFi connection so need to restart
    restart("No Wifi")

#Let Slack know we're up
print("Posting to Slack")
slack.send_msg(pico,f":up: {pico} is up")

if not TESTMODE:
    #Have another go at syncing the time if that failed during initialisation
    if ipaddr and not ntp_sync:
        #Retry NTP sync
        ntp_sync = do_ntp_sync() # pylint: disable=invalid-name

    #Assuming we have the time now get the init time
    timeInit = time.time()

    #Upload latest local log file
    report_exceptions()

    #Now load and call the specific code for this pico
    try:
        main = __import__(pico)
        gc.collect()
        log.status(f"Free memory: {gc.mem_free()}") # pylint: disable=no-member
        log.status(f"Calling {pico}.py main()")
        main_result = main.main()
        try:
            slack.send_msg(pico,f":warning: Restarting after dropping out of main: {main_result}")
        except Exception: # pylint: disable=broad-except
            log.log("Failed to send message to Slack")
    #Catch any exceptions detected by the pico specific code
    except Exception as oops: # pylint: disable=broad-except
        exception = log.log_exception(oops)
        #Now pause a while then restart
        time.sleep(10)
        #Assume MQTT might be broken so don't try and send the restarting message
        mqtt.client = False
        try:
            slack.send_msg(pico,f":fire: Restarting after exception:\n{exception}")
        except Exception as oops2: # pylint: disable=broad-except
            log.log("Failed to send message to Slack")
        restart("Main Exception")

    restart("Dropped through")
