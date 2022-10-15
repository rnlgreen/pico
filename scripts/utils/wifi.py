#Wi-Fi specific functions
import network # type: ignore
import time

def wlan_connect(hostname):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    attempts = 0
    while attempts < 5 and not wlan.isconnected():
    #    ssid = "osprey"
    #    wlan_pass = "birdsofprey"
        ssid = "owl"
        wlan_pass = "dodgyiot"
        print("Connecting to {}...".format(ssid))
        #wlan.config(dhcp_hostname = hostname)
        wlan.connect(ssid,wlan_pass)
        time.sleep(5)
        print(wlan.isconnected())
    if wlan.isconnected():
        print(wlan.ifconfig())
        return True
    else:
        print("Failed to connect to WLAN")
        return False