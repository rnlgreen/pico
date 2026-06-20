"""Main routine for all picos"""
import time
import gc

# Import my supporting code
from utils import myid
from utils import mqtt
from utils import slack
from utils import status
from utils import log
from utils import commands
from utils.blink import blink
from utils.control import restart
from utils.config import TESTMODE
from utils.filesystem import file_exists
from utils.init import initialize

### STARTUP SEQUENCE ###

# Blink the LED to show we're starting up
blink(0.1, 0.1, 3)

# Get my ID (e.g. 'pico0', based on the MAC address of this device)
pico = myid.get_id()
if pico.startswith("pico"):
    print(f"I am {pico}")
    newpico = False
else:
    print(f"Unrecognised ID: {pico}")
    newpico = True

# Log MicroPython version information
mp_release = status.log_versions()

# main_module is the module that will be loaded for this specific pico (e.g. pico0.py, pico1.py, etc.)
main_module = None  # Will be set after module is loaded

def on_message(topic, payload):
    """Process incoming MQTT messages - delegates to commands module"""
    global main_module # pylint: disable=global-variable-not-assigned
    # Get timeInit from init_result (will be available after initialization)
    timeInit = init_result.timeInit if 'init_result' in globals() else 0
    commands.process_message(topic, payload, pico, timeInit, main_module)

# Run initialization sequence
try:
    init_result = initialize(pico, mp_release, on_message, TESTMODE)
except Exception as oops: # pylint: disable=broad-except
    # If we fail to initialize, log the exception and restart
    log.status("Initialisation exception", logit=True, handling_exception=True)
    exception = log.log_exception(oops)
    slack.send_msg(pico, f":fire: Restarting after initialisation exception:\n{exception}")
    time.sleep(10)
    restart("Initialisation Exception")

# Check if initialization was successful
if not init_result.success:
    log.status("Initialisation failed, restarting...", logit=True)
    slack.send_msg(pico, ":fire: Restarting after failed initialisation")
    time.sleep(10)
    restart("Initialisation failed")

### MAIN EXECUTION ###

if not TESTMODE:
    if not newpico and file_exists(f"{pico}.py"):
        # Report that we are up
        log.status(f"{pico} is up", logit=True)

        # Upload latest local exception log file
        if not init_result.standalone:
            log.upload_exceptions()

        # Now load and call the specific code for this pico
        try:
            main_module = __import__(pico)
            gc.collect()
            log.status(f"MicroPython {mp_release}")
            log.status(f"Free memory: {gc.mem_free()}", logit=True) # pylint: disable=no-member
            log.status(f"Free storage: {status.fs_stats()}%", logit=True)
            log.status(f"Initialisation: {init_result.init_duration_ms/1000:.1f}s", logit=True)

            # Warn if storage is low
            if float(status.fs_stats()) < 10:
                log.status("Warning: Free storage is low", logit=True)
                slack.send_msg(pico, ":warning: Warning: Free storage is low")

            log.status(f"Temperature: {status.read_internal_temperature()}C", logit=True)

            # Upload latest local exception log file again
            if not init_result.standalone:
                log.upload_exceptions()

            log.status(f"Calling {pico}.py main()", logit=True)

            # Call the pico-specific main function
            if init_result.standalone:
                main_result = main_module.main(standalone=True)
            else:
                main_result = main_module.main()

            # Handle result from main function
            if main_result == "Wi-Fi Lost":
                from utils import wifi
                main_result = f"Wi-Fi Lost: {wifi.wifi_reason}"

            slack.send_msg(pico, f":warning: Restarting after dropping through: {main_result}")

            restart(f"Dropped through: {main_result}")

        # Catch any exceptions detected by the pico specific code
        except Exception as oops: # pylint: disable=broad-except
            # Assume MQTT might be broken so don't try and send the restarting message
            mqtt.client = False
            log.status("Handling main exception", logit=True, handling_exception=True)
            exception = log.log_exception(oops)
            slack.send_msg(pico, f":fire: Restarting after exception:\n{exception}")
            # Now pause a while then restart
            time.sleep(10)
            restart("Main Exception")

    else:
        # Unknown pico or no main script found
        print(f"Unknown pico {pico} or no main script not found")
        log.status(f"Unknown pico {pico}")
        log.upload_exceptions()
        slack.send_msg(pico, f":interrobang: Restarting - unknown {pico} or no script to run")
        time.sleep(300)
        restart("Unknown pico")

# We should never get here... but just in case
log.log("Dropped all the way through, attempting restart")
restart("The twilight zone")
