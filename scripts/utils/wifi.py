#Wi-Fi specific functions
import network # type: ignore
import time
import secrets

def wlan_connect(hostname):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    attempts = 0
    while attempts < 5 and not wlan.isconnected():
        print("Connecting to {}...".format(secrets.ssid))
        #The following config should work but wasn't yet merged with the latest build of micropython
        #wlan.config(dhcp_hostname = hostname)
        wlan.connect(secrets.ssid,secrets.wlan_pass)
        time.sleep(5)
        print(wlan.isconnected())
    if wlan.isconnected():
        print(wlan.ifconfig())
        return wlan.ifconfig()[0]
    else:
        print("Failed to connect to WLAN")
        return False
