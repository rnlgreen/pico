"""Main routine for Pico9"""
#Reads and reports temperatures from the hot water tank sensors
import utime # type: ignore # pylint: disable=import-error
import machine # pylint: disable=import-error
import onewire # pylint: disable=import-error
import ds18x20 # pylint: disable=import-error
from utils.log import status
from utils import mqtt
from utils import wifi


ds_pin = machine.Pin(22)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

rom_hex = {
           '283b8b46d444007e': 'sensor1',
           '2876fa46d4d01e9b': 'sensor2',
          }

#Return which sensor we have based on the hex values of the unique code
def get_sensor(byte_array):
    hex_string = ''.join(f'{byte:02x}' for byte in byte_array)
    if hex_string in rom_hex:
        return rom_hex[hex_string]
    else:
        return "unknown"

def get_status():
    #Temperature sensors
    roms = ds_sensor.scan()
    ds_sensor.convert_temp()
    utime.sleep(0.75)
    for rom in roms:
        sensor = get_sensor(rom)
        tempC = ds_sensor.read_temp(rom)
        status(f'{sensor}: {tempC:.2f} deg C')
    return

def report_temperatures():
    roms = ds_sensor.scan()
    ds_sensor.convert_temp()
    utime.sleep(0.75)
    for rom in roms:
        sensor = get_sensor(rom)
        tempC = ds_sensor.read_temp(rom)
        if mqtt.client is not False:
            topic = f"tank/{sensor}"
            mqtt.send_mqtt(topic,f"{tempC:.2f}")
    return


def main():
    last_sensor = utime.ticks_add(utime.ticks_ms(),-30000)

    while True:
        sensor_elapsed = utime.ticks_diff(utime.ticks_ms(),last_sensor)
        if sensor_elapsed > 60000:
            last_sensor = utime.ticks_add(last_sensor,60000)
            report_temperatures()

        #Check for messages
        if mqtt.client is not False:
            mqtt.client.check_msg()

        #Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        #Wait a bit
        utime.sleep(0.5)

if __name__ == "__main__":
    main()
