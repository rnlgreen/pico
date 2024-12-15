"""Utility functions to do pretty things with a WS2812 LED strip"""
import time
from math import sin, radians  # Used in bouncing_balls
import random
import utime # type: ignore # pylint: disable=import-error
from utils import myid
from utils import log
from utils import settings
from utils import light
from utils.colours import colours
from utils.common import list_to_rgb, set_pixel, sleep_for
from utils.common import sleep, time_to_go, check_mqtt, wheel, rgb_to_hsv
from utils.common import get_pixel_rgb, fade_rgb
from utils.common import millis, set_all, show, hsv_to_colour, ticks_diff
from utils.common import send_control, send_colour, set_speed, set_brightness
from utils.common import off, auto_off, set_colour, new_brightness, mqtt
#from utils.more_leds2 import statics_cycle, twinkling, splashing, shimmer

from lib.neopixel import Neopixel # pylint: disable=import-error

log.DEBUGGING = False

INITIAL_COLOUR = [210, 200, 160]
INITIAL_COLOUR_COMMAND = "rgb(" + ", ".join(map(str,INITIAL_COLOUR)) + ")"

#Light thresholds
DIM = 45
BRIGHT = 55 #(was 55)

#Light On/Off Schedule
LIGHTS_OFF = 0
LIGHTS_ON = 7

def init_strip(strip_type="GRBW",pixels=16,GPIO=0):
    """Initialise new pixel strip"""
    settings.numPixels = pixels
    settings.LED_COUNT = pixels

    #Create strip object
    #parameters: number of LEDs, state machine ID, GPIO number and mode (RGB or RGBW)
    log.status("Initialising strip")
    #strip = Neopixel(numPixels, 0, 0, "GRBW")
    settings.strip = Neopixel(pixels, 0, GPIO, strip_type)
    settings.pixel_colours = [[0, 0, 0, 0]] * pixels
    set_brightness(0)
    set_colour(INITIAL_COLOUR)
    set_speed(settings.speed)
    settings.strip.clear()
    show()
    if settings.master:
        mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness","0")
        mqtt.send_mqtt("pico/"+myid.pico+"/status/auto","on")
        mqtt.send_mqtt("pico/"+myid.pico+"/status/boost","off")
    #now_running("None")

#LED control function to accept commands and launch effects
def led_control(topic="", payload=""):
    """Process control commands"""
    #Topic is pico/lights or pico/xlights with the command in payload with args after a colon
    #Standalone mode sends topic "standalone xlights" and the payload routines have a duration after the colon
    log.status(f"received topic:{topic} payload:{payload}")
    arg = ""
    if ":" in payload:
        command, arg = payload.lower().strip().split(":")
    else:
        command = payload.lower().strip()
    log.status(f"command:{command} arg:{arg}")
    if settings.xstrip:
        if "xlights" not in topic and not settings.xsync:
            log.status(f"xstrip ignoring {topic}")
            return
        if command == "xsync":
            if arg == "on":
                settings.xsync = True
            else:
                settings.xsync = False
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
        settings.hue = h
    elif command == "brightness":
        b = arg
        new_brightness(int(b))
    elif command == "speed":
        s = arg
        set_speed(int(s))
    elif command == "saturation":
        s = arg
        settings.saturation = int(s)
        log.status(f"Saturation set to: {s}")
    elif command == "auto":
        log.status(f"Turning auto {arg}")
        if arg == "off":
            settings.auto = False
        else:
            settings.auto = True
        if settings.master:
            mqtt.send_mqtt("pico/"+myid.pico+"/status/auto",arg)
    elif command == "boost":
        log.status(f"Turning boost {arg}")
        if arg == "off":
            settings.boost = False
            log.status("Boost off")
        else:
            settings.boost = True
            log.status("Boost on")
        if settings.master:
            manage_lights()
    else:
        #If running and command is an effect turn the lights off and queue up the new effect
        if settings.running:
            if command not in ["off","auto_off"]:
                settings.next_up = command #Store the new routine so that it gets called by ""
            settings.stop = True
            #effects[command]()
        else: #otherwise just run the effect or off
            if command != "stopping":
                try:
                    #status(f"Calling {effects[command]}")
                    if arg != "":
                        if arg == "-1":
                            settings.stop_after = -1
                        else:
                            settings.stop_after = time.time() + int(arg)
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

#Rotate the strip through a rainbow of colours
def rainbow():
    """Rainbow sequence"""
    now_running("Rainbow")
    #set_speed(75)
    settings.hue = 0
    t = millis()
    n = 0
    updated = False
    while not settings.stop and not time_to_go():
        check_mqtt()
        settings.colour = hsv_to_colour(settings.hue, 255, 255)
        #Returns list (r, g, b)
        set_all(settings.colour)
        show()
        settings.hue += 100
        if settings.hue > 65535:
            settings.hue -= 65535
            if settings.master and settings.auto: #if this is the master pico then send the new settings.hue to the others
                send_control(f"hue:{settings.hue}")
        #Only pico5 controls the brightness using the light sensor
        if settings.master and settings.auto:
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
        time.sleep(settings.dyndelay / 1000)
    #set_all(0, 0, 0)
    now_running("None")

# Rainbow2 function - cycle  every settings.colour of the rainbow across all the pixels
def rainbowCycle(iterations=0):
    now_running("rainbowCycle")
    speedfactor = 1  # smaller is faster, no less than 0.1
    limit_run = iterations > 0
    while not (settings.stop or (limit_run and iterations == 0)) and not time_to_go():
        check_mqtt()
        for j in range(256):
            for i in range(settings.numPixels):
                r, g, b, w = list_to_rgb(wheel((int(i * 256 / settings.numPixels) + j) & 255))
                set_pixel(i, r, g, b, w)
#                if lcd_effects and i == numPixels / 2:
#                    set_lcd_colour(wheel((int(i * 256 / numPixels) + j) & 255))
            show()
            sleep(settings.dyndelay * speedfactor / 1000.0)  # Needs to run a bit faster than others
            if settings.stop:
                break
        if limit_run:
            iterations -= 1
    now_running("None")

#Step round the settings.colour palette, with a 120 degree offset based on the pico ID
def xmas():
    """xmas sequence"""
    now_running("Christmas")
    #lightsoff = False
    set_speed(75)
    #Setup the starting settings.hue. We are using the strip.colorHSV() function that expects 0 to 65535.
    #We are using picos 3, 4, 5 and X (!)
    if myid.pico == "picoX":
        settings.hue = int(3 * 163484)
    else:
        settings.hue = int((-3 + int(myid.pico[4])) * 16384)
    t = millis()
    settings.colour = hsv_to_colour(settings.hue, 255, 255) # settings.hue (0-65535), settings.saturation (0-255), brightness (0-255)
    #Returns list (r, g, b)
    set_all(settings.colour)
    show()
    n = 0
    while not settings.stop and not time_to_go():
        check_mqtt()
        settings.colour = hsv_to_colour(settings.hue, 255, 255)
        #Returns list (r, g, b)
        set_all(settings.colour)
        show()
        settings.hue += 64
        if settings.hue > 65535:
            settings.hue -= 65535
        #Only pico5 controls the brightness using the light sensor
        if settings.master and settings.auto:
            if ticks_diff(t, millis()) > 1000:
                n += 1
                manage_lights()
                t = millis()
        if settings.master:
            if n >= 5:
                send_colour()
                n = 0
        time.sleep(settings.dyndelay / 1000)
    #set_all(0, 0, 0)
    now_running("None")

#Function to report now running, also used to trigger the next effect if switching from one to another
def now_running(new_effect): #new_effect is the name of the new effect that just launched
    """Report what is running"""
    if new_effect == "None":
        #reset running and settings.stop flags
        settings.running = False
        settings.stop = False
        if settings.effect != "None":  # we running something so log that it finished
            log.status(f"Completed {settings.effect}")
        if not settings.next_up == "stopping": # pylint: disable=used-before-assignment
            if not settings.next_up == "None":
                new_effect = settings.next_up # store 'next_up' as 'new_effect' so that we can reset 'next_up'
                settings.next_up = "None"
                led_control(payload=new_effect)
            else:
                pass
                #off()
        else:
            #Just stopping existing effect to set new_effect to "None" and leave the lights on
            settings.next_up = "None"
    else:
        settings.running = True
        log.status(f"Starting {new_effect}")
    settings.effect = new_effect
    log.status(f"Running: {settings.running}; previously_running: {settings.previously_running}; effect: {settings.effect}")
    mqtt.send_mqtt("pico/"+myid.pico+"/status/running",str(new_effect))

#Routine to manage LED brightness
# #Control LEDs based on light and time of day
#Returns True if lights were updated so we can slow the rate of changes
def manage_lights():
    """Update lights based on light levels"""
    #Get the latest rolling average light level
    lightlevel = light.rolling_average()
    #Flag whether we changed the lights or not
    updated = False

    if settings.auto:
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
        if (hour >= LIGHTS_ON or hour < LIGHTS_OFF): #e.g. from > 7 or < 0
            #Turn off for high light levels
            if lightlevel > BRIGHT and not settings.lightsoff:
                log.status("Turning lights off (auto)")
                log.debug("lightlevel: {lightlevel}")
                if settings.running: #Remember if we were running a lighting effect before we turn off
                    settings.previously_running = settings.effect
                else:
                    settings.previously_running = ""
                send_control("auto_off")
                updated = True
            #Turn on or adjust for low light levels
            elif lightlevel < DIM:
                #New brightness something between 10 and 80 step 5
                new_brightness_level = light.get_brightness(lightlevel,settings.boost)
                #If the brightness level has changed check for hysteresis
                h = light.check_hysteresis(lightlevel)
                if settings.brightness != new_brightness_level:
                    #Only change for large steps or significant hysteresis
                    if abs(new_brightness_level - settings.brightness) > 5 or  h > 0.1:
                        #If the lights are off then we need to turn them on
                        if settings.lightsoff:
                            log.status("Turning lights on")
                            if settings.previously_running != "":
                                log.status(f"Restarting {settings.previously_running}")
                                send_control(settings.previously_running)
                            else:
                                if settings.colour == [0, 0, 0]:
                                    send_control(INITIAL_COLOUR_COMMAND)
                        # log.status(f"Brightness {brightness} -> {new_brightness_level}")
                        send_control(f"brightness:{new_brightness_level}")
                        updated = True
                    else:
                        msg = f"Skipping brightness change {settings.brightness} -> {new_brightness_level}"
                        msg += f" to avoid flutter ({h}), brightness: {lightlevel}"
                        log.debug(msg)
        elif not settings.lightsoff: #If out of control hours then turn off
            log.status("Turning lights off (auto)")
            if settings.running: #Remember if we were running a lighting effect before we turn off
                log.status(f"Remembering effect: {settings.effect}")
                settings.previously_running = settings.effect
            else:
                settings.previously_running = ""
            send_control("auto_off")
            updated = True
    return updated
# MORE LED ROUTINES
## NOTES:
# New routines need "" removed and check_mqtt() adding to the main loop

# First dummy functions for "debuglog" to save me from editing stuff
def debuglog(message):
    log.status(message)

# Static colour setting, used by statics_cycle
def static(block_size, colour_list, transition_time=5):
    debuglog(f"static: {block_size}, {colour_list}")
    num_colours = len(colour_list)
    #debuglog(f"Number of colours: {num_colours}")
    br = [0] * settings.numPixels
    bg = [0] * settings.numPixels
    bb = [0] * settings.numPixels
    bw = [0] * settings.numPixels
    fr = [0] * settings.numPixels
    fg = [0] * settings.numPixels
    fb = [0] * settings.numPixels
    fw = [0] * settings.numPixels

    #work out the new pixel colours
    for p in range(settings.numPixels):
        c = int(p / block_size) % num_colours
        fr[p], fg[p], fb[p], fw[p] = list_to_rgb(colour_list[c])
        #if p < 10:
        #    debuglog(f"{p}: {fr[p]}, {fg[p]}, {fb[p]}, {fw[p]}")
    #get the current pixel colours
    for p in range(settings.numPixels):
        br[p], bg[p], bb[p], bw[p] = get_pixel_rgb(p)

    #Now fade quickly from old to new
    for intensity in range(51):
        for i in range(settings.numPixels):
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
def statics_cycle(sleep_time=5):
    now_running("statics_cycle")
    base_wheel_pos = 0
    num_colours = 2
    while not settings.stop and not time_to_go():
        check_mqtt()
        debuglog(f"base_wheel_pos: {base_wheel_pos}")
        block_size = random.randint(2,5)
        num_colours += 1
        if num_colours > 4:
            num_colours = 2
        static_colours = [[]] * num_colours
        #wheel uses saturation, so pick one of those first
        #settings.saturation = random.randint(75,100)
        settings.saturation = 100
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

#Lighting effect to create a shimmer effect along the length of the lights
def shimmer(shimmer_width=5,iterations=0):
    now_running("shimmer")
    if settings.colour == [0, 0, 0]: #if the colour is black
        settings.colour = colours["gold"]
    limit_run = iterations > 0
    #Even numbers of steps mean pixels turn off at the lowest level
    #eg. width 6, or width 5 with a 0.5 delta
    loop_delta = 0.2 #1 gives 100,60,20 brightness, 0.5 gives 100,80,60,40,20,0 levels
    while not (settings.stop or (limit_run and iterations == 0)) and not time_to_go():
        check_mqtt()
        j = 0
        while j < shimmer_width:
            for i in range(settings.numPixels):
                p = 100 * abs(((i+j)%shimmer_width - shimmer_width/2) / (shimmer_width / 2))
                r, g, b, w = list_to_rgb(settings.colour, p)
                set_pixel(i, r, g, b, w)
            show()
            sleep(settings.dyndelay * loop_delta / 1000.0)  # the more steps the lower the sleep time
            if settings.stop:
                break
            j += loop_delta
        if limit_run:
            iterations -= 1
    now_running("None")

#Return splash parameters, used by splashing
class splash(): # pylint: disable=missing-class-docstring
    def __init__(self, colour):
        self.new(colour)

    def new(self, colour):
        colour_spread = 15     #spread of colours around the wheel
        (r, g, b, _) = list_to_rgb(colour)
        (h, _, v) = rgb_to_hsv(r/255,g/255,b/255)
        c = h * 255 + random.randint(int(-colour_spread/2), int(colour_spread/2))
        if not 0 < c < 255:
            c = c % 256

        brightness_spread = 30  #spread of brightness
        p = max(10, 50 * v + random.randint(-brightness_spread, brightness_spread))

        self.colour   = list_to_rgb(wheel(c), p)
        self.size     = random.randint(1,settings.splash_size)
        self.radius   = int(self.size * settings.numPixels / 64) #No science in the divider at the end!
        self.origin   = random.randint(0,settings.numPixels-1)
        self.speed    = 360 / self.size #will be factored by the elapsed miiliseconds
        self.rotation = 0

    def rotate(self,elapsed):
        delta = self.speed * elapsed * max(1,settings.speed) / 15000 #Changed from 60000 to 15000 to speed things up
        self.rotation += delta * settings.speed / 100                #Added speed factor

#Splash puddles of colour at target pixel (class version)
#"leave" is for painting - leaves the splash behind
def splashing(num=5,colour_list=["-1"],leave=False): # pylint: disable=dangerous-default-value
    debuglog(f"Starting with num: {num} and colour list: {colour_list}")
    now_running("splashing")
    rand_colours = False
    colour_index = 0
    #Start by resetting to the background colour
    br, bg, bb, bw = list_to_rgb(settings.colour)
    #set_all(br, bg, bb, bw)
    led_colours = [[br, bg, bb, bw]] * settings.LED_COUNT

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
        if leave:
            for p in range(settings.numPixels):
                led_colours[p] = list(get_pixel_rgb(p))
        else:
            br, bg, bb, bw = list_to_rgb(settings.colour)
            led_colours = [[br, bg, bb, bw]] * settings.LED_COUNT

        #changed = [False] * settings.LED_COUNT

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
                if not settings.stop and not time_to_go():
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
            splash_end   = min(settings.numPixels - 1, splashes[s].origin + splash_width)
            for p in range(splash_start, splash_end + 1):
                #Now add the splash to the current led_colours
                if not leave:
                    led_colours[p] = [min(255, x+y) for x,y in zip(led_colours[p],[fr, fg, fb, fw])]
                else:
                    led_colours[p] = [fr, fg, fb, fw]
                #changed[p] = True

        #Now set the pixels that need changing
        for p in range(settings.numPixels):
            set_pixel(p, led_colours[p][0], led_colours[p][1], led_colours[p][2], led_colours[p][3])
        show()

        sleep(0.005) # Sleep a little to give the CPU a break
    now_running("None")

# Class the defines an individual twink
class twink: # pylint: disable=missing-class-docstring
    #On creation of a twink call new() to initialise settings
    def __init__(self, twinkling_start, colour_list, colour_index):
        self.new(twinkling_start, colour_list, colour_index)

    #Function to generate a new set of twink settings when one expires
    def new(self, twinkling_start, colour_list, colour_index):
        m = millis()
        if twinkling_start: #quick start if first time around
            self.start    = m + (random.randint(0,250) * 100 / max(5, settings.speed))
            self.end      = self.start + (random.randint(100,500) * 100 / max(5, settings.speed))
        else:
            self.start    = m + (random.randint(250,500) * 100 / max(5, settings.speed))
            self.end      = self.start + (random.randint(750,1250) * 100 / max(5, settings.speed))
        self.position = random.randint(0, settings.numPixels - 1)
        self.colour   = colour_list[colour_index]

# One funtion to manage lots of twinkles - using twink class
def twinkling(num=0,colour_list=[]): # pylint: disable=dangerous-default-value
    debuglog(f"Starting with num: {num} and colour list: {colour_list}")
    if num == 0:
        if colour_list == []: #fewer pixels needed if all white
            numTwinkles = int(settings.numPixels / 5) # some number of twinkles to do
        else:
            numTwinkles = int(settings.numPixels / 2) # some number of twinkles to do
    else:
        numTwinkles = num

    if colour_list == []:
        colour_list = [[255, 255, 255, 255]]

    debuglog(f"Number of twinkles: {numTwinkles}")

    colour_index   = 0
    old_speed = settings.speed
    twinkling_start = True
    count_lit = 0

    if settings.cycle:
        settings.hue = 0
        settings.colour = hsv_to_colour(settings.hue,255,30)

    twinks = []

    #Initialise all the twinks
    for _ in range(numTwinkles):
        twinks.append(twink(twinkling_start, colour_list, colour_index))
        colour_index += 1
        if colour_index == len(colour_list):
            colour_index = 0

    #Time to fade the pixels in and out, in milliseconds
    fade_time = 150

    while count_lit > 0 or not (settings.stop or time_to_go()):
        check_mqtt()
        #start by clearing all pixels
        if settings.cycle:
            settings.hue += 10
            if settings.hue > 65535:
                settings.hue -= 65535
            settings.colour = hsv_to_colour(settings.hue,255,30)
        last_colour = settings.colour
        r, g, b, w = list_to_rgb(last_colour)
        set_all(r, g, b, w)
        count_lit = 0
        m = millis()
        for t in range(numTwinkles):
            #If this twinkle has out lived it's life:
            if m > twinks[t].end: #time to turn this one off
                if not settings.stop and not time_to_go(): #if we are not stopping then reset the twink
                    if old_speed == settings.speed: #same speed, so just reset the twink
                        twinks[t].new(twinkling_start, colour_list, colour_index)
                        colour_index += 1
                        if colour_index >= len(colour_list):
                            colour_index = 0
                    else: #just pick a new end time and keep it lit for now
                        twinks[t].end = twinks[t].start + (random.randint(750,1250) * 100 / max(5, settings.speed))
                        if not twinks[t].colour == last_colour:
                            r, g, b, w = list_to_rgb(twinks[t].colour)
                        count_lit += 1
                        set_pixel(twinks[t].position,r, g, b, w)
            #if we are displaying this twinkle:
            elif twinks[t].start < m < twinks[t].end:
                if old_speed != settings.speed: #speed has changed so adjust the end time by a random proportion
                    twinks[t].end =  twinks[t].end + (random.randint(750,1250) * 100 / max(5, settings.speed)) * random.uniform(0, 1)
                #Now set the colour for this pixel
                count_lit += 1
                #Adjust the pixel intensity to fade in and out
                if (twinks[t].start + fade_time) < m < (twinks[t].end - fade_time):
                    #if not twinks[t].colour == last_colour:   # <--- what is this doing!!?
                    r, g, b, w = list_to_rgb(twinks[t].colour)
                else:
                    if m - twinks[t].start < fade_time:
                        brightness = 100 * (m - twinks[t].start) / fade_time
                    else:
                        brightness = 100 * (twinks[t].end - m) / fade_time
                    r, g, b, w = list_to_rgb(twinks[t].colour,brightness)
                set_pixel(twinks[t].position,r, g, b, w)
            else: #not time to turn this on yet, but might want to adjust the start time
                if settings.stop or time_to_go(): #set end time to 0 to avoid turning this on in the future
                    twinks[t].end = 0
                elif old_speed != settings.speed: #speed has changed so adjust the start time by a random proportion
                    twinks[t].start = twinks[t].start + (random.randint(250,500) * 100 / max(5, settings.speed)) * random.uniform(0, 1)

        twinkling_start = False
        #debuglog("Speed now {:>3}; currently lit: {:>3}".format(settings.speed,count_lit))
        show()
        old_speed = settings.speed

        #Sleep a bit to give the pi a rest
        sleep(0.005)
    now_running("None")

effects = { "rainbow":   rainbow,
            "rainbow2":  rainbowCycle,
            "xmas":      xmas,
            "off":       off,
            "auto_off":  auto_off,
            "statics":   statics_cycle,
            "twinkling": twinkling,
            "splashing": splashing,
            "shimmer":   shimmer,
            }

where = myid.where[myid.pico]
