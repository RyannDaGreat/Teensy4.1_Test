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

class SingleTouchReading:
	GATE_THRESHOLD=500 #This needs to be calibrated after observing the raw_gap when touching and not touching the ribbon. You can do this automatically with some fancy algorithm, or you can just look at the serial monitor while printing reading.raw_gap over and over again
	def __init__(self):
		activate_single_transistors()
		single_pull.value=True
		self.raw_upper=ads_single.value
		single_pull.value=False
		self.raw_lower=ads_single.value

		self.raw_gap=abs(self.raw_upper-self.raw_lower)
		self.gate=self.raw_gap<SingleTouchReading.GATE_THRESHOLD

		self.raw_value=(self.raw_upper+self.raw_lower)/2

while True:
	single=SingleTouchReading()
	print(single.raw_gap)
	# print(single.raw_upper)
	# print(single.raw_lower)
	# print(single.raw_value)