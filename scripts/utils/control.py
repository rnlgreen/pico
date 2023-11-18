"""General logging and control functions"""
import time
from utils import mqtt
from utils import log
from machine import reset # pylint: disable=import-error # type: ignore

#Restart picox``
def restart(reason):
    """Function to restart the pico"""
    log.status(f'Restarting: {reason}')
    log.log(f"Restarting: {reason}")
    if mqtt.client is not False:
        try:
            mqtt.client.disconnect()
        except Exception as e: # pylint: disable=broad-except
            log.log_exception(e)
    time.sleep(1)
    reset()
