#Code for Pico2 - measure and report temperature and pressure
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import myid
from utils import mqtt
from utils import wifi
from utils.log import status
from utils import ruuvi

#Send alert
def send_mqtt(topic,message):
    print(f"{topic}: {message}")
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

#Return i2cscan to status commands
def get_status():
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    ruuvi.get_status()

def main():
    memory_check = utime.time()

    while True:
        #Get RuuviTag readings, returns false if we haven't had any for a while
        if not ruuvi.get_readings():
            status("RuuviTag data missing")
            return "RuuviTag data missing"

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        #Report memory usage
        if utime.time() - memory_check > 600:
            memory_check = utime.time()
            get_status()

        utime.sleep(0.5)

pico = myid.get_id()
#where = myid.where[pico]
where = "garage1"

if __name__ == "__main__":
    main()
