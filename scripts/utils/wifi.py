#Wi-Fi specific functions
import time
import secrets
import socket
import network # type: ignore # pylint: disable=import-error
from utils import log
from utils.blink import blink

#Global varaible so other functions can test the status
wlan = False
wifi_reason = "unknown"

def wlan_connect(hostname): # pylint: disable=unused-argument
    """" Connect to Wi-FI, returns ip address or False if fails """
    global wlan, wifi_reason # pylint: disable=global-statement
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        #The following config should work but wasn't yet merged with the latest build of micropython
        try:
            #wlan.config(dhcp_hostname = hostname)
            network.hostname(hostname)
        except Exception as e: # pylint: disable=broad-exception-caught
            log.status("Unable to set hostname", logit=True, handling_exception=True)
            log.log_exception(e)
        attempts = 0
        while attempts < 5 and not wlan.isconnected():
            blink(0.2,0.1,1)
            attempts += 1
            log.status(f"Connecting to {secrets.ssid}...", logit=True)
            wlan.connect(secrets.ssid,secrets.wlan_pass)
            time.sleep(5)
    except Exception as e: # pylint: disable=broad-exception-caught
        log.status(f"Exception connecting to Wi-Fi: {e}", logit=True, handling_exception=True)
        log.log_exception(e)
        wifi_reason = "Failed to connect Wi-Fi"
        return False

    if wlan.isconnected():
        log.status(",".join(wlan.ifconfig()), logit=True)
        return wlan.ifconfig()[0]
    else:
        log.status("Failed to connect to WLAN", logit=True)
        wifi_reason = "Failed to connect Wi-Fi"
        return False

# module-level cache for rate-limited checks
_last_wifi_check = 0
_last_wifi_status = True
_wifi_check_interval = 10  # seconds

def check_wifi(force=False):
    global wifi_reason, _last_wifi_check, _last_wifi_status # pylint: disable=global-statement

    now = time.time()
    if not force and (now - _last_wifi_check) < _wifi_check_interval:
        return _last_wifi_status

    if wlan.isconnected() is not True or wlan.status() != 3:
        log.status("Wi-Fi down", logit=True)
        log.status(f"wlan.isconnected(): {wlan.isconnected()}")
        log.status(f"wlan.status(): {wlan.status()}")
        wifi_reason = "Wi-Fi not connected"
        result = False
    else:
        dns_working = False
        tries = 0
        while not dns_working and tries < 2:
            tries += 1
            #Now check the network is working
            #This depends on the ttl value of the hostname looked up
            #Most times getadrinfo will get the cached result
            try:
                socket.getaddrinfo("condor",21)
                dns_working = True
            except Exception as e: #pylint: disable=broad-exception-caught
                log.status(f"DNS error {e}",logit=True)
            if not dns_working and tries < 3:
                time.sleep(5)
                log.status("...retrying DNS lookup",logit=True)
        if not dns_working:
            wifi_reason = "DNS lookup failed"
            result = False
        else:
            result = True

    _last_wifi_check = now
    _last_wifi_status = result
    return result

#Report Wi-Fi status
def wifi_status():
    log.status(f"wlan.isconnected(): {wlan.isconnected()}", logit=True)
    log.status(f"wlan.status(): {wlan.status()}", logit=True)
    log.status(f"IP: {wlan.ifconfig()[0]}", logit=True)
