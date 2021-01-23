import board
import neopixel_write
import digitalio
from urp import *

pin = digitalio.DigitalInOut(board.D30)
pin.direction = digitalio.Direction.OUTPUT

pixel_off = bytearray([32, 32, 32]*144)
neopixel_write.neopixel_write(pin, pixel_off)

import ulab
from urp import seconds

def get_wav(freq,phase):
	theta=ulab.arange(144)/144*3.14159*2
	wav=(ulab.vector.sin(theta*freq+phase)+1)/2
	wav=wav*32
	return wav

while True:
	tic()
	r=get_wav(freq=10,phase=seconds()*5)
	g=get_wav(freq=5,phase=-seconds()*5)
	b=get_wav(freq=5,phase=seconds()*20)
	wav=ulab.array([r,g,b])
	wav=ulab.array(wav,dtype=ulab.uint8)
	wav=wav.transpose()
	wav=bytearray(wav)
	neopixel_write.neopixel_write(pin, wav)
	ptoc()

