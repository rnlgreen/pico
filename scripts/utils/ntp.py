#Util module to set the system clock from NTP
import socket
import time
import struct
import machine # type: ignore # pylint: disable=import-error
from utils import mqtt
from utils import myid

NTP_DELTA = 2208988800
host = "0.uk.pool.ntp.org"

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

def set_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    try:
        addr = socket.getaddrinfo(host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(10)
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    except Exception as e: # pylint: disable=broad-exception-caught
        status(f"Exception getting NTP: {e}")
        return False
    finally:
        s.close()
    #status("NTP fetch was successful")
    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    return True
