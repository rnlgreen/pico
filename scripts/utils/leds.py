#Utility functions to do pretty things with a WS2812 LED strip
import time
import utils.mqtt as mqtt
import utils.myid as myid

from lib.neopixel import Neopixel
from math import sin, pi, radians
#import colorsys
import random

# Convert a list [1, 2, 3] to integer values, and adjust for brightness
def list_to_rgb(c, p=100):
    r, g, b = [min(255, int(int(x) * (p / 100.0))) for x in c]

    if not saturation == 100:
        h, s, v = rgb_to_hsv(r, g, b)
        s = saturation / 100
        #status("h: {}, s: {}, v: {}".format(h, s, v))
        r, g, b = hsv_to_rgb(h, s, v)
        #status("r: {}, g: {}, b: {}".format(r, g, b))
    return r, g, b

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
def fade_rgb(fr, fg, fb, br, bg, bb, factor):
    #Clip factor to a value between 0 and 1
    factor = max(0,min(1,factor))
    r = int(br + (fr - br) * factor)
    g = int(bg + (fg - bg) * factor)
    b = int(bb + (fb - bb) * factor)
    return r, g, b

# Function to return a colour that contrasts to the current background
# either using settings.colour_index (assuming we are cycling) or takes a colour
def contrasting_colour(colour=[]):
    spread = 128
    (r, g, b) = list_to_rgb(colour)
    (h, s, v) = rgb_to_hsv(r/255,g/255,b/255)
    index = h * 255
    if not 0 < index < 255:
        index = index % 256

    c = index + random.randint(0, spread) + int((255 - spread) / 2)
    if c > 255:
        c -= 255
    return wheel(c)

def set_all(r=0, g=0, b=0):
    global colour, pixel_colours
    strip[:] = (r, g, b)
    colour = [r, g, b]
    pixel_colours = [[r, g, b]] * numPixels
    strip.show()

def set_pixel(i=0, r=0, g=0, b=0):
    global pixel_colours
    strip[i] = (r, g, b)
    pixel_colours[i] = [r, g, b]

def get_pixel_rgb(i):
    if i >= numPixels or i < 0:
        status("Out of range pixel: {}".format(i))
        return 0,0,0
    else:
        r, g, b = pixel_colours[i]
        return r, g, b

def rainbow():
    global running, effect, stop
    hue = 0
    if running:
        status("Already running {}".format(effect))
    else:
        effect = "rainbow"
        status("Running {}...".format(effect))
        running = True
        if stop:
            stop = False
        start = time.time()
        while not stop:
            elapsed = time.time()-start
            if elapsed > 0.1:
                if mqtt.client != False:
                    mqtt.client.check_msg() 
                start = time.time()
            color = strip.colorHSV(hue, 255, 150)
            strip.fill(color)
            strip.show()
            hue += 150
            if hue > 65535:
                hue -= 65535
            time.sleep(0.01)
        status("Finished {}".format(effect))
        set_all(0, 0, 0)
        running = False
        stop = False
        effect = "None"

# Function to fade a new colour in from the centre of the strip
# Fades a new colour in from the centre of the strip
def plume(colour, steps=100):
    factor = 3 #defines how quickly the colour fades in, less than 3 doesn't complete the transition
    fr, fg, fb = list_to_rgb(colour)
    #Get the current state of the pixels to use for fading
    br = [0] * numPixels
    bg = [0] * numPixels
    bb = [0] * numPixels
    for i in range(numPixels):
        br[i], bg[i], bb[i] = get_pixel_rgb(i)
    for s in range(steps):
        current_colours = "Step {0:3d}: ".format(s) #string to report to status state of pixels
        for p in range(numPixels):
            #Inverse SIN:
            fade = max(0, min(1,s*factor/steps+2*(sin(radians(180*p/(numPixels - 1)))-1)))
            r, g, b = fade_rgb(fr, fg, fb, br[i], bg[i], bb[i], fade)
            set_pixel(p, r, g, b)
            if p == 0 or p == numPixels / 2 or p == numPixels - 1:
                current_colours += "{0:1.4f}: {1:3d}, {2:3d}, {3:3d}    ".format(fade, r, g, b)
        #status("{}".format(current_colours))
        strip.show()
        if mqtt.client != False:
            mqtt.client.check_msg() 
        time.sleep(dyndelay / 1000.0)  # dyndelay is in milliseconds from 10 to 1000
        if stop:
            break

# Function to call plume continualyl with random colours
def pluming(delay=10):
    global colour, running, effect, stop
    status("Starting pluming with delay {}".format(delay))
    running = True
    effect = "pluming"
    while not stop:
        colour = contrasting_colour(colour) #pick a new colour
        plume(colour) #Call plume with the new colour and the number of steps to take
        countdown = delay
        while not stop and countdown > 0:
            if mqtt.client != False:
                mqtt.client.check_msg() 
            time.sleep(1)
            countdown -= 1
    set_all(0,0,0)
    running = False
    stop = False
    effect = ""
    status("Exiting pluming")

#Stop running functions and if not running turn off
def off():
    global stop
    if running:
        status("Stopping..")
        stop = True
    else:
        set_all(0,0,0)

#LED control function to accept commands and launch effects
def led_control(command=""):
    if command.startswith("rgb"):
        #rgb(219, 132, 56)
        r, g, b = [int(x) for x in command[4:-1].split(", ")]
        set_all(r, g, b)
    elif command.startswith("brightness:"):
        _, b = command.split(":")
        strip.brightness(int(b))
        if not running:
            r, g, b = list_to_rgb(colour)
            set_all(r, g, b)
    elif command.startswith("saturation:"):
        _, s = command.split(":")
        saturation = int(s)
    else:
        try:
            effects[command]()
        except Exception as e:
            status("Exception: {}".format(e))

effects = { "rainbow": rainbow,
            "pluming": pluming,
            "off":     off }

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

numPixels = 8
#Create strip object
#parameters: number of LEDs, state machine ID, GPIO number and mode (RGB or RGBW)
status("Initialising strip")
#strip = Neopixel(numPixels, 0, 0, "GRB")
strip = Neopixel(numPixels, 0, 0, "GRBW")
strip.brightness(20)

colour = [0, 0, 0]
saturation = 100
dyndelay = 30
pixel_colours = [[0, 0, 0]] * numPixels
stop = False
running = False
effect = ""
