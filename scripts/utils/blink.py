#Blink util
from machine import Pin
import time

led = Pin('LED', Pin.OUT)

def blink(on=1,off=1,loop=1):
    for i in range(loop):
        led.value(1)
        time.sleep(on)
        led.value(0)
        time.sleep(off)
