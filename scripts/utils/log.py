"""General logging and control functions"""
from utils import myid
from utils import mqtt
from utils.timeutils import strftime

EXCEPTION_FILE = "exception.txt"
DEBUGGING = False

#Print and send status messages
def status(message, logit=False):
    """Function for reporting status."""
    print(message)
    if logit:
        log(message)
    if mqtt.client is not False:
        message = myid.pico + ": " + message
        topic = 'pico/'+myid.pico+'/status'
        try:
            mqtt.send_mqtt(topic,message)
        except Exception as e: # pylint: disable=broad-except
            log_exception(e)

#Print and send status messages
def debug(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/debug'
    mqtt.send_mqtt(topic,message)

def log(message):
    """Function to write status message to exception logfile"""
    try:
        with open(EXCEPTION_FILE,"at",encoding="utf-8") as file:
            file.write(f"{strftime()}: {myid.pico} {message}\n")
            file.close()
    except Exception: # pylint: disable=broad-except
        status("Unable to log message to file")

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
    try:
        status(f"Caught exception:\n{exception1}")
    except Exception: # pylint: disable=broad-except
        pass
    return exception1
