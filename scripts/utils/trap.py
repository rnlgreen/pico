"""Trigger script to record and report the status of the mouse trap"""
#Uses the tilt switches on GPIO 15 (pin 10) and GPIO 3 (pin 5)
#Switches should be attached to the GPIO pin and to ground
#Allows for some flutter on the horizontal

import time
from machine import Pin, RTC as rtc, PWM # type: ignore # pylint: disable=import-error
from utils import myid # pylint: disable=import-error
from utils import mqtt # pylint: disable=import-error
from utils.blink import blink # pylint: disable=import-error,no-name-in-module

do_beam = True
do_servo = True

BEAM_PIN = 22
SERVO_PIN = 28

TESTING = False

start_angle = -5
end_angle = 10
min_duty = 1900 #through testing this is a reasonable approximation for -90 degrees

'''
traps = {
            "Trap 1": {"button": Pin(16, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0},
            "Trap 2": {"button": Pin(17, Pin.IN, Pin.PULL_UP), "sprung": True, "spring trigger": 0}
}
'''

traps = {}

#Return formatted time string
def strftime():
    """Return formatted time string"""
    timestamp=rtc().datetime()
    timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] + timestamp[4:7])
    return timestring

#Send alert
def send_alert(sensor,message):
    """Send alert"""
    print(f"Sending alert {message}")
    topic = "pico/"+myid.pico+"/alerts/"+sensor
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

#Print and send status messages
def status(message):
    """report status"""
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    if mqtt.client is not False:
        mqtt.send_mqtt(topic,message)

def get_status():
    """get status"""
    if do_servo:
        if done_servo:
            status("Servo has been triggered")
        else:
            status("Servo still primed")

    for t in traps: # pylint: disable=consider-using-dict-items
        #Pin will be high (1) if open, as we are using pull-up logic
        if traps[t]["sprung"] is False:
            status(f"{t} is set")
        else:
            status(f"{t} is sprung")

#Callback function for when the IR Beam state changes
#pin_details contains something like Pin(22, mode=IN, pull=PULL_UP)
def break_beam_callback(pin_details):
    """Beam callback"""
    global ir_last_sent, done_servo # pylint: disable=global-statement
    dt = strftime()
    print(f"Beam break for pin {pin_details}")
    #Blink the LED - useful when testing the trap
    blink(0.2,0,1)
    #Check trap status and only send status updates and alerts if the trap is open
    if not traps["Trap 1"]["sprung"]:
        #If we haven't triggered the trap previously then do it now
        if not done_servo:
            status(f"{dt}: Closing trap!")
            send_alert("beam",":mouse: IR beam broken, closing trap!")
            set_servo(end_angle)
            time.sleep(5)
            set_servo(start_angle)
            done_servo = True
        #Otherwise send periodic notices of activity detected, although we shouldn't ever get here
        elif time.time() - ir_last_sent > 300:
            ir_last_sent = time.time()
            status("Motion detected but already done servo; trap should be closed")
        else:
            print("Waiting for time to elapse before another alert is sent")
    elif time.time() - ir_last_sent > 300:
        ir_last_sent = time.time()
        status(f"{dt}: beam broken in closed trap")

#Servo control to trigger the trap on IR Beam break
#Updated allow for -90 to +90 as that's more accurate
def set_servo(angle):
    #Validate the angle in case I get it wrong
    angle = max(min(90,angle),-90)

    #servo control
    #Declare PWM Pin
    frequency = 50
    servo = PWM(Pin(SERVO_PIN))
    servo.freq(frequency)

    #some documentation suggests duty of:
    # 1ms = 0 degrees, 1.5ms = 90 degrees, 2ms = 180 degrees (based on 20ms (50Hz) cycle)
    #https://youtu.be/_fdwE4EznYo sees similar behaviour as me,
    #he goes 0.5ms-2.5ms to get the full range on his servo
    #micropython is from 0 to 65536, so 0 is 0% duty and 65536 is 100% duty,
    #so should need range 3276.8 to 6553.6, mid point 4915.2
    #that you-tuber would need 1638.4 to 8192
    #from testing it seems my motor needs 2000 to 7830 (same mid point of 4915)
    #duty = 1000 + angle * 50.0/9.0
    mid_duty = 65536*1.5/20

    #returns [min_duty -> (mid_duty + min_duty)] for -90 to 90
    duty = int(mid_duty + (angle * (mid_duty - min_duty))/90)
    print(f"Setting angle to {angle}, duty {duty}")
    servo.duty_u16(duty)
    time.sleep(0.1)
    servo.deinit()

#Servo control tester
def set_duty(duty):
    #Declare PWM Pin
    frequency = 50
    servo = PWM(Pin(SERVO_PIN))
    servo.freq(frequency)
    print(f"Setting duty {duty}")
    servo.duty_u16(duty)
    time.sleep(0.5)
    servo.deinit()

def trap():
    """Check trap status"""
    dt = strftime()
    for t in traps: # pylint: disable=consider-using-dict-items
        #Pin will be high (1) if open, as we are using pull-up logic
        #which for tilt switch is when the trap is closed
        if traps[t]["button"].value() == 0:
            if TESTING:
                print(f"{t} Set")
            else:
                if traps[t]["sprung"]:
                    #Blink the LED - useful when testing the trap
                    blink(0.1,0.05,3)
                    traps[t]["sprung"] = False
                    status (f"{t} is set")
                    traps[t]["spring trigger"] = 0
                #else:
                #    print ("{} already set".format(trap))
        else:
            if TESTING:
                print(f"{t} Sprung")
            else:
                if not traps[t]["sprung"]:
                    #counter to allow for some flutter and make sure it is closed and staying closed
                    traps[t]["spring trigger"] += 1
                    #Blink the LED - useful when testing the trap
                    blink(0.1,0.05,3)
                    if traps[t]["spring trigger"] > 0:
                        traps[t]["sprung"] = True
                        print  (f"{dt}: {t} is sprung")
                        send_alert (t,f":mouse_trap: {t} sprung!!!")
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
    set_servo(start_angle)
    status("Servo initialised")

if __name__ == "__main__":
    while True:
        trap()
        time.sleep(0.1)
