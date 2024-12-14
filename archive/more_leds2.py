"""Utility functions to do pretty things with a WS2812 LED settings.strip"""
from math import sin, radians  # Used in bouncing_balls
import random
from utils import log
from utils.common import list_to_rgb, get_pixel_rgb, fade_rgb, set_pixel
from utils.common import sleep, now_running, time_to_go, check_mqtt, wheel, sleep_for
from utils.common import rgb_to_hsv, millis, set_all, show
from utils import settings

from utils.colours import colours

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
        if p < 10:
            debuglog(f"{p}: {fr[p]}, {fg[p]}, {fb[p]}, {fw[p]}")
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
def statics_cycle(sleep_time=20):
    now_running("statics_cycle")
    base_wheel_pos = 0
    num_colours = 2
    while not settings.stop and not time_to_go():
        check_mqtt()
        debuglog(f"base_wheel_pos: {base_wheel_pos}")
        block_size = random.randint(2,3)
        num_colours += 1
        if num_colours > 4:
            num_colours = 2
        static_colours = [[]] * num_colours
        #wheel uses saturation, so pick one of those first
        settings.saturation = random.randint(75,100)
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
    now_running("shimmer")
    if colour == [0, 0, 0]: #if the colour is black
        colour = colours["gold"]
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
                r, g, b, w = list_to_rgb(colour, p)
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
        self.radius   = int(self.size * settings.numPixels / 64) #No science in the divider at the end!
        self.origin   = random.randint(0,settings.numPixels-1)
        self.speed    = 360 / self.size #will be factored by the elapsed miiliseconds
        self.rotation = 0

    def rotate(self,elapsed):
        delta = self.speed * elapsed * max(1,settings.speed) / 15000 #Changed from 60000 to 15000 to speed things up
        self.rotation += delta * settings.speed / 100                #Added speed factor

#Splash puddles of colour at target pixel (class version)
def splashing(num=5,colour_list=[],leave=False): # pylint: disable=dangerous-default-value
    now_running("splashing")
    rand_colours = False
    colour_index = 0
    #Start by resetting to the background colour
    br, bg, bb, bw = list_to_rgb(settings.colour)
    #set_all(br, bg, bb, bw)
    led_colours = [[br, bg, bb, bw]] * settings.numPixels

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

        if leave:
            for p in range(settings.numPixels):
                led_colours[p] = list(get_pixel_rgb(p))
        else:
            led_colours = [[0, 0, 0, 0]] * settings.numPixels

        changed = [False] * settings.numPixels

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
                changed[p] = True

        #Now set the pixels that need changing
        for p in range(settings.numPixels):
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
            self.start    = m + (random.randint(0,250) * 100 / max(5, settings.speed))
            self.end      = self.start + (random.randint(100,500) * 100 / max(5, settings.speed))
        else:
            self.start    = m + (random.randint(250,500) * 100 / max(5, settings.speed))
            self.end      = self.start + (random.randint(750,1250) * 100 / max(5, settings.speed))
        self.position = random.randint(0, settings.numPixels - 1)
        self.colour   = colour_list[colour_index]

# One funtion to manage lots of twinkles - using twink class
def twinkling(num=0,colour_list=[]): #pylint: disable=dangerous-default-value
    now_running("twinkling")
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

    twinks = []

    #Initialise all the twinks
    for _ in range(numTwinkles):
        twinks.append(twink(twinkling_start, colour_list, colour_index))
        colour_index += 1
        if colour_index == len(colour_list):
            colour_index = 0

    #Time to fade the pixels in and out, in milliseconds
    fade_time = 150

    while not settings.stop or count_lit > 0 and not time_to_go():
        check_mqtt()

        #start by clearing all pixels
        last_colour = settings.colour
        r, g, b, w = list_to_rgb(last_colour)
        set_all(r, g, b, w)
        count_lit = 0
        m = millis()
        for t in range(numTwinkles):
            #If this twinkle has out lived it's life:
            if m > twinks[t].end: #time to turn this one off
                if not settings.stop: #if we are not settings.stopping then reset the twink
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
                        b = 100 * (m - twinks[t].start) / fade_time
                    else:
                        b = 100 * (twinks[t].end - m) / fade_time
                    r, g, b, w = list_to_rgb(twinks[t].colour,b)
                set_pixel(twinks[t].position,r, g, b, w)
            else: #not time to turn this on yet, but might want to adjust the start time
                if settings.stop: #set end time to 0 to avoid turning this on in the future
                    twinks[t].end = 0
                elif old_speed != settings.speed: #speed has changed so adjust the start time by a random proportion
                    twinks[t].start = twinks[t].start + (random.randint(250,500) * 100 / max(5, settings.speed)) * random.uniform(0, 1)

        twinkling_start = False
        #debuglog("Speed now {:>3}; currently lit: {:>3}".format(speed,count_lit))
        show()
        old_speed = settings.speed

        #Sleep a bit to give the pi a rest
        sleep(0.005)
    now_running("None")
