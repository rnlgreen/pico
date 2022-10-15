#Trigger script to record and report the status of the mouse trap 
#Uses the tilt switches on GPIO 15 (pin 10) and GPIO 3 (pin 5)
#Switches should be attached to the GPIO pin and to ground
#Allows for some flutter on the horizontal

from machine import Pin, RTC as rtc
from time import sleep, time

traps = {
            "Trap 1": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0},
            "Trap 2": {"button": Pin(17, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0}
}

#Return formatted time strin
def strftime():
    timestamp=rtc().datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

def trap():
    dt = strftime()
    while True:
        for trap in (traps):
            if traps[trap]["button"].value() == 1:
                if traps[trap]["sprung"]:
                    traps[trap]["sprung"] = False
                    print  ("{}: {} is set".format(dt,trap))
                    traps[trap]["spring trigger"] = 0
                else:
                    print ("{}:{} already set".format(dt,trap))
            else:
                if not traps[trap]["sprung"]:
                    traps[trap]["spring trigger"] += 1
                    if (traps[trap]["spring trigger"] > 5):
                        traps[trap]["sprung"] = True
                        print  ("{}: {} is sprung".format(dt,trap))
                else:
                    print ("{}: {} already sprung".format(dt,trap))
        sleep(0.25)

if __name__ == "__main__":
    trap()
