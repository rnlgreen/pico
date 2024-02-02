#Code for Pico2 - measure and report temperature and pressure
import gc # Garbage Collector
import utime # type: ignore # pylint: disable=import-error # MicroPython time function (time is an alias to utime)
from utils import myid
from utils import mqtt
from utils import wifi
from utils.log import log
from utils.control import restart
from ruuvitag import RuuviTag

last_ruuvi = 0
no_ruuvi_since_start = True
got_one = False

mytags = { 'f34584d173cb': "woodstore", 'dc7eb48031b4': "garage", 'fab5c40c4095': "loft" }

#Callback handler that receives a tuple of data from the RuuviTag class object
#RuuviTagRAWv2(mac=b'f34584d173cb', rssi=-100, format=5, humidity=91.435, temperature=9.01,
#pressure=101617, acceleration_x=-20, acceleration_y=-40, acceleration_z=1020,
#battery_voltage=2851, power_info=4, movement_counter=122, measurement_sequence=31396)
def ruuvicb(ruuvitag):
    global last_ruuvi, no_ruuvi_since_start, got_one # pylint: disable=global-statement
    #elapsed = utime.ticks_diff(utime.ticks_ms(),last_ruuvi) / 1000
    last_ruuvi = utime.ticks_ms()
    got_one = True
    tagwhere = mytags[ruuvitag.mac.decode('ascii')]
    #status(f"Processing data for {tagwhere} RuuviTag after {elapsed} seconds")
    if mqtt.client is not False:
        for thing in ["temperature", "humidity", "pressure", "battery_voltage"]:
            print(f"{thing}: {getattr(ruuvitag, thing)}")
            value = getattr(ruuvitag, thing)
            if thing == "battery_voltage":
                thing = "battery"
                value = value / 1000
            topic = thing+"/"+tagwhere
            if thing == "pressure":
                value = value / 100
            mqtt.send_mqtt(topic,str(value))
    no_ruuvi_since_start = False

#Print and send status messages
def status(message):
    print(message)
    message = pico + ": " + message
    topic = 'pico/'+pico+'/status'
    send_mqtt(topic,message)

#Send alert
def send_mqtt(topic,message):
    print(f"{topic}: {message}")
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

#Return i2cscan to status commands
def get_status():
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    # gc.collect()
    # status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member

def main():
    global last_ruuvi, got_one # pylint: disable=global-statement

    #Inititialise Ruuvi
    ruuvi = RuuviTag()
    ruuvi._callback_handler = ruuvicb # pylint: disable=protected-access

    last_ruuvi = utime.ticks_add(utime.ticks_ms(),-60000)
    memory_check = utime.time()

    while True:
        ruuvi_elapsed = utime.ticks_diff(utime.ticks_ms(),last_ruuvi)
        #Check we've got an update from RuuviTag
        if ruuvi_elapsed > 70000 and not no_ruuvi_since_start and not got_one:
            status("RuuviTag data missing")
            return "RuuviTag data missing"
        elif ((ruuvi_elapsed >= 10000 and not got_one) #keep trying every 10 seconds
          or (ruuvi_elapsed >= 60000 and got_one)):    #or wait 60 seconds after we got one
            gc.collect()
            #Get Ruuvi Data
            got_one = False
            ruuvi.scan()

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if wifi.wlan.isconnected() is not True or wifi.wlan.status() != 3:
            log("Wi-Fi down")
            log(f"wlan.isconnected(): {wifi.wlan.isconnected()}")
            log(f"wlan.status(): {wifi.wlan.status()}")
            restart("Wi-Fi Lost")

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
