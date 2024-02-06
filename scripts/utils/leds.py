"""Utility functions to do pretty things with a WS2812 LED strip"""
import time
from math import sqrt
#import random
import utime # type: ignore # pylint: disable=import-error
from utils import mqtt
from utils import myid
from utils import light
from utils import log

from lib.neopixel import Neopixel # pylint: disable=import-error

log.DEBUGGING = False

#INITIAL_COLOUR = [0, 255, 255] #CYAN
INITIAL_COLOUR = [210, 200, 160]
INITIAL_COLOUR_COMMAND = "rgb(" + ", ".join(map(str,INITIAL_COLOUR)) + ")"

#Light thresholds
DIM = 45
BRIGHT = 55 #(was 55)

#Send control message to MQTT
def send_control(payload):
    """Send message to MQTT"""
    topic = 'pico/lights'
    mqtt.send_mqtt(topic,payload)

#Routine to manage LED brightness
# #Control LEDs based on light and time of day
#Returns True if lights were updated so we can slow the rate of changes
def manage_lights():
    """Update lights based on light levels"""
    global previously_running # pylint: disable=global-statement
    #Get the latest rolling average light level
    lightlevel = light.rolling_average()
    #Flag whether we changed the lights or not
    updated = False

    if auto:
        #Publish light level every 5 seconds
        if time.time() - light.last_reading >= 5:
            lightlevel = light.readLight()
            light.send_measurement(where,"light",lightlevel)
            light.last_reading = time.time()
        #Check time of day first
        hour = utime.localtime()[3]
        #Check month to approximate daylight savings time
        month = utime.localtime()[1]
        if (month > 3 and month < 11):
            hour += 1
            if hour == 23:
                hour = 0
        #Only manage lights between certain hours
        if (hour >= 6 or hour < 2) and not test_off: #from 06:00 to 01:59
            #Turn off for high light levels
            if lightlevel > BRIGHT and not lightsoff:
                status("Turning lights off (auto)")
                log.debug("lightlevel: {lightlevel}")
                if running: #Remember if we were running a lighting effect before we turn off
                    previously_running = effect
                else:
                    previously_running = ""
                send_control("auto_off")
                updated = True
            #Turn on or adjust for low light levels
            elif lightlevel < DIM:
                #New brightness something between 10 and 80 step 5
                new_brightness_level = light.get_brightness(lightlevel,boost)
                #If the brightness level has changed check for hysteresis
                h = light.check_hysteresis(lightlevel)
                if brightness != new_brightness_level:
                    #Only change for large steps or significant hysteresis
                    if abs(new_brightness_level - brightness) > 5 or  h > 0.1:
                        #If the lights are off then we need to turn them on
                        if lightsoff:
                            status("Turning lights on")
                            if previously_running != "":
                                status(f"Restarting {previously_running}")
                                send_control(previously_running)
                            else:
                                if colour == [0, 0, 0]:
                                    send_control(INITIAL_COLOUR_COMMAND)
                        # status(f"Brightness {brightness} -> {new_brightness_level}")
                        send_control(f"brightness:{new_brightness_level}")
                        updated = True
                    else:
                        msg = f"Skipping brightness change {brightness} -> {new_brightness_level}"
                        msg += f" to avoid flutter ({h}), brightness: {lightlevel}"
                        log.debug(msg)
        elif not lightsoff: #If out of control hours then turn off
            status("Turning lights off (auto)")
            if running: #Remember if we were running a lighting effect before we turn off
                status(f"Remembering effect: {effect}")
                previously_running = effect
            else:
                previously_running = ""
            send_control("auto_off")
            updated = True
    return updated

# Convert a list [1, 2, 3] to integer values, and adjust for saturation
def list_to_rgb(c):
    """Convert list to rgb values"""
    r, g, b = c
    if not saturation == 100:
        h, s, v = rgb_to_hsv(r, g, b)
        s = saturation / 100
        r, g, b = hsv_to_rgb(h, s, v)
    return r, g, b, 0

#rgb to hsv conversion - works, but colorsys.rgb_to_hsv is slightly quicker when doing rgb->hsv->rgb
def rgb_to_hsv(r, g, b):
    """rgb to hsv"""
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df/mx)*100
    v = mx*100
    return h, s, v

#Alternative fast hsv to rgb routine
#From https://stackoverflow.com/questions/24852345/hsv-to-rgb-color-conversion
#This code is what is in colorsys but tweaked for improved performance
def hsv_to_rgb(h, s, v):
    """alternative hsv to rgb"""
    if s == 0.0:
        v*=255
        return (v, v, v)
    i = int(h*6.) #assume int() truncates!
    f = (h*6.)-i
    p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f))))
    v*=255
    i%=6
    if i == 0:
        return [v, t, p]
    if i == 1:
        return [q, v, p]
    if i == 2:
        return [p, v, t]
    if i == 3:
        return [p, q, v]
    if i == 4:
        return [t, p, v]
    if i == 5:
        return [v, p, q]

#Alternative wheel based on HSV
def wheel(pos):
    """Return RGB based on Wheel position"""
    sat = saturation / 100
    return hsv_to_rgb(pos/255,sat,1)

# Funtion to fade colours given the foreground, background and a factor
def fade_rgb(fr, fg, fb, fw, br, bg, bb, bw, factor):
    """Return faded RGB values"""
    #Clip factor to a value between 0 and 1
    factor = max(0,min(1,factor))
    r = int(br + (fr - br) * factor)
    g = int(bg + (fg - bg) * factor)
    b = int(bb + (fb - bb) * factor)
    w = int(bw + (fw - bw) * factor)
    return r, g, b, w

#Set the whole strip to a new colour
def set_all(r=0, g=0, b=0, w=0):
    """Set all pixels to new values"""
    global colour, lightsoff # pylint: disable=global-statement
    colour = [r, g, b]
    strip.fill((r, g, b))
    for p in range(numPixels):
        pixel_colours[p] = [r, g, b, w] # pixel_colours doesn't need to be "global" as it is mutated
    strip.show()
    if colour == [0, 0, 0]:
        lightsoff = True
    else:
        lightsoff = False

#Set an individual pixel to a new colour
def set_pixel(i=0, r=0, g=0, b=0, w=0):
    #No need for global when using lists like this
    """Set an individual pixel to a new colour"""
    strip[i] = (r, g, b, w)
    pixel_colours[i] = [r, g, b, w]

#Get the current value for a pixel
def get_pixel_rgb(i):
    """Get current rgb value of pixel"""
    if i >= numPixels or i < 0:
        status(f"Out of range pixel: {i}")
        return 0,0,0,0
    else:
        r, g, b, _ = pixel_colours[i]
        return r, g, b, 0

#Function to set the speed during demo sequences
def set_speed(new_speed):
    """Set update speed for sequences"""
    global speed, dyndelay # pylint: disable=global-statement
    if not speed == new_speed:
        speed = new_speed
        dyndelay = int(1000 - 100 * sqrt(int(speed)))
        mqtt.send_mqtt("pico/"+myid.pico+"/status/speed",str(speed))

#Function to set the brightness
def set_brightness(new_brightness_level):
    """Function to set the brightness"""
    global brightness, lightsoff # pylint: disable=global-statement
    if not brightness == new_brightness_level:
        brightness = new_brightness_level
        strip.brightness(brightness)
        if not running:
            r, g, b, _ = list_to_rgb(colour)
            #need to call set_all as this is what updates pixels with the new brightness level
            #set_all includes a call to strip.show()
            set_all(r, g, b)
        if brightness == 0:
            lightsoff = True
        else:
            lightsoff = False

# Fade to new brightness
def new_brightness(new_level):
    """Fade to new brightness"""
    old_level = brightness
    if new_level != old_level:
        #status("Fading from {} to {}".format(old_level,new_level))
        sleeptime = 1.5 #number of seconds to make the transition
        sleepstep = sleeptime / abs(new_level - old_level)
        if old_level < new_level:
            start = old_level + 1
            end = new_level + 1
            step = 1
        else:
            start = old_level - 1
            end = new_level - 1
            step = -1
        for nb in range(start, end, step):
            set_brightness(nb)
            time.sleep(sleepstep)
        #status("Fade complete")
    if master or not auto:
        mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness",str(brightness))

#Function to set the colour
def set_colour(new_colour):
    """set the colour"""
    global colour # pylint: disable=global-statement
    if not colour == new_colour:
        colour = new_colour
        set_all(colour[0],colour[1],colour[2])
        send_colour()

#Send colour update to NodeRed
def send_colour():
    """Update NodeRed with new colour"""
    if master or not auto:
        hexcolour = f"#{colour[0]:02x}{colour[1]:02x}{colour[2]:02x}"
        mqtt.send_mqtt(f"pico/{myid.pico}/status/colour",str(hexcolour))

# #RGB to hex, used to send updates back to Node-Red
# def rgb_to_hex(rgb):
#     """RGB to Hex for Node-Red"""
#     return '#%02x%02x%02x' % rgb

#Return current time in milliseconds
def millis():
    """Current time in ticks"""
    #return int(round(time.time() * 1000))
    return time.ticks_ms() # pylint: disable=no-member

#Return elapsed time between two ticks
def ticks_diff(start,now):
    """Time delta in ticks"""
    diff = time.ticks_diff(int(now),int(start)) # pylint: disable=no-member
    return diff

#Rotate the strip through a rainbow of colours
def rainbow():
    """Rainbow sequence"""
    global colour # pylint: disable=global-statement
    global hue # pylint: disable=global-statement
    now_running("Rainbow")
    set_speed(75)
    hue = 0
    t = millis()
    n = 0
    updated = False
    while not stop:
        check_mqtt()
        colour = strip.colorHSV(hue, 255, 255)
        #Returns list (r, g, b)
        strip.fill(colour)
        strip.show()
        hue += 150
        if hue > 65535:
            hue -= 65535
            if master and auto: #if this is the master pico then send the new hue to the others
                send_control(f"hue:{hue}")
        #Only pico5 controls the brightness using the light sensor
        if master and auto:
            if ticks_diff(t, millis()) > 1000:
                n += 1
                if not updated:
                    updated = manage_lights()
                else:
                    updated = False
                    light.rolling_average()
                if n >= 5:
                    send_colour()
                    n = 0
                t = millis()
        time.sleep(dyndelay / 1000)
    set_all(0, 0, 0)
    now_running("None")

#Step round the colour palette, with a 120 degree offset based on the pico ID
def xmas():
    """xmas sequence"""
    global colour, hue # pylint: disable=global-statement
    now_running("Christmas")
    #lightsoff = False
    set_speed(75)
    #We are using picos 3, 4, 5
    hue = int(0 + int(myid.pico[4]) * 65536 / 3)
    t = millis()
    colour = strip.colorHSV(hue, 255, 255)
    #Returns list (r, g, b)
    strip.fill(colour)
    strip.show()
    n = 0
    while not stop:
        check_mqtt()
        colour = strip.colorHSV(hue, 255, 255)
        #Returns list (r, g, b)
        strip.fill(colour)
        strip.show()
        hue += 64
        if hue > 65535:
            hue -= 65535
        #Only pico5 controls the brightness using the light sensor
        if master and auto:
            if ticks_diff(t, millis()) > 1000:
                n += 1
                manage_lights()
                t = millis()
        if master:
            if n >= 5:
                send_colour()
                n = 0
        time.sleep(dyndelay / 1000)
    set_all(0, 0, 0)
    now_running("None")

#Train
#New train function with hopefully better logic
def train(num_carriages=5, colour_list=[], iterations=0): # pylint: disable=dangerous-default-value
    """train sequence"""
    status(f"Starting with {num_carriages}, {colour_list}, {iterations}")
    now_running("Train")

    #limit_run is a flag to say whether we are running a limited number of passes
    limit_run = iterations > 0

    if len(colour_list) == 0:
        for c in range(num_carriages):
            colour_list += [wheel(int(255*c/num_carriages))]

    status(f"Colour list: {colour_list}")

    #progression is a counter to say how far the train has travelled
    progression = numPixels
    t = millis()

    while not (stop or (limit_run and iterations == 0)):
        check_mqtt()
        carriage_length = int(numPixels / num_carriages)
        progression += 1
        for i in range(numPixels):
            if progression > i:
                carriage_no = int((progression - i) / carriage_length) % len(colour_list)
                mycolour = colour_list[carriage_no]
                r, g, b, _ = list_to_rgb(mycolour)
            else:
                r, g, b = [0, 0, 0]

            set_pixel(i, r, g, b)
        strip.show()
        if stop:
            break
        #Only pico5 controls the brightness using the light sensor
        if master and auto:
            if ticks_diff(t, millis()) > 10000:
                manage_lights()
                t = millis()
        time.sleep(0.75 * dyndelay / 1000)
    set_all(0, 0, 0)
    now_running("None")
    status("Exiting")

#Stop running functions and if not running turn off
#Called from Node-Red
def off(from_auto=False):
    """All off"""
    global auto, stop, lightsoff, previously_running # pylint: disable=global-statement
    #status(f"called with {from_auto}")
    if not from_auto:
        auto = False
        if master:
            mqtt.send_mqtt("pico/"+myid.pico+"/status/auto","off")
    if running:
        mqtt.send_mqtt("pico/"+myid.pico+"/status/running","stopping...")
        if not from_auto: #if it's an external "off" command then forget what was running
            previously_running = ""
        stop = True
    else:
        new_brightness(0)
        #set_all(0,0,0)
        #hexcolour = "#%02x%02x%02x" % (colour[0],colour[1],colour[2])
        #mqtt.send_mqtt("pico/"+myid.pico+"/status/colour",str(hexcolour))
        strip.clear()
        strip.show()
        lightsoff = True
        status("LEDs Off")

#Off command called via manage_lights through MQTT
def auto_off():
    #status("Running off(True)")
    off(True)

#Function to report now running
def now_running(new_effect):
    """Report what is running"""
    global effect, stop, running, next_up # pylint: disable=global-statement
    if new_effect == "None":
        running = False
        stop = False
        if not effect == "None":
            status(f"Completed {effect}")
        if not next_up == "None":
            new_effect = next_up
            next_up = "None"
            led_control(new_effect)
        else:
            off()
    else:
        running = True
        status(f"Starting {new_effect}")
    effect = new_effect
    status(f"Running: {running}; previously_running: {previously_running}; effect: {effect}")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/running",str(new_effect))

#LED control function to accept commands and launch effects
def led_control(command="",arg=""):
    """Process control commands"""
    command = command.lower()
    #status(f"received command {command}..")
    global saturation, next_up, auto, hue, boost # pylint: disable=global-statement
    if command.startswith("rgb"):
        #rgb(219, 132, 56)
        try:
            r, g, b = [int(x) for x in command[4:-1].split(", ")]
            set_colour([r, g, b])
        except: # pylint: disable=bare-except
            status(f"Invalid RGB command: {command}")
    elif command.startswith("hue:"):
        _, h = command.split(":")
        h = int(h) + 225
        hue = h
    elif command.startswith("brightness:"):
        _, b = command.split(":")
        new_brightness(int(b))
    elif command.startswith("speed:"):
        _, s = command.split(":")
        set_speed(int(s))
    elif command.startswith("saturation:"):
        _, s = command.split(":")
        saturation = int(s)
        status(f"Saturation set to: {s}")
    elif command == "auto":
        status(f"Turning auto {arg}")
        if arg == "off":
            auto = False
        else:
            auto = True
        if master:
            mqtt.send_mqtt("pico/"+myid.pico+"/status/auto",arg)
    elif command == "boost":
        status(f"Turning boost {arg}")
        if arg == "off":
            boost = False
            status("Boost off")
        else:
            boost = True
            status("Boost on")
        if master:
            manage_lights()
    elif command == "test_off":
        toggle_test_off()
    else:
        #If running and command is an effect turn the lights off and queue up the new effect
        if running:
            if command not in ["off","auto_off"]:
                next_up = command
            effects[command]()
        else: #otherwise just run the effect or off
            try:
                #status(f"Calling {effects[command]}")
                effects[command]()
            except Exception as e: # pylint: disable=broad-exception-caught
                import io # pylint: disable=import-outside-toplevel
                import sys # pylint: disable=import-outside-toplevel
                output = io.StringIO()
                #status("main.py caught exception: {}".format(e))
                sys.print_exception(e, output) # pylint: disable=no-member
                exception = output.getvalue()
                status(f"Main caught exception:\n{exception}")
                import utils.slack as slack
                slack.send_msg(myid.pico,f"{myid.pico} caught exception:\n{exception}")

#Print and send status messages
def status(message):
    """report status"""
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

#Check for new MQTT instructions
def check_mqtt():
    """check for new mqtt messages"""
    if not mqtt.client is False:
        mqtt.client.check_msg()

def init_strip(strip_type="GRBW",pixels=16,GPIO=0):
    """Initialise new pixel strip"""
    global numPixels # pylint: disable=global-statement
    global strip # pylint: disable=global-statement
    global pixel_colours # pylint: disable=global-statement

    numPixels = pixels

    #Create strip object
    #parameters: number of LEDs, state machine ID, GPIO number and mode (RGB or RGBW)
    status("Initialising strip")
    #strip = Neopixel(numPixels, 0, 0, "GRBW")
    strip = Neopixel(numPixels, 0, GPIO, strip_type)
    pixel_colours = [[0, 0, 0, 0]] * numPixels
    set_brightness(0)
    set_colour(INITIAL_COLOUR)
    set_speed(speed)
    strip.clear()
    strip.show()
    if master:
        mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness","0")
        mqtt.send_mqtt("pico/"+myid.pico+"/status/auto","on")
        mqtt.send_mqtt("pico/"+myid.pico+"/status/boost","off")
    #now_running("None")

def toggle_test_off():
    """toggle test mode"""
    global test_off # pylint: disable=global-statement
    test_off = not test_off

numPixels = 0
pixel_colours = []
colour = [0, 0, 0]
saturation = 100
hue = 0
speed = 90
dyndelay = 0
brightness = -1
stop = False
running = False
lightsoff = True
effect = "None"
next_up = "None"
auto = True
boost = False
previously_running = ""
last_lights = 0
master = False
test_off = False
strip = False

effects = { "rainbow":  rainbow,
            "xmas":     xmas,
            "train":    train,
            "off":      off,
            "auto_off": auto_off}

where = myid.where[myid.pico]
