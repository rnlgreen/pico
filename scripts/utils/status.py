#Utili functions to report the status of the pico
import uos # type: ignore # pylint: disable=import-error
from machine import ADC # type: ignore # pylint: disable=import-error

# Internal temperature sensor is connected to ADC channel 4
temp_sensor = ADC(4)

def read_internal_temperature():
    # Read the raw ADC value
    adc_value = temp_sensor.read_u16()

    # Convert ADC value to voltage
    voltage = adc_value * (3.3 / 65535.0)

    # Temperature calculation based on sensor characteristics
    temperature_celsius = 27 - (voltage - 0.706) / 0.001721

    return str(round(temperature_celsius,1))

#Function to return total and free space
def fs_stats():
    fs_stat = uos.statvfs('/')
    t = fs_stat[0] * fs_stat[2] / 1024
    f = fs_stat[0] * fs_stat[3] / 1024
    return str(round(100*f/t, 1))
