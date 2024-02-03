#Wi-Fi specific functions
import time
import secrets
import network # type: ignore # pylint: disable=import-error
from utils.log import log

#Global varaible so other functions can test the status
wlan = False

def wlan_connect(hostname): # pylint: disable=unused-argument
    """" Connect to Wi-FI, returns ip address or False if fails """
    global wlan # pylint: disable=global-statement
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    attempts = 0
    while attempts < 5 and not wlan.isconnected():
        attempts += 1
        print(f"Connecting to {secrets.ssid}...")
        #The following config should work but wasn't yet merged with the latest build of micropython
        try:
            #wlan.config(dhcp_hostname = hostname)
            network.hostname(hostname)
        except: # pylint: disable=bare-except
            print("Unable to set hostname")
        wlan.connect(secrets.ssid,secrets.wlan_pass)
        time.sleep(5)
        print(wlan.isconnected())
    if wlan.isconnected():
        print(wlan.ifconfig())
        return wlan.ifconfig()[0]
    else:
        print("Failed to connect to WLAN")
        return False

def check_wifi():
    if wlan.isconnected() is not True or wlan.status() != 3:
        log("Wi-Fi down")
        log(f"wlan.isconnected(): {wlan.isconnected()}")
        log(f"wlan.status(): {wlan.status()}")
        return False
    else:
        return True
