#Utility functions to do pretty things with a WS2812 LED strip
import time
import utils.mqtt as mqtt
import utils.myid as myid
from utils.colours import colours

from lib.neopixel import Neopixel
from math import sin, pi, radians, sqrt
#import colorsys
import random

# Convert a list [1, 2, 3] to integer values, and adjust for brightness
def list_to_rgb(c, p=100):
    #Add in value for white if we didn't get one
    if len(c) == 3:
        c += [0]

    r, g, b, w = [min(255, int(int(x) * (p / 100.0))) for x in c]

    if not saturation == 100:
        h, s, v = rgb_to_hsv(r, g, b)
        s = saturation / 100
        r, g, b = hsv_to_rgb(h, s, v)
    
    return r, g, b, w

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
    global colour, pixel_colours
    colour = [r, g, b]
    strip.fill((r, g, b))
    for p in range(numPixels):
        pixel_colours[p] = [r, g, b]
    strip.show()

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
    global brightness
    if not brightness == new_brightness:
        brightness = new_brightness
        strip.brightness(brightness)
        mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness",str(brightness))

#Function to set the speed during demo sequences
def set_colour(new_colour):
    global colour
    if not colour == new_colour:
        colour = new_colour
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
    while not stop:
        check_mqtt()
        color = strip.colorHSV(hue, 255, 150)
        #Returns list (r, g, b)
        strip.fill(color)
        strip.show()
        hue += 150
        if hue > 65535:
            hue -= 65535
        time.sleep(dyndelay / 1000)
    set_all(0, 0, 0)
    now_running("None")

# Function to fade a new colour in from the centre of the strip
# Fades a new colour in from the centre of the strip
def plume(colour, steps=100):
    factor = 3 #defines how quickly the colour fades in, less than 3 doesn't complete the transition
    fr, fg, fb, _ = list_to_rgb(colour)
    #Get the current state of the pixels to use for fading
    br = [0] * numPixels
    bg = [0] * numPixels
    bb = [0] * numPixels
    
    for i in range(numPixels):
        br[i], bg[i], bb[i], _ = get_pixel_rgb(i)
    for s in range(steps):
        current_colours = "Step {0:3d}: ".format(s) #string to report to status state of pixels
        for p in range(numPixels):
            #Inverse SIN:
            fade = max(0, min(1,s*factor/steps+2*(sin(radians(180*p/(numPixels - 1)))-1)))
            r, g, b, _ = fade_rgb(fr, fg, fb, 0, br[i], bg[i], bb[i], 0, fade)
            set_pixel(p, r, g, b)
            if p == 0 or p == numPixels / 2 or p == numPixels - 1:
                current_colours += "{0:1.4f}: {1:3d}, {2:3d}, {3:3d}    ".format(fade, r, g, b)
        #status("{}".format(current_colours))
        strip.show()
        check_mqtt()
        time.sleep(dyndelay / 1000.0)  # dyndelay is in milliseconds from 10 to 1000
        if stop:
            break

# Function to call plume continualyl with random colours
def pluming(delay=10):
    global colour
    now_running("Pluming")
    set_speed(85)
    while not stop:
        colour = contrasting_colour(colour) #pick a new colour
        plume(colour) #Call plume with the new colour and the number of steps to take
        countdown = delay
        while not stop and countdown > 0:
            check_mqtt()
            time.sleep(1)
            countdown -= 1
    set_all(0, 0, 0)
    now_running("None")

#Lighting effect to create a twinkling/shimmer effect along the length of the lights
def shimmer(shimmer_width=5,iterations=0):
    global colour
    now_running("Shimmer")
    set_speed(95)
    speedfactor = 1  # smaller is faster
    if colour == [0, 0, 0] or colour == [0, 0, 0, 0]: #if the colour is black
        status("Setting colour to gold")
        set_colour(colours["gold"])
    print("Colour is: {}".format(colour))
    limit_run = (iterations > 0)
    while not (stop or (limit_run and iterations == 0)):
        for j in range(shimmer_width):
            for i in range(numPixels):
                p = 100 * abs(((i+j)%shimmer_width - shimmer_width/2) / (shimmer_width / 2))
                r, g, b, w = list_to_rgb(colour, p)
                set_pixel(i, r, g, b, w)
            strip.show()
            check_mqtt()
            time.sleep(dyndelay * speedfactor / 1000.0)  # Needs to run a bit faster than others
            if stop:
                break
        if limit_run:
            iterations -= 1
    set_all(0, 0, 0)
    now_running("None")

#Return splash parameters, used by splashing
def get_splash(colour):
    #status("Called with {}".format(colour))
    colour_spread = 15     #spread of colours around the wheel
    (r, g, b, _) = list_to_rgb(colour)
    (h, _, v) = rgb_to_hsv(r/255,g/255,b/255)
    #status("h: {}, s: {}, v: {}".format(h, s, v))
    c = h * 255 + random.randint(int(-colour_spread/2), int(colour_spread/2))
    if not 0 < c < 255:
        c = c % 256
    #status("Wheel colour value: {}".format(c))

    brightness_spread = 30  #spread of brightness
    p = max(10, 50 * v + random.randint(-brightness_spread, brightness_spread))
    #status("Brightness percentage set to {}".format(p))

    colour = list_to_rgb(wheel(c), p)
    #status("Colour set to: {}".format(colour))

    size   = random.randint(1,4)
    radius = max(4,int(size * numPixels / 64)) #No science in the divider at the end!
    #origin = random.randint(radius, settings.numPixels - 1 - radius)
    origin = random.randint(0,numPixels-1)

    #Speed is number of degrees to step through based on the size, faster for smaller splashes
    speed  = 360 / size #will be factored by the elapsed miiliseconds

    return colour, origin, radius, speed

#Start splashes
def splashing(num=5,colour_list=["-1"],leave=False):
    global colour
    now_running("Splashing")
    set_speed(50)
    splash_colour = [0,0,0,0] * num
    splash_origin = [0] * num
    splash_size = [0] * num
    splash_speed = [0] * num
    splash_rotation = [0] * num
    random_colours = False
    colour_index = 0
    led_colours = [[0,0,0,0]] * numPixels

    # Pick a wheel position to splash
    if len(colour_list) == 0:
        colour = list_to_rgb(wheel(random.randint(0, 255)))
        colour_list.append(colour)
    elif "-1" in colour_list[0]:
        random_colours = True

    # Populate all the splashes with new values
    for splash in range(num):
        if random_colours:
            colour = list_to_rgb(wheel(random.randint(0, 255)))
        else:
            colour = colour_list[colour_index]
            colour_index += 1
            if colour_index == len(colour_list):
                colour_index = 0
        (splash_colour[splash], splash_origin[splash], splash_size[splash], splash_speed[splash]) = get_splash(colour)


    #Grab the current time in millisecons
    t = millis()
    iterations = 0
    total_elapsed = 0

    while num > 0:
        #Optionally leave the exist splash effects behind
        if leave:
            for p in range(numPixels):
                led_colours[p] = list(get_pixel_rgb(p))
        else:
            led_colours = [[0, 0, 0, 0]] * LED_COUNT
        
        changed = [False] * LED_COUNT

        #Get the elapsed time since last time we were here
        elapsed = ticks_diff(t,millis())
        total_elapsed += elapsed
        iterations += 1
        t = millis()
        for splash in range(num):
            #Calculate the new splash rotation based on speed, elapsed time and a factor of the overall display speed
            delta = splash_speed[splash] * elapsed * max(1,speed) / 60000
            splash_rotation[splash] += delta

            #If the splash angle goes above 180 it's time to create a new splash
            if splash_rotation[splash] > 180 or (leave and splash_rotation[splash] >= 90):
                if not stop:
                    if random_colours:
                        colour = wheel(random.randint(0, 255))
                    else:
                        colour = colour_list[colour_index]
                        colour_index += 1
                        if colour_index == len(colour_list):
                            colour_index = 0
                    (splash_colour[splash], splash_origin[splash], splash_size[splash], splash_speed[splash]) = get_splash(colour)
                    splash_rotation[splash]  = 0
                    #status("New splash {}: origin {}; size: {}, speed: {}, colour: {}".
                    #         format(splash, splash_origin[splash], splash_size[splash], splash_speed[splash], splash_colour[splash]))
                else:
                    print("Dropping splash {}".format(splash))
                    num -= 1
                    splash_origin.pop(splash)
                    splash_colour.pop(splash)
                    splash_speed.pop(splash)
                    splash_size.pop(splash)
                    splash_rotation.pop(splash)
                    break

            # Calculate the colour levels for this splash
            fr, fg, fb, fw = list_to_rgb(splash_colour[splash])

            #Loop over length of the wave
            splash_width = int(sin(radians(splash_rotation[splash])) * splash_size[splash])
            splash_start = max(0, splash_origin[splash] - splash_width)
            splash_end   = min(numPixels - 1, splash_origin[splash] + splash_width)
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
        strip.show()
        check_mqtt()
        time.sleep(0.005) # Sleep a little to give the CPU a break
    status("Average elapsed time: {}ms".format(total_elapsed / iterations))
    set_all(0, 0, 0)
    now_running("None")

#Like shimmer, but without the pixels moving along...
def wobble(wobble_width=8,iterations=0):
    now_running("Wobble")
    limit_run = (iterations > 0)
    #12 is the fewest steps to give us a reasonble sin wave and make it to 100% on or off
    #10 doesn't quite make it to fully on or off, so might be a good choice
    #(that's if the wavelength is 12 or greater)
    steps = 12
    speedfactor = 0.25
    r360 = radians(360)
    if colour == [0, 0, 0] or colour == [0, 0, 0, 0]: #if the colour is black
        status("Setting colour to gold")
        set_colour(colours["gold"])
    while not (stop or (limit_run and iterations == 0)):
        for j in range(steps):
            #Angle from 0 to 360 over time
            intensity_angle = (r360*j)/steps
            #Factor to apply to the brightness over time, from 0 -> 1 -> 0 -> -1 -> 0
            travel_factor   = sin(intensity_angle)
            for i in range(numPixels):
                #Angle from 0 to 360 along the width of the wobble
                wave_angle = (r360*(i%wobble_width))/wobble_width
                #Brightness factor along the width of the wobble, from 0 -> 1 -> 0 -> -1 -> 0
                sin_angle  = sin(wave_angle)
                #Combined percentage brightness for this pixel from 0 to 100 (or within that depending on the width and steps)
                p = 50 * (1 + (sin_angle * travel_factor))
                #Calculate the colour intensity for this pixel
                r, g, b, w = list_to_rgb(colour, p)
                set_pixel(i, r, g, b, w)
            #Show the new waves
            strip.show()
            check_mqtt()
            time.sleep(dyndelay * speedfactor / 1000.0)  # Needs to run a bit faster than others
            if stop:
                break
        if limit_run:
            iterations -= 1
    set_all(0, 0, 0)
    now_running("None")

#One funtion to manage lots of twinkles
def twinkling(num=0,colour_list=[]):
    now_running("twinkling")
    debug = False
    if num == 0:
        if colour_list == []: #fewer pixels needed if all white
            numTwinkles = int(numPixels / 5) # some number of twinkles to do
        else:
            numTwinkles = int(numPixels / 3) # some number of twinkles to do
    else:
        numTwinkles = num

    if colour_list == []:
            colour_list = [[255, 255, 255, 255]]

    twink_start    = [0] * numTwinkles
    twink_end      = [0] * numTwinkles
    twink_position = [-1]  * numTwinkles
    twink_colour   = [[0,0,0,0]] * numTwinkles

    #New flag to say whether a new twinkle is scheduled for 
    twink_scheduled = [False] * numPixels

    colour_index   = 0
    old_speed = speed
    count_lit = 0
    twinkling_start = True

    #Time to fade the pixels in and out, in milliseconds
    fade_time = 250

    status("{} twinkles".format(numTwinkles))

    while not stop or count_lit > 0:
        #start by clearing all pixels
        r, g, b, w = list_to_rgb(colour)
        #Can't use set_all here as it calls strip.show()
        strip.fill((r, g, b))
        count_lit = 0
        m = millis()
        for t in range(numTwinkles):
            #If this twinkle has out lived it's life:
            if ticks_diff(twink_end[t], m) > 0: #time to turn this one off
                #Mark this pixel position as unscheduled
                twink_scheduled[twink_position[t]] = False
                if not stop:
                    if t == 0 and debug:
                        status("twinkle {} now off".format(t))
                    if old_speed == speed: #same speed, so turn off and process as normal
                        #Pick a new start time for this twinkle
                        if twinkling_start: #quick start if first time around
                            twink_start[t]    = int(m + (random.randint(0,250) * 100 / max(5, speed)))
                            twink_duration    = int((random.randint(500,1000) * 100 / max(5, speed)))
                            twink_end[t]      = twink_start[t] + twink_duration
                        else:
                            twink_start[t]    = int(m + (random.randint(250,500) * 100 / max(5, speed)))
                            twink_duration    = int((random.randint(750,1250) * 100 / max(5, speed)))
                            twink_end[t]      = twink_start[t] + twink_duration
                        if t == 0:
                            twink_position[t] = 0
                            twink_scheduled[0] = True
                        else:
                            new_twinkle_position = random.randint(1, numPixels - 1)
                            while twink_scheduled[new_twinkle_position]:
                                new_twinkle_position = random.randint(1, numPixels - 1)
                            twink_position[t] = new_twinkle_position
                        #Mark this pixel position as scheduled to avoid driving the same position twice
                        twink_scheduled[twink_position[t]] = True
                        twink_colour[t]   = colour_list[colour_index]
                        colour_index += 1
                        if colour_index >= len(colour_list):
                            colour_index = 0
                    else: #just pick a new end time and keep it lit for now
                        twink_end[t]      = twink_start[t] + int((random.randint(750,1250) * 100 / max(5, speed)))
                        r, g, b, w = list_to_rgb(twink_colour[t])
                        count_lit += 1
            #if we are displaying this twinkle:
            elif ticks_diff(twink_start[t],m) > 0:
                if not old_speed == speed: #speed has changed so adjust the end time by a random proportion
                    twink_end[t] =  twink_end[t] + int((random.randint(750,1250) * 100 / max(5, speed)) * random.uniform(0, 1))
                #Now set the colour for this pixel
                count_lit += 1
                #Adjust the pixel intensity to fade in and out
### FIX THIS NEXT LINE ###
                if (twink_start[t] + fade_time) < m < (twink_end[t] - fade_time):
                    if t == 0 and debug:
                        print("twinkle 0 is fully on\t",end='')
                    r, g, b, w = list_to_rgb(twink_colour[t])
                else:
                    if ticks_diff(twink_start[t],m) < fade_time:
                        if t == 0:
                            print("twinkle 0 fading in\t",end='')
                        brightness = 100 * (m - twink_start[t]) / fade_time
                    else:
                        if t == 0:
                            print("twinkle 0 fading out\t",end='')
                        brightness = 100 * (twink_end[t] - m) / fade_time
                    r, g, b, w = list_to_rgb(twink_colour[t],brightness)
                if t == 0 and debug:
                    print("{}\t{}\t{}\t{}".format(r, g, b, w))
                set_pixel(twink_position[t],r, g, b, w)
            else: #not time to turn this on yet, but might want to adjust the start time
                if t == 0 and debug: 
                    print("twinkle is off")
                if stop: #set end time to 0 to avoid turning this on in the future
                    twink_end[t] = 0
                elif not old_speed  == speed: #speed has changed so adjust the end time by a random proportion
                    twink_start[t] = twink_start[t] + int((random.randint(250,500) * 100 / max(5, speed)) * random.uniform(0, 1))

        #Disable startup logic
        twinkling_start = False

        time.sleep(0.05)
        strip.show()
        check_mqtt()
        old_speed = speed

    now_running("None")

#Stop running functions and if not running turn off
#Called from Node-Red
def off():
    global stop
    if running:
        status("off() called whilst running {}".format(effect))
        mqtt.send_mqtt("pico/"+myid.pico+"/status/running","stopping...")
        stop = True
    else:
        set_all(0,0,0)

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
        running = True
        status("Starting {}".format(new_effect))
    effect = new_effect
    mqtt.send_mqtt("pico/"+myid.pico+"/status/running",str(new_effect))
    status("Left now_running")

#LED control function to accept commands and launch effects
def led_control(command=""):
    global stop, saturation, next_up
    if command.startswith("rgb"):
        #rgb(219, 132, 56)
        r, g, b = [int(x) for x in command[4:-1].split(", ")]
        set_all(r, g, b)
    elif command.startswith("brightness:"):
        _, b = command.split(":")
        strip.brightness(int(b))
        if not running:
            r, g, b, _ = list_to_rgb(colour)
            set_all(r, g, b)
    elif command.startswith("speed:"):
        _, s = command.split(":")
        set_speed(int(s))
    elif command.startswith("saturation:"):
        _, s = command.split(":")
        saturation = int(s)
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

numPixels = 16
#numPixels = 288
LED_COUNT = numPixels

#Create strip object
#parameters: number of LEDs, state machine ID, GPIO number and mode (RGB or RGBW)
status("Initialising strip")
strip = Neopixel(numPixels, 0, 0, "GRBW")
#strip = Neopixel(numPixels, 0, 0, "GRB")

#Set initial brightness
strip.brightness(20)

colour = [0, 0, 0]
set_colour(colour)
saturation = 100
speed = 90
dyndelay = 0
set_speed(speed)
brightness = 20
set_brightness(brightness)
pixel_colours = [[0, 0, 0, 0]] * numPixels
stop = False
running = False
effect = "None"
next_up = "None"
now_running(effect)

effects = { "rainbow":   rainbow,
            "pluming":   pluming,
            "shimmer":   shimmer,
            "splashing": splashing,
            "wobble":    wobble,
            "twinkling": twinkling,
            "off":       off }
