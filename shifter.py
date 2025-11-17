# Shift register class
"""
from RPi import GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

class Shifter():

    def __init__(self, data, clock, latch):
        self.dataPin = data
        self.latchPin = latch
        self.clockPin = clock
        GPIO.setup(self.dataPin, GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT)
        GPIO.setup(self.clockPin, GPIO.OUT)

    def ping(self, p):  # ping the clock or latch pin
        GPIO.output(p,1)
        sleep(0)
        GPIO.output(p,0)

    # Shift all bits in an arbitrary-length word, allowing
    # multiple 8-bit shift registers to be chained (with overflow
    # of SR_n tied to input of SR_n+1):
    def shiftWord(self, dataword, num_bits):
        for i in range((num_bits+1) % 8):  # Load bits short of a byte with 0
            # self.dataPin.value(0)  # MicroPython for ESP32
            GPIO.output(self.dataPin, 0) 
            self.ping(self.clockPin)
        for i in range(num_bits):          # Send the word
            # self.dataPin.value(dataword & (1<<i))  # MicroPython for ESP32
            GPIO.output(self.dataPin, dataword & (1<<i))
            self.ping(self.clockPin)
        self.ping(self.latchPin)

    # Shift all bits in a single byte:
    def shiftByte(self, databyte):
        self.shiftWord(databyte, 8)
"""
# shifter.py  — fixed 74HC595 driver for Raspberry Pi (MSB-first)
from RPi import GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

class Shifter:

    def __init__(self, data, clock, latch):
        """
        Keep signature compatible with existing code:
            Shifter(data=16, latch=20, clock=21)
        It will map named args correctly.
        """
        self.dataPin = data
        self.clockPin = clock
        self.latchPin = latch

        GPIO.setup(self.dataPin, GPIO.OUT)
        GPIO.setup(self.clockPin, GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT)

        # Ensure outputs start low
        GPIO.output(self.dataPin, 0)
        GPIO.output(self.clockPin, 0)
        GPIO.output(self.latchPin, 0)

    def _pulse(self, pin, t=0.0005):
        """Generate a short HIGH pulse on pin (default 0.5 ms)."""
        GPIO.output(pin, 1)
        sleep(t)
        GPIO.output(pin, 0)
        # small settle
        sleep(t/4)

    def shiftByte(self, databyte):
        """
        Send a single byte to the 74HC595 MSB-first (bit 7 down to 0),
        then pulse the latch so outputs update simultaneously.
        """
        # Send bits 7..0 (MSB first)
        for i in range(7, -1, -1):
            bit = (databyte >> i) & 1
            GPIO.output(self.dataPin, 1 if bit else 0)
            # pulse clock
            self._pulse(self.clockPin, t=0.0003)

        # latch outputs
        self._pulse(self.latchPin, t=0.0005)

    # Optional convenience: send a full word of arbitrary bitlength (MSB-first)
    def shiftWord(self, dataword, num_bits):
        """
        Send num_bits from dataword, MSB-first. Useful for chained 595s.
        num_bits should be <= 32 (practical limit here).
        """
        if num_bits <= 0:
            return
        for i in range(num_bits-1, -1, -1):
            bit = (dataword >> i) & 1
            GPIO.output(self.dataPin, 1 if bit else 0)
            self._pulse(self.clockPin, t=0.0003)
        self._pulse(self.latchPin, t=0.0005)


# Example:
#
# from time import sleep
# s = Shifter(data=16,clock=20,latch=21)   # convenient Pi pins
# for i in range(256):
#     s.shiftByte(i)
#     sleep(0.1)
