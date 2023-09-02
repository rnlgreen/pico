#Some time related functions
import time # type: ignore
from machine import RTC as rtc # type: ignore

#Return formatted time string
def strftime():
    timestamp=rtc().datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

#Report back the uptime based on the initialisation time
def uptime(timeInit):  
    timeDiff = time.time()-timeInit  
    (minutes, seconds) = divmod(timeDiff, 60)  
    (hours, minutes) = divmod(minutes, 60)  
    (days,hours) = divmod(hours, 24)
    #what to do comes next, I serial printed it for now  
    return(str(days)+":"+f"{hours:02d}"+":"+f"{minutes:02d}"+":"+f"{seconds:02d}")  
