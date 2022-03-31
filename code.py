from lightboard.config import config
from linear_modules import *
from urp import *
import lightboard.buttons as buttons
import lightboard.display as display
import lightboard.neopixels as neopixels
import lightboard.pressure as pressure
import lightboard.ribbons as ribbons
import lightboard.transceiver as transceiver
import lightboard.widgets as widgets
import math
attempt_to_mount()

def jiggle_mod_wheel():
	#Use this to learn the mod wheel in MIDI synths (e.g. FL Studio) 
	with buttons.TemporaryMetalButtonLights(0,1,1):
		while not buttons.metal_press_viewer.value:
			value=math.sin(seconds())
			value=value+1
			value=value/2
			display.set_text("Jiggling Mod Wheel:\n%f\n\nPress metal to exit"%value)
			transceiver.send(midi_mod_wheel_from_float(value),fast=False)

use_pressure=False
while True:
	option=widgets.input_select(
		['Play','Play With Pressure','Calibrate Ribbons','Calibrate Pressure','Brightness','Jiggle Mod Wheel'],
		prompt="Please choose new option\n    Old option: "+repr(config['weeble wobble wooble'])+'\n'+repr(config),
		can_cancel=False,
		must_confirm=True)
	if option=='Play':
		break
	if option=='Play With Pressure':
		use_pressure=True
		break
	elif option=='Brightness':
		widgets.edit_config_int('neopixels brightness')
	elif option=='Calibrate Ribbons':
		ribbons.show_calibration_menu()
	elif option=='Calibrate Pressure':
		pressure.show_calibration_menu()
	elif option=='Jiggle Mod Wheel':
		jiggle_mod_wheel()

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
	if use_pressure:
		message+=midi_mod_wheel_from_float(pressure.get_pressure())
	transceiver.send(message,fast=fast)
	midi_message_state={'notes_off':set()}

def note_on(note):
	note+=semitone_shift
	if 0<=note<=127:
		midi_message_state['note_on']=note
		if note in midi_message_state['notes_off']:
			midi_message_state['notes_off']-={note}

def gate_off(note):
	note+=semitone_shift
	if 0<=note<=127:
		global midi_message_state
		midi_message_state={'notes_off':midi_message_state['notes_off']|{note}}

def note_off(note):
	note+=semitone_shift
	if 0<=note<=127:
		midi_message_state['notes_off']|={note}
		if 'note_on' in midi_message_state and midi_message_state['note_on']==note:
			del midi_message_state['note_on']

def pitch_bend(semitones):
	midi_message_state['pitch_bend']=semitones

buttons.set_green_button_lights(0,0,0,0)
buttons.metal_button.color=(0,0,0)

scales=[major_scale,
        natural_minor_scale,
        harmonic_minor_scale,
        blues_scale,
        chromatic_scale]

scale_names=['Major Scale',
             'Natural Minor Scale',
             'Harmonic Minor Scale',
             'Blues Scale',
             'Chromatic Scale']

def switch_scale():
	global current_scale
	scale_index=(scales.index(current_scale)+1)%len(scales)
	current_scale=scales[scale_index]
	display.set_text("Using:\n"+scale_names[scale_index])

switch_scale_button_index=1
switch_scale_button_press_viewer=buttons.green_press_viewers[switch_scale_button_index]
buttons.green_buttons[switch_scale_button_index].light=True

current_scale=chromatic_scale
switch_scale()
neopixels.draw_pixel_colors(current_scale)
neopixels.refresh()

#SETTINGS START:
pixels_per_note=3
pixel_offset=12#The number of pixels below the start of the first note
semitone_shift=0
#SETTINGS END

pixel_offset-=pixels_per_note
last_midi_time=seconds()
position=0
while True:

	# reading_a=ribbons.ribbon_a.processed_cheap_single_touch_reading()
	# reading_b=ribbons.ribbon_b.processed_cheap_single_touch_reading()

	# reading_a=ribbons.ribbon_a.processed_single_touch_reading()
	# reading_b=ribbons.ribbon_b.processed_single_touch_reading()

	reading_a=ribbons.ribbon_a.processed_dual_touch_reading()
	reading_b=ribbons.ribbon_b.processed_dual_touch_reading()


	reading=reading_a
	if reading_b.gate:
		reading=reading_b
	if reading.gate:
		reading.value=reading.top

	if reading.gate:
		position=reading.value
		position+=pixel_offset
		value=note_to_pitch(int(position/pixels_per_note),*current_scale)
		ribbon=reading.ribbon
		assert isinstance(ribbon,ribbons.Ribbon)
		if ribbon.name=='b':#CHOO CHOO
			value+=12#Up a full octave (12 semitones)
		new_note=value
		new_note=int(new_note)
		remainder=value-new_note
		if new_note != note:
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
		neopixels.draw_pixel_colors(current_scale,position=position,pixels_per_note=pixels_per_note,pixel_offset=pixel_offset)
		neopixels.refresh()
		
	if switch_scale_button_press_viewer.value:
		switch_scale()
	if buttons.green_1_press_viewer.value:
		semitone_shift+=1
	if buttons.green_3_press_viewer.value:
		semitone_shift-=1