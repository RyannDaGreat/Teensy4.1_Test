#PINS:
#	ADS1115 A0: Single Touch
#	ADS1115 A1: Double Touch A
#	ADS1115 A2: Double Touch B
#	GPIO 12: Single Touch Pullup/Pulldown (Alternates between HIGH and LOW)
#	GPIO 11: Single Touch NPN Transistor (HIGH to activate)
#	GPIO 10: Dual   Touch NPN Transistor (HIGH to activate)
#	GPIO  9: Dual   Touch PNP Transistor (LOW  to activate)

from urp import *
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn
from digitalio import DigitalInOut, Direction, Pull

if 'i2c' not in dir():
	i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)# Create the I2C bus with a fast frequency

ads = ADS.ADS1115(i2c)

ads.data_rate = 860 #Maximum frequency of ADS1115 in Hz

ads_gain_single=1
ads_gain_dual  =8 #Uses 100kΩ
ads.gain=ads_gain_single #Change this depending on whether you're measuring dual or single

ads_a0 = AnalogIn(ads, ADS.P0)
ads_a1 = AnalogIn(ads, ADS.P1)
ads_a2 = AnalogIn(ads, ADS.P2)
ads_single=ads_a0
ads_dual_a=ads_a1
ads_dual_b=ads_a2

single_pull=DigitalInOut(board.D12)
single_npn =DigitalInOut(board.D11)
dual_npn   =DigitalInOut(board.D10)
dual_pnp   =DigitalInOut(board.D9 )
single_pull.direction=Direction.OUTPUT
single_npn .direction=Direction.OUTPUT
dual_npn   .direction=Direction.OUTPUT
dual_pnp   .direction=Direction.OUTPUT

def activate_single_transistors():
	single_npn.value=False
	dual_pnp  .value=False
	dual_npn  .value=True

def activate_dual_transistors():
	single_npn.value=True
	dual_pnp  .value=True
	dual_npn  .value=False

class CheapSingleTouchReading:
	#TODO: Implement a variation of the SingleTouchReading class called quick-gate check via the Teensy's internal ADC to save a bit of time and get more accurate results on the dual touch readings (because then we can check both upper and lower both before and after the dual readings which means less spikes)
	pass

class SingleTouchReading:
	GATE_THRESHOLD=500 #This needs to be calibrated after observing the raw_gap when touching and not touching the ribbon. You can do this automatically with some fancy algorithm, or you can just look at the serial monitor while printing reading.raw_gap over and over again

	def __init__(self):
		self.read_raw_lower()
		self.read_raw_upper()
		self.process_readings()
		
	@staticmethod
	def prepare_to_read():
		activate_single_transistors()
		ads.gain=ads_gain_single

	def read_raw_lower(self):
		SingleTouchReading.prepare_to_read()
		single_pull.value=False
		self.raw_lower=ads_single.value

	def read_raw_upper(self):
		SingleTouchReading.prepare_to_read()
		single_pull.value=True
		self.raw_upper=ads_single.value

	def process_readings(self):
		self.raw_gap=abs(self.raw_upper-self.raw_lower)
		self.gate=self.raw_gap<SingleTouchReading.GATE_THRESHOLD
		self.raw_value=(self.raw_upper+self.raw_lower)/2

class DualTouchReading:
	@staticmethod
	def prepare_to_read():
		activate_dual_transistors()
		ads.gain=ads_gain_dual

	def __init__(self):
		DualTouchReading.prepare_to_read()
		self.raw_a=ads_dual_a.value
		self.raw_b=ads_dual_b.value

while True:
	single_before=SingleTouchReading()
	dual=DualTouchReading()
	single_after=SingleTouchReading()

	if single_before.gate and single_after.gate: #TODO: Implement CheapSingleTouchReading so we can run nearly 3x as fast
		print(single_before.raw_value,
		      single_after.raw_value,
		      (single_before.raw_value+single_after.raw_value)/2,
		      dual.raw_a,
		      2**15-dual.raw_b)
