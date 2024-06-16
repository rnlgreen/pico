#Util module to set the system clock from NTP
import socket
import time
import struct
import machine # type: ignore # pylint: disable=import-error
from utils import log

NTP_DELTA = 2208988800
host = "0.uk.pool.ntp.org"

def set_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    try:
        addr = socket.getaddrinfo(host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(10)
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        s.close()
    except Exception as e: # pylint: disable=broad-exception-caught
        log.status("Exception getting NTP", logit=True, handling_exception=True)
        log.log_exception(e)
        return False
    #status("NTP fetch was successful")
    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    return True
