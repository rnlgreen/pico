"""Main routine for Pico8"""
#Monitors the heat and water valves using photoresistors
import time
import gc
from machine import Pin, ADC # type: ignore # pylint: disable=import-error
from utils import mqtt
from utils import wifi
from utils import myid
from utils import slack
from utils import ruuvi
from utils.log import status

sensors = {"heating": {"pin": 26, "state": "off", "ontime": 0, "icon": "hot_springs"},
           "water": {"pin": 27, "state": "off", "ontime": 0, "icon": "potable_water"}}

states = {"on": 100, "off": 0}

#heatPIN  = 26 #GPIO26 - ADC0 - has to be one of the ADC pins - defined in light module
#waterPIN = 27 #GPIO27 - ADC1 - has to be one of the ADC pins - defined in light module

#Measure light levels
def readLight(adc_pin):
    """Measure light levels"""
    photoRes = ADC(Pin(adc_pin))
    light = photoRes.read_u16()
    light = round(100*light/65535,2)
    return light

def get_status():
    for which in ['heating','water']:
        status(f"{which} is currently {sensors[which]['state']}")
        status(f"{which} valve light level: {readLight(sensors[which]['pin'])}")
    ruuvi.get_status()
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member
    gc.collect()
    status(f"freemem: {gc.mem_free()}") # pylint: disable=no-member

    return

#Send measurement
def send_measurement(here,what,value):
    """Send measurement"""
    print(f"Sending measurement {what}: {value}")
    topic = what+"/"+here
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,str(value))

def main():
    last_update = 0
    do_update = True

    while True:
        do_update = (time.time() - last_update) >= 60 #Update once a minute regardless

        for which in ['heating','water']:
            lightlevel = readLight(sensors[which]["pin"])
            if lightlevel > 25:
                newstate = "on"
            else:
                newstate = "off"
            if not newstate == sensors[which]["state"] or do_update:
                icon = sensors[which]["icon"]
                if not newstate == sensors[which]["state"]:
                    sensors[which]["state"] = newstate
                    if newstate == "on":
                        slack.send_msg(myid.pico,f"{icon} {which} is now {newstate}")
                        sensors[which]["ontime"] = time.time()
                    else:
                        on_duration = round((time.time() - sensors[which]["ontime"]) / 60,2)
                        slack.send_msg(myid.pico,f"{icon} {which} is now {newstate}; was on for {on_duration} mins")
                send_measurement(where,which,states[newstate])
                last_update = time.time()

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

        #Wait a bit
        time.sleep(0.5)

pico = myid.get_id()
where = myid.where[pico]

if __name__ == "__main__":
    main()
