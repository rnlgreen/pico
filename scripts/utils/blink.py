from machine import Pin # type: ignore
from time import sleep

led = Pin('LED', Pin.OUT)

def blink(on=1,off=1,loop=1):
    for i in range(loop):
        led.value(1)
        sleep(on)
        led.value(0)
        sleep(off)
