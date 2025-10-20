import time
import RPi.GPIO as GPIO
import random 
from shifter import Shifter 

class Bug:
	def __init__(self,timestep = .1, x=3, isWrapOn = False):
		self.timestep = timestep
		self.x = x  
		self.isWrapOn = isWrapOn
		self.__shifter = Shifter(23,24,25)
		self._running = False


def start(self):
    self._running = True 
    while self._running:
    	self.__shifter.shiftByte(1<<self.x)
    	time.sleep(self.timesleep)

    	step = random.choice([-1,1])
    	new_x = self.x + step

    	if self.isWrapOn:
    	    self.x = new_x%8
    	else:
    	    if 0 <= new_x <= 7:
    	        self.x = new_x
def stop(self):
    self._running = False
    self.__shifter.shiftByte(0) 




if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    s1,s2,s3 = 17,27,22#green purple blue wires
    GPIO.setup(s1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(s2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(s3, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

    bug = Bug()
    prev_s2 = GPIO.input(s2)

    try:
    	while True:
    		s1_state = GPIO.input(s1)
    		s2_state = GPIO.input(s2)
    		s3_state = GPIO.input(s3)

    		#controlling s1 on/off
    		if s1_state and not bug._running:
    			print ("Bug on")
    			bug._running = True
    		elif not s1_state and bug._running:
    			print("Bug off")
    			bug.stop()

    		#s2 wrap mode 
    		if s2_state!= prev_s2:
    			if s2_state ==1:
    				bug.isWrapOn = not bug.isWrapOn
    				print(f"Wrap toggled: {bug.isWrapOn}")
    		prev_s2 = s2_state

    		#s3 Speed control
    		bug.timestep = .1/3 if s3_state else .1

    		if bug._running:
    			bug.__shifter.shiftByte(1<<bug.x)
    			time.sleep(bug.timestep)
    			bug.x += random.choice([-1,1])

    			if bug.isWrapOn:
    				bug.x %=8
    			else:
    				bug.x = max(0,min(7,bug.x))
    		else:
    			bug.__shifter.shiftByte(0)
    		time.sleep(.05)

except KeyboardInterrupt:
	GPIO.cleanup()
