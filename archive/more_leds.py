"""Utility functions to do pretty things with a WS2812 LED strip"""
import time
from math import sqrt, sin, radians  # Used in bouncing_balls
import random
import utime # type: ignore # pylint: disable=import-error
from utils import mqtt
from utils import myid
from utils import light
from utils import log

from utils.colours import colours

from lib.neopixel import Neopixel # pylint: disable=import-error

log.DEBUGGING = False

#INITIAL_COLOUR = [0, 255, 255] #CYAN
INITIAL_COLOUR = [210, 200, 160]
INITIAL_COLOUR_COMMAND = "rgb(" + ", ".join(map(str,INITIAL_COLOUR)) + ")"

#Light thresholds
DIM = 45
BRIGHT = 55 #(was 55)

#Light On/Off Schedule
LIGHTS_OFF = 0
LIGHTS_ON = 7

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
        if (hour >= LIGHTS_ON or hour < LIGHTS_OFF) and not test_off: #e.g. from > 7 or < 0
            #Turn off for high light levels
            if lightlevel > BRIGHT and not lightsoff:
                log.status("Turning lights off (auto)")
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
                            log.status("Turning lights on")
                            if previously_running != "":
                                log.status(f"Restarting {previously_running}")
                                send_control(previously_running)
                            else:
                                if colour == [0, 0, 0]:
                                    send_control(INITIAL_COLOUR_COMMAND)
                        # log.status(f"Brightness {brightness} -> {new_brightness_level}")
                        send_control(f"brightness:{new_brightness_level}")
                        updated = True
                    else:
                        msg = f"Skipping brightness change {brightness} -> {new_brightness_level}"
                        msg += f" to avoid flutter ({h}), brightness: {lightlevel}"
                        log.debug(msg)
        elif not lightsoff: #If out of control hours then turn off
            log.status("Turning lights off (auto)")
            if running: #Remember if we were running a lighting effect before we turn off
                log.status(f"Remembering effect: {effect}")
                previously_running = effect
            else:
                previously_running = ""
            send_control("auto_off")
            updated = True
    return updated

# Convert a list [1, 2, 3] to integer values, and adjust for saturation
def list_to_rgb(c, p=100):
    """Convert list to rgb values"""
    #Sometimes we get a tuple that is 3 long so need to allow for that
    if len(c) == 3:
        c = list(c) + [0]

    if p == 100:
        r, g, b, _ = c
    else:
        r, g, b, _ = (min(255, int(int(x) * (p / 100.0))) for x in c)

    if saturation != 100:
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
    h = 0
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
        log.status(f"Out of range pixel: {i}")
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

#Check if it is time to finish, if we are running standalone
def time_to_go():
    return (stop_after > 0 and time.time() > stop_after)

#Rotate the strip through a rainbow of colours
def rainbow():
    """Rainbow sequence"""
    global colour # pylint: disable=global-statement
    global hue # pylint: disable=global-statement
    now_running("Rainbow")
    #set_speed(75)
    hue = 0
    t = millis()
    n = 0
    updated = False
    while not stop and not time_to_go():
        check_mqtt()
        colour = strip.colorHSV(hue, 255, 255)
        #Returns list (r, g, b)
        strip.fill(colour)
        strip.show()
        hue += 100
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
    #set_all(0, 0, 0)
    now_running("None")

# Rainbow2 function - cycle  every colour of the rainbow across all the pixels
def rainbowCycle(iterations=0):
    now_running("rainbowCycle")
    speedfactor = 1  # smaller is faster, no less than 0.1
    limit_run = iterations > 0
    while not (stop or (limit_run and iterations == 0)) and not time_to_go():
        if pause:
            wait_for_pause()
        for j in range(256):
            for i in range(numPixels):
                r, g, b, w = list_to_rgb(wheel((int(i * 256 / numPixels) + j) & 255))
                set_pixel(i, r, g, b, w)
#                if lcd_effects and i == numPixels / 2:
#                    set_lcd_colour(wheel((int(i * 256 / numPixels) + j) & 255))
            show()
            sleep(dyndelay * speedfactor / 1000.0)  # Needs to run a bit faster than others
            if stop:
                break
        if limit_run:
            iterations -= 1
    now_running("None")

#Step round the colour palette, with a 120 degree offset based on the pico ID
def xmas():
    """xmas sequence"""
    global colour, hue # pylint: disable=global-statement
    now_running("Christmas")
    #lightsoff = False
    set_speed(75)
    #Setup the starting hue. We are using the strip.colorHSV() function that expects 0 to 65535.
    #We are using picos 3, 4, 5 and X (!)
    if myid.pico == "picoX":
        hue = int(3 * 163484)
    else:
        hue = int((-3 + int(myid.pico[4])) * 16384)
    t = millis()
    colour = strip.colorHSV(hue, 255, 255) # hue (0-65535), saturation (0-255), brightness (0-255)
    #Returns list (r, g, b)
    strip.fill(colour)
    strip.show()
    n = 0
    while not stop and not time_to_go():
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
    #set_all(0, 0, 0)
    now_running("None")

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
        #status("LEDs Off")

# MORE LED ROUTINES
## NOTES:
# New routines need "" removed and check_mqtt() adding to the main loop

# First dummy functions for "debuglog" to save me from editing stuff
def debuglog(message):
    log.status(message)

def wait_for_pause():
    return

def show():
    strip.show()

def sleep(s):
    time.sleep(s)

#Function to sleep for 'countdown' seconds whilst keeping an eye on stop
def sleep_for(countdown):
    loop_sleep = 0.5
    countdown = countdown / loop_sleep
    while not stop and countdown > 0:
        check_mqtt()
        sleep(0.5)
        countdown -= 1

# Static colour setting, used by statics_cycle
def static(block_size, colour_list, transition_time=5):
    debuglog(f"static: {block_size}, {colour_list}")
    num_colours = len(colour_list)
    #debuglog(f"Number of colours: {num_colours}")
    br = [0] * LED_COUNT
    bg = [0] * LED_COUNT
    bb = [0] * LED_COUNT
    bw = [0] * LED_COUNT
    fr = [0] * LED_COUNT
    fg = [0] * LED_COUNT
    fb = [0] * LED_COUNT
    fw = [0] * LED_COUNT

    #work out the new pixel colours
    for p in range(numPixels):
        c = int(p / block_size) % num_colours
        fr[p], fg[p], fb[p], fw[p] = list_to_rgb(colour_list[c])
        if p < 10:
            debuglog(f"{p}: {fr[p]}, {fg[p]}, {fb[p]}, {fw[p]}")
    #get the current pixel colours
    for p in range(numPixels):
        br[p], bg[p], bb[p], bw[p] = get_pixel_rgb(p)

    #Now fade quickly from old to new
    for intensity in range(51):
        for i in range(numPixels):
            r, g, b, w = fade_rgb(fr[i], fg[i], fb[i], fw[i], br[i], bg[i], bb[i], bw[i], intensity / 10)
            set_pixel(i, r, g, b, w)
        show()
        sleep(transition_time / 50)
    #debuglog("Exiting")

# Cycling static display
# Random block size
# Goes from 2 to 5 colours
# Steps round the wheel by 34 degress
# Random saturation
def statics_cycle(sleep_time=20):
    global saturation # pylint: disable=global-statement
    now_running("statics_cycle")
    base_wheel_pos = 0
    num_colours = 2
    while not stop and not time_to_go():
        check_mqtt()
        debuglog(f"base_wheel_pos: {base_wheel_pos}")
        if pause:
            wait_for_pause()
        block_size = random.randint(2,3)
        num_colours += 1
        if num_colours > 4:
            num_colours = 2
        static_colours = [[]] * num_colours
        #wheel uses saturation, so pick one of those first
        saturation = random.randint(75,100)
        #saturation = 100
        static_colours[0] = wheel(base_wheel_pos)
        for c in range(num_colours):
            wheel_pos = base_wheel_pos + c * (int(255 / num_colours))
            if wheel_pos > 255:
                wheel_pos -= 255
            static_colours[c] = wheel(wheel_pos)
        static(block_size,static_colours,5)
        #Step round the wheel by slightly less than a quarter
        base_wheel_pos += 34
        if base_wheel_pos > 255:
            base_wheel_pos -= 256
        sleep_for(sleep_time)
    now_running("None")

#Lighting effect to create a twinkling/shimmer effect along the length of the lights
def shimmer(shimmer_width=5,iterations=0):
    global colour # pylint: disable=global-statement
    now_running("shimmer")
    if colour == [0, 0, 0]: #if the colour is black
        colour = colours["gold"]
    limit_run = iterations > 0
    #Even numbers of steps mean pixels turn off at the lowest level
    #eg. width 6, or width 5 with a 0.5 delta
    loop_delta = 0.2 #1 gives 100,60,20 brightness, 0.5 gives 100,80,60,40,20,0 levels
    while not (stop or (limit_run and iterations == 0)) and not time_to_go():
        check_mqtt()
        if pause:
            wait_for_pause()
        j = 0
        while j < shimmer_width:
            for i in range(numPixels):
                p = 100 * abs(((i+j)%shimmer_width - shimmer_width/2) / (shimmer_width / 2))
                r, g, b, w = list_to_rgb(colour, p)
                set_pixel(i, r, g, b, w)
            show()
            sleep(dyndelay * loop_delta / 1000.0)  # the more steps the lower the sleep time
            if stop:
                break
            j += loop_delta
        if limit_run:
            iterations -= 1
    now_running("None")

#Return splash parameters, used by splashing
class splash(): # pylint: disable=missing-class-docstring
    def __init__(self, c):
        self.new(c)

    def new(self, c):
        colour_spread = 15     #spread of colours around the wheel
        (r, g, b, _) = list_to_rgb(c)
        (h, _, v) = rgb_to_hsv(r/255,g/255,b/255)
        c = h * 255 + random.randint(int(-colour_spread/2), int(colour_spread/2))
        if not 0 < c < 255:
            c = c % 256

        brightness_spread = 30  #spread of brightness
        p = max(10, 50 * v + random.randint(-brightness_spread, brightness_spread))

        self.colour   = list_to_rgb(wheel(c), p)
        self.size     = random.randint(1,4)
        self.radius   = int(self.size * numPixels / 64) #No science in the divider at the end!
        self.origin   = random.randint(0,numPixels-1)
        self.speed    = 360 / self.size #will be factored by the elapsed miiliseconds
        self.rotation = 0

    def rotate(self,elapsed):
        delta = self.speed * elapsed * max(1,speed) / 15000 #Changed from 60000 to 15000 to speed things up
        self.rotation += delta * speed / 100                #Added speed factor

#Splash puddles of colour at target pixel (class version)
def splashing(num=5,colour_list=[],leave=False): # pylint: disable=dangerous-default-value
    global colour # pylint: disable=global-statement
    #debuglog(f"Starting with num: {num} and colour list: {colour_list}")
    now_running("splashing")
    rand_colours = False
    colour_index = 0
    #Start by resetting to the background colour
    br, bg, bb, bw = list_to_rgb(colour)
    #set_all(br, bg, bb, bw)
    led_colours = [[br, bg, bb, bw]] * LED_COUNT

    splashes = []

    # Pick a wheel position to splash
    if len(colour_list) == 0:
        colour = list_to_rgb(wheel(random.randint(0, 255)))
        colour_list.append(colour)
    elif "-1" in colour_list[0]:
        rand_colours = True

    # Populate all the splashes with new values
    for s in range(num):
        if rand_colours:
            colour = list_to_rgb(wheel(random.randint(0, 255)))
        else:
            colour = colour_list[colour_index]
            colour_index += 1
            if colour_index == len(colour_list):
                colour_index = 0
        splashes.append(splash(colour))

    #Grab the current time in millisecons
    t = millis()
    iterations = 0
    total_elapsed = 0

    while num > 0:
        check_mqtt()

        if pause:
            wait_for_pause()

        if leave:
            for p in range(numPixels):
                led_colours[p] = list(get_pixel_rgb(p))
        else:
            led_colours = [[0, 0, 0, 0]] * LED_COUNT

        changed = [False] * LED_COUNT

        #Get the elapsed time since last time we were here
        elapsed = millis() - t
        total_elapsed += elapsed
        iterations += 1
        t = millis()
        for s in range(num):
            #Calculate the new splash rotation based on speed, elapsed time and a factor of the overall display speed
            splashes[s].rotate(elapsed)

            #If the splash angle goes above 180 it's time to create a new splash
            if splashes[s].rotation > 180 or (leave and splashes[s].rotation >= 90):
                if not stop and not time_to_go():
                    if rand_colours:
                        colour = wheel(random.randint(0, 255))
                    else:
                        colour = colour_list[colour_index]
                        colour_index += 1
                        if colour_index == len(colour_list):
                            colour_index = 0
                    splashes[s].new(colour)
                else:
                    debuglog(f"Dropping splash {s}")
                    num -= 1
                    splashes.pop(s)
                    break

            # Calculate the colour levels for this splash
            fr, fg, fb, fw = list_to_rgb(splashes[s].colour)

            #Loop over length of the wave
            splash_width = int(sin(radians(splashes[s].rotation)) * splashes[s].size)
            splash_start = max(0, splashes[s].origin - splash_width)
            splash_end   = min(numPixels - 1, splashes[s].origin + splash_width)
            for p in range(splash_start, splash_end + 1):
                #Now add the splash to the current led_colours
                if not leave:
                    led_colours[p] = [min(255, x+y) for x,y in zip(led_colours[p],[fr, fg, fb, fw])]
                else:
                    led_colours[p] = [fr, fg, fb, fw]
                changed[p] = True

        #Now set the pixels that need changing
        for p in range(numPixels):
            set_pixel(p, led_colours[p][0], led_colours[p][1], led_colours[p][2], led_colours[p][3])
        show()

        sleep(0.005) # Sleep a little to give the CPU a break
    #debuglog(f"Average elapsed time: {total_elapsed / iterations}ms")
    now_running("None")

# Class the defines an individual twink
class twink: #pylint: disable=missing-class-docstring
    #On creation of a twink call new() to initialise settings
    def __init__(self, twinkling_start, colour_list, colour_index):
        self.new(twinkling_start, colour_list, colour_index)

    #Function to generate a new set of twink settings when one expires
    def new(self, twinkling_start, colour_list, colour_index):
        m = millis()
        if twinkling_start: #quick start if first time around
            self.start    = m + (random.randint(0,250) * 100 / max(5, speed))
            self.end      = self.start + (random.randint(100,500) * 100 / max(5, speed))
        else:
            self.start    = m + (random.randint(250,500) * 100 / max(5, speed))
            self.end      = self.start + (random.randint(750,1250) * 100 / max(5, speed))
        self.position = random.randint(0, numPixels - 1)
        self.colour   = colour_list[colour_index]

# One funtion to manage lots of twinkles - using twink class
def twinkling(num=0,colour_list=[]): #pylint: disable=dangerous-default-value
    now_running("twinkling")
    if num == 0:
        if colour_list == []: #fewer pixels needed if all white
            numTwinkles = int(numPixels / 5) # some number of twinkles to do
        else:
            numTwinkles = int(numPixels / 2) # some number of twinkles to do
    else:
        numTwinkles = num

    if colour_list == []:
        colour_list = [[255, 255, 255, 255]]

    debuglog(f"Number of twinkles: {numTwinkles}")

    colour_index   = 0
    old_speed = speed
    twinkling_start = True
    count_lit = 0

    twinks = []

    #Initialise all the twinks
    for _ in range(numTwinkles):
        twinks.append(twink(twinkling_start, colour_list, colour_index))
        colour_index += 1
        if colour_index == len(colour_list):
            colour_index = 0

    #Time to fade the pixels in and out, in milliseconds
    fade_time = 150

    while not stop or count_lit > 0 and not time_to_go():
        check_mqtt()
        if pause:
            wait_for_pause()

        #start by clearing all pixels
        last_colour = colour
        r, g, b, w = list_to_rgb(last_colour)
        set_all(r, g, b, w)
        count_lit = 0
        m = millis()
        for t in range(numTwinkles):
            #If this twinkle has out lived it's life:
            if m > twinks[t].end: #time to turn this one off
                if not stop: #if we are not stopping then reset the twink
                    if old_speed == speed: #same speed, so just reset the twink
                        twinks[t].new(twinkling_start, colour_list, colour_index)
                        colour_index += 1
                        if colour_index >= len(colour_list):
                            colour_index = 0
                    else: #just pick a new end time and keep it lit for now
                        twinks[t].end = twinks[t].start + (random.randint(750,1250) * 100 / max(5, speed))
                        if not twinks[t].colour == last_colour:
                            r, g, b, w = list_to_rgb(twinks[t].colour)
                        count_lit += 1
                        set_pixel(twinks[t].position,r, g, b, w)
            #if we are displaying this twinkle:
            elif twinks[t].start < m < twinks[t].end:
                if old_speed != speed: #speed has changed so adjust the end time by a random proportion
                    twinks[t].end =  twinks[t].end + (random.randint(750,1250) * 100 / max(5, speed)) * random.uniform(0, 1)
                #Now set the colour for this pixel
                count_lit += 1
                #Adjust the pixel intensity to fade in and out
                if (twinks[t].start + fade_time) < m < (twinks[t].end - fade_time):
                    #if not twinks[t].colour == last_colour:   # <--- what is this doing!!?
                    r, g, b, w = list_to_rgb(twinks[t].colour)
                else:
                    if m - twinks[t].start < fade_time:
                        b = 100 * (m - twinks[t].start) / fade_time
                    else:
                        b = 100 * (twinks[t].end - m) / fade_time
                    r, g, b, w = list_to_rgb(twinks[t].colour,b)
                set_pixel(twinks[t].position,r, g, b, w)
            else: #not time to turn this on yet, but might want to adjust the start time
                if stop: #set end time to 0 to avoid turning this on in the future
                    twinks[t].end = 0
                elif old_speed != speed: #speed has changed so adjust the start time by a random proportion
                    twinks[t].start = twinks[t].start + (random.randint(250,500) * 100 / max(5, speed)) * random.uniform(0, 1)

        twinkling_start = False
        #debuglog("Speed now {:>3}; currently lit: {:>3}".format(speed,count_lit))
        show()
        old_speed = speed

        #Sleep a bit to give the pi a rest
        sleep(0.005)
    now_running("None")

#Off command called via manage_lights through MQTT
def auto_off():
    #log.status("Running off(True)")
    off(True)

#Function to report now running, also used to trigger the next effect if switching from one to another
def now_running(new_effect): #new_effect is the name of the new effect that just launched
    """Report what is running"""
    global effect, stop, running, next_up # pylint: disable=global-statement
    if new_effect == "None":
        #reset running and stop flags
        running = False
        stop = False
        if not effect == "None":  # we running something so log that it finished
            log.status(f"Completed {effect}")
        if not next_up == "stopping": # pylint: disable=used-before-assignment
            if not next_up == "None":
                new_effect = next_up # store 'next_up' as 'new_effect' so that we can reset 'next_up'
                next_up = "None"
                led_control(payload=new_effect)
            else:
                pass
                #off()
        else:
            #Just stopping existing effect to set new_effect to "None" and leave the lights on
            next_up = "None"
    else:
        running = True
        log.status(f"Starting {new_effect}")
    effect = new_effect
    log.status(f"Running: {running}; previously_running: {previously_running}; effect: {effect}")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/running",str(new_effect))

#LED control function to accept commands and launch effects
def led_control(topic="", payload=""):
    """Process control commands"""
    #Topic is /pico/lights or /pico/xlights with the command in payload with args after a colon
    #Standalone mode sends topic "standalone xlights" and the payload routines have a duration after the colon
    global saturation, next_up, auto, hue, boost, stop, xsync, stop_after # pylint: disable=global-statement
    log.status(f"received command {topic} {payload}")
    arg = ""
    if ":" in payload:
        command, arg = payload.lower().strip().split(":")
    else:
        command = payload.lower().strip()
    if xstrip:
        if "xlights" not in topic and not xsync:
            log.status(f"xstrip ignoring {topic}")
            return
        if command == "xsync":
            if arg == "on":
                xsync = True
            else:
                xsync = False
    if command.startswith("rgb"):
        #rgb(219, 132, 56)
        try:
            r, g, b = [int(x) for x in command[4:-1].split(", ")]
            set_colour([r, g, b])
        except: # pylint: disable=bare-except
            log.status(f"Invalid RGB command: {command}")
    elif command == "hue":
        h = arg
        h = int(h) + 225
        hue = h
    elif command == "brightness":
        b = arg
        new_brightness(int(b))
    elif command == "speed":
        s = arg
        set_speed(int(s))
    elif command == "saturation":
        s = arg
        saturation = int(s)
        log.status(f"Saturation set to: {s}")
    elif command == "auto":
        log.status(f"Turning auto {arg}")
        if arg == "off":
            auto = False
        else:
            auto = True
        if master:
            mqtt.send_mqtt("pico/"+myid.pico+"/status/auto",arg)
    elif command == "boost":
        log.status(f"Turning boost {arg}")
        if arg == "off":
            boost = False
            log.status("Boost off")
        else:
            boost = True
            log.status("Boost on")
        if master:
            manage_lights()
    else:
        #If running and command is an effect turn the lights off and queue up the new effect
        if running:
            if command not in ["off","auto_off"]:
                next_up = command #Store the new routine so that it gets called by ""
            stop = True
            #effects[command]()
        else: #otherwise just run the effect or off
            if command != "stopping":
                try:
                    #status(f"Calling {effects[command]}")
                    if arg != "":
                        stop_after = time.time() + int(arg)
                    effects[command]()
                except Exception as e: # pylint: disable=broad-exception-caught
                    import io # pylint: disable=import-outside-toplevel
                    import sys # pylint: disable=import-outside-toplevel
                    output = io.StringIO()
                    #status("main.py caught exception: {}".format(e))
                    sys.print_exception(e, output) # pylint: disable=no-member
                    exception = output.getvalue()
                    log.status(f"Main caught exception:\n{exception}")
                    import utils.slack as slack
                    slack.send_msg(myid.pico,f"{myid.pico} caught exception:\n{exception}")

#Check for new MQTT instructions
def check_mqtt():
    """check for new mqtt messages"""
    if mqtt.client:
        mqtt.client.check_msg()

def init_strip(strip_type="GRBW",pixels=16,GPIO=0,x=False):
    """Initialise new pixel strip"""
    global numPixels, LED_COUNT # pylint: disable=global-statement
    global strip # pylint: disable=global-statement
    global pixel_colours # pylint: disable=global-statement
    global xstrip # pylint: disable=global-statement

    numPixels = pixels
    LED_COUNT = numPixels

    if x:
        xstrip = True

    #Create strip object
    #parameters: number of LEDs, state machine ID, GPIO number and mode (RGB or RGBW)
    log.status("Initialising strip")
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

numPixels = 0 # Set during init_strip, called by the pico'x'.py with the appropriate number
LED_COUNT = 0
pixel_colours = []
colour = [0, 0, 0]
saturation = 100
hue = 0
speed = 90
dyndelay = 0
brightness = -1
stop = False
pause = False
running = False             # Flag to say if we are running a light sequence or not
lightsoff = True            # Flag to say if the lights are off or not
effect = "None"             # The currently running effect
next_up = "None"            # Set to "command", a key value for effects (perhaps should be the value?)
auto = True                 # Automatic light brightness control
boost = False               # Add a litle more to the auto lighting
previously_running = ""     # Remember what we were running when we automatically turn the lights off
last_lights = 0
master = False
test_off = False
strip = False
xstrip = False
xsync = True
stop_after = 0

effects = { "rainbow":   rainbow,
            "xmas":      xmas,
            "off":       off,
            "auto_off":  auto_off,
            "statics":   statics_cycle,
            "shimmer":   shimmer,
            "splashing": splashing,
            "twinkle": twinkling,
            }

where = myid.where[myid.pico]
