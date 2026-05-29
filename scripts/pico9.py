"""Main routine for Pico9

Reads and reports temperatures from the hot water tank sensors.
Also detects state of Tado CH and HW controls, Cylinder Stat (when water is on) and Boiler state.
"""
import utime  # type: ignore # pylint: disable=import-error
from machine import Pin  # pylint: disable=import-error
import onewire  # pylint: disable=import-error
import ds18x20  # pylint: disable=import-error
from utils.log import status
from utils import mqtt
from utils import wifi

# 1Wire pin and sensor setup
ds_pin = Pin(22)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

# 1Wire ROM hex values for the sensors, these are unique to each sensor
ROM_HEX = {
    '283b8b46d444007e': 'sensor1',
    '2876fa46d4d01e9b': 'sensor2',
}

# GPIO Pins for the relays
RELAY_CONFIG = {
    'ch':     {'pin': Pin(7, Pin.IN, Pin.PULL_UP), 'meaning': 'OFF'},  # Tado CH N/C
    'hw':     {'pin': Pin(9, Pin.IN, Pin.PULL_UP), 'meaning': 'OFF'},  # Tado HW N/C
    'cyl':    {'pin': Pin(6, Pin.IN, Pin.PULL_UP), 'meaning': 'ON'},   # Cylinder Stat N/O
    'boiler': {'pin': Pin(8, Pin.IN, Pin.PULL_UP), 'meaning': 'ON'},   # Boiler N/O
}

# Track last-known states to avoid MQTT spam
last_states = {key: None for key in RELAY_CONFIG}

def get_sensor_name(byte_array):
    """Return sensor name based on ROM hex value."""
    hex_string = ''.join(f'{byte:02x}' for byte in byte_array)
    return ROM_HEX.get(hex_string, hex_string)

def read_temperatures():
    """Read temperatures from all DS18X20 sensors."""
    roms = ds_sensor.scan()
    ds_sensor.convert_temp()
    utime.sleep(0.75)

    temperatures = {}
    for rom in roms:
        sensor_name = get_sensor_name(rom)
        temp_c = ds_sensor.read_temp(rom)
        temperatures[sensor_name] = temp_c

    return temperatures


def get_relay_state(pin_value, meaning):
    """Determine relay state based on pin value and meaning.
    
    Shelly pulls GPIO LOW when AC is present.
    meaning = "OFF": N/C contacts (CH/HW) - LOW means OFF, HIGH means ON
    meaning = "ON":  N/O contacts (Boiler/Cyl) - LOW means ON, HIGH means OFF
    """
    if meaning == "OFF":
        return "OFF" if pin_value == 0 else "ON"
    return "ON" if pin_value == 0 else "OFF"


def read_relay_states():
    """Read current state of all relays."""
    return {
        name: get_relay_state(config['pin'].value(), config['meaning'])
        for name, config in RELAY_CONFIG.items()
    }


def get_status():
    wifi.wifi_status()
    """Log current temperatures and relay states."""
    # Temperature sensors
    temperatures = read_temperatures()
    for sensor, temp in temperatures.items():
        status(f'{sensor}: {temp:.2f} deg C')

    # Relay states
    current_states = read_relay_states()
    for name, state in current_states.items():
        status(f'{name}: {state}')

    # Publish to MQTT
    if mqtt.client:
        for name, state in last_states.items():
            mqtt.send_mqtt(f"heating/{name}", state)


def report_temperatures():
    """Read and publish temperatures to MQTT."""
    temperatures = read_temperatures()
    if mqtt.client:
        for sensor, temp in temperatures.items():
            mqtt.send_mqtt(f"tank/{sensor}", f"{temp:.2f}")

def main():
    """Main loop: monitor temperatures and relay states."""
    last_sensor_time = utime.ticks_add(utime.ticks_ms(), -30000)
    force_publish = False

    while True:
        # Check for MQTT messages
        if mqtt.client:
            mqtt.client.check_msg()

        # Check WiFi status
        if not wifi.check_wifi():
            return "Wi-Fi Lost"

        # Report temperatures every 60 seconds
        sensor_elapsed = utime.ticks_diff(utime.ticks_ms(), last_sensor_time)
        if sensor_elapsed > 60000:
            last_sensor_time = utime.ticks_add(last_sensor_time, 60000)
            report_temperatures()
            force_publish = True

        # Read current relay states
        current_states = read_relay_states()

        # Publish on change or forced update
        if mqtt.client:
            for name, current_state in current_states.items():
                if current_state != last_states[name] or force_publish:
                    mqtt.send_mqtt(f"heating/{name}", current_state)
                    last_states[name] = current_state

        force_publish = False

        # Wait before next iteration
        utime.sleep(0.5)

if __name__ == "__main__":
    main()
