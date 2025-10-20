import RPi.GPIO as GPIO
import time

class Shifter:
    def __init__(self, serialPin,latchPin,clockPin):#for thread code conductor 
    self.serialPin = serialPin
    self.latchPin = latchPin #store the numbers of pins as attributes
    self.clockPin = clockPin

GPIO.setmode(GPIO.BCM)



GPIO.setup(dataPin, GPIO.OUT)
GPIO.setup(latchPin, GPIO.OUT, initial=0)  # start latch low
GPIO.setup(clockPin, GPIO.OUT, initial=0)  # start clock low


def __ping(self,pin):  # ping the clock or latch pin private the method
    GPIO.output(pin, 1)#pin high
    time.sleep(0)
    GPIO.output(pin, 0)#pin low

def shiftByte(self,byte):  # send a byte of data to the output
    for i in range(8):
        GPIO.output(self.serialPin, byte & (1 << i))
        self.__ping(self.clockPin)# add bit to register
    self.__ping(self.latchPin)    # send register to output


