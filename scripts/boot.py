""" boot script to syntax check main.py """
# If main.py does not compile, report via MQTT and refresh code via FTP
import time
import machine # pylint: disable=import-error

# Configuration constants
SLEEP_BEFORE_RESTART = 300  # 5 minutes
NETWORK_TIMEOUT = 30  # seconds for network operations
MAX_FTP_RETRIES = 2

def syntax_check():
    """Function to check the syntax of main.py"""
    try:
        with open("main.py", "r") as f: # pylint: disable=unspecified-encoding
            code = f.read()
        compile(code, "main.py", "exec")
        return True, None
    except Exception as e: # pylint: disable=broad-except
        import io  # pylint: disable=import-outside-toplevel, redefined-outer-name
        import sys # pylint: disable=import-outside-toplevel, redefined-outer-name
        output = io.StringIO()
        sys.print_exception(e, output) # pylint: disable=maybe-no-member
        e_str = output.getvalue()
        output.close()
        return False, e_str

def refresh_code_from_ftp():
    """Attempt to refresh code from FTP server"""
    try:
        from utils import update # pylint: disable=import-outside-toplevel
        print("Attempting to refresh code from FTP...")

        for attempt in range(MAX_FTP_RETRIES):
            try:
                files_updated = update.update(cleanup=False)
                if files_updated > 0:
                    print(f"Successfully updated {files_updated} files")
                    return True
                else:
                    print("No files needed updating")
                    return False
            except Exception as ftp_error: # pylint: disable=broad-except
                print(f"FTP attempt {attempt + 1} failed: {ftp_error}")
                if attempt < MAX_FTP_RETRIES - 1:
                    time.sleep(2)  # Brief pause before retry

        print("All FTP refresh attempts failed")
        return False
    except Exception as e: # pylint: disable=broad-except
        print(f"Failed to import update module: {e}")
        return False

def safe_network_setup():
    """Set up networking with timeout protection"""
    try:
        from utils import myid # pylint: disable=import-outside-toplevel
        from utils import wifi # pylint: disable=import-outside-toplevel
        from utils import log # pylint: disable=import-outside-toplevel, redefined-outer-name

        # Get device ID
        pico = myid.get_id() # pylint: disable=redefined-outer-name
        if pico.startswith("pico"):
            print(f"I am {pico}")
        else:
            print(f"Unrecognised ID: {pico}")

        # Connect to WiFi with timeout
        print("Connecting to WiFi...")
        start_time = time.time()
        try:
            ipaddr = wifi.wlan_connect(pico) # pylint: disable=redefined-outer-name
        except Exception as wlan_error: # pylint: disable=broad-except
            log.status("Exception in wlan_connect", logit=True, handling_exception=True)
            log.log_exception(wlan_error)
            ipaddr = False

        # Check for timeout
        if time.time() - start_time > NETWORK_TIMEOUT:
            print("WiFi connection timed out")
            return None, None

        if not ipaddr:
            print("Failed to get IP address")
            return pico, None

        print(f"Connected with IP: {ipaddr}")

        # Optional: Skip NTP to save time, uncomment if time sync needed
        # from utils import ntp # pylint: disable=import-outside-toplevel
        # ntp.do_ntp_sync()

        # Connect to MQTT for logging
        print("Connecting to MQTT...")
        try:
            from utils import mqtt # pylint: disable=import-outside-toplevel
            mqtt_start = time.time()
            mqtt.mqtt_connect(client_id=pico)
            if time.time() - mqtt_start > NETWORK_TIMEOUT:
                print("MQTT connection timed out")
        except Exception as mqtt_error: # pylint: disable=broad-except
            log.status("Exception in mqtt_connect", logit=True, handling_exception=True)
            log.log_exception(mqtt_error)

        return pico, ipaddr

    except Exception as e: # pylint: disable=broad-except
        print(f"Network setup failed: {e}")
        return None, None

# Main boot logic
ok, err = syntax_check()

if ok:
    print("main.py syntax check passed")
else:
    print("=" * 50)
    print("CRITICAL: main.py has syntax errors!")
    print("=" * 50)
    print(err)
    print("=" * 50)

    # Attempt recovery
    try:
        # Set up networking
        pico, ipaddr = safe_network_setup() # pylint: disable=redefined-outer-name

        if ipaddr:
            # Import log for reporting
            from utils import log # pylint: disable=import-outside-toplevel,redefined-outer-name

            # Log the error
            log.status(f"Syntax error in main.py: {err}", logit=True)

            # Attempt to refresh code from FTP
            if refresh_code_from_ftp():
                log.status("Code refreshed from FTP, restarting now", logit=True)
                time.sleep(2)
                machine.reset()
            else:
                log.status("FTP refresh failed, will restart after delay", logit=True)
        else:
            print("No network available, cannot refresh code")

    except Exception as e: # pylint: disable=broad-except,redefined-outer-name
        # Minimal exception handling without external dependencies
        import io # pylint: disable=import-outside-toplevel
        import sys # pylint: disable=import-outside-toplevel

        buf = io.StringIO()
        sys.print_exception(e, buf) # pylint: disable=maybe-no-member
        exception_str = buf.getvalue()
        buf.close()

        print(f"Exception in boot.py recovery: {exception_str}")

    # Sleep before restart to avoid rapid reboot loops
    print(f"Sleeping {SLEEP_BEFORE_RESTART} seconds before restart...")
    time.sleep(SLEEP_BEFORE_RESTART)
    print("Restarting now...")
    machine.reset()

# If syntax check passed, continue to main.py normally
print("Boot complete, loading main.py...")
