#ribbon_a and ribbon_b are the two important variables here
ribbon_a=None
ribbon_b=None

__all__=['ribbon_a','ribbon_b']

from urp import *
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn as ADS1115_AnalogIn
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn as Internal_AnalogIn
from tools import *
import storage
from linear_modules import *

i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)# Create the I2C bus with a fast frequency

#I2C addresses for ADS1115's: 0x48 and 0x4a for Ribbon A and Ribbon B respectively
ads_a = ADS.ADS1115(i2c,address=0x48) 
ads_b = ADS.ADS1115(i2c,address=0x4a) 

data_rate=860 # Maximum number of samples per second
ads_a.data_rate = data_rate
ads_b.data_rate = data_rate

ads_gain_single=1
ads_gain_dual  =8 #Uses 100kΩ

#Change the gains depending on whether you're measuring dual or single touches
ads_a.gain=ads_gain_single
ads_b.gain=ads_gain_single

ads_a_a0 = ADS1115_AnalogIn(ads_a, ADS.P0)
ads_a_a1 = ADS1115_AnalogIn(ads_a, ADS.P1)
ads_a_a2 = ADS1115_AnalogIn(ads_a, ADS.P2)
ads_a_single=ads_a_a0
ads_a_dual_a=ads_a_a1
ads_a_dual_b=ads_a_a2
rib_a_mid = Internal_AnalogIn(board.D26)

ads_b_a0 = ADS1115_AnalogIn(ads_b, ADS.P0)
ads_b_a1 = ADS1115_AnalogIn(ads_b, ADS.P1)
ads_b_a2 = ADS1115_AnalogIn(ads_b, ADS.P2)
ads_b_single=ads_b_a0
ads_b_dual_a=ads_b_a1
ads_b_dual_b=ads_b_a2
rib_b_mid = Internal_AnalogIn(board.D27)

single_pull=DigitalInOut(board.D32)
single_pin =DigitalInOut(board.D31)
dual_pin_2 =DigitalInOut(board.D25)
dual_pin_1 =DigitalInOut(board.D24)
single_pull.direction=Direction.OUTPUT
single_pin .direction=Direction.OUTPUT
dual_pin_2 .direction=Direction.OUTPUT
dual_pin_1 .direction=Direction.OUTPUT

def activate_single_touch_transistors():
	single_pin.value=True
	dual_pin_1  .value=False
	dual_pin_2  .value=False

def activate_dual_touch_transistors():
	single_pin.value=False
	dual_pin_1  .value=True
	dual_pin_2  .value=True

class I2CError(OSError):
	pass

class Ribbon:
	def __init__(self,name,rib_mid,ads,ads_single,ads_dual_a,ads_dual_b):
		self.name=name
		self.rib_mid=rib_mid
		self.ads=ads
		self.ads_single=ads_single
		self.ads_dual_a=ads_dual_a
		self.ads_dual_b=ads_dual_b

		dual_touch_a_to_neopixel_calibration_path       = self.name+'dual_touch_a_to_neopixel_calibration'
		dual_touch_b_to_neopixel_calibration_path       = self.name+'dual_touch_b_to_neopixel_calibration'
		single_touch_to_neopixel_calibration_path       = self.name+'single_touch_to_neopixel_calibration'
		cheap_single_touch_to_neopixel_calibration_path = self.name+'cheap_single_touch_to_neopixel_calibration'

		dual_touch_a_to_neopixel_calibration       = HistogramFitter(dual_touch_a_to_neopixel_calibration_path      )
		dual_touch_b_to_neopixel_calibration       = HistogramFitter(dual_touch_b_to_neopixel_calibration_path      )
		single_touch_to_neopixel_calibration       = HistogramFitter(single_touch_to_neopixel_calibration_path      )
		cheap_single_touch_to_neopixel_calibration = HistogramFitter(cheap_single_touch_to_neopixel_calibration_path)

	def dual_touch_reading(self):
		return DualTouchReading(self)

	def single_touch_reading(self):
		return SingleTouchReading(self)

	def cheap_single_touch_reading(self):
		return CheapSingleTouchReading(self)

	def processed_dual_touch_reading(self):
		return ProcessedDualTouchReading(self)
	
	def run_calibration(self,samples_per_pixel=25,ads_bin_size=100,rib_bin_size=100):
		import lightboard.display as display
		import lightboard.neopixels as neopixels
		import lightboard.buttons as buttons
		import lightboard.widgets as widgets

		def display_dot(index,r=63,g=63,b=63):
			index=max(0,min(index,neopixels.length-1))
			neopixel_data=bytearray([0,0,0]*3*neopixels.length)
			neopixel_data[index*3:index*3+3]=bytearray([g,r,b])
			neopixels.write(neopixel_data)

		dual_touch_a_to_neopixel_calibration       = HistogramFitter(bin_size=ads_bin_size)
		dual_touch_b_to_neopixel_calibration       = HistogramFitter(bin_size=ads_bin_size)
		single_touch_to_neopixel_calibration       = HistogramFitter(bin_size=ads_bin_size)
		cheap_single_touch_to_neopixel_calibration = HistogramFitter(bin_size=rib_bin_size)

		buttons.metal_button.color=(255,0,255)

		display.set_text('Running calibration on ribbon '+self.name+'\nPlease press the glowing green buttons until\nthe red dot is barely on the ribbon')
		buttons.set_green_button_lights(1,1,0,0)
		button_press_next_neopixel=buttons.ButtonPressViewer(buttons.green_button_1)
		button_press_prev_neopixel=buttons.ButtonPressViewer(buttons.green_button_2)


		i=0
		display_dot(i,63,0,0)
		while True:
			reading=self.cheap_single_touch_reading()
			if reading.gate:
				break

			refresh_flag=False
			if button_press_next_neopixel.value:
				i+=1
				refresh_flag=True
			if button_press_prev_neopixel.value:
				i-=1
				refresh_flag=True
			if refresh_flag:
				i=min(neopixels.length-1,max(0,i))
				display_dot(i,63,0,0)

			if buttons.metal_button.value:
				if widgets.input_yes_no("Do you want to cancel calibration?\n(All progress will be lost)"):
					return


		button_press_skip=buttons.ButtonPressViewer(buttons.green_button_1)
		button_press_back=buttons.ButtonPressViewer(buttons.green_button_2)
		button_press_finished=buttons.ButtonPressViewer(buttons.green_button_3)
		buttons.set_green_button_lights(1,1,1,0)

		display.set_text('Running calibration on ribbon '+self.name+'\nPlease press cyan dots on ribbon\nuntil they become orange\nPress the 3rd green button when you\'re done\nPress button 1 to skip the current dot\nPress button 2 to go back a dot')
		finished=False
		while i<neopixels.length and not finished:
			i=max(0,min(i,neopixels.length-1))
			display_dot(i,0,63,63)
			pixel_num_samples=0
			while pixel_num_samples<samples_per_pixel:
				if buttons.metal_button.value:
					if widgets.input_yes_no("Do you want to cancel calibration?\n(All progress will be lost)"):
						return
				if button_press_skip.value:
					break
				if button_press_back.value:
					i-=2
					break
				if button_press_finished.value:
					if widgets.input_yes_no("Are you sure your're done\ncalibrating this ribbon?"):
						finished=True
						break
				if self.cheap_single_touch_reading().gate:
					with neopixels.TemporarilyTurnedOff():
						cheap_single_touch_reading=self.cheap_single_touch_reading()
						single_touch_reading      =self.single_touch_reading()
						dual_touch_reading        =self.dual_touch_reading()

						dual_touch_a_to_neopixel_calibration      .add_sample(dual_touch_reading        .raw_a    ,i)
						dual_touch_b_to_neopixel_calibration      .add_sample(dual_touch_reading        .raw_b    ,i)
						single_touch_to_neopixel_calibration      .add_sample(single_touch_reading      .raw_value,i)
						cheap_single_touch_to_neopixel_calibration.add_sample(cheap_single_touch_reading.raw_value,i)

						pixel_num_samples+=1
			i+=1
			display_dot(i,63,31,0)
			while self.cheap_single_touch_reading().gate:
				pass

		display.set_text('Finished calibration on ribbon '+self.name+'\nWould you like to save it?\nPrinting out sensor values to serial for a demo\n(Watch in the arduino plotter)')

		neopixels.turn_off()

		while not buttons.metal_button.value:
			if self.cheap_single_touch_reading().gate:
				with neopixels.TemporarilyTurnedOff():
					cheap_single_touch_reading=self.cheap_single_touch_reading()
					single_touch_reading      =self.single_touch_reading()
					dual_touch_reading        =self.dual_touch_reading()

					dual_a      =dual_touch_a_to_neopixel_calibration      (dual_touch_reading        .raw_a    )
					dual_b      =dual_touch_b_to_neopixel_calibration      (dual_touch_reading        .raw_b    )
					single      =single_touch_to_neopixel_calibration      (single_touch_reading      .raw_value)
					cheap_single=cheap_single_touch_to_neopixel_calibration(cheap_single_touch_reading.raw_value)

					if cheap_single_touch_reading.gate and single_touch_reading.gate:

						display_dot(int(cheap_single),0,128,0)

						print(dual_a,dual_b,single,cheap_single)

		display.set_text("Now for a smoooooth demo...")

		#This is a show-offy demo lol. Try miscalibrating it such that a tiny vibrato makes it move from one side of the lightwave to the otehr...
		DISCRETE=True
		N=10
		V=[]
		def mean(l):
			l=list(l)
			return sum(l)/len(l)
		def std(l):
			u=mean(l)
			return mean((x-u)**2 for x in l)**.5
		tether=SoftTether(size=5)
		tet2=Tether(1)
		while not buttons.metal_button.value:
			single=self.single_touch_reading()
			# if single_reader.error:
				# print("ERROR:",single_reader.error)
			# else:
			if single.gate:
				V.append(single.raw_value)
				while len(V)>N:
					del V[0]
				val=tether(mean(V))
				if DISCRETE:
					Val=(tet2(int(val)))
				else:
					Val=(val)
				val=single_touch_to_neopixel_calibration(Val)
				display_dot(int(val),64,0,128)
			else:
				V.clear()
				tether.value=None




ribbon_a=Ribbon('a',rib_a_mid,ads_a,ads_a_single,ads_a_dual_a,ads_a_dual_b)
ribbon_b=Ribbon('b',rib_b_mid,ads_b,ads_b_single,ads_b_dual_a,ads_b_dual_b)

class SingleTouchReading:
	GATE_THRESHOLD=500 #This needs to be calibrated after observing the raw_gap when touching and not touching the ribbon. You can do this automatically with some fancy algorithm, or you can just look at the serial monitor while printing reading.raw_gap over and over again

	def __init__(self,ribbon):
		self.ribbon=ribbon
		self.read_raw_lower()
		self.read_raw_upper()
		self.process_readings()
		
	def prepare_to_read(self):
		activate_single_touch_transistors()
		self.ribbon.ads.mode=ADS.Mode.SINGLE
		self.ribbon.ads.gain=ads_gain_single

	def read_raw_lower(self):
		single_pull.value=False
		self.prepare_to_read()
		try:
			self.raw_lower=self.ribbon.ads_single.value
		except OSError as exception:
			raise I2CError(exception)

	def read_raw_upper(self):
		single_pull.value=True
		self.prepare_to_read()
		try:
			self.raw_upper=self.ribbon.ads_single.value
		except OSError as exception:
			raise I2CError(exception)

	def process_readings(self):
		self.raw_gap=abs(self.raw_upper-self.raw_lower)
		self.gate=self.raw_gap<self.GATE_THRESHOLD
		self.raw_value=(self.raw_upper+self.raw_lower)/2

class ContinuousSingleTouchReading(SingleTouchReading):
	#Should be similar to SingleTouchReading, but much faster when not using DualTouchReading
	#WARNING AND TODO: This function isn't currently doing enough to flush out anything. Perhaps continous can use the CheapSingleTouchReading's gate, and a single non-wobbling single_pull value
	@staticmethod
	def prepare_to_read():
		activate_single_touch_transistors()
		ads.mode=ADS.Mode.CONTINUOUS
		ads.gain=ads_gain_single
		self.ribbon.ads_single.value #Flush out the current reading of the ADC, in-case we changed single_pull in the middle of the ADS's reading (which happens 99% of the time if we don't do this lol - making detecting the gate practically useless)

class CheapSingleTouchReading(SingleTouchReading):
	#TODO: The Teensy's internal ADC is wonked. Between around raw values 30000 and 35000, it jumps (whereas the ADS1115 doesn't jump).
	#		Calibration with respect to the ADS1115's non-cheap single touch should mitigate this problem
	#		Even though the raw range is the same for both analog_in and ads_single, we need a larger GATE_THRESHOLD for CheapSingleTouchReading beacause of this flaw in Teensy's ADC.
	#Uses the Teensy's internal ADC that can read up to 6000x per second
	#TODO: Implement a variation of the SingleTouchReading class called quick-gate check via the Teensy's internal ADC to save a bit of time and get more accurate results on the dual touch readings (because then we can check both upper and lower both before and after the dual readings which means less spikes)
	GATE_THRESHOLD=5000
	def read_raw_lower(self):
		self.prepare_to_read()
		single_pull.value=False
		self.raw_lower=self.ribbon.rib_mid.value

	def read_raw_upper(self):
		self.prepare_to_read()
		single_pull.value=True
		self.raw_upper=self.ribbon.rib_mid.value

class DualTouchReading:
	def __init__(self,ribbon):
		self.ribbon=ribbon
		self.prepare_to_read()
		try:
			self.raw_a=self.ribbon.ads_dual_a.value
			self.raw_b=self.ribbon.ads_dual_b.value
		except OSError as exception:
			raise I2CError(exception)

	def prepare_to_read(self):
		activate_dual_touch_transistors()
		self.ribbon.ads.gain=ads_gain_dual

class ProcessedDualTouchReading:
	def __init__(self,ribbon):
		single_before=ribbon.cheap_single_touch_reading()

		if not single_before.gate:
			self.gate=False
			#Don't waste time with the dual touch reading if one of the gates is False
			return

		dual=ribbon.dual_touch_reading()

		single_after=ribbon.cheap_single_touch_reading()

		self.gate=single_before.gate and single_after.gate
		if self.gate:
			self.dual_a=ribbon.dual_touch_a_to_neopixel_calibration(dual.raw_a)
			self.dual_b=ribbon.dual_touch_b_to_neopixel_calibration(dual.raw_b)
			self.single=(single_before.raw_value+single_after.raw_value)/2
			self.single=ribbon.cheap_single_touch_to_neopixel_calibration(self.single)



