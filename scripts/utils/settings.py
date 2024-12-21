#shared settings
LED_COUNT = 0               # Fixed count of physical LEDs in the strip, set by the pico'x'.py
numPixels = 0               # Dynamic LED count, typically either LED_COUNT or LED_COUNT/2 for reflect mode
colour = [0, 0, 0]          # Current background colour
saturation = 100            # Saturation level of LEDs
hue = 0                     # Current hue value
speed = 90                  # Speed factor, 0-100
dyndelay = 0                # Delay factor, calculated from speed
brightness = -1             # Brightness level of the LED strip
stop = False                # Do I need to stop the current routine
auto = True                 # Automatic light brightness control
master = False              # Am I the master controller for light levels (pico5)
running = False             # Is a routine running already
boost = False               # Add a litle more to the auto lighting
cycle = False               # Used in e.g. twinkling to give a rotating backgroud colour
xstrip = False              # Is this a special strip that might do its own thing
xsync = True                # If a special strip, is it syncing with the rest of the kitchen lights
lightsoff = True            # Flag to say if the lights are off or not
effect = "None"             # The currently running effect
stop_after = 0              # Time to stop a routine, used when in standalone mode
next_up = "None"            # Set to "command", a key value for effects (perhaps should be the value?)
previously_running = ""     # Remember what we were running when we automatically turn the lights off
strip = None                # Will become the class representing the strip of LEDs
pixel_colours = []          # What all the pixels are currently set to
running = False             # Flag to say if we are running a light sequence or not
splash_size = 4             # Size of splashes in splashing
#last_lights = 0             # Don't think this is used
singlepattern = False       # When in standalone mode whether to loop or not