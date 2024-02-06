#Functions to collect and send data from RuuviTags
import gc # Garbage collector
import utime # type: ignore # pylint: disable=import-error
from ruuvitag import RuuviTag
from utils import mqtt
from utils import log

log.DEBUGGING = True

no_ruuvi_since_start = True
got_one = False
scanning = False
found = []

mytags = { 'f34584d173cb': "woodstore", 'dc7eb48031b4': "garage", 'fab5c40c4095': "loft" }

def get_status():
    log.status(f"no_ruuvi_since_start: {no_ruuvi_since_start}")
    log.status(f"got_one: {got_one}")
    log.status(f"scanning: {scanning}")
    log.status(f"last_ruuvi: {last_ruuvi}")

#Callback handler that receives a tuple of data from the RuuviTag class object
#RuuviTagRAWv2(mac=b'f34584d173cb', rssi=-100, format=5, humidity=91.435, temperature=9.01,
#pressure=101617, acceleration_x=-20, acceleration_y=-40, acceleration_z=1020,
#battery_voltage=2851, power_info=4, movement_counter=122, measurement_sequence=31396)
def ruuvicb(ruuvitag):
    global last_ruuvi, no_ruuvi_since_start, got_one, scanning, found # pylint: disable=global-statement
    #elapsed = utime.ticks_diff(utime.ticks_ms(),last_ruuvi) / 1000
    if not ruuvitag is None:
        last_ruuvi = utime.ticks_ms()
        got_one = True
        tagwhere = mytags[ruuvitag.mac.decode('ascii')]
        found.append(tagwhere)
        log.debug(f"Processing data for {tagwhere} RuuviTag")
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
    else:
        scanning = False
        log.debug("Scanning complete")
        if got_one:
            log.debug(f"Found: {','.join(found)}")
            found = []
        else:
            log.status("No tags found")

def get_readings():
    global got_one, scanning # pylint: disable=global-statement
    ruuvi_elapsed = utime.ticks_diff(utime.ticks_ms(),last_ruuvi)
    #Check we've got an update from RuuviTag
    if ruuvi_elapsed > 70000 and not no_ruuvi_since_start and not got_one:
        return False
    elif ((ruuvi_elapsed >= 10000 and not got_one and not scanning) #keep trying every 10 seconds
        or (ruuvi_elapsed >= 60000 and got_one)):  #or wait 60 seconds after we got one
        #Get Ruuvi Data
        scanning = True #to avoid multiple scans kicking off
        got_one = False
        log.debug("Scanning...")
        gc.collect() #Do a quick garbage collect
        ruuvi.scan(ruuvicb) #scans for 5 seconds
    return True

#Inititialise Ruuvi
ruuvi = RuuviTag()
#ruuvi._callback_handler = ruuvicb # pylint: disable=protected-access
last_ruuvi = utime.ticks_add(utime.ticks_ms(),-30000)
