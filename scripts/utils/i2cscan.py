#Scan i2c bus
from machine import I2C, Pin # type: ignore # pylint: disable=import-error

#Pins from left to right:
#1: Voltage in, 3-5 VDC
#2: SDA: I2C data in/out
#3: Ground
#4: SCL: I2C clock in

I2CID = 1
SDAPIN = 26 #GPIO26
SCLPIN = 27 #GPIO27

def main():
    i2c = I2C(id=I2CID, scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=400000)

    devices = i2c.scan()

    if len(devices) == 0:
        print("No I2C device found")
    elif len(devices) > 1:
        print("Multiple I2C devices found -")
        for d in devices:
            print(f"  0x{d:02X}")
    else:
        print(f"I2C device found at 0x{devices[0]:02X}")

if __name__ == "__main__":
    main()
