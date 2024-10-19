"""Main routine for Pico8"""
#Monitors the heat and water valves using photoresistors
import time
from machine import Pin, ADC # type: ignore # pylint: disable=import-error
from utils import mqtt
from utils import wifi
from utils import myid
from utils.log import status

pins = {"heat": 26, "water": 27}
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
    for which in ['heat','water']:
        status(f"{which} valve light level: {readLight(pins[which])}")
    return

#Send measurement
def send_measurement(here,what,value):
    """Send measurement"""
    print(f"Sending measurement {what}: {value}")
    topic = what+"/"+here
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,str(value))

def main():
    last_reading = time.time()

    while True:
        if time.time() - last_reading >= 5:
            for which in ['heat','water']:
                lightlevel = readLight(pins[which])
                if lightlevel > 25:
                    send_measurement(where,which,100)
                else:
                    send_measurement(where,which,0)

            last_reading = time.time()

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
