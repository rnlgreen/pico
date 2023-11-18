"""Blink util"""
import time
from machine import Pin # type: ignore # pylint: disable=import-error

led = Pin('LED', Pin.OUT)

def blink(on=1,off=1,loop=1):
    """blink the led"""
    for _ in range(loop):
        led.value(1)
        time.sleep(on)
        led.value(0)
        time.sleep(off)
