import board
import neopixel_write
import digitalio
from micropython import const

length=const(125) #Enter the number of neopixels on the lightboard

pin = digitalio.DigitalInOut(board.D30)
pin.direction = digitalio.Direction.OUTPUT

buffer = bytearray()
def draw(data:bytearray):
	#Manually draw bytes to the neopixel strip
	#This method runs very fast
	buffer[:len(data)]=data

def refresh():
	#Sometimes buffer can be mutated, since buffer is a bytearray
	neopixel_write.neopixel_write(pin, buffer)

def write(data):
	draw(data)
	refresh()

def draw_fill(r,g,b):
	assert 0<=r<=255 and 0<=g<=255 and 0<=b<=255,'Neopixel color channels must be integers in the range [0,255]'
	draw(bytes([g,r,b]*length)) # For some reason, my neopixels appear to be in g,r,b order instead of r,g,b order...

def display_fill(r,g,b):
	draw_fill(r,g,b)
	refresh()

all_off=bytes([0,0,0]*length)
def turn_off():
	#Turn off all of the LED's
	write(all_off)

def draw_all_off():
	draw(all_off)

class TemporarilyTurnedOff:
	#Meant to be used like this:
	#	with neopixels.TemporarilyTurnedOff():
	#		(do stuff)
	#Because this is an object, it can be nested while remembering all past buffer
	def __enter__(self):
		self.old_data=bytes(buffer)
		turn_off()
	def __exit__(self,*args):
		write(self.old_data)

def assert_is_valid_byte_color(r,g,b):
	assert 0<=r<=255 and 0<=g<=255 and 0<=b<=255,'Neopixel color channels must be integers in the range [0,255]'

def assert_is_valid_index(index):
	assert isinstance(index,int) and 0<=index<length,'%i is an invalid neopixel index. Please choose an int in the range [0,%i]'%(index,length-1)

def draw_line(start,end,r,g,b):
	#draw a line of uniform color from start to end, inclusive, on the neopixel strip
	start=int(start)
	end=int(end)
	start,end=min(start,end),max(start,end)
	assert start<=end
	if end<0 or start>=length:
		return
	buffer[start*3:end*3+3]=bytearray([g,r,b])*(end-start+1)

def draw_dot(index,r=63,g=63,b=63):
	index=int(index)
	assert index>=0
	if index>=length:
		return #You'd never be able to see it anyway...
	buffer[index*3:index*3+3]=bytearray([g,r,b])

def display_dot(index,r=63,g=63,b=63):
	draw_all_off()
	draw_dot(index,r,g,b)
	refresh()

def display_line(start,end,r=63,g=63,b=63):
	draw_all_off()
	draw_line(start,end,r,g,b)
	refresh()



