#Utility functions to do pretty things with a WS2812 LED strip
import time, utime # type: ignore
import utils.mqtt as mqtt
import utils.myid as myid
import utils.light as light

from utils.colours import colours

from lib.neopixel import Neopixel
from math import sin, radians, sqrt
import random

debugging = False

#INITIAL_COLOUR = [0, 255, 255] #CYAN
INITIAL_COLOUR = [210, 200, 160]
INITIAL_COLOUR_COMMAND = "rgb(" + ", ".join(map(str,INITIAL_COLOUR)) + ")"

#Print and send status messages
def debug(message):
    print(message)
    if debugging:
        message = myid.pico + ": " + message
        topic = 'pico/'+myid.pico+'/debug'
        mqtt.send_mqtt(topic,message)

#Send control message to MQTT
def send_control(payload):
    topic = 'pico/lights'
    mqtt.send_mqtt(topic,payload)

#Routine to manage LED brightness
# #Control LEDs based on light and time of day
#Returns True if lights were updated so we can slow the rate of changes
def manage_lights():
    global previously_running
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
            if (hour == 23):
                hour = 0
        #Only manage lights between certain hours
        DIM = 45
        BRIGHT = 55 #(was 55)
        if (hour >= 6 or hour < 2) and not test_off: #from 06:00 to 01:59
            #Turn off for high light levels
            if lightlevel > BRIGHT and not lightsoff:
                status("Turning lights off")
                debug("lightlevel: {}".format(lightlevel))
                if running: #Remember if we were running a lighting effect before we turn off
                    previously_running = effect
                else:
                    previously_running = ""
                send_control("off")
                updated = True
            #Turn on or adjust for low light levels
            elif lightlevel < DIM:
                #New brightness something between 10 and 80 step 5
                new_brightness = light.get_brightness(lightlevel,boost)
                #If the brightness level has changed check for hysteresis 
                h = light.check_hysteresis(lightlevel)
                if brightness != new_brightness:
                    #Only change for large steps or significant hysteresis
                    if abs(new_brightness - brightness) > 5 or  h > 0.1:
                        #If the lights are off then we need to turn them on
                        if lightsoff:
                            status("Turning lights on")
                            if not previously_running == "":
                                status(f"Restarting {previously_running}")
                                send_control(previously_running)
                            else:
                                if colour == [0, 0, 0]:
                                    send_control(INITIAL_COLOUR_COMMAND)
                        status("Brightness {} -> {}".format(brightness,new_brightness))
                        send_control("brightness:{}".format(new_brightness))
                        updated = True
                    else:
                        debug("Skipping brightness change {} -> {} to avoid flutter ({}), brightness: {}".format(brightness,new_brightness,h,lightlevel))
        elif not lightsoff: #If out of control hours then turn off
            status("Turning lights off")
            if running: #Remember if we were running a lighting effect before we turn off
                status(f"Remembering effect: {effect}")
                previously_running = effect
            else:
                previously_running = ""
            send_control("off")
            updated = True
    return updated
    
# Convert a list [1, 2, 3] to integer values, and adjust for saturation
def list_to_rgb(c):
    r, g, b = c
    if not saturation == 100:
        h, s, v = rgb_to_hsv(r, g, b)
        s = saturation / 100
        r, g, b = hsv_to_rgb(h, s, v)
    return r, g, b, 0

#rgb to hsv conversion - this works, but using colorsys.rgb_to_hsv is slightly quicker especially when doing rgb->hsv->rgb
def rgb_to_hsv(r, g, b):
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
    if s == 0.0: v*=255; return (v, v, v)
    i = int(h*6.) # XXX assume int() truncates!
    f = (h*6.)-i
    p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f))))
    v*=255
    i%=6
    if i == 0: return [v, t, p]
    if i == 1: return [q, v, p]
    if i == 2: return [p, v, t]
    if i == 3: return [p, q, v]
    if i == 4: return [t, p, v]
    if i == 5: return [v, p, q]

#Alternative wheel based on HSV
def wheel(pos):
    sat = saturation / 100
    return hsv_to_rgb(pos/255,sat,1)

# Funtion to fade colours given the foreground, background and a factor
def fade_rgb(fr, fg, fb, fw, br, bg, bb, bw, factor):
    #Clip factor to a value between 0 and 1
    factor = max(0,min(1,factor))
    r = int(br + (fr - br) * factor)
    g = int(bg + (fg - bg) * factor)
    b = int(bb + (fb - bb) * factor)
    w = int(bw + (fw - bw) * factor)
    return r, g, b, w

# Function to return a colour that contrasts to the current background
# either using colour_index (assuming we are cycling) or takes a colour
def contrasting_colour(colour=[]):
    spread = 128
    (r, g, b, _) = list_to_rgb(colour)
    (h, _, _) = rgb_to_hsv(r/255,g/255,b/255)
    index = h * 255
    if not 0 < index < 255:
        index = index % 256

    c = index + random.randint(0, spread) + int((255 - spread) / 2)
    if c > 255:
        c -= 255
    return wheel(c)

#Set the whole strip to a new colour
def set_all(r=0, g=0, b=0, w=0):
    global colour, pixel_colours, lightsoff
    colour = [r, g, b]
    strip.fill((r, g, b))
    for p in range(numPixels):
        pixel_colours[p] = [r, g, b, w]
    strip.show()
    if colour == [0, 0, 0]:
        lightsoff = True
    else:
        lightsoff = False

#Set an individual pixel to a new colour
def set_pixel(i=0, r=0, g=0, b=0, w=0):
    global pixel_colours
    strip[i] = (r, g, b, w)
    pixel_colours[i] = [r, g, b, w]

#Get the current value for a pixel
def get_pixel_rgb(i):
    if i >= numPixels or i < 0:
        status("Out of range pixel: {}".format(i))
        return 0,0,0,0
    else:
        r, g, b, _ = pixel_colours[i]
        return r, g, b, 0

#Function to set the speed during demo sequences
def set_speed(new_speed):
    global speed, dyndelay
    if not speed == new_speed:
        speed = new_speed
        dyndelay = int(1000 - 100 * sqrt(int(speed)))
        mqtt.send_mqtt("pico/"+myid.pico+"/status/speed",str(speed))

#Function to set the speed during demo sequences
def set_brightness(new_brightness):
    global brightness, lightsoff
    if not brightness == new_brightness:
        brightness = new_brightness
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
    old_level = brightness
    if new_level != old_level:
        #status("Fading from {} to {}".format(old_level,new_level))
        sleeptime = 1.5 #number of seconds to make the transition
        sleepstep = (sleeptime / abs(new_level - old_level))
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
    mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness",str(brightness))

#Function to set the colour
def set_colour(new_colour):
    global colour
    if not colour == new_colour:
        colour = new_colour
        set_all(colour[0],colour[1],colour[2])
        send_colour()

#Send colour update to NodeRed
def send_colour():
    if master or not auto:
        hexcolour = "#%02x%02x%02x" % (colour[0],colour[1],colour[2])
        mqtt.send_mqtt("pico/"+myid.pico+"/status/colour",str(hexcolour))

#RGB to hex, used to send updates back to Node-Red
def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

#Return current time in milliseconds
def millis():
    #return int(round(time.time() * 1000))
    return time.ticks_ms()

#Return elapsed time between two ticks
def ticks_diff(start,now):
    diff = time.ticks_diff(int(now),int(start))
    return diff

#Rotate the strip through a rainbow of colours
def rainbow():
    global colour
    global hue
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
    global colour, lightsoff
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
                manage_lights()
                t = millis()
        time.sleep(dyndelay / 1000)
    set_all(0, 0, 0)
    now_running("None")

#Stop running functions and if not running turn off
#Called from Node-Red
def off():
    global stop, lightsoff
    if running:
        mqtt.send_mqtt("pico/"+myid.pico+"/status/running","stopping...")
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

#Function to report now running 
def now_running(new_effect):
    global effect, stop, running, next_up
    if new_effect == "None":
        running = False
        stop = False
        if not effect == "None":
            status("Completed {}".format(effect))
        if not next_up == "None":
            new_effect = next_up
            next_up = "None"
            led_control(new_effect)
        else:
            off()
    else:
        running = True
        status("Starting {}".format(new_effect))
    effect = new_effect
    status(f"Running: {running}; previously_running: {previously_running}; effect: {effect}")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/running",str(new_effect))

#LED control function to accept commands and launch effects
def led_control(command="",arg=""):
    command = command.lower()
    global saturation, next_up, auto, hue, boost
    if command.startswith("rgb"):
        #rgb(219, 132, 56)
        try:
            r, g, b = [int(x) for x in command[4:-1].split(", ")]
            set_colour([r, g, b])
        except:
            status("Invalid RGB command: {}".format(command))
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
    elif command == "auto":
        status(f"Turning auto {arg}")
        if arg == "off":
            auto = False
        else:
            auto = True
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
        #If we are running and the command 
        if running:
            if not command == "off":
                next_up = command
            off()
        else:
            try:
                effects[command]()
            except Exception as e:
                import io
                import sys
                output = io.StringIO()
                #status("main.py caught exception: {}".format(e))
                sys.print_exception(e, output)
                exception = output.getvalue()
                status(f"Main caught exception:\n{exception}")
                import utils.slack as slack
                slack.send_msg(myid.pico,f"{myid.pico} caught exception:\n{exception}")
        
#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

#Check for new MQTT instructions
def check_mqtt():
    if not mqtt.client == False:
        mqtt.client.check_msg() 

def init_strip(strip_type="GRBW",pixels=16,GPIO=0):
    global numPixels
    global strip
    global pixel_colours

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
    mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness","0")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/auto","on")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/boost","off")
    #now_running("None")

def toggle_test_off():
    global test_off
    test_off = not(test_off)

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

effects = { "rainbow":  rainbow,
            "xmas":     xmas,
            "off":      off }

where = myid.where[myid.pico]