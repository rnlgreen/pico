import time

from ruuvitag import RuuviTag

mytags = { 'f34584d173cb': "Woodstore", 'dc7eb48031b4': "Garage", 'fab5c40c4095': "Loft" }

#Callback handler that receives a tuple of data from the RuuviTag class object
#RuuviTagRAWv2(mac=b'f34584d173cb', rssi=-100, format=5, humidity=91.435, temperature=9.01,
#pressure=101617, acceleration_x=-20, acceleration_y=-40, acceleration_z=1020,
#battery_voltage=2851, power_info=4, movement_counter=122, measurement_sequence=31396)
def cb(ruuvitag):
    print(f"Data from {mytags[ruuvitag.mac.decode('ascii')]}:")
    for thing in ["temperature", "humidity", "pressure", "battery_voltage"]:
        print(f"{thing}: {getattr(ruuvitag, thing)}")

def run(ruuvi):
    try:
        while True:
            ruuvi.scan()
            time.sleep_ms(1000)
    except KeyboardInterrupt:
        ruuvi.stop()


#Inititialise Ruuvi
ruuvi = RuuviTag()
ruuvi._callback_handler = cb

run(ruuvi)
