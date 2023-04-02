#Utility functions to do pretty things with a WS2812 LED strip
import time
import utils.mqtt as mqtt
import utils.myid as myid
from utils.colours import colours

from lib.neopixel import Neopixel
from math import sin, radians, sqrt
import random
    
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
    (h, _, v) = rgb_to_hsv(r/255,g/255,b/255)
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
        for new_brightness in range(start, end, step):
            set_brightness(new_brightness)
            time.sleep(sleepstep)
        #status("Fade complete")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness",str(brightness))

#Function to set the speed during demo sequences
def set_colour(new_colour):
    global colour
    if not colour == new_colour:
        colour = new_colour
        set_all(colour[0],colour[1],colour[2])
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
    now_running("Rainbow")
    set_speed(75)
    hue = 0
    t = millis()
    while not stop:
        check_mqtt()
        colour = strip.colorHSV(hue, 255, 255)
        #Returns list (r, g, b)
        strip.fill(colour)
        strip.show()
        hue += 150
        if hue > 65535:
            hue -= 65535
#        if ticks_diff(t, millis()) > 1000:
#            hexcolour = "#%02x%02x%02x" % (colour[0],colour[1],colour[2])
#            mqtt.send_mqtt("pico/"+myid.pico+"/status/colour",str(hexcolour))
#            t = millis()
        time.sleep(dyndelay / 1000)
    set_all(0, 0, 0)
    now_running("None")

#Step round the colour palette, with a 120 degree offset based on the pico ID
def xmas():
    now_running("Christmas")
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
#        if ticks_diff(t, millis()) > 1000:
#            hexcolour = "#%02x%02x%02x" % (colour[0],colour[1],colour[2])
#            mqtt.send_mqtt("pico/"+myid.pico+"/status/colour",str(hexcolour))
#            t = millis()
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
    mqtt.send_mqtt("pico/"+myid.pico+"/status/running",str(new_effect))

#LED control function to accept commands and launch effects
def led_control(command="",arg=""):
    global stop, saturation, next_up, auto
    if command.startswith("rgb"):
        #rgb(219, 132, 56)
        try:
            r, g, b = [int(x) for x in command[4:-1].split(", ")]
            set_colour([r, g, b])
        except:
            status("Invalid RGB command: {}".format(command))
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
        status("Setting auto to {}".format(arg))
        if arg == "off":
            auto = False
        else:
            auto = True
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
                status("Main caught exception:\n{}".format(output.getvalue()))
        
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
    set_colour([0, 255, 255])
    set_speed(speed)
    mqtt.send_mqtt("pico/"+myid.pico+"/status/auto","off")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness","0")
    #now_running("None")

numPixels = 0
pixel_colours = []
colour = [0, 0, 0]
saturation = 100
speed = 90
dyndelay = 0
brightness = -1
stop = False
running = False
lightsoff = True
effect = "None"
next_up = "None"
auto = False

effects = { "rainbow":  rainbow,
            "xmas":     xmas,
            "off":      off }
