"""Initialization utilities for pico startup"""
import time
from utils import wifi
from utils import ntp
from utils import mqtt
from utils import slack
from utils import log
from utils import update
from utils.control import restart
from utils import myid

class InitializationResult:
    """Container for initialization results"""
    def __init__(self):
        self.ipaddr = False
        self.ntp_sync = False
        self.timeInit = 0
        self.standalone = False
        self.mp_release = None
        self.success = True

def connect_wifi(pico):
    """Connect to WiFi with error handling
    
    Returns:
        IP address string or False on failure
    """
    try:
        ipaddr = wifi.wlan_connect(pico)
        return ipaddr
    except Exception as wlan_error: # pylint: disable=broad-except
        log.status("Exception in wlan_connect", logit=True, handling_exception=True)
        log.log_exception(wlan_error)
        return False

def sync_ntp():
    """Synchronize time with NTP server
    
    Returns:
        True if sync successful, False otherwise
    """
    return ntp.do_ntp_sync()

def connect_mqtt(pico):
    """Connect to MQTT broker
    
    Returns:
        True if connected, False otherwise
    """
    if not mqtt.mqtt_connect(client_id=pico):
        log.log("Pausing before restart (MQTT)")
        time.sleep(30)
        restart("No MQTT connection")
        return False
    return True

def check_for_updates(pico):
    """Check for and apply code updates
    
    Returns:
        True if updates were applied (should restart), False otherwise
    """
    updates_applied = update.update(cleanup=False)
    if updates_applied > 0:
        log.status("Restarting...")
        slack.send_msg(pico, ":repeat: Restarting to load new code")
        restart("New code loaded")
        return True
    return False

def setup_subscriptions(pico, callback):
    """Subscribe to MQTT topics
    
    Args:
        pico: Pico identifier string
        callback: Message callback function
    """
    if mqtt.client is not False:
        mqtt.client.set_callback(callback) # type: ignore
        mqtt.client.subscribe(f"pico/{pico}/control") # type: ignore
        mqtt.client.subscribe("pico/all/control") # type: ignore
        mqtt.client.subscribe("pico/poll") # type: ignore

def initialize(pico, mp_release, callback, testmode=False):
    """Run full initialization sequence
    
    Args:
        pico: Pico identifier string
        mp_release: MicroPython release version
        callback: MQTT message callback function
        testmode: If True, skip normal initialization
        
    Returns:
        InitializationResult object with status
    """
    result = InitializationResult()
    result.mp_release = mp_release

    # Connect to WiFi
    result.ipaddr = connect_wifi(pico)

    if result.ipaddr:
        # Report restart reason
        restart_reason = log.restart_reason()
        slack.send_msg(pico, f":repeat: Restart reason: {restart_reason}")

        # Sync time
        result.ntp_sync = sync_ntp()

        # Connect to MQTT
        if not connect_mqtt(pico):
            result.success = False
            return result

        # Check for updates
        if check_for_updates(pico):
            # Will restart, so we shouldn't reach here
            result.success = False
            return result

        # Setup MQTT subscriptions
        setup_subscriptions(pico, callback)
        log.status(f"IP {result.ipaddr}")

    # Check for standalone mode
    elif pico in myid.standalone:
        result.standalone = True
        log.log("No WiFi so running standalone")
    else:
        # No WiFi connection so need to restart
        time.sleep(10)
        restart(f"No Wi-Fi: {wifi.wifi_reason}")
        result.success = False
        return result

    # Send startup message to Slack
    if not result.standalone:
        slack.send_msg(pico, f":up: {pico} is up")

    # Retry NTP sync if needed
    if not testmode:
        if result.ipaddr and not result.ntp_sync:
            log.log("Attempting time sync #2")
            result.ntp_sync = sync_ntp()

        # Set initial time
        result.timeInit = time.time()

    return result
