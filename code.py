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
import lightboard.widgets as widgets
import lightboard.transceiver as transceiver



if widgets.input_yes_no("Would you like to calibrate the ribbon?"):
	ribbons.ribbon_a.run_calibration()
#TODO: Make this into a function somehow so we can then autotune it
note=None
bend_range=48 #Make sure you set your synths in FL studio to accomadate this
alloff=b''.join([midi_note_off(note) for note in range(128)])
fast=False
# midi_note_off=lambda *args:b''

midi_messages_per_second=60

midi_message_state={'notes_off':set()}
def send_state():
	global midi_message_state
	print(midi_message_state)
	message=b''
	if 'pitch_bend' in midi_message_state:
		message+=midi_pitch_bend_from_semitones(midi_message_state['pitch_bend'],-bend_range,bend_range)
	if 'note_on' in midi_message_state:
		message+=midi_note_on(midi_message_state['note_on'])
	if 'notes_off' in midi_message_state:
		message+=b''.join([midi_note_off(note) for note in set(midi_message_state['notes_off'])])
	transceiver.send(message,fast=fast)
	midi_message_state={'notes_off':set()}

def note_on(note):
	midi_message_state['note_on']=note
	if note in midi_message_state['notes_off']:
		midi_message_state['notes_off']-={note}

def gate_off(note):
	global midi_message_state
	midi_message_state={'notes_off':midi_message_state['notes_off']|{note}}

def note_off(note):
	midi_message_state['notes_off']|={note}
	if midi_message_state['note_on']==note:
		del midi_message_state['note_on']

def pitch_bend(semitones):
	midi_message_state['pitch_bend']=semitones

last_midi_time=seconds()
while True:
	reading=ribbons.ribbon_a.processed_cheap_single_touch_reading()
	if reading.gate:
		value=reading.value
		new_note=int(value)
		remainder=value-new_note
		if new_note != note:
			neopixels.display_dot(new_note)
			if note is None:
				note_on(new_note)
				pitch_bend(remainder)
				note=new_note
			else:
				if abs(value-note)>bend_range:
					note_on(new_note)
					note_off(note)
					pitch_bend(remainder)
					note=new_note
				else:
					pitch_bend(value-note)
		else:
			pitch_bend(remainder)
	else:
		if note is not None:
			gate_off(note)
			note=None
	if seconds()-last_midi_time>1/midi_messages_per_second:
		last_midi_time=seconds()
		send_state()


# if widgets.input_yes_no("Would you like to calibrate the ribbon?"):
# 	ribbons.ribbon_a.run_calibration()

# #TODO: Make this into a function somehow so we can then autotune it
# note=None
# bend_range=48 #Make sure you set your synths in FL studio to accomadate this
# alloff=b''.join([midi_note_off(note) for note in range(128)])
# # midi_note_off=lambda *args:b''
# while True:
# 	tic()
# 	reading=ribbons.ribbon_a.processed_cheap_single_touch_reading()
# 	if reading.gate:
# 		value=reading.value
# 		new_note=int(value)
# 		remainder=value-new_note
# 		if new_note != note:
# 			neopixels.display_dot(new_note)
# 			if note is None:
# 				transceiver.send(midi_note_on(new_note)+midi_pitch_bend_from_semitones(remainder,-bend_range,bend_range))
# 				note=new_note
# 			else:
# 				if abs(value-note)>bend_range:
# 					transceiver.send(midi_note_on(new_note)\
# 						+midi_note_off(note)
# 						+midi_pitch_bend_from_semitones(remainder,-bend_range,bend_range))
# 					note=new_note
# 				else:
# 					transceiver.send(midi_pitch_bend_from_semitones(value-note,-bend_range,bend_range))
# 			ptoc()
# 		else:
# 			transceiver.send(midi_pitch_bend_from_semitones(remainder,-bend_range,bend_range))
# 	else:
# 		if note is not None:
# 			transceiver.send(midi_note_off(note))
# 			# transceiver.send(alloff)
# 			ptoc()
# 			note=None





# while True:
# 	tic()
# 	reading=ribbons.ribbon_a.processed_cheap_single_touch_reading()
# 	if reading.gate:
# 		value=reading.value
# 		new_note=int(value)
# 		remainder=value-new_note
# 		if new_note != note:
# 			neopixels.display_dot(new_note)
# 			if note is None:
# 				transceiver.send(midi_note_on(new_note)+midi_pitch_bend_from_semitones(remainder,-bend_range,bend_range),fast=fast)
# 				note=new_note
# 			else:
# 				if abs(value-note)>bend_range:
# 					transceiver.send(midi_note_on(new_note)+
# 						+midi_note_off(note)
# 						+midi_pitch_bend_from_semitones(remainder,-bend_range,bend_range),fast=fast)
# 					note=new_note
# 				else:
# 					transceiver.send(midi_pitch_bend_from_semitones(value-note,-bend_range,bend_range),fast=fast)
# 			ptoc()
# 		else:
# 			transceiver.send(midi_pitch_bend_from_semitones(remainder,-bend_range,bend_range),fast=fast)
# 	else:
# 		if note is not None:
# 			transceiver.send(midi_note_off(note),fast=fast)
# 			# transceiver.send(alloff,fast=fast)
# 			ptoc()
# 			note=None
