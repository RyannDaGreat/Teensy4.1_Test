#ribbon_a and ribbon_b are the two important variables here
ribbon_a=None
ribbon_b=None

#Notes:
#    - As it turns out, the internal ADC in the Teensy is NOT very susceptible to fluctuations in the Neopixels' current...BUT...the ADS1115 IS. 
#      Therefore, I think a better model would ditch the ADS1115 alltogether - replacing it with a simple 8x toggleable amp for dual touches. 
#    - Shouldn't cause errors. No scl/sda pullup means the board isn't connected. No i2c at 48 means the individual chip isn't powered or connected etc. I just ficed a bad solder joint that took a while to flare up.......maybe this is what happened with the old lightwave? I was too quick with the solder joints, leaving a bubble that didn't touch it because of some stress bs later on?

__all__=['ribbon_a','ribbon_b']

from urp import *
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from collections import OrderedDict
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn as ADS1115_AnalogIn
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogIn as Internal_AnalogIn
from tools import *
import storage
from linear_modules import *
import lightboard.neopixels as neopixels
import time
from micropython import const


i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)# Create the I2C bus with a fast frequency

#I2C addresses for ADS1115's: 0x48 and 0x4a for Ribbon A and Ribbon B respectively
ads_a = ADS.ADS1115(i2c,address=0x48) 
ads_b = ADS.ADS1115(i2c,address=0x4a) 

data_rate=const(860) # Maximum number of samples per second
ads_a.data_rate = data_rate
ads_b.data_rate = data_rate

ads_gain_single=const(1)
ads_gain_dual  =const(8) #Uses 100kΩ

#Change the gains depending on whether you're measuring dual or single touches
ads_a.gain=ads_gain_single
ads_b.gain=ads_gain_single

ads_a_a0 = ADS1115_AnalogIn(ads_a, ADS.P0)
ads_a_a1 = ADS1115_AnalogIn(ads_a, ADS.P1)
ads_a_a2 = ADS1115_AnalogIn(ads_a, ADS.P2)
ads_a_single=ads_a_a0
ads_a_dual_top=ads_a_a1
ads_a_dual_b=ads_a_a2
rib_a_mid = Internal_AnalogIn(board.D26)

ads_b_a0 = ADS1115_AnalogIn(ads_b, ADS.P0)
ads_b_a1 = ADS1115_AnalogIn(ads_b, ADS.P1)
ads_b_a2 = ADS1115_AnalogIn(ads_b, ADS.P2)
ads_b_single=ads_b_a0
ads_b_dual_top=ads_b_a1
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

	ADS_BIN_SIZE=100
	RIB_BIN_SIZE=100
	CALIBRATION_FOLDER='/generated/calibrations/ribbons'

	def __init__(self,name,rib_mid,ads,ads_single,ads_dual_top,ads_dual_bot):
		self.name=name
		self.rib_mid=rib_mid
		self.ads=ads
		self.ads_single=ads_single
		self.ads_dual_top=ads_dual_top
		self.ads_dual_bot=ads_dual_bot

		dual_touch_top_to_neopixel_calibration_path     = path_join(self.CALIBRATION_FOLDER,self.name+'_dual_touch_top_to_neopixel_calibration'    )
		dual_touch_bot_to_neopixel_calibration_path     = path_join(self.CALIBRATION_FOLDER,self.name+'_dual_touch_bot_to_neopixel_calibration'    )
		single_touch_to_neopixel_calibration_path       = path_join(self.CALIBRATION_FOLDER,self.name+'_single_touch_to_neopixel_calibration'      )
		cheap_single_touch_to_neopixel_calibration_path = path_join(self.CALIBRATION_FOLDER,self.name+'_cheap_single_touch_to_neopixel_calibration')

		self.dual_touch_top_to_neopixel_calibration     = HistogramFitter(bin_size=self.ADS_BIN_SIZE,file_path=dual_touch_top_to_neopixel_calibration_path    ,auto_load=True)
		self.dual_touch_bot_to_neopixel_calibration     = HistogramFitter(bin_size=self.ADS_BIN_SIZE,file_path=dual_touch_bot_to_neopixel_calibration_path    ,auto_load=True)
		self.single_touch_to_neopixel_calibration       = HistogramFitter(bin_size=self.ADS_BIN_SIZE,file_path=single_touch_to_neopixel_calibration_path      ,auto_load=True)
		self.cheap_single_touch_to_neopixel_calibration = HistogramFitter(bin_size=self.RIB_BIN_SIZE,file_path=cheap_single_touch_to_neopixel_calibration_path,auto_load=True)

		self.previous_gate=False

		self.dual_num_fingers=0
		dual_filter_moving_average_length=3
		dual_filter_soft_tether_size=.1
		dual_filter_tether_size=.05
		self.dual_bot_filter=NoiseFilter(moving_average_length=dual_filter_moving_average_length,soft_tether_size=dual_filter_soft_tether_size,tether_size=dual_filter_tether_size)
		self.dual_top_filter=NoiseFilter(moving_average_length=dual_filter_moving_average_length,soft_tether_size=dual_filter_soft_tether_size,tether_size=dual_filter_tether_size)

		self.cheap_single_filter=NoiseFilter(moving_average_length=3,soft_tether_size=.3,tether_size=.01,moving_median_length=3)


	@property
	def is_calibrated(self):
		return self.dual_touch_top_to_neopixel_calibration    .is_fitted and \
		       self.dual_touch_bot_to_neopixel_calibration    .is_fitted and \
		       self.single_touch_to_neopixel_calibration      .is_fitted and \
		       self.cheap_single_touch_to_neopixel_calibration.is_fitted

	def dual_touch_reading(self):
		reading=DualTouchReading(self)
		#DualTouchReading objects don't have a gate as of right now (though they will probably soon - we can get the gate by comparing the top value to the bot value and setting a threshold)
		return reading

	def single_touch_reading(self):
		reading=SingleTouchReading(self)
		self.previous_gate=reading.gate
		return reading

	def cheap_single_touch_reading(self):
		reading=CheapSingleTouchReading(self)
		self.previous_gate=reading.gate
		return reading

	def processed_single_touch_reading(self,blink=False):
		# if not self.is_calibrated: #Unnessecary CPU time...its cheap but so unimportant...
			# print("Ribbon.processed_single_touch_reading: Warning: This ribbon is not calibrated!")
		reading=ProcessedSingleTouchReading(self,blink=blink)
		self.previous_gate=reading.gate
		return reading

	def processed_cheap_single_touch_reading(self,blink=False):
		reading=ProcessedCheapSingleTouchReading(self,blink=blink)
		self.previous_gate=reading.gate
		return reading

	def processed_dual_touch_reading(self,blink=False):
		reading=ProcessedDualTouchReading(self,blink=blink)
		self.previous_gate=reading.gate
		return reading
	
	def run_calibration(self,samples_per_pixel=25):
		def ask_to_try_again():
			if widgets.input_yes_no("Would you like to try calibrating again?"):
				self.run_calibration(samples_per_pixel)


		import lightboard.display as display
		import lightboard.neopixels as neopixels
		import lightboard.buttons as buttons
		import lightboard.widgets as widgets

		dual_touch_top_to_neopixel_calibration     = HistogramFitter(bin_size=self.ADS_BIN_SIZE,file_path=self.dual_touch_top_to_neopixel_calibration    .file_path,auto_load=False)
		dual_touch_bot_to_neopixel_calibration     = HistogramFitter(bin_size=self.ADS_BIN_SIZE,file_path=self.dual_touch_bot_to_neopixel_calibration    .file_path,auto_load=False)
		single_touch_to_neopixel_calibration       = HistogramFitter(bin_size=self.ADS_BIN_SIZE,file_path=self.single_touch_to_neopixel_calibration      .file_path,auto_load=False)
		cheap_single_touch_to_neopixel_calibration = HistogramFitter(bin_size=self.RIB_BIN_SIZE,file_path=self.cheap_single_touch_to_neopixel_calibration.file_path,auto_load=False)

		buttons.metal_button.color=(255,0,255)

		display.set_text('Running calibration on ribbon '+self.name+'\nPlease press the glowing green buttons until\nthe red dot is barely on the ribbon')
		buttons.set_green_button_lights(1,1,0,0)
		button_press_next_neopixel=buttons.ButtonPressViewer(buttons.green_button_1)
		button_press_prev_neopixel=buttons.ButtonPressViewer(buttons.green_button_2)


		i=0
		neopixels.display_dot(i,63,0,0)
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
				neopixels.display_dot(i,63,0,0)

			if buttons.metal_press_viewer.value:
				if widgets.input_yes_no("Do you want to cancel calibration?\n(All progress will be lost)"):
					ask_to_try_again()
					return


		button_press_skip    =buttons.ButtonPressViewer(buttons.green_button_1)
		button_press_back    =buttons.ButtonPressViewer(buttons.green_button_2)
		button_press_finished=buttons.ButtonPressViewer(buttons.green_button_3)
		buttons.set_green_button_lights(1,1,0,0)

		display.set_text('Running calibration on ribbon '+self.name+'\nPlease press cyan dots on ribbon\nuntil they become orange\nPress the 3rd green button when you\'re done\n(If the 3rd green button isnt lit, calibrate at least two points)\nPress button 1 to skip the current dot\nPress button 2 to go back a dot')
		finished=False
		num_pixels_calibrated=0 #We need at least two to be useful...
		while not finished:
			i=max(0,min(i,neopixels.length-1))
			neopixels.display_dot(i,0,63,63)
			pixel_num_samples=0
			while True:
				buttons.green_button_3.light=num_pixels_calibrated>=2
				if buttons.metal_button.value:
					if widgets.input_yes_no("Do you want to cancel calibration?\n(All progress will be lost)"):
						ask_to_try_again()
						return
				if button_press_skip.value:
					break
				if button_press_back.value:
					i-=2
					break
				if button_press_finished.value and num_pixels_calibrated>=2:
					if widgets.input_yes_no("Are you sure your're done\ncalibrating this ribbon?"):
						finished=True
						break
				if self.cheap_single_touch_reading().gate:
					with neopixels.TemporarilyTurnedOff():
						cheap_single_touch_reading=self.cheap_single_touch_reading()
						single_touch_reading      =self.single_touch_reading()
						dual_touch_reading        =self.dual_touch_reading()

						dual_touch_top_to_neopixel_calibration    .add_sample(dual_touch_reading        .raw_a    ,i)
						dual_touch_bot_to_neopixel_calibration    .add_sample(dual_touch_reading        .raw_b    ,i)
						single_touch_to_neopixel_calibration      .add_sample(single_touch_reading      .raw_value,i)
						cheap_single_touch_to_neopixel_calibration.add_sample(cheap_single_touch_reading.raw_value,i)

						pixel_num_samples+=1

				if pixel_num_samples>=samples_per_pixel:
					num_pixels_calibrated+=1
					break

			i+=1
			neopixels.display_dot(i,63,31,0)
			while self.cheap_single_touch_reading().gate:
				pass

		buttons.set_green_button_lights(0,0,0,0)
		buttons.metal_button.color=(0,1,1)
		neopixels.turn_off()

		display.set_text('Finished calibration on ribbon '+self.name+'\nTry the ribbon out to see if you like it\nAlso rinting out sensor values to serial for a demo\n(Watch in the arduino plotter)\nPress the metal button when you\'re done')


		while not buttons.metal_press_viewer.value:
			if self.cheap_single_touch_reading().gate:
				with neopixels.TemporarilyTurnedOff():
					cheap_single_touch_reading=self.cheap_single_touch_reading()
					single_touch_reading      =self.single_touch_reading()
					dual_touch_reading        =self.dual_touch_reading()

					dual_top = dual_touch_top_to_neopixel_calibration(dual_touch_reading  .raw_a    )
					dual_bot = dual_touch_bot_to_neopixel_calibration(dual_touch_reading  .raw_b    )
					single   = single_touch_to_neopixel_calibration  (single_touch_reading.raw_value)
					cheap_single=cheap_single_touch_to_neopixel_calibration(cheap_single_touch_reading.raw_value)

					if cheap_single_touch_reading.gate and single_touch_reading.gate:

						neopixels.display_dot(int(cheap_single),0,128,0)

						print(dual_top,dual_bot,single,cheap_single)

		self.test_smooth_demo(single_touch_to_neopixel_calibration)

		if widgets.input_yes_no("Would you like to save this\ncalibration for ribbon "+self.name+"?"):
			self.dual_touch_top_to_neopixel_calibration     = dual_touch_top_to_neopixel_calibration
			self.dual_touch_bot_to_neopixel_calibration     = dual_touch_bot_to_neopixel_calibration
			self.single_touch_to_neopixel_calibration       = single_touch_to_neopixel_calibration
			self.cheap_single_touch_to_neopixel_calibration = cheap_single_touch_to_neopixel_calibration
			self.dual_touch_top_to_neopixel_calibration    .save_to_file()
			self.dual_touch_bot_to_neopixel_calibration    .save_to_file()
			self.single_touch_to_neopixel_calibration      .save_to_file()
			self.cheap_single_touch_to_neopixel_calibration.save_to_file()
			display.set_text("Saved calibrations for ribbon "+self.name+"!")
			time.sleep(2)
		else:
			display.set_text("Cancelled. No calibrations were saved.")
			time.sleep(2)
			ask_to_try_again()
			return

	def test_smooth_demo(self,single_touch_to_neopixel_calibration=None):
		import lightboard.buttons   as buttons
		import lightboard.neopixels as neopixels
		import lightboard.display   as display

		buttons.metal_button.color=(1,0,1)
		display.set_text("Now for a smoooooth demo...\n(Press the metal button when you're done)")

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
		while not buttons.metal_press_viewer.value:
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
				if single_touch_to_neopixel_calibration is None:
					single_touch_to_neopixel_calibration=self.single_touch_to_neopixel_calibration
				val=single_touch_to_neopixel_calibration(Val)
				neopixels.display_dot(int(val),64,0,128)
			else:
				V.clear()
				tether.value=None

		neopixels.turn_off()

class NoiseFilter:
	#This is a LinearModule
	#It should be cleared whever the gate is off
	def __init__(self,moving_average_length=10,
	                  soft_tether_size     =5,
	                  tether_size          =1,
	                  moving_median_length =1):
		self.moving_average=MovingAverage(moving_average_length)
		self.soft_tether=SoftTether(size=soft_tether_size)
		self.tether=Tether(size=tether_size)
		self.moving_median=MovingMedian(moving_median_length)
	def __call__(self,value):
		value=self.moving_average(value)
		value=self.soft_tether   (value)
		value=self.tether        (value)
		value=self.moving_median (value)
		return value
	def clear(self):
		self.soft_tether   .clear()
		self.tether        .clear()
		self.moving_average.clear()
		self.moving_median .clear()
	def copy(self):
		#Create a duplicate filter with the same parameters
		return NoiseFilter(self.moving_average.length,self.soft_tether.size,self.tether.size)


class SingleTouchReading:
	__slots__=['gate','raw_lower','raw_upper','raw_gap', 'raw_value']

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
	GATE_THRESHOLD=1500
	def read_raw_lower(self):
		self.prepare_to_read()
		single_pull.value=False
		self.raw_lower=self.ribbon.rib_mid.value

	def read_raw_upper(self):
		self.prepare_to_read()
		single_pull.value=True
		self.raw_upper=self.ribbon.rib_mid.value

class DualTouchReading:
	__slots__ = ['raw_a', 'raw_b']

	def __init__(self,ribbon):
		self.ribbon=ribbon
		self.prepare_to_read()
		try:
			self.raw_a=self.ribbon.ads_dual_top.value
			self.raw_b=self.ribbon.ads_dual_bot.value
		except OSError as exception:
			raise I2CError(exception)

	def prepare_to_read(self):
		activate_dual_touch_transistors()
		self.ribbon.ads.gain=ads_gain_dual

class ProcessedDualTouchReading:
	__slots__=['gate','bot','top','mid','num_fingers','old','new']

	DELTA_THRESHOLD=-4 # A distance, measured in neopixel widths, that the two dual touches can be apart from one another before registering as not being touched. (This is because, as it turns out, it can sometimes take more than one sample for dual touch values to go all the way back to the top after releasing your finger from the ribbon)
	#You want to calibrate DELTA_THRESHOLD such that it's high enough to keep good readings once you release your finger, but low enough that it doesn't require pressing down too hard to activate. 
	#DELTA_THRESHOLD can be a negative value.
	#DELTA_THRESHOLD might need to be changed if you calibrate with a pencil eraser instead of your fingertip, because the pencil eraser is a narrower touch area etc.
	#You should always calibrate using your finger for this reason...

	TWO_TOUCH_THRESHOLD=1#A distance, measured in neopixel widths, that the dual readings must be apart from each other to register as 
	TWO_TOUCH_THRESHOLD_SLACK=.05 #A bit of hysterisis used here...like a tether. Basically, to prevent flickering on the bonudary, to switch between two touch and one touch you must move this much distance.

	def __init__(self,ribbon,blink=False):
		#If self.gate is False, your code shouldn't try to check for a .bot, .top, or .middle value - as it was never measured
		#If your fingers are pressing the ribbon in two different places, after calibration the 'top' value should be above the 'bot' value
		#	In the event that the hardware of the z
		self.ribbon=ribbon

		previous_gate=ribbon.previous_gate

		single_before=ribbon.cheap_single_touch_reading()

		if not single_before.gate:
			self.gate=False
			#Don't waste time with the dual touch reading if one of the gates is False
			return

		with neopixels.TemporarilyTurnedOff() if blink else EmptyContext():
			dual_reading=ribbon.dual_touch_reading()

		single_after=ribbon.cheap_single_touch_reading()

		if not previous_gate:
			ribbon.dual_bot_filter.clear()
			ribbon.dual_top_filter.clear()

		self.gate=single_before.gate and single_after.gate
		if self.gate:
			#TODO: Lower the DELTA_THRESHOLD and use self.middle whenever it gets too crazy; that way we can have maximum sensitivity and never miss a sample...
			mid=(single_before.raw_value+single_after.raw_value)/2
			top=dual_reading.raw_a
			bot=dual_reading.raw_b

			top=ribbon.dual_touch_top_to_neopixel_calibration(top)
			bot=ribbon.dual_touch_bot_to_neopixel_calibration(bot)
			mid=ribbon.cheap_single_touch_to_neopixel_calibration(mid)
			delta=top-bot

			#The older and newer dual touch positions. Only different when num_fingers>1
			if not hasattr(ribbon,'previous_dual_old'):
				ribbon.previous_dual_old=mid
			old,new=sorted([bot,top],key=lambda pos:abs(pos-ribbon.previous_dual_old))

			old_num_fingers=ribbon.dual_num_fingers
			changed_num_fingers=False
			if not previous_gate:
				 ribbon.dual_num_fingers = 2 if delta>self.TWO_TOUCH_THRESHOLD else 1
				 changed_num_fingers=old_num_fingers!=ribbon.dual_num_fingers
			elif ribbon.dual_num_fingers == 1 and delta>self.TWO_TOUCH_THRESHOLD+self.TWO_TOUCH_THRESHOLD_SLACK:
				 ribbon.dual_num_fingers = 2
				 changed_num_fingers=old_num_fingers!=ribbon.dual_num_fingers
			elif ribbon.dual_num_fingers == 2 and delta<self.TWO_TOUCH_THRESHOLD-self.TWO_TOUCH_THRESHOLD_SLACK:
				 ribbon.dual_num_fingers = 1
				 changed_num_fingers=old_num_fingers!=ribbon.dual_num_fingers
			self.num_fingers=ribbon.dual_num_fingers

			# if changed_num_fingers:
			# 	ribbon.dual_bot_filter.clear()
			# 	ribbon.dual_top_filter.clear()

			self.gate=self.gate and delta>self.DELTA_THRESHOLD
			if self.gate:
				if bot>top:
					#The only time self.bot>self.top is when your're barely pressing on the ribbon at all...
					#...we can average these two values out to get a single, more reasonable value
					bot=top=(bot+top)/2

				if self.num_fingers==1:
					bot=top=sorted((top,bot,mid))[1]

				self.top=ribbon.dual_top_filter(top)
				self.bot=ribbon.dual_bot_filter(bot)
				self.mid=mid
				self.old=old
				self.new=new
				ribbon.previous_dual_old=old

class ProcessedSingleTouchReading:
	def __init__(self,ribbon,blink=False):
		self.ribbon=ribbon
		if ribbon.previous_gate:
			#If it was previously pressed, don't check the gate with the expensive reading...
			with neopixels.TemporarilyTurnedOff() if blink else EmptyContext():
				single_touch_reading=ribbon.single_touch_reading()
			self.gate=single_touch_reading.gate
		else:
			cheap_single_touch_reading=ribbon.cheap_single_touch_reading()
			if cheap_single_touch_reading.gate:
				with neopixels.TemporarilyTurnedOff() if blink else EmptyContext():
					single_touch_reading=ribbon.single_touch_reading()
				self.gate=single_touch_reading.gate
			else:
				self.gate=False

		if self.gate:
			self.raw_value=single_touch_reading.raw_value
			self.value=ribbon.single_touch_to_neopixel_calibration(self.raw_value)

class ProcessedCheapSingleTouchReading:
	def __init__(self,ribbon,blink=False):
		self.ribbon=ribbon
		with neopixels.TemporarilyTurnedOff() if blink else EmptyContext():
			if not ribbon.previous_gate:
				ribbon.cheap_single_touch_reading()#Sometimes it spikes on the first value for some reason...idk why
			cheap_single_touch_reading=ribbon.cheap_single_touch_reading()
		self.gate=cheap_single_touch_reading.gate

		if self.gate:
			self.raw_value=cheap_single_touch_reading.raw_value
			self.value=ribbon.cheap_single_touch_to_neopixel_calibration(self.raw_value)
			self.value=ribbon.cheap_single_filter(self.value)
		else:
			ribbon.cheap_single_filter.clear()
			# pass

def test_ribbon_raw_uart(ribbon):
	#Use this test to print all (raw, uncalibrated) ribbon values to uart
	#Then, you can view them in an arduino grapher
	import lightboard.buttons as buttons
	import lightboard.display as display

	display.set_text('Running raw uart test\nPress metal button\nto end this test\n\nThe green buttons show\ncheap_gate and single_gate\n(They\'re just for display)')
	buttons.set_green_button_lights(0,0,0,0)
	buttons.metal_button.color=(255,0,0)

	while True:
		cheap =ribbon.cheap_single_touch_reading()
		single=ribbon.single_touch_reading()
		dual  =ribbon.dual_touch_reading()

		c_raw_value,c_gate = cheap .raw_value, cheap .gate
		raw_value  ,s_gate = single.raw_value, single.gate
		raw_a,raw_b = dual.raw_a,dual.raw_b

		message = '%s %i %i %.5f %.5f %.5f %.5f'%(ribbon.name, int(c_gate), int(s_gate), c_raw_value, raw_value, raw_a, raw_b)
		print(message)

		buttons.set_green_button_lights(c_gate,s_gate,0,0)

		if buttons.metal_press_viewer.value:
			buttons.metal_button.color=(0,0,0)
			display.set_text('Running raw uart test:\nDone!')
			break

def test_ribbon_dual_touch(ribbon):
	import lightboard.buttons as buttons
	import lightboard.display as display

	display.set_text('Running raw uart test\nPress metal button\nto end this test\n\nThe green buttons show\ncheap_gate and single_gate\n(They\'re just for display)')
	buttons.set_green_button_lights(0,0,0,0)
	buttons.metal_button.color=(255,0,0)

	while True:
		dual  =ribbon.processed_dual_touch_reading()

		if not dual.gate:
			continue

		neopixels.draw_all_off()
		neopixels.draw_dot(dual.top, 64,0,128)
		neopixels.draw_dot(dual.bot, 128,0,64)
		neopixels.draw_dot(dual.mid, 128,128,128*(dual.num_fingers-1))
		neopixels.refresh()


		# message = '%s %i %i %.5f %.5f %.5f %.5f'%(ribbon.name, int(c_gate), int(s_gate), c_raw_value, raw_value, raw_a, raw_b)
		# print(message)

		# buttons.set_green_button_lights(c_gate,s_gate,0,0)

		# if buttons.metal_press_viewer.value:
		# 	buttons.metal_button.color=(0,0,0)
		# 	display.set_text('Running raw uart test:\nDone!')
		# 	break

def show_calibration_menu():
	import lightboard.widgets as widgets

	options = OrderedDict()

	options['Calibrate Rib A'] = ribbon_a.run_calibration
	options['Calibrate Rib B'] = ribbon_b.run_calibration
	options['Smooth Demo A'  ] = ribbon_a.test_smooth_demo
	options['Smooth Demo B'  ] = ribbon_b.test_smooth_demo
	options['Raw UART Demo A'] = lambda: test_ribbon_raw_uart(ribbon_a)
	options['Raw UART Demo B'] = lambda: test_ribbon_raw_uart(ribbon_b)
	options['Dual Touch Demo A'] = lambda: test_ribbon_dual_touch(ribbon_a)
	options['Dual Touch Demo B'] = lambda: test_ribbon_dual_touch(ribbon_b)

	widgets.run_select_subroutine(options)

ribbon_a=Ribbon('a',rib_a_mid,ads_a,ads_a_single,ads_a_dual_top,ads_a_dual_b)
ribbon_b=Ribbon('b',rib_b_mid,ads_b,ads_b_single,ads_b_dual_top,ads_b_dual_b)
