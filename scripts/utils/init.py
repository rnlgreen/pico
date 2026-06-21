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
        self.success = False  # Only set to True if initialization completes successfully
        self.init_duration_ms = 0  # Duration of initialization in milliseconds

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
        # !!! restart will reset the device, so we shouldn't reach here
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
        # !!! restart will reset the device, so we shouldn't reach here
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
    # Start timing (using ticks_ms which is independent of system clock)
    start_ticks = time.ticks_ms() # pylint: disable=no-member

    result = InitializationResult()
    result.mp_release = mp_release

    # Connect to WiFi
    result.ipaddr = connect_wifi(pico)

    if result.ipaddr:
        # Sync time
        result.ntp_sync = sync_ntp()

        # Report restart reason
        restart_reason = log.restart_reason()

        # Send previous restart reason to Slack
        if restart_reason not in ["New code loaded", "mqtt command"]: #No need to log these, it'll be obvious from previous messages
            slack.send_msg(pico, f":repeat: Previous restart reason: {restart_reason}")

        # Connect to MQTT
        if not connect_mqtt(pico):
            result.init_duration_ms = time.ticks_diff(time.ticks_ms(), start_ticks) # pylint: disable=no-member
            return result

        # Report IP address to MQTT (it is logged to file at connection time)
        log.status(f"IP {result.ipaddr}", logit=False)

        # Send previous restart reason to MQTT, now that we've connected to that
        if restart_reason not in ["New code loaded", "mqtt command"]: #No need to log these, it'll be obvious from previous messages
            log.status(f"Previous restart reason: {restart_reason}", logit=False)

        # Check for updates
        if check_for_updates(pico):
            # !!! restart will reset the device, so we shouldn't reach here
            result.init_duration_ms = time.ticks_diff(time.ticks_ms(), start_ticks) # pylint: disable=no-member
            return result

        # Setup MQTT subscriptions
        setup_subscriptions(pico, callback)

    # Check for standalone mode is an option
    elif pico in myid.standalone:
        result.standalone = True
        log.log("No WiFi so running standalone")

    else:
        # No WiFi connection so need to restart
        time.sleep(60)
        restart(f"No Wi-Fi: {wifi.wifi_reason}")
        # !!! restart will reset the device, so we shouldn't reach here
        result.init_duration_ms = time.ticks_diff(time.ticks_ms(), start_ticks) # pylint: disable=no-member
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

    # Calculate initialization duration
    result.init_duration_ms = time.ticks_diff(time.ticks_ms(), start_ticks) # pylint: disable=no-member

    # Mark initialization as successful
    result.success = True

    return result
