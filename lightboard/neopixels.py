import board
import neopixel_write
import digitalio

length=125 #Enter the number of neopixels on the lightboard

pin = digitalio.DigitalInOut(board.D30)
pin.direction = digitalio.Direction.OUTPUT

def write(data:bytes):
	#Manually write bytes to the neopixel strip
	#This method runs very fast
	global written_data
	neopixel_write.neopixel_write(pin, data)
	written_data=data

def fill(r,g,b):
	assert 0<=r<=255 and 0<=g<=255 and 0<=b<=255,'Neopixel color channels must be in the range [0,255]'
	write(bytes([g,r,b]*length)) # For some reason, my neopixels appear to be in g,r,b order instead of r,g,b order...

def turn_off():
	#Turn off all of the LED's
	fill(0,0,0)

written_data = None
turn_off() #Initialize written_data

class TemporarilyTurnedOff:
	#Meant to be used like this:
	#	with neopixels.TemporarilyTurnedOff():
	#		(do stuff)
	#Because this is an object, it can be nested while remembering all past written_data
	def __enter__(self):
		self.old_data=written_data
		turn_off()
	def __exit__(self,*args):
		write(self.old_data)