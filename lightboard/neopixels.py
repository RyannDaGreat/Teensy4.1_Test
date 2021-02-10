import board
import neopixel_write
import digitalio
from micropython import const
from lightboard.config import config
from urp import *

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





################################ HIGH LEVEL FUNCTIONS BELOW #################################
c=[0,.15,.4,5]
old_lightwave_new_colors=[
					(c[3],c[3],c[3]),#5
					(c[1],c[1],c[2]),
					(c[3],c[0],c[0]),#3
					(c[1],c[2],c[1]),
					(c[3],c[3],c[0]),#4
					(c[0],c[3],c[0]),#1
					(c[2],c[1],c[2]),
					(c[0],c[3],c[3]),#6
					(c[2],c[2],c[1]),
					(c[0],c[0],c[3]),#2
					(c[1],c[2],c[2]),
					(c[3],c[0],c[3]),#0
				]
old_lightwave_old_colors=[
					(c[3],c[3],c[3]),#5
					(c[1],c[1],c[2]),
					(c[3],c[0],c[3]),#3
					(c[1],c[2],c[1]),
					(c[3],c[0],c[0]),#4
					(c[3],c[3],c[0]),#1
					(c[2],c[1],c[2]),
					(c[0],c[3],c[0]),#6
					(c[2],c[2],c[1]),
					(c[0],c[3],c[3]),#2
					(c[1],c[2],c[2]),
					(c[0],c[0],c[3]),#0
				]
semitone_colors=old_lightwave_old_colors

def float_color_to_bytes(r,g,b):
	r=clamp(int(r*256),0,255)
	g=clamp(int(g*256),0,255)
	b=clamp(int(b*256),0,255)
	return bytes([g,r,b])

def draw_pixel_colors(scale=major_scale,pixels_per_note=3,num_pixels=125,brightness=None,offset=0,position=None,extra_brightness=3,touch_color=(1,1,1)):
	import math
	if brightness is None:
		brightness=config.get_with_default('neopixels brightness')
	colors=[semitone_colors[semitone] for semitone in scale[:-1]]
	# data=b''.join([float_color_to_bytes(r*brightness,g*brightness,b*brightness)*pixels_per_note for r,g,b in colors])
	right_padding=bytes([0,0,0])*int(math.floor((pixels_per_note-1)/2))
	left_padding =bytes([0,0,0])*int(math.ceil ((pixels_per_note-1)/2))
	data=bytearray(b''.join([left_padding+float_color_to_bytes(r*brightness,g*brightness,b*brightness)+right_padding for r,g,b in colors]))
	if position is not None:
		start_index=int(position/pixels_per_note)
		start_index=start_index%(len(scale)-1)
		r,g,b=colors[start_index]
		data[3*start_index*pixels_per_note:3*start_index*pixels_per_note+3*pixels_per_note]=float_color_to_bytes(r*brightness*extra_brightness,
		                                                                   g*brightness*extra_brightness,
		                                                                   b*brightness*extra_brightness)*pixels_per_note
	data=data*(num_pixels*3//len(data)+2)
	data=data[offset:][:3*num_pixels]
	if position is not None:
		index=int(position)*3
		if index<=len(data)-3:
			#Make the individual pixel we're touching glow
			data[index:index+3]=float_color_to_bytes(*touch_color)
	draw(data)
	return data


