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
    status("Checking for new code...")
    totalfiles = 0
    import utils.ftp as ftp
    try:
        session = ftp.login(secrets.ftphost,secrets.ftpuser,secrets.ftppw)
        #status("Comparing files...")
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

blink(0.1,0.1,3)

#Get my ID
pico = myid.get_id()

print("I am {}".format(pico))

#Call wifi_connect with our hostname
ipaddr = wifi.wlan_connect(pico)
if ipaddr:
    #Try and connect to MQTT
    mqtt.mqtt_connect(client_id=pico)
    status("Wi-Fi: {}".format(ipaddr))

    status("Attempting time sync...")
    ntp_sync = do_ntp_sync()

    blink(0.1,0.1,4)

    #Get latest code
    if reload() > 0:
        status("New code loaded")
        restart()

    if mqtt.client == False:
        status("MQTT Connection failed...")
    else:
        #Subscribe to control and heartbeat channels
        status("Subscribing to MQTT...")
        mqtt.client.set_callback(on_message) # type: ignore
        mqtt.client.subscribe("pico/"+pico+"/control") # type: ignore
        mqtt.client.subscribe("pico/all/control") # type: ignore
        mqtt.client.subscribe("pico/poll") # type: ignore

if not testmode:
    blink(0.2,0.2,5)
    if not ntp_sync:
        #Retry NTP sync
        ntp_sync = do_ntp_sync()

    #Now load and call the specific code for this pico
    status("Loading main...")
    try:
        main = __import__(pico)
        gc.collect()
        #status("Free memory: {}".format(gc.mem_free()))
        main.main()
    except Exception as e:
        import io
        import sys
        output = io.StringIO()
        #status("main.py caught exception: {}".format(e))
        sys.print_exception(e, output)
        try:
            status("Main caught exception:\n{}".format(output.getvalue()))
        except:
            pass
        #Now pause a while then restart
        time.sleep(10)
        #Assume MQTT might be broken
        mqtt.client = False
        restart()