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
        #The following config should work but wasn't yet merged with the latest build of micropython
        try:
            #wlan.config(dhcp_hostname = hostname)
            network.hostname(hostname)
        except Exception as e: # pylint: disable=broad-exception-caught
            log.status(f"Unable to set hostname", logit=True, handling_exception=True)
            log.log_exception(e)
        attempts = 0
        while attempts < 5 and not wlan.isconnected():
            attempts += 1
            log.status(f"Connecting to {secrets.ssid}...", logit=True)
            wlan.connect(secrets.ssid,secrets.wlan_pass)
            time.sleep(5)
    except Exception as e: # pylint: disable=broad-exception-caught
        log.status(f"Exception connecting to Wi-Fi: {e}", logit=True, handling_exception=True)
        log.log_exception(e)
        return False

    if wlan.isconnected():
        log.status(wlan.ifconfig(), logit=True)
        return wlan.ifconfig()[0]
    else:
        log.status("Failed to connect to WLAN", logit=True)
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
