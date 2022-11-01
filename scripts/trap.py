#Trigger script to record and report the status of the mouse trap 
#Uses the tilt switches on GPIO 15 (pin 10) and GPIO 3 (pin 5)
#Switches should be attached to the GPIO pin and to ground
#Allows for some flutter on the horizontal

from machine import Pin, RTC as rtc, PWM # type: ignore
import time
import utils.myid as myid
import utils.mqtt as mqtt
from utils.blink import blink

do_beam = True
do_servo = True

BEAM_PIN = 22
SERVO_PIN = 28

traps = {
            "Trap 1": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0}
}

'''
traps = {
            "Trap 1": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0},
            "Trap 2": {"button": Pin(17, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0}
}
'''

#Return formatted time string
def strftime():
    timestamp=rtc().datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

#Send alert 
def send_alert(sensor,message):
    print("Sending alert {}".format(message))
    topic = "pico/"+myid.pico+"/alerts/"+sensor
    if mqtt.client != False:
        mqtt.send_mqtt(topic,message)

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client != False:
        mqtt.send_mqtt(topic,message)

#Callback function for when the IR Beam state changes
#pin_details contains something like Pin(22, mode=IN, pull=PULL_UP)
def break_beam_callback(pin_details):
    global ir_last_sent, done_servo
    dt = strftime()
    #Blink the LED - useful when testing the trap
    blink(0.2,0,1)
    #Check trap status and only send status updates and alerts if the trap is open
    if not traps["Trap 1"]["sprung"]:
        #If we haven't triggered the trap previously then do it now
        if not done_servo:
            status("{}: Closing trap!".format(dt))
            send_alert("beam",":mouse: IR beam broken, closing trap!")
            set_servo(180)
            time.sleep(5)
            set_servo(0)
            done_servo = True
        #Otherwise send periodic notices of activity detected, although we shouldn't ever get here
        elif time.time() - ir_last_sent > 300:
            ir_last_sent = time.time()
            status("Motion detected but already done servo; trap should be closed")
        else:
            print("Waiting for time to elapse before another alert is sent")
    elif time.time() - ir_last_sent > 300:
        ir_last_sent = time.time()
        status("{}: beam broken in closed trap".format(dt))

#Servo control to trigger the trap on IR Beam break
def set_servo(angle):
    #Declare PWM Pin
    frequency = 50
    servo = PWM(Pin(SERVO_PIN))
    servo.freq(frequency)
    #some documentation suggests 1000ms = 0 degrees, 1500 = 90 degrees, 2000 = 180 degrees
    #duty = 1000 + angle * 50.0/9.0
    #but micropython says it's from 0 to 65536
    #and from testing it seems my motor takes 2000 to 8000!
    duty = int(angle * 6000 / 180) + 2000
    print("Setting angle to {}, duty {}".format(angle,duty))
    servo.duty_u16(duty)
    time.sleep(0.5)
    servo.deinit()

def trap():
    dt = strftime()
    for trap in (traps):
        #Pin will be high (1) if open, as we are using pull-up logic
        if traps[trap]["button"].value() == 1:
            if traps[trap]["sprung"]:
                traps[trap]["sprung"] = False
                status ("{} is set".format(trap))
                traps[trap]["spring trigger"] = 0
            #else:
            #    print ("{} already set".format(trap))
        else:
            if not traps[trap]["sprung"]:
                #Spring trigger is a counter to allow for some flutter and make sure it is closed and staying closed
                traps[trap]["spring trigger"] += 1
                if (traps[trap]["spring trigger"] > 5):
                    traps[trap]["sprung"] = True
                    print  ("{}: {} is sprung".format(dt,trap))
                    send_alert (trap,":mouse_trap: {} sprung!!!".format(trap))
            #else:
            #    print ("{} already sprung".format(trap))

if do_beam:
    beam = Pin(BEAM_PIN, Pin.IN, Pin.PULL_UP)
    #Set time last sent to the past so we get alerts straight away
    ir_last_sent = time.time() - 300
    beam.irq(break_beam_callback, Pin.IRQ_FALLING)
    status("IR Beam enabled")

if do_servo:
    done_servo = False
    set_servo(0)
    status("Servo initialised")

if __name__ == "__main__":
    while True:
        trap()
        time.sleep(0.25)