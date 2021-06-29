import board
import busio
from urp import *
from linear_modules import *
import lightboard.display as display
import lightboard.buttons as buttons
from lightboard.config import config

calibration_weight_address='load_cell calibration weight'

uart =busio.UART(board.D29, board.D28, baudrate=115200, timeout=1000*(1/115200),receiver_buffer_size=512) #Make timeout as small as possible without accidently not reading the whole line...


uart_stopwatch=Stopwatch()
UART_INTERVAL=1/80/2 #How often should we poll the Nano? (It should output a message 80 times a second)
print=lambda *x:0
class LoadCellFilter:
	def __init__(self):
		self.soft_tether=SoftTether(10000)
		self.value=0
	def __call__(self,value):
		# value=self.soft_tether(value)
		self.value=value
		return value

class LoadCellCalibration:
	def __init__(self,load_cell):
		self.load_cell=load_cell

		#The following two values should be calibrated; they shouldn't actually be 0 and 1 (0 and 1 are just placeholder values here)
		self.raw_tare_value=0
		self.grams_per_raw_value=1

	def get_precise_raw_reading(self,message:str):
		countdown_time=7
		countdown_stopwatch=Stopwatch()
		sampling_delay=2 #When you press the button, you wobble the lightwave. Wait till the wobbling is finished before sampling the weight.
		assert sampling_delay<=countdown_time,'The sampling_delay is part of the countdown_time'
		raw_total=0
		raw_count=0

		while countdown_stopwatch.toc()<countdown_time:
			text=message+'\n\nCountdown:\n    '+str(int(countdown_time-countdown_stopwatch.toc()))+' seconds'
			num_lines=text.count('\n')+1
			do_sampling=countdown_stopwatch.toc()>sampling_delay
			colors=[0xFFFFFF]*(num_lines-1)+[0x44FF88 if do_sampling else 0xFF8800]
			if do_sampling:
				raw_total+=self.load_cell.raw_value
				raw_count+=1
			display.set_menu(text.split('\n'),colors=colors)

		return raw_total/raw_count

	def run_calibration(self,grams):
		#grams represents the weight of the object that we use to calibrate the load cell
		with display.TemporarySetText('Please take all weight off \nload cell '+repr(self.load_cell.name)+'\nThen press green button 1'):
			with buttons.TemporaryMetalButtonLights(0,0,0):
				with buttons.TemporaryGreenButtonLights(1,0,0,0):
					while not buttons.green_1_press_viewer.value:pass
					buttons.green_button_1.light=False

					self.raw_tare_value=self.get_precise_raw_reading('Please don\'t wobble the lightwave!\nPreparing to calibrate (taring...)\n'+repr(self.load_cell.name))
					display.set_text('Taring complete! Please put your\n'+str(grams)+' gram weight on load cell\n'+repr(self.load_cell.name)+'\nThen press the green button')

					buttons.green_button_1.light=True
					while not buttons.green_1_press_viewer.value:pass
					buttons.green_button_1.light=False

					raw_weighed_value=self.get_precise_raw_reading('Please don\'t wobble the lightwave!\nPreparing to calibrate ('+str(grams)+' grams...)\n'+repr(self.load_cell.name))
					display.set_text('Weighing complete!')

					self.grams_per_raw_value=grams/(raw_weighed_value-self.raw_tare_value)
					display.set_text('Weighing complete!')
					self.run_test()

	def run_test(self):
		movmean=MovingAverage(10)
		buttons.green_button_1.light=True
		while not buttons.green_1_press_viewer.value:
			tic()
			value=self(self.load_cell.raw_value)
			value=movmean(value)
			display.set_text(str(value))
			# ptoc()
		buttons.green_button_1.light=False

	def __call__(self,raw_value):
		return (raw_value-self.raw_tare_value)*self.grams_per_raw_value

class LoadCell:
	def __init__(self,name:str):
		self.filter=LoadCellFilter()
		self.calibration=LoadCellCalibration(self)
		self._raw_value=0
		self.name=name

	@property
	def raw_value(self):
		refresh()
		return self._raw_value
	
	@raw_value.setter
	def raw_value(self,value):
		self._raw_value=value
		self.filter(value)

	@property
	def value(self):
		refresh()
		return self.filter.value

	def __repr__(self):
		return self.name

top_left =LoadCell('1: Top Left'    )
top_right=LoadCell('2: Top Right'   )
mid_left =LoadCell('3: Middle Left' )
mid_right=LoadCell('4: Middle Right')
bot_left =LoadCell('5: Bottom Left' )
bot_right=LoadCell('6: Bottom Right')


load_cells=[top_left,top_right,
            mid_left,mid_right,
            bot_left,bot_right]

SILENT_ERRORS=True

def error_blink():
	colors=[(0,0,1),(0,1,0),(1,0,0)]
	if buttons.metal_button.color not in colors:
		buttons.metal_button.color=(0,0,1)
	else:
		color=buttons.metal_button.color
		color=colors[(colors.index(color)+1)%len(colors)]
		buttons.metal_button.color=color

last_message=None
raw_weights=[0]*6
raw_imu    =[0]*6
def refresh():
	#TODO: We need an explanation for why using readline twice seems to make everything ok. Maybe we don't need to make a complex stateful parser?
	if uart_stopwatch.toc()<UART_INTERVAL:
		return
	global last_message,raw_weights,raw_imu
	# tic()
	data = uart.readline() #For some reason, calling readline twice avoids parsing errors. 
	data = uart.readline() #I'm not entirely sure why, but the average time it takes to do it twice is about 0.0004883 seconds, so it seems fine...
	# data = uart.readline() #I'm not entirely sure why, but the average time it takes to do it twice is about 0.0004883 seconds, so it seems fine...
	# data = uart.readline() #I'm not entirely sure why, but the average time it takes to do it twice is about 0.0004883 seconds, so it seems fine...
	# data = uart.readline() #I'm not entirely sure why, but the average time it takes to do it twice is about 0.0004883 seconds, so it seems fine...
	# ptoc()
	if data is not None:
		uart_stopwatch.tic()
		try:
			last_message=data.decode().strip()
			#Should look like:
			#	last_message=">,-178070,-251194,-64062,185960,50025,-168551,0.6081,-0.5267,8.9232,0.0580,0.0112,0.0548,<"
			assert last_message.count(',')==6*2-1+2,'Failed Commacount: '+repr(last_message)#'There should be 12 comma-separated values', otherwise we likely misread the NANO's message
			assert last_message[0]=='>' and last_message[-1]=='<','Failed ><: '+repr(last_message)
		except Exception as e:
			if not SILENT_ERRORS:
				print("Nano UART Error:",str(e))
			display.set_text('+++++++++++++\n\n\n'+str(len(data))+'\n'+str(e))
			error_blink()
			return #Eager to give up if something goes wrong, which happens occasionally...don't sweat it when it does, we'll get another message in 1/80 seconds from now...
		else:
			try:
				split_message=last_message.split(',')
				new_raw_weights=list(map(int  ,split_message[1:1+6]))
				new_raw_imu    =list(map(float,split_message[1+6:-1]))#This returns 6 numbers, but honesltly I don't know which number correponds to which (and actually, we don't need to - all that matters is that it contains X,Y,Z for both the gyroscope and the accelerometer)
				raw_weights=new_raw_weights
				raw_imu    =new_raw_imu

				for raw_weight,load_cell in zip(raw_weights,load_cells):
					load_cell.raw_value=raw_weight
				# print(*load_cells)
				# print([bool(abs(x.raw_value)>10000) for x in load_cells]) 
			except Exception as e:
				if not SILENT_ERRORS:
					print_error("Nano Parsing Error:",str(e))
				display.set_text(str(len(data))+'\nParse\n'+str(e))
				error_blink()
				return
	elif not data:
		error_blink()
		display.set_text("XXXXXXXX")

calibration_weight_address='load_cell calibration weight'

def get_calibration_weight():
	if calibration_weight_address not in config:
		config[calibration_weight_address]=250
	return config[calibration_weight_address]

def input_set_calibration_weight():
	import lightboard.widgets as widgets
	try:
		config[calibration_weight_address]=widgets.input_integer(get_calibration_weight(),prompt='Enter calibration weight:')
	except KeyboardInterrupt:
		pass

def show_calibration_menu():
	import lightboard.display as display
	import lightboard.buttons as buttons
	import lightboard.widgets as widgets

	test_cell     ='Test Load Cell'
	calibrate_cell='Calibrate Load Cell'
	set_weight    ='Set Calibration Weight'

	while True:
		task=widgets.input_select([calibrate_cell,test_cell,set_weight],prompt='What do you want to do?',can_cancel=True,must_confirm=False,confirm_cancel=False)
		if task==calibrate_cell or task==test_cell:
			try:
				while True:
					load_cell=widgets.input_select(load_cells,prompt='Calibration:\nSelect a load cell',can_cancel=True,must_confirm=False,confirm_cancel=False)
					if task==calibrate_cell:
						load_cell.calibration.run_calibration(get_calibration_weight())
					else:
						assert task==test_cell
						load_cell.calibration.run_test()
			except KeyboardInterrupt:
				pass
		elif task==set_weight:
			input_set_calibration_weight()
		else:
			assert False,'Internal logical error: invalid task'
bot_right.calibration.run_test()
show_calibration_menu()

while True:
	tic()
	refresh()