"""General logging and control functions"""
from utils import myid
from utils import mqtt
from utils.timeutils import strftime
import uos as os # pylint: disable=import-error

EXCEPTION_FILE = "exception.txt"
DEBUGGING = False

#Print and send status messages
def status(message, logit=False, handling_exception=False):
    """Function for reporting status."""
    print(message)
    if logit:
        log(message)
    if mqtt.client is not False:
        message = myid.pico + ": " + message
        topic = 'pico/'+myid.pico+'/status'
        try:
            mqtt.send_mqtt(topic,message)
            return True
        except Exception as e: # pylint: disable=broad-except
            mqtt.client = False # just adding this in here to try and avoid a failure loop
            if not handling_exception:
                log_exception(e)
            return False

#Print and send status messages
def debug(message, subtopic = None):
    #print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/debug'
    if not subtopic is None:
        topic = topic + "/" + subtopic
    mqtt.send_mqtt(topic,message)

_in_prune_log = False

#Function to prune the exception log file to a manageable size
def prune_log():
    """Function to prune the exception log file to a manageable size (memory-safe)."""
    global _in_prune_log # pylint: disable=global-statement
    _in_prune_log = True
    log_limit = 2500
    try:
        # Stream: count lines, then rewrite skipping first 10% without loading all lines
        total_lines = 0
        with open(EXCEPTION_FILE, "r", encoding="utf-8") as src:
            for _ in src:
                total_lines += 1
        if total_lines > log_limit:
            remove_count = int(total_lines * 0.2) #Remove 20% of lines
            status(f"Pruning exception log, too many lines ({total_lines})")
            tmp_name = EXCEPTION_FILE + ".tmp"
            with open(EXCEPTION_FILE, "r", encoding="utf-8") as src, open(tmp_name, "w", encoding="utf-8") as dst:
                for i, line in enumerate(src):
                    if i >= remove_count:
                        dst.write(line)
            # Replace original file with tmp (ignore errors)
            try:
                os.remove(EXCEPTION_FILE)
            except Exception: # pylint: disable=broad-except
                status("Failed to remove old exception log")
            try:
                os.rename(tmp_name, EXCEPTION_FILE)
            except Exception:# pylint: disable=broad-except
                status("Failed to rename new exception log")
            status("Pruned exception log", logit=True)
    except Exception as e:  # pylint: disable=broad-except
        status(f"Unable to prune exception log {e}", logit=True)
    _in_prune_log = False

def log(message):
    """Function to write status message to exception logfile"""
    try:
        with open(EXCEPTION_FILE,"at",encoding="utf-8") as file:
            file.write(f"{strftime()}: {myid.pico} {message}\n")
        if not _in_prune_log: # avoid recursion
            prune_log()
    except Exception as e: # pylint: disable=broad-except
        status(f"Unable to log message to file: {e}")

def log_exception(e):
    """Function to log exceptions to file"""
    import io  #pylint: disable=import-outside-toplevel
    import sys #pylint: disable=import-outside-toplevel
    output = io.StringIO()
    sys.print_exception(e, output) # pylint: disable=maybe-no-member
    exception1=output.getvalue()
    #Write exception to logfile
    print("Writing exception to storage")
    try:
        file = open(EXCEPTION_FILE,"at",encoding="utf-8")
        file.write(f"{strftime()}: {myid.pico} detected exception:\n{e}:{exception1}")
        file.close()
    except Exception as f: # pylint: disable=broad-except
        output2 = io.StringIO()
        sys.print_exception(f, output2) # pylint: disable=maybe-no-member
        print(f"Failed to write exception:\n{output2.getvalue()}")
    #Try sending the original exception to MQTT
    if mqtt.client is not False:
        try:
            status(f"Caught exception:\n{exception1}", handling_exception=True)
        except Exception: # pylint: disable=broad-except
            pass
    return exception1

def restart_reason():
    """Function to report the last restart reason, called by main after a restart"""
    reason = "unknown"
    try:
        with open(EXCEPTION_FILE,"r",encoding="utf-8") as file:
            for line in file:
                if "Restart reason:" in line:
                    reason = " ".join(line.split()[5:])
                if "is up" in line:
                    reason = "crash or power loss?"
        if reason not in ["New code loaded", "mqtt command"]: #No need to log this, it'll be obvious from previous messages
            status(f"Restart reason: {reason}")
    except Exception as e: # pylint: disable=broad-except
        status("Unable to read exception log", logit=True)
        log_exception(e)
    return reason
