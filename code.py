# import board
# import busio
# import sdcardio
# import storage
# spi = board.SPI()
# cs = board.FLASH_CS
# sdcard = sdcardio.SDCard(spi, cs)

#PINS:
#	ADS1115 A0: Single Touch
#	ADS1115 A1: Double Touch A
#	ADS1115 A2: Double Touch B
#	Teensy 12: WOB-bble: Single Touch Pullup/Pulldown (Alternates between HIGH and LOW)
#	Teensy 11: DUA-l 1: Set to HIGH when reading a dual   touch and LOW when reading a single touch
#	Teensy 10: DUA-l 2: Set to HIGH when reading a dual   touch and LOW when reading a single touch
#	Teensy  9: SIN-gle: Set to HIGH when reading a single touch and LOW when reading a dual   touch
#	Teensy 23: Ribbon : Read this from the teensy's internal ADC instead of the ADS1115 when in DUAL mode and we just want to get the gate value

#SOFTWARE TODO: 
#	Get rid of spikes in dual touch mode.
#		- Calibrate the dual touches to match the single touch so we have compatiable numbers everywhere
#			- This can be done in constant space with histograms and bins that fill up as you slowly move a credit card's edge along the ribbon
#		- When the upper and lower touch move away or to the single touch position at roughly opposite velocities, don't change single touch/dual touch status until they appear to be from two fingers (if single touch isn't moving much but both top and bottom dual touches are it should be a red flag...watch the graph...)

# from linear_modules import *

# import lightboard.transceiver as transceiver
1/0

from urp import *
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn as ADS1115_AnalogIn
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn as Internal_AnalogIn
import tools
import storage

import lightboard.ribbons as ribbons
import lightboard.neopixels as neopixels

# while True:
# 	time.sleep(.5)
# 	transceiver.send(midi_note_on())
# 	time.sleep(.5)
# 	transceiver.send(midi_note_off())

old_value=0
while True:
	tic()
	# neopixels.display_fill(255,255,255)
	reading =ribbons.ribbon_a.processed_cheap_single_touch_reading(blink=False)
	# neopixels.display_fill(0,0,0)
	# reading2=ribbons.ribbon_a.processed_cheap_single_touch_reading(blink=False)
	if reading.gate:
	# ptoc()
		print(reading.value*1000)
	# t=toc()
	# if t!=0:
	# 	print(1/t)
	# if reading.gate:
	# 	value=reading.value
	# 	neopixels.display_line(old_value,value)
	# 	old_value=value
