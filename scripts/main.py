"""Main routine for all picos"""
import time
import gc
import secrets
import uos # type: ignore # pylint: disable=import-error

#Import my supporting code
from utils import myid
from utils import wifi
from utils import mqtt
from utils import ntp
from utils import ftp
from utils import slack
from utils import status
from utils.blink import blink
from utils.timeutils import strftime, uptime
from utils import log
from utils.control import restart

TESTMODE = False
EXCEPTION_FILE = "exception.txt"

#Send message with specific topic
def send_mqtt(topic,message):
    """Function for sending MQTT message."""
    if mqtt.client is not False:
        try:
            mqtt.send_mqtt(topic,message)
            return True
        except Exception as e: # pylint: disable=broad-except
            mqtt.client = False # Adding this here to avoid repeatedly trying to use MQTT
            log.status("Error sending to mqtt", logit=True, handling_exception=True)
            log.log_exception(e)
            return False

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
def reload(cleanup=False):
    """Function to reload new code if there is any"""
    # log.status("Checking for new code")
    totalfiles = 0
    try:
        session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
        if session:
            #Check all the folders for new files
            folders = ["."]
            # Get parent folders
            ftp.cwd(session,'/pico/scripts')
            folders += ftp.list_folders(session)
            # Get sub folders
            subfolders = []
            for source in (folders):
                if source != '.':
                    ftp.cwd(session,f'/pico/scripts/{source}')
                    subfolderlist = []
                    subfolderlist += ftp.list_folders(session)
                    for f in subfolderlist:
                        subfolders.append(f"{source}/{f}")
            folders += subfolders
            #log.status(f"Checking folders: {folders}",logit=True)
            for source in (folders):
                ftp.cwd(session,'/pico/scripts')
                if not dir_exists(source):
                    log.status(f"Creating new folder {source}", logit=True)
                    uos.mkdir(source)
                numfiles = ftp.get_changedfiles(session,source,cleanup)
                totalfiles += numfiles
            ftp.ftpquit(session)
            if totalfiles > 0:
                log.status(f"Updated {totalfiles} files", logit=True)
            else:
                pass
                #log.status("No new files found")
        else:
            log.status("FTP error occurred", logit=True)
    except Exception as e: # pylint: disable=broad-except
        log.status("Failed during reload", logit=True, handling_exception=True)
        log.log_exception(e)
    return totalfiles

#Check if there is a local exception file from before and copy to FTP site
def upload_exceptions():
    """Function to upload exception files via FTP"""
    print("Uploading latest exception file")
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
            log.status("Error uploading exception log", logit=True, handling_exception=True)
            log.log_exception(e)

def clear_log():
    """Function to clear the local exception log"""
    try:
        with open(EXCEPTION_FILE,"wt",encoding="utf-8") as file:
            file.write(f"{strftime()}: {pico} Cleared exception log\n")
            file.close()
        #Load the cleared file up to FTP site
        upload_exceptions()
    except Exception: # pylint: disable=broad-except
        log.log("Failed to create new exception file {EXCEPTION_FILE}")

def log_versions():
    _, _, release, version, machine = uos.uname()
    log.log(machine)
    log.log(version)
    return release

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
        #elif command == "reload": #These just result in memory issues and corrupt files
        #    reload()
        #elif command == "cleanup":
        #    reload(cleanup=True)
        elif command == "restart":
            log.status("Restarting")
            restart("mqtt command")
        elif command == "datetime":
            thetime = strftime()
            log.status(f"Time is: {thetime}")
        elif command == "uptime":
            log.status(f"Uptime: {uptime(timeInit)}")
        elif command == "status":
            log.status(f"Uptime: {uptime(timeInit)}")
            log.status(f"My temperature: {status.read_internal_temperature()}C")
            main.get_status() # pylint: disable=used-before-assignment
        elif command=="temperature":
            temperature = status.read_internal_temperature()
            temp_topic = f"temperature/{pico}"
            if not send_mqtt(temp_topic,temperature):
                restart("MQTT Failure detected")
        elif command == "clear":
            log.status("Clearing exception log")
            clear_log()
        else:
            log.status(f"Unknown command: {payload}")
    elif topic == "pico/lights" or topic == "pico/xlights" or topic == "pico/plights":
        main.led_control(topic,payload)
    elif topic == "pico/poll":
        heartbeat_topic = f"pico/{pico}/heartbeat"
        if not send_mqtt(heartbeat_topic,"Yes, I'm here"):
            restart("MQTT Failure detected")
    elif topic == "pico/pico2w0/heartbeat": # Used by pico7 to check the lights should be on still
        main.heartbeat()

### INITIALISATION STEPS ###
#Blink the LED to show we're starting up
blink(0.1,0.1,3)

#Get my ID (e.g. 'pico0', based on the MAC address of this device)
pico = myid.get_id()
if pico.startswith("pico"):
    print(f"I am {pico}")
    newpico = False
else:
    print(f"Unrecognised ID: {pico}")
    newpico = True

#log.status("Initialising, about to connect Wi-Fi", logit=True)
mp_release = log_versions()

#Call wifi_connect with our hostname; my routine tries multiple times to connect
try:
    ipaddr = wifi.wlan_connect(pico)
except Exception as wlan_error: # pylint: disable=broad-except
    log.status("Exception in wlan_connect", logit=True, handling_exception=True)
    exception = log.log_exception(wlan_error)
    ipaddr = False

ntp_sync = False #just to avoid an pylint error
timeInit = 0 #and the same
standalone = False

#If we got an IP address we can update code adn setup MQTT connection and subscriptions
if ipaddr:
    restart_reason = log.restart_reason()
    slack.send_msg(pico,f":repeat: Restart reason: {restart_reason}")

    #log.status(f"Wi-Fi: {ipaddr}", logit=True)

    #log.log("Attempting time sync #1")
    ntp_sync = do_ntp_sync() # pylint: disable=invalid-name

    #log.log("Attempting MQTT connection")
    #Try MQTT connect here so we get reload log events
    if not mqtt.mqtt_connect(client_id=pico):
        log.log("Pausing befire restart (MQTT)")
        time.sleep(30)
        restart("No MQTT connection")

    #Get latest code by calling reload(); it returns the number of files updated
    if reload(cleanup=False) > 0:
        log.status("Restarting...")
        slack.send_msg(pico,":repeat: Restarting to load new code")
        restart("New code loaded")

    #Subscribe to the relevant channels
    if mqtt.client is not False:
        #Subscribe to control and heartbeat channels
        #log.status("Subscribing to MQTT", logit=True)
        mqtt.client.set_callback(on_message) # type: ignore
        mqtt.client.subscribe("pico/"+pico+"/control") # type: ignore
        mqtt.client.subscribe("pico/all/control") # type: ignore
        mqtt.client.subscribe("pico/poll") # type: ignore
elif pico in myid.standalone:
    standalone = True
    log.log("No WiFi so running standalone")
else:
    #No WiFi connection so need to restart
    time.sleep(10)
    restart(f"No Wi-Fi: {wifi.wifi_reason}")

#Let Slack know we're up
#log.status("Posting to Slack", logit=True)
if not standalone:
    slack.send_msg(pico,f":up: {pico} is up")

if not TESTMODE:
    #Have another go at syncing the time if that failed during initialisation
    if ipaddr and not ntp_sync:
        #Retry NTP sync
        log.log("Attempting time sync #2")
        ntp_sync = do_ntp_sync() # pylint: disable=invalid-name

    #Assuming we have the time now get the init time
    timeInit = time.time()

    if not newpico and file_exists(f"{pico}.py"):
        #Report that we are up
        log.status(f"{pico} is up", logit=True)

        #Upload latest local log file
        if not standalone:
            upload_exceptions()

        #Now load and call the specific code for this pico
        try:
            main = __import__(pico)
            gc.collect()
            log.status(f"MicroPython {mp_release}")
            log.status(f"Free memory: {gc.mem_free()}", logit=True) # pylint: disable=no-member
            log.status(f"Free storage: {status.fs_stats()}%", logit=True) # pylint: disable=no-member
            log.status(f"Temperature: {status.read_internal_temperature()}C", logit=True)
            log.status(f"Calling {pico}.py main()", logit=True)
            if standalone:
                main_result = main.main(standalone)
            else:
                main_result = main.main()
            if not main_result == "Wi-Fi Lost":
                slack.send_msg(pico,f":warning: Restarting after dropping through: {main_result}")
            else:
                main_result = f"Wi-Fi Lost: {wifi.wifi_reason}"
            restart(f"Dropped through: {main_result}")
        #Catch any exceptions detected by the pico specific code
        except Exception as oops: # pylint: disable=broad-except
            log.status("Handling main exception", logit=True, handling_exception=True)
            exception = log.log_exception(oops)
            #Assume MQTT might be broken so don't try and send the restarting message
            mqtt.client = False
            slack.send_msg(pico,f":fire: Restarting after exception:\n{exception}")
            #Now pause a while then restart
            time.sleep(10)
            restart("Main Exception")
    else:
        print(f"Unknown pico {pico} or no main script not found")
        log.status(f"Unknown pico {pico}")
        #Upload latest local log file
        upload_exceptions()
        slack.send_msg(pico,f":interrobang: Restarting - unknown {pico} or no script to run")
        time.sleep(60)
        restart("Unknown pico")

#We should never get here... but just in case
log.log("Dropped all the way through, attempting restart")
restart("The twilight zone")
