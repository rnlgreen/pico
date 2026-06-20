#Functions to collect and send data from RuuviTags
#import gc # Garbage collector
import json
import utime # type: ignore # pylint: disable=import-error
from ruuvitag import RuuviTag
from utils import mqtt
from utils import log
from utils.timeutils import strftime

log.DEBUGGING = True

no_ruuvi_since_start = True
got_one = False
scanning = False
found = []

mytags = { 'f34584d173cb': "lounge", 'dc7eb48031b4': "kitchen", 'fab5c40c4095': "orangery",  'f9a8d010746c': "utility" }
discovered_macs = set()

def get_status():
    log.status(f"no_ruuvi_since_start: {no_ruuvi_since_start}")
    log.status(f"got_one: {got_one}")
    log.status(f"scanning: {scanning}")
    log.status(f"last_ruuvi_time: {last_ruuvi_time}")
    #log.debug(f"blacklist unique values: {len(set(ruuvi._blacklist))}", subtopic="blacklist")
    #log.debug(f"blacklist: {ruuvi._blacklist}", subtopic="blacklist")
    log.debug(f"addrs: {ruuvi._addrs}", subtopic="ruuvi/addrs") # pylint: disable=protected-access

def battery_voltage_to_percent(v):
    # Clamp to safe range
    if v >= 3.00:
        return 100
    if v <= 2.50:
        return 0

    # Piecewise linear interpolation
    table = [
        (3.00, 100),
        (2.90, 90),
        (2.80, 70),
        (2.70, 40),
        (2.60, 10),
        (2.50, 0)
    ]

    for i in range(len(table) - 1):
        v_high, p_high = table[i]
        v_low, p_low = table[i + 1]

        if v <= v_high and v >= v_low:
            # Linear interpolation
            ratio = (v - v_low) / (v_high - v_low)
            return int(p_low + (p_high - p_low) * ratio)

    return 0

def publish_discovery(mac):
    base = f"homeassistant/sensor/ruuvi_{mac}"
    state_topic = f"ruuvi/{mac}/data"

    sensors = {
        "temperature": {
            # HA infers °C automatically from device_class
            "template": "{{ value_json.temperature }}",
            "device_class": "temperature",
            "state_class": "measurement"
        },
        "humidity": {
            "unit": "%",
            "template": "{{ value_json.humidity }}",
            "device_class": "humidity",
            "state_class": "measurement"
        },
        "pressure": {
            "unit": "hPa",
            "template": "{{ (value_json.pressure / 100) }}",
            "device_class": "pressure",
            "state_class": "measurement"
        },
        "battery": {
            # Now reporting percentage
            "unit": "%",
            "template": "{{ value_json.battery_percent }}",
            "device_class": "battery",
            "state_class": "measurement",
            "entity_category": "diagnostic"
        },
        "rssi": {
            "unit": "dBm",
            "template": "{{ value_json.rssi }}",
            "device_class": "signal_strength",
            "state_class": "measurement",
            "entity_category": "diagnostic"
        }
    }

    friendly = {
        "temperature": "Temperature",
        "humidity": "Humidity",
        "pressure": "Pressure",
        "battery": "Battery",
        "rssi": "RSSI"
    }

    for key, cfg in sensors.items():
        topic = f"{base}/{key}/config"

        payload = {
            "name": f"Ruuvi {mac} {friendly[key]}",
            "state_topic": state_topic,
            "value_template": cfg["template"],
            "unique_id": f"ruuvi_{mac}_{key}",
            "state_class": cfg["state_class"],
            "device": {
                "identifiers": [f"ruuvi_{mac}"],
                "name": f"RuuviTag {mac}",
                "manufacturer": "Ruuvi"
            }
        }

        if "unit" in cfg:
            payload["unit_of_measurement"] = cfg["unit"]

        if "device_class" in cfg:
            payload["device_class"] = cfg["device_class"]

        if "entity_category" in cfg:
            payload["entity_category"] = cfg["entity_category"]

        try:
            payload_json = json.dumps(payload)
        except Exception as e: # pylint: disable=broad-exception-caught
            print("JSON ERROR for", key, ":", e)
            continue

        try:
            mqtt.send_mqtt(topic, payload_json)
        except Exception as e: # pylint: disable=broad-exception-caught
            print("MQTT ERROR for", key, ":", e)

def publish_ruuvi_to_ha(mac, data):
    # mac should be lowercase hex without colons: "aa11bb22cc33"
    #log.debug(f"Publishing RuuviTag data to HA for {mac}: {data}", "ruuvi")
    topic = f"ruuvi/{mac}/data"
    payload = json.dumps(data)
    mqtt.send_mqtt(topic, payload)

#Callback handler that receives a tuple of data from the RuuviTag class object
#RuuviTagRAWv2(mac=b'f34584d173cb', rssi=-100, format=5, humidity=91.435, temperature=9.01,
#pressure=101617, acceleration_x=-20, acceleration_y=-40, acceleration_z=1020,
#battery_voltage=2851, power_info=4, movement_counter=122, measurement_sequence=31396)
def ruuvicb(ruuvitag):
    global last_ruuvi, last_ruuvi_time, no_ruuvi_since_start, got_one, scanning, found, discovered_macs # pylint: disable=global-statement
    #elapsed = utime.ticks_diff(utime.ticks_ms(),last_ruuvi) / 1000
    if not ruuvitag is None:
        mac = ruuvitag.mac.decode('ascii')
        if mac not in discovered_macs:
            discovered_macs.add(mac)
            log.debug(f"Discovered new RuuviTag: {mac}", "ruuvi")
            publish_discovery(mac)
        last_ruuvi = utime.ticks_ms()
        last_ruuvi_time = strftime()
        got_one = True
        tagwhere = mytags[ruuvitag.mac.decode('ascii')]
        found.append(tagwhere)
        #log.debug(f"Processing data for {tagwhere} RuuviTag","ruuvi")
        if mqtt.client is not False:
            data = {}
            for thing in ["temperature", "humidity", "pressure", "battery_voltage", "rssi"]:
                print(f"{thing}: {getattr(ruuvitag, thing)}")
                value = getattr(ruuvitag, thing)
                if thing == "battery_voltage":
                    thing = "battery"
                    value = value / 1000
                if thing == "battery":
                    data["battery_percent"] = battery_voltage_to_percent(value)
                else:
                    data[thing] = value
                topic = thing+"/"+tagwhere
                if thing == "pressure":
                    value = value / 100
                if not thing in ["rssi"]:
                    mqtt.send_mqtt(topic,str(value))
            publish_ruuvi_to_ha(ruuvitag.mac.decode('ascii'), data)
        no_ruuvi_since_start = False
    else: #scanning finished
        scanning = False
        #log.debug("Scanning complete","ruuvi")
        #if len(set(ruuvi._blacklist)) > bl:
        #    bl = len(set(ruuvi._blacklist))
        #    log.status(f"Blacklist now {bl}")
        if got_one:
            #log.debug(f"Found: {','.join(found)}","ruuvi")
            found = []
        else:
            log.status("No tags found")

def get_readings(timeout=70000):
    global got_one, scanning # pylint: disable=global-statement
    ruuvi_elapsed = utime.ticks_diff(utime.ticks_ms(),last_ruuvi)
    #Check we've got an update from RuuviTag
    #log.debug(f"Time since last RuuviTag reading: {ruuvi_elapsed}ms","ruuvi")
    if ruuvi_elapsed > timeout and not no_ruuvi_since_start and not got_one: #over a minute since we got one, and we've had one since start, so something is wrong
        log.debug("No RuuviTag data for more than timeout, returning false","ruuvi")
        get_status()
        return False
    elif scanning:
        log.debug("Still scanning for RuuviTags, please wait...","ruuvi")
    elif  ((ruuvi_elapsed >= 10000 and not got_one) #keep trying every 10 seconds
       or (ruuvi_elapsed >= 60000 and got_one)):  #wait 60 seconds after we got one
        #Get Ruuvi Data
        scanning = True #to avoid multiple scans kicking off
        got_one = False #about to kick off a scan, so reset this to false until we get a callback
        if ruuvi_elapsed < 60000 and not no_ruuvi_since_start:
            log.debug("Retrying scan...","ruuvi")
        #else:
            #log.debug("Scanning...","ruuvi")
        ruuvi.scan(ruuvicb) #scans for 5 seconds
    #else:
    #    log.debug("RuuviTag data is recent, no need to scan","ruuvi")
    return True

#Inititialise Ruuvi
log.debug("Initialising Ruuvi","ruuvi")
ruuvi = RuuviTag()

#ruuvi._callback_handler = ruuvicb # pylint: disable=protected-access
last_ruuvi = utime.ticks_add(utime.ticks_ms(),-30000)
last_ruuvi_time = strftime()
