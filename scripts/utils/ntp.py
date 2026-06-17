#Util module to set the system clock from NTP
import socket
import time
import struct
import machine # type: ignore # pylint: disable=import-error
from utils.timeutils import strftime
from utils import log

NTP_DELTA = 2208988800
host = "condor"

def set_time(ntphost=host):
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    try:
        log.status(f"Getting NTP time from {ntphost}", logit=True)
        addr = socket.getaddrinfo(ntphost, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(10)
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        s.close()
    except Exception as e: # pylint: disable=broad-exception-caught
        log.status(f"Exception getting NTP from {ntphost}", logit=True, handling_exception=True)
        log.log_exception(e)
        return False
    #status("NTP fetch was successful")
    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    return True

#Attempt NTP sync
def do_ntp_sync():
    """Function to do NTP Time Sync"""
    #Sync the time up
    if not set_time():
        log.status("Failed to set time", logit=True)
        return False
    else:
        log.status(f"{strftime()}")
        return True
