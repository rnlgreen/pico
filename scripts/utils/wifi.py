#Wi-Fi specific functions
import time
import secrets
import socket
import network # type: ignore # pylint: disable=import-error
from utils import log

#Global varaible so other functions can test the status
wlan = False

def wlan_connect(hostname): # pylint: disable=unused-argument
    """" Connect to Wi-FI, returns ip address or False if fails """
    global wlan # pylint: disable=global-statement
    try:
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
    except Exception as e: # pylint: disable=broad-exception-caught
        log.status(f"Exception connecting to Wi-Fi: {e}", logit=True)
        return False

    if wlan.isconnected():
        print(wlan.ifconfig())
        return wlan.ifconfig()[0]
    else:
        print("Failed to connect to WLAN")
        return False

def check_wifi():
    if wlan.isconnected() is not True or wlan.status() != 3:
        log.status("Wi-Fi down", logit=True)
        log.status(f"wlan.isconnected(): {wlan.isconnected()}")
        log.status(f"wlan.status(): {wlan.status()}")
        return False
    else:
        #Now check the network is working
        #This depends on the ttl value of the hostname looked up
        #Most times getadrinfo will get the cached result
        try:
            socket.getaddrinfo("condor.rghome",21)
        except: #pylint: disable=bare-except
            log.status("socket error, assume the network is down")
            return False
        return True
