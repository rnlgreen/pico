#Common utils here to avoid circular imports
from math import sqrt
import time
from utils import settings
from utils import mqtt
from utils import myid
from utils import log

#Set an individual pixel to a new colour
def set_pixel(i=0, r=0, g=0, b=0, w=0):
    #No need for global when using lists like this
    """Set an individual pixel to a new colour"""
    settings.strip[i] = (r, g, b, w)
    settings.pixel_colours[i] = [r, g, b, w]

# Convert a list [1, 2, 3] to integer values, and adjust for settings.saturation
def list_to_rgb(c, p=100):
    """Convert list to rgb values"""
    #Sometimes we get a tuple that is 3 long so need to allow for that
    if len(c) == 3:
        c = list(c) + [0]

    if p == 100:
        r, g, b, _ = c
    else:
        r, g, b, _ = (min(255, int(int(x) * (p / 100.0))) for x in c)

#    if settings.saturation != 100:
#        h, s, v = rgb_to_hsv(r, g, b)
#        s = settings.saturation / 100
#        r, g, b = hsv_to_rgb(h, s, v)
    return r, g, b, 0

def hsv_to_colour(h, s=255, v=255):
    return settings.strip.colorHSV(h, s, v)

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
    saturation = settings.saturation / 100
    r, g, b = hsv_to_rgb(pos/255,saturation,1)
    return ([r, g, b])

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

#Show the LED changes
def show():
    settings.strip.show()

#Set the whole strip to a new colour
def set_all(r=0, g=0, b=0, w=0):
    """Set all pixels to new values"""
    settings.colour = [r, g, b]
    settings.strip.fill((r, g, b))
    for p in range(settings.numPixels):
        settings.pixel_colours[p] = [r, g, b, w] # pixel_colours doesn't need to be "global" as it is mutated
    #show()

    if settings.colour == [0, 0, 0]:
        settings.lightsoff = True
    else:
        settings.lightsoff = False

#Get the current value for a pixel
def get_pixel_rgb(i):
    """Get current rgb value of pixel"""
    if i >= settings.numPixels or i < 0:
        log.status(f"Out of range pixel: {i}")
        return 0,0,0,0
    else:
        r, g, b, _ = settings.pixel_colours[i]
        return r, g, b, 0

# Euclidean colour difference
def euclidean_distance(c2):
    #Allow for settings.colour to have a white value
    if len(settings.colour) == 4:
        r1, g1, b1, _ = settings.colour
    else:
        r1, g1, b1 = settings.colour

    r2, g2, b2 = c2
    distance = sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)
    return distance

#Function to set the speed during demo sequences
def set_speed(new_speed):
    """Set update speed for sequences"""
    if not settings.speed == new_speed:
        settings.speed = new_speed
        settings.dyndelay = int(1000 - 100 * sqrt(int(settings.speed)))
        mqtt.send_mqtt("pico/"+myid.pico+"/status/speed",str(settings.speed))

#Function to set the brightness
def set_brightness(new_brightness_level):
    """Function to set the brightness"""
    if not settings.brightness == new_brightness_level:
        settings.brightness = new_brightness_level
        settings.strip.brightness(settings.brightness)
        if not settings.running:
            r, g, b, _ = list_to_rgb(settings.colour)
            #need to call set_all as this is what updates pixels with the new brightness level
            #set_all includes a call to strip.show()
            set_all(r, g, b)
            show()
        if settings.brightness == 0:
            settings.lightsoff = True
        else:
            settings.lightsoff = False

#Function to set the colour
def set_colour(new_colour):
    """set the colour"""
    if not settings.colour == new_colour:
        settings.colour = new_colour
        set_all(settings.colour[0],settings.colour[1],settings.colour[2])
        show()
        send_colour()

#Send settings.colour update to NodeRed
def send_colour():
    """Update NodeRed with new colour"""
    if settings.master or not settings.auto:
        hexcolour = f"#{settings.colour[0]:02x}{settings.colour[1]:02x}{settings.colour[2]:02x}"
        mqtt.send_mqtt(f"pico/{myid.pico}/status/colour",str(hexcolour))

# Fade to new brightness
def new_brightness(new_level):
    """Fade to new brightness"""
    old_level = settings.brightness
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
    if settings.master or not settings.auto:
        mqtt.send_mqtt("pico/"+myid.pico+"/status/brightness",str(settings.brightness))

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
    if settings.stop_after == 1: #Button has been pressed, time to move on
        return True
    if settings.stop_after > 1 and time.time() > settings.stop_after and not settings.singlepattern:
        return True
    return False

#Translate sleep to time.sleep
def sleep(s):
    time.sleep(s)

#Function to sleep for 'countdown' seconds whilst keeping an eye on stop
def sleep_for(countdown):
    loop_sleep = 0.5
    countdown = countdown / loop_sleep
    while not settings.stop and countdown > 0:
        check_mqtt()
        sleep(0.5)
        countdown -= 1

#Check for new MQTT instructions
def check_mqtt():
    """check for new mqtt messages"""
    if mqtt.client:
        mqtt.client.check_msg()

#Send control message to MQTT
def send_control(payload):
    """Send message to MQTT"""
    topic = 'pico/lights'
    mqtt.send_mqtt(topic,payload)

#Stop running functions and if not running turn off
#Called from Node-Red
def off(from_auto=False):
    """All off"""
    #status(f"called with {from_auto}")
    if not from_auto:
        settings.auto = False
        if settings.master:
            mqtt.send_mqtt("pico/"+myid.pico+"/status/auto","off")
    if settings.running:
        mqtt.send_mqtt("pico/"+myid.pico+"/status/running","stopping...")
        if not from_auto: #if it's an external "off" command then forget what was running
            settings.previously_running = ""
        settings.stop = True
    else:
        new_brightness(0)
        #set_all(0,0,0)
        #hexcolour = "#%02x%02x%02x" % (colour[0],colour[1],colour[2])
        #mqtt.send_mqtt("pico/"+myid.pico+"/status/colour",str(hexcolour))
        settings.strip.clear()
        show()
        settings.lightsoff = True
        #status("LEDs Off")

#Off command called via manage_lights through MQTT
def auto_off():
    #log.status("Running off(True)")
    off(True)

where = myid.where[myid.pico]
