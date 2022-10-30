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
def send_mqtt(topic,message):
    print("{}: {}".format(topic,message))
    if client != False:
        mqtt.send_mqtt(client,topic,message)

#Send alert 
def send_alert(sensor,message):
    print("Sending alert {}".format(message))
    topic = "pico/"+pico+"/alerts/"+sensor
    send_mqtt(topic,message)

#Print and send status messages
def status(message):
    print(message)
    message = pico + ": " + message
    topic = 'pico/'+pico+'/status'
    send_mqtt(topic,message)

#Callback function for when the IR Beam state changes
#pin_details contains something like Pin(22, mode=IN, pull=PULL_UP)
def break_beam_callback(pin_details):
    global ir_last_sent, done_servo
    dt = strftime()
    status("{}: beam broken".format(dt))
    blink(0.2,0,1)
    if time.time() - ir_last_sent > 5:
        ir_last_sent = time.time()
        sprung = False
        #Check trap status and only send alerts if the trap is open
        if not traps["Trap 1"]["sprung"]:
            print("Infrared beam broken, triggering servo")
            send_alert("beam",":mouse: infrared beam has been broken!")
            if not done_servo:
                status("Closing trap!")
                set_servo(180)
                time.sleep(5)
                set_servo(0)
                done_servo = True
            else:
                print("Motion detected but already done servo")
        else:
            print("Motion detected but already sprung")
    else:
        print("Waiting for time to elapse before another alert is sent")
        #send_status("Motion detected too soon to process")

#Servo control to trigger the trap on IR Beam break
def set_servo(angle):
    #Declare PWM Pin
    frequency = 50
    servo = PWM(Pin(SERVO_PIN))
    servo.freq(frequency)
    #some documentation suggests 1000ms = 0 degrees, 1500 = 90 degrees, 2000 = 180 degrees
    #duty = 1000 + angle * 50.0/9.0
    #but micropython says it's from 0 to 65536
    #and from testing it seems my moto takes 2000 to 8000!
    duty = int(angle * 6000 / 180) + 2000
    print("Setting angle to {}, duty {}".format(angle,duty))
    servo.duty_u16(duty)
    time.sleep(0.5)
    servo.deinit()

def trap():
    dt = strftime()
    for trap in (traps):
        if traps[trap]["button"].value() == 1:
            if traps[trap]["sprung"]:
                traps[trap]["sprung"] = False
                status ("{} is set".format(trap))
                traps[trap]["spring trigger"] = 0
            #else:
            #    print ("{} already set".format(trap))
        else:
            if not traps[trap]["sprung"]:
                traps[trap]["spring trigger"] += 1
                if (traps[trap]["spring trigger"] > 5):
                    traps[trap]["sprung"] = True
                    print  ("{}: {} is sprung".format(dt,trap))
                    send_alert (trap,":mouse_trap: {} sprung!!!".format(trap))
            #else:
            #    print ("{} already sprung".format(trap))

pico = myid.get_id()

#Try and connect to MQTT
client = mqtt.mqtt_connect(client_id=pico+'-trap')
if client == False:
    status("Trap failed to connect to MQTT")
else:
    status("Trap MQTT initialised")

if do_beam:
    beam = Pin(BEAM_PIN, Pin.IN, Pin.PULL_UP)
    ir_last_state = "unbroken"
    #Set time last sent to 5 seconds in the future to allow for setup
    ir_last_sent = time.time() + 5
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